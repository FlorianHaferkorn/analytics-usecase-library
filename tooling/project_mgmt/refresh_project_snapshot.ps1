# Read Backlog/Planned items from the GitHub Project (no status change). Write PROJECT_SNAPSHOT.md
# so the Assistant Agent can use it for daily briefings. Run from repo root.
# Same env as start_next_task.ps1.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_project_env.ps1"

function Get-GitHubToken {
    $t = $env:GITHUB_TOKEN; if (-not $t) { $t = $env:GH_TOKEN }; if (-not $t) { try { $t = (gh auth token 2>$null) } catch {} }
    if (-not $t) { Write-Error "Set GITHUB_TOKEN (repo + project scope)." }; return $t
}
function Get-RepoOwnerAndName {
    if ($env:GITHUB_REPOSITORY -match "^([^/]+)/(.+)$") { return @{ owner = $Matches[1]; name = $Matches[2] } }
    $r = (git config --get remote.origin.url 2>$null); if ($r -match "github\.com[:/]([^/]+)/([^/.]+)") { return @{ owner = $Matches[1]; name = ($Matches[2] -replace "\.git$", "") } }
    Write-Error "Set GITHUB_REPOSITORY or run from git repo with origin."
}
function Get-RepoRoot {
    $d = $PSScriptRoot
    while ($d -and -not (Test-Path (Join-Path $d ".git") -PathType Container)) { $d = Split-Path -Parent $d }
    if (-not $d) { Write-Error "Repo root not found." }; return $d
}
function Invoke-GitHubGraphQL { param([hashtable]$Payload, [string]$Token)
    $r = Invoke-RestMethod -Method Post -Uri "https://api.github.com/graphql" -Headers @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" } -Body ([System.Text.Encoding]::UTF8.GetBytes(($Payload | ConvertTo-Json -Depth 15 -Compress)))
    if ($r.errors) { Write-Error ("GraphQL: " + ($r.errors | ConvertTo-Json -Compress)) }; return $r.data
}

$token = Get-GitHubToken
$repo = Get-RepoOwnerAndName
$owner = $repo.owner; $name = $repo.name
$projectNumber = 1; if ($env:PROJECT_NUMBER) { $projectNumber = [int]$env:PROJECT_NUMBER }
$scope = "repo"; if ($env:PROJECT_SCOPE) { $scope = $env:PROJECT_SCOPE }; $scope = $scope.ToLower()

if ($scope -eq "user") {
    $projectOwner = $owner; if ($env:PROJECT_OWNER) { $projectOwner = $env:PROJECT_OWNER }
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $proj = $data.user.projectV2
} else {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $proj = $data.repository.projectV2
}
if (-not $proj) { Write-Error "Project not found." }
$projectId = $proj.id

$itemQuery = @'
query($id: ID!, $after: String) {
  node(id: $id) {
    ... on ProjectV2 {
      items(first: 100, after: $after) {
        nodes {
          id
          content { ... on Issue { number title } }
          fieldValues(first: 10) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
            }
          }
        }
        pageInfo { endCursor hasNextPage }
      }
    }
  }
}
'@

$candidates = @(); $cursor = $null
do {
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $itemQuery; variables = $vars } -Token $token
    $items = $out.node.items
    foreach ($node in $items.nodes) {
        $statusVal = $null; $priorityVal = $null; $areaVal = $null
        foreach ($fv in $node.fieldValues.nodes) {
            if ($fv.field.name -eq "Status") { $statusVal = $fv.name }
            if ($fv.field.name -eq "Priority") { $priorityVal = $fv.name }
            if ($fv.field.name -eq "Area") { $areaVal = $fv.name }
        }
        if ($statusVal -in @("Backlog", "Planned")) {
            $candidates += @{ issueNumber = $node.content.number; title = $node.content.title; priority = $priorityVal; area = $areaVal }
        }
    }
    $cursor = $items.pageInfo.endCursor; if (-not $items.pageInfo.hasNextPage) { break }
} while ($cursor)

$priorityOrder = @{ P0 = 0; P1 = 1; P2 = 2 }
$candidates = $candidates | Sort-Object { if ($null -eq $_.priority -or -not $priorityOrder.ContainsKey($_.priority)) { 99 } else { $priorityOrder[$_.priority] } }, { $_.issueNumber }

$repoRoot = Get-RepoRoot
$snapshotPath = Join-Path $repoRoot "internal\project_mgmt\PROJECT_SNAPSHOT.md"
$date = Get-Date -Format "yyyy-MM-dd HH:mm"

$lines = @(
    "# Project snapshot (Backlog / Planned)",
    "",
    "**Generated:** $date - use for daily briefing. Refresh with .\tooling\project_mgmt\refresh_project_snapshot.ps1.",
    ""
)
if ($candidates.Count -eq 0) {
    $lines += "No items in Backlog or Planned."
    $lines += ""
    $lines += "**Recommended next:** None. Add issues to the project or move items to Backlog first."
} else {
    $lines += "## Recommended next (by priority)"
    $first = $candidates[0]
    $expert = "Implementer (general)"
    $expertRulePath = ""
    if ($first.area -eq "FabricPowerBI" -or $first.area -eq "Aurora") { $expert = "Fabric-Expert"; $expertRulePath = "docs/agent/rules/fabric-expert.md" }
    elseif ($first.area -eq "Framework") { $expert = "Framework-Expert"; $expertRulePath = "docs/agent/rules/framework-expert.md" }
    $lines += ""
    $lines += "| # | Title | Priority | Area | Expert |"
    $lines += "|---|-------|----------|------|--------|"
    $lines += "| $($first.issueNumber) | $($first.title) | $($first.priority) | $($first.area) | $expert |"
    $lines += ""
    if ($expertRulePath) { $lines += "**Expert rule:** $expertRulePath"; $lines += "" }
    $lines += "**To start this task:**"
    $lines += "1. Run: .\tooling\project_mgmt\start_next_task.ps1"
    $lines += "2. In an Implementer session say: **Implement issue #$($first.issueNumber)**"
    $lines += ""
    $lines += "## All Backlog / Planned (sorted)"
    $lines += ""
    $lines += "| # | Title | Priority | Area |"
    $lines += "|---|-------|----------|------|"
    foreach ($c in $candidates) {
        $lines += "| $($c.issueNumber) | $($c.title) | $($c.priority) | $($c.area) |"
    }
}
$lines += ""
$lines += "---"
$lines += "*Do not edit this file by hand; it is overwritten by refresh_project_snapshot.ps1.*"

$content = $lines -join "`r`n"
[System.IO.File]::WriteAllText($snapshotPath, $content, [System.Text.UTF8Encoding]::new($false))
Write-Host "Wrote $snapshotPath" -ForegroundColor Green
if ($candidates.Count -gt 0) {
    Write-Host "Recommended next: #$($candidates[0].issueNumber) - $($candidates[0].title)" -ForegroundColor Cyan
}
