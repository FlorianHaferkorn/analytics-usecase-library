# Set Status, Milestone, Area, Priority, Risk on existing project items.
# If the project is missing these fields, they are created via GitHub API (createProjectV2Field).
# Token: set GITHUB_TOKEN or use .env in repo root (see .env.example). Run from repo root.

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
function Invoke-GitHubRest { param([string]$Method, [string]$Path, [object]$Body = $null, [string]$Token)
    $h = @{ "Authorization" = "Bearer $Token"; "Accept" = "application/vnd.github+json"; "X-GitHub-Api-Version" = "2022-11-28" }; $uri = "https://api.github.com$Path"
    $p = @{ Method = $Method; Uri = $uri; Headers = $h }; if ($Body) { $p["Body"] = ($Body | ConvertTo-Json -Depth 6 -Compress); $p["ContentType"] = "application/json" }; return Invoke-RestMethod @p
}
function Invoke-GitHubGraphQL { param([hashtable]$Payload, [string]$Token)
    $r = Invoke-RestMethod -Method Post -Uri "https://api.github.com/graphql" -Headers @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" } -Body ([System.Text.Encoding]::UTF8.GetBytes(($Payload | ConvertTo-Json -Depth 15 -Compress)))
    if ($r.errors) { Write-Error ("GraphQL: " + ($r.errors | ConvertTo-Json -Compress)) }; return $r.data
}

$token = Get-GitHubToken
$repo = Get-RepoOwnerAndName
$owner = $repo.owner; $name = $repo.name
$projectNumber = 1; if ($env:PROJECT_NUMBER) { $projectNumber = [int]$env:PROJECT_NUMBER }
Write-Host "Repo: $owner/$name | Project: $projectNumber" -ForegroundColor Cyan

# 1) Get project + fields
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

# Standard field definitions (match PROJECT_FIELDS_AND_LABELS.md)
$requiredFields = @(
    @{ name = "Status"; options = @("Backlog", "Planned", "In progress", "In review", "Done") },
    @{ name = "Milestones"; options = @("Project completion", "Framework Package 1", "Phase 2", "Technical backlog") },
    @{ name = "Area"; options = @("Framework", "FabricPowerBI", "Aurora", "Tooling", "Docs") },
    @{ name = "Priority"; options = @("P0", "P1", "P2") },
    @{ name = "Risk"; options = @("On track", "At risk") }
)
$createFieldMutation = 'mutation($input: CreateProjectV2FieldInput!) { createProjectV2Field(input: $input) { projectV2Field { ... on ProjectV2SingleSelectField { id name options { id name } } } } }'
$created = 0
foreach ($def in $requiredFields) {
    $hasField = $fieldMap[$def.name]
    if (-not $hasField) {
        foreach ($k in $fieldMap.Keys) { if ($k -eq $def.name) { $hasField = $fieldMap[$k]; break } }
    }
    if (-not $hasField) {
        # GitHub API requires color and description per option (non-null). Color: BLUE, GRAY, GREEN, ORANGE, PINK, PURPLE, RED, YELLOW.
        $optInputs = @($def.options | ForEach-Object { @{ name = $_; description = ""; color = "GRAY" } })
        $fieldInput = @{ projectId = $projectId; name = $def.name; dataType = "SINGLE_SELECT"; singleSelectOptions = $optInputs }
        try {
            $out = Invoke-GitHubGraphQL -Payload @{ query = $createFieldMutation; variables = @{ input = $fieldInput } } -Token $token
            $created++; Write-Host "Created field: $($def.name)" -ForegroundColor Green
        } catch {
            if ($_.Exception.Message -match "already been taken|reserved value") {
                Write-Host "Field '$($def.name)' already exists or is reserved, skipping create." -ForegroundColor Yellow
            } else { throw }
        }
    }
}
# Re-fetch fields after create attempts so we see existing or newly created single-select fields
$fieldMap = @{}
if ($scope -eq "user") {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $proj = $data.user.projectV2
} else {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $proj = $data.repository.projectV2
}
foreach ($node in $proj.fields.nodes) {
    if ($node.__typename -eq "ProjectV2SingleSelectField" -and $node.options) { $opts = @{}; foreach ($o in $node.options) { $opts[$o.name] = $o.id }; $fieldMap[$node.name] = @{ id = $node.id; options = $opts } }
}

