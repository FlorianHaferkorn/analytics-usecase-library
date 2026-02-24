# Full project setup: create granular milestones, labels, issues; add every issue
# to the GitHub Project and set Status, Milestone, Area, Priority, Risk.
# Token: set GITHUB_TOKEN or use .env in repo root (see .env.example). Run from repo root.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Load-ProjectEnv.ps1"

function Get-GitHubToken {
    $token = $env:GITHUB_TOKEN
    if (-not $token) { $token = $env:GH_TOKEN }
    if (-not $token) {
        try { $token = (gh auth token 2>$null) } catch {}
    }
    if (-not $token) { Write-Error "Set GITHUB_TOKEN or GH_TOKEN (repo + project scope). See internal/project_mgmt/WHAT_I_NEED.md." }
    return $token
}

function Get-RepoOwnerAndName {
    $repo = $env:GITHUB_REPOSITORY
    if ($repo -and $repo -match "/") { $p = $repo -split "/", 2; return @{ owner = $p[0]; name = $p[1] } }
    $remote = (git config --get remote.origin.url 2>$null)
    if ($remote -match "github\.com[:/]([^/]+)/([^/.]+)") { return @{ owner = $Matches[1]; name = ($Matches[2] -replace "\.git$", "") } }
    Write-Error "Set GITHUB_REPOSITORY to owner/repo or run from a git repo with origin pointing to GitHub."
}

