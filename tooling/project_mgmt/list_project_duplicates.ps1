# List project items with duplicate titles (same title = duplicate).
# Output: for each duplicate group, which issue numbers to KEEP (lowest) and which to REMOVE from project.
# Run from repo root. Requires GITHUB_TOKEN and project with fields.

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

# Resolve project ID
if ($scope -eq "user") {
    $projectOwner = $owner; if ($env:PROJECT_OWNER) { $projectOwner = $env:PROJECT_OWNER }
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id } } }'; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $projectId = $data.user.projectV2.id
} else {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id } } }'; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $projectId = $data.repository.projectV2.id
}
if (-not $projectId) { Write-Error "Project not found." }

# Fetch all project items with issue number and title
$items = @(); $cursor = $null
do {
    $q = 'query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) { nodes { id content { ... on Issue { number title } } } pageInfo { endCursor hasNextPage } } } } }'
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $q; variables = $vars } -Token $token
    $n = $out.node.items
    foreach ($i in $n.nodes) {
        if ($i.content.number -and $i.content.title) {
            $items += @{ itemId = $i.id; issueNumber = $i.content.number; title = $i.content.title }
        }
    }
    $cursor = $n.pageInfo.endCursor; if (-not $n.pageInfo.hasNextPage) { break }
} while ($cursor)

# Group by title (exact match)
$byTitle = @{}
foreach ($it in $items) {
    $t = $it.title
    if (-not $byTitle[$t]) { $byTitle[$t] = @() }
    $byTitle[$t] += $it
}

$duplicates = $byTitle.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 }
if ($duplicates.Count -eq 0) {
    Write-Host "No duplicate titles in project. Total items: $($items.Count)" -ForegroundColor Green
    exit 0
}

Write-Host "Duplicate titles (keep lowest issue #, remove others from project):" -ForegroundColor Yellow
Write-Host ""
foreach ($d in $duplicates) {
    $list = $d.Value | Sort-Object { $_.issueNumber }
    $keep = $list[0].issueNumber
    $remove = $list[1..($list.Count - 1)] | ForEach-Object { $_.issueNumber }
    $tit = $d.Key; if ($tit.Length -gt 70) { $tit = $tit.Substring(0, 70) + "..." }
    Write-Host "Title: $tit" -ForegroundColor Cyan
    Write-Host "  KEEP:  #$keep" -ForegroundColor Green
    Write-Host "  REMOVE from project (or close): $($remove -join ', #')" -ForegroundColor Red
    Write-Host ""
}

Write-Host "To remove duplicates: In GitHub Project, remove the listed issues from the project (right-click item -> Remove from project), or close the duplicate issues in the Issues tab." -ForegroundColor Gray