# Case-insensitive lookup; accept "Milestones" if project uses plural
$fieldMapByLower = @{}; foreach ($k in $fieldMap.Keys) { $fieldMapByLower[$k.ToLower()] = $fieldMap[$k] }
$statusF = $fieldMap["Status"]; if (-not $statusF) { $statusF = $fieldMapByLower["status"] }
$milestoneF = $fieldMap["Milestone"]; if (-not $milestoneF) { $milestoneF = $fieldMapByLower["milestone"] }; if (-not $milestoneF) { $milestoneF = $fieldMap["Milestones"] }; if (-not $milestoneF) { $milestoneF = $fieldMapByLower["milestones"] }
$areaF = $fieldMap["Area"]; if (-not $areaF) { $areaF = $fieldMapByLower["area"] }
$priorityF = $fieldMap["Priority"]; if (-not $priorityF) { $priorityF = $fieldMapByLower["priority"] }
$riskF = $fieldMap["Risk"]; if (-not $riskF) { $riskF = $fieldMapByLower["risk"] }
if (-not ($statusF -and $milestoneF -and $areaF -and $priorityF)) {
    $found = @($fieldMap.Keys); if ($found.Count -eq 0) { $found = @("(none - only Single select fields are read)") }
    Write-Host "Required fields Status, Milestone, Area, Priority not found. Single-select fields on this project: $($found -join ', ')" -ForegroundColor Yellow
    Write-Error "Add fields in Project Settings: Status, Milestones (or Milestone), Area, Priority (see internal/project_mgmt/SETUP_PROJECT_FIELDS.md)."
}

# 2) Build issue number -> milestone, area, priority from repo issues (with milestone)
$issueMeta = @{}
$page = 1; $perPage = 100
do {
    $list = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/issues?state=all&per_page=$perPage&page=$page" -Token $token
    foreach ($iss in $list) {
        if ($iss.number -and $iss.body -match '\*\*Milestone:\*\*\s*([^|]+)\s*\|\s*\*\*Area:\*\*\s*([^|]+)\s*\|\s*\*\*Priority:\*\*\s*(\S+)') {
            $issueMeta[$iss.number] = @{ milestone = $Matches[1].Trim(); area = $Matches[2].Trim(); priority = $Matches[3].Trim() }
        } elseif ($iss.milestone) {
            $issueMeta[$iss.number] = @{ milestone = $iss.milestone.title; area = "Tooling"; priority = "P2" }
        }
    }
    $page++; if ($list.Count -lt $perPage) { break }
} while ($list.Count -eq $perPage)

# 3) Get all project items (paginated)
$items = @(); $cursor = $null
do {
    $q = 'query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) { nodes { id content { ... on Issue { number } } } pageInfo { endCursor hasNextPage } } } } }'
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $q; variables = $vars } -Token $token
    $n = $out.node.items; foreach ($i in $n.nodes) { if ($i.content.number) { $items += @{ itemId = $i.id; issueNumber = $i.content.number } } }; $cursor = $n.pageInfo.endCursor; if (-not $n.pageInfo.hasNextPage) { break }
} while ($cursor)

Write-Host "Project items: $($items.Count). Setting fields..." -ForegroundColor Cyan
$updateMutation = 'mutation($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } } }'
$set = 0
foreach ($it in $items) {
    $meta = $issueMeta[$it.issueNumber]
    if (-not $meta) { Write-Host "  #$($it.issueNumber): no milestone/area in body, skip" -ForegroundColor Gray; continue }
    if ($statusF.options["Backlog"]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $statusF.id; value = @{ singleSelectOptionId = $statusF.options["Backlog"] } } } } -Token $token | Out-Null }
    if ($milestoneF.options[$meta.milestone]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $milestoneF.id; value = @{ singleSelectOptionId = $milestoneF.options[$meta.milestone] } } } } -Token $token | Out-Null }
    if ($areaF.options[$meta.area]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $areaF.id; value = @{ singleSelectOptionId = $areaF.options[$meta.area] } } } } -Token $token | Out-Null }
    if ($priorityF.options[$meta.priority]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $priorityF.id; value = @{ singleSelectOptionId = $priorityF.options[$meta.priority] } } } } -Token $token | Out-Null }
    if ($riskF -and $riskF.options["On track"]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId; fieldId = $riskF.id; value = @{ singleSelectOptionId = $riskF.options["On track"] } } } } -Token $token | Out-Null }
    $set++; Write-Host "  #$($it.issueNumber) -> $($meta.milestone) / $($meta.area) / $($meta.priority)"
}
Write-Host "Done. Set fields on $set items." -ForegroundColor Green