function Invoke-GitHubRest {
    param([string]$Method, [string]$Path, [object]$Body = $null, [string]$Token)
    $headers = @{ "Authorization" = "Bearer $Token"; "Accept" = "application/vnd.github+json"; "X-GitHub-Api-Version" = "2022-11-28" }
    $uri = "https://api.github.com$Path"
    $params = @{ Method = $Method; Uri = $uri; Headers = $headers }
    if ($Body) { $params["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress); $params["ContentType"] = "application/json" }
    return Invoke-RestMethod @params
}

function Invoke-GitHubGraphQL {
    param([hashtable]$Payload, [string]$Token)
    $body = $Payload | ConvertTo-Json -Depth 15 -Compress
    $headers = @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" }
    $r = Invoke-RestMethod -Method Post -Uri "https://api.github.com/graphql" -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    if ($r.errors) { Write-Error ("GraphQL errors: " + ($r.errors | ConvertTo-Json -Compress)) }
    return $r.data
}

. "$PSScriptRoot\GranularIssues.ps1"

$token = Get-GitHubToken
$repo = Get-RepoOwnerAndName
$owner = $repo.owner
$name = $repo.name
$projectNumber = 1
if ($env:PROJECT_NUMBER) { $projectNumber = [int]$env:PROJECT_NUMBER }
Write-Host "Repo: $owner/$name | Project number: $projectNumber" -ForegroundColor Cyan

# 1. Milestones
Write-Host "`n1. Milestones" -ForegroundColor Cyan
$existingMs = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/milestones?state=all" -Token $token
$byTitle = @{}
foreach ($m in $existingMs) { $byTitle[$m.title] = $m.number }
$milestones = @{}
foreach ($title in @("Project completion", "Framework Package 1", "Phase 2", "Technical backlog")) {
    if ($byTitle[$title]) {
        $milestones[$title] = $byTitle[$title]
        Write-Host "  Milestone exists: $title #$($byTitle[$title])"
    } else {
        $c = Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/milestones" -Body @{ title = $title } -Token $token
        $milestones[$title] = $c.number
        Write-Host "  Created milestone: $title #$($c.number)"
    }
}

# 2. Labels
Write-Host "`n2. Labels" -ForegroundColor Cyan
$existingLb = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/labels" -Token $token
$lbNames = @($existingLb | ForEach-Object { $_.name })
foreach ($lb in @(@{ name = "epic"; color = "7C4DFF"; description = "Epic" }, @{ name = "bug"; color = "d73a4a"; description = "Bug" }, @{ name = "blocker"; color = "b60205"; description = "Blocker" })) {
    if ($lbNames -notcontains $lb.name) {
        Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/labels" -Body $lb -Token $token | Out-Null
        Write-Host "  Created label: $($lb.name)"
    }
}

# 3. Issues
Write-Host "`n3. Issues (granular)" -ForegroundColor Cyan
$createdIssues = @()
foreach ($item in $script:GranularIssues) {
    $msNum = $milestones[$item.milestone]
    $body = "**Milestone:** $($item.milestone) | **Area:** $($item.area) | **Priority:** $($item.priority)`n`n$($item.body)"
    $payload = @{ title = $item.title; body = $body; labels = $item.labels; milestone = $msNum }
    $issue = Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/issues" -Body $payload -Token $token
    $createdIssues += @{ number = $issue.number; node_id = $issue.node_id; title = $issue.title; milestone = $item.milestone; area = $item.area; priority = $item.priority }
    Write-Host "  Created issue #$($issue.number): $($item.title.Substring(0, [Math]::Min(60, $item.title.Length)))..."
}

# 4. Project: get project + fields (user or repo)
Write-Host "`n4. Project: add items and set fields" -ForegroundColor Cyan
$scope = "repo"
if ($env:PROJECT_SCOPE) { $scope = $env:PROJECT_SCOPE }
$scope = $scope.ToLower()
if ($scope -eq "user") {
    $projectOwner = if ($env:PROJECT_OWNER) { $env:PROJECT_OWNER } else { $owner }
    $query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'
    $data = Invoke-GitHubGraphQL -Payload @{ query = $query; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $proj = $data.user.projectV2
} else {
    $query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'
    $data = Invoke-GitHubGraphQL -Payload @{ query = $query; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $proj = $data.repository.projectV2
}
if (-not $proj) { Write-Error "Project not found. Check PROJECT_NUMBER and PROJECT_SCOPE (user vs repo)." }
$projectId = $proj.id
$fieldMap = @{}
foreach ($node in $proj.fields.nodes) {
    if ($node.__typename -eq "ProjectV2SingleSelectField" -and $node.options) {
        $opts = @{}
        foreach ($o in $node.options) { $opts[$o.name] = $o.id }
        $fieldMap[$node.name] = @{ id = $node.id; options = $opts }
    }
}

$statusF = $fieldMap["Status"]
$milestoneF = $fieldMap["Milestone"]; if (-not $milestoneF) { $milestoneF = $fieldMap["Milestones"] }
$areaF = $fieldMap["Area"]
$priorityF = $fieldMap["Priority"]
$riskF = $fieldMap["Risk"]
if (-not ($statusF -and $milestoneF -and $areaF -and $priorityF)) {
    Write-Host "  WARNING: Project is missing required fields (Status, Milestone/Milestones, Area, Priority). Add them in Project Settings. Skipping field updates." -ForegroundColor Yellow
} else {
    $addMutation = 'mutation($projectId: ID!, $contentId: ID!) { addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) { projectItem { id } } }'
    $updateMutation = 'mutation($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectItem { id } } }'
    foreach ($i in $createdIssues) {
        $addResult = Invoke-GitHubGraphQL -Payload @{ query = $addMutation; variables = @{ projectId = $projectId; contentId = $i.node_id } } -Token $token
        $itemId = $addResult.addProjectV2ItemById.projectItem.id
        if ($statusF.options.Backlog) {
            Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $statusF.id; value = @{ singleSelectOptionId = $statusF.options.Backlog } } } } -Token $token | Out-Null
        }
        if ($milestoneF.options[$i.milestone]) {
            Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $milestoneF.id; value = @{ singleSelectOptionId = $milestoneF.options[$i.milestone] } } } } -Token $token | Out-Null
        }
        if ($areaF.options[$i.area]) {
            Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $areaF.id; value = @{ singleSelectOptionId = $areaF.options[$i.area] } } } } -Token $token | Out-Null
        }
        if ($priorityF.options[$i.priority]) {
            Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $priorityF.id; value = @{ singleSelectOptionId = $priorityF.options[$i.priority] } } } } -Token $token | Out-Null
        }
        if ($riskF -and $riskF.options["On track"]) {
            Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $riskF.id; value = @{ singleSelectOptionId = $riskF.options["On track"] } } } } -Token $token | Out-Null
        }
        Write-Host "  Added #$($i.number) to project, set Status/Milestone/Area/Priority"
    }
}
Write-Host "`nDone. Issues: $($createdIssues.number -join ', ')" -ForegroundColor Green
