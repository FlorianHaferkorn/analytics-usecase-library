# Pick the next task from the Project (Status = Backlog or Planned), set it to "In progress", and output issue number and recommended expert.
# Use this so the PM flow is: Backlog -> (this script) In progress -> Implementer works on the printed issue.
# Same env as set_project_fields_only.ps1. Run from repo root.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Load-ProjectEnv.ps1"

function Get-GitHubToken {
    $t = $env:GITHUB_TOKEN; if (-not $t) { $t = $env:GH_TOKEN }; if (-not $t) { try { $t = (gh auth token 2>$null) } catch {} }
    if (-not $t) { Write-Error "Set GITHUB_TOKEN (repo + project scope)." }; return $t
}
function Get-RepoOwnerAndName {
    if ($env:GITHUB_REPOSITORY -match "^([^/]+)/(.+)$") { return @{ owner = $Matches[1]; name = $Matches[2] } }
    $r = (git config --get remote.origin.url 2>$null); if ($r -match "github\.com[:/]([^/]+)/([^/.]+)") { return @{ owner = $Matches[1]; name = ($Matches[2] -replace "\.git$", "") } }
    Write-Error "Set GITHUB_REPOSITORY or run from git repo with origin."
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

# Query project: id and fields (Status, Priority)
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
$fieldMap = @{}; foreach ($node in $proj.fields.nodes) {
    if ($node.__typename -eq "ProjectV2SingleSelectField" -and $node.options) { $opts = @{}; foreach ($o in $node.options) { $opts[$o.name] = $o.id }; $fieldMap[$node.name] = @{ id = $node.id; options = $opts } }
}
$fieldMapByLower = @{}; foreach ($k in $fieldMap.Keys) { $fieldMapByLower[$k.ToLower()] = $fieldMap[$k] }
$statusF = $fieldMap["Status"]; if (-not $statusF) { $statusF = $fieldMapByLower["status"] }
if (-not $statusF) { Write-Error "Project has no Status field." }
$inProgressId = $statusF.options["In progress"]; if (-not $inProgressId) { Write-Error "Status 'In progress' not found." }

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
            $candidates += @{ itemId = $node.id; issueNumber = $node.content.number; title = $node.content.title; priority = $priorityVal; area = $areaVal }
        }
    }
    $cursor = $items.pageInfo.endCursor; if (-not $items.pageInfo.hasNextPage) { break }
} while ($cursor)

if ($candidates.Count -eq 0) { Write-Host "No items in Backlog or Planned. Add issues to the project or move items to Backlog first." -ForegroundColor Yellow; exit 0 }

# Sort: P0 then P1 then P2, then by issue number (unknown priority = 99)
$priorityOrder = @{ P0 = 0; P1 = 1; P2 = 2 }; $candidates = $candidates | Sort-Object { if ($null -eq $_.priority -or -not $priorityOrder.ContainsKey($_.priority)) { 99 } else { $priorityOrder[$_.priority] } }, { $_.issueNumber }
$pick = $candidates[0]

# Set Status to In progress
$updateMutation = 'mutation($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } } }'
Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $pick.itemId; fieldId = $statusF.id; value = @{ singleSelectOptionId = $inProgressId } } } } -Token $token | Out-Null

$expert = "Implementer (general)"
if ($pick.area -eq "FabricPowerBI" -or $pick.area -eq "Aurora") { $expert = "Fabric-Expert" }
elseif ($pick.area -eq "Framework") { $expert = "Framework-Expert" }

Write-Host "Next task moved to In progress:" -ForegroundColor Green
Write-Host "  Issue #$($pick.issueNumber): $($pick.title)" -ForegroundColor Cyan
Write-Host "  Area: $($pick.area) | Priority: $($pick.priority) | Recommended expert: $expert" -ForegroundColor Gray
Write-Host ""
Write-Host "Open an Implementer session and say:" -ForegroundColor Yellow
Write-Host "  Implement issue #$($pick.issueNumber)" -ForegroundColor White
Write-Host ""
Write-Host "Issue number for scripts: $($pick.issueNumber)" -ForegroundColor Gray
