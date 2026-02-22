# Set Status for one or more GitHub issues on the Project.
# Usage: .\set_issue_status.ps1 -Issue 23 -Status "In progress"
#        .\set_issue_status.ps1 -Issue 23,24 -Status "Done"
# Same env as set_project_fields_only.ps1 (.env or GITHUB_TOKEN, PROJECT_NUMBER, PROJECT_SCOPE, PROJECT_OWNER). Run from repo root.

param(
    [Parameter(Mandatory = $true)]
    [int[]]$Issue,
    [Parameter(Mandatory = $true)]
    [ValidateSet("Backlog", "Planned", "In progress", "In review", "Done")]
    [string]$Status
)

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
$statusOptionId = $statusF.options[$Status]; if (-not $statusOptionId) { Write-Error "Status value '$Status' not found. Options: $($statusF.options.Keys -join ', ')." }

$items = @(); $cursor = $null
do {
    $q = 'query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) { nodes { id content { ... on Issue { number } } } pageInfo { endCursor hasNextPage } } } } }'
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $q; variables = $vars } -Token $token
    $n = $out.node.items; foreach ($i in $n.nodes) { if ($i.content.number) { $items += @{ itemId = $i.id; issueNumber = $i.content.number } } }; $cursor = $n.pageInfo.endCursor; if (-not $n.pageInfo.hasNextPage) { break }
} while ($cursor)

$issueSet = @{}; foreach ($num in $Issue) { $issueSet[$num] = $true }
$updateMutation = 'mutation($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } } }'
$updated = 0
foreach ($it in $items) {
    if (-not $issueSet[$it.issueNumber]) { continue }
    Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $statusF.id; value = @{ singleSelectOptionId = $statusOptionId } } } } -Token $token | Out-Null
    $updated++; Write-Host "Issue #$($it.issueNumber) -> Status = $Status" -ForegroundColor Green
}
if ($updated -eq 0) { Write-Warning "No project items found for issue(s): $($Issue -join ', '). They may not be on the project." }
Write-Host "Updated $updated item(s)." -ForegroundColor Cyan
