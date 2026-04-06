# Remove duplicate project items (same title): keeps lowest issue #, removes others from the project.
# Run from repo root. Requires GITHUB_TOKEN with project scope.

param([switch]$WhatIf)

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
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id } } }'; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $projectId = $data.user.projectV2.id
} else {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id } } }'; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $projectId = $data.repository.projectV2.id
}
if (-not $projectId) { Write-Error "Project not found." }

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

$byTitle = @{}
foreach ($it in $items) {
    $t = $it.title
    if (-not $byTitle[$t]) { $byTitle[$t] = @() }
    $byTitle[$t] += $it
}

$toRemove = @()
foreach ($entry in $byTitle.GetEnumerator()) {
    if ($entry.Value.Count -le 1) { continue }
    $list = $entry.Value | Sort-Object { $_.issueNumber }
    for ($i = 1; $i -lt $list.Count; $i++) {
        $toRemove += $list[$i]
    }
}

if ($toRemove.Count -eq 0) {
    Write-Host "No duplicate project items to remove." -ForegroundColor Green
    exit 0
}

Write-Host "Removing $($toRemove.Count) duplicate items from project..." -ForegroundColor Cyan
if ($WhatIf) {
    foreach ($it in $toRemove) { Write-Host "  Would remove: #$($it.issueNumber) ($($it.title.Substring(0, [Math]::Min(50, $it.title.Length)))...)" -ForegroundColor Yellow }
    Write-Host "Run without -WhatIf to remove." -ForegroundColor Gray
    exit 0
}

$deleteMutation = 'mutation($input: DeleteProjectV2ItemInput!) { deleteProjectV2Item(input: $input) { deletedItemId } }'
$removed = 0
foreach ($it in $toRemove) {
    try {
        Invoke-GitHubGraphQL -Payload @{ query = $deleteMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId } } } -Token $token | Out-Null
        $removed++
        Write-Host "  Removed #$($it.issueNumber) from project" -ForegroundColor Green
    } catch {
        Write-Host "  Failed to remove #$($it.issueNumber): $_" -ForegroundColor Red
    }
}
Write-Host "Done. Removed $removed duplicate items from project." -ForegroundColor Green
