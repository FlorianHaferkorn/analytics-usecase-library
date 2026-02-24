# Idempotent sync: granular_issues.json -> GitHub Issues + Project.
# Ensures milestones, labels, project fields; get-or-create issues by title; adds to project; sets fields; removes duplicates.
# Token: GITHUB_TOKEN. Run from repo root. In CI, set PROJECT_NUMBER (default 2). Writes summary to GITHUB_STEP_SUMMARY if set.

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Load-ProjectEnv.ps1"
. "$PSScriptRoot\GranularIssues.ps1"

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
$projectNumber = 2; if ($env:PROJECT_NUMBER) { $projectNumber = [int]$env:PROJECT_NUMBER }
$scope = "repo"; if ($env:PROJECT_SCOPE) { $scope = $env:PROJECT_SCOPE }; $scope = $scope.ToLower()
Write-Host "Repo: $owner/$name | Project: $projectNumber" -ForegroundColor Cyan

# --- 1. Milestones ---
$existingMs = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/milestones?state=all" -Token $token
$byTitle = @{}; foreach ($m in $existingMs) { $byTitle[$m.title] = $m.number }
$milestones = @{}
foreach ($title in @("Project completion", "Framework Package 1", "Phase 2", "Technical backlog")) {
    if ($byTitle[$title]) { $milestones[$title] = $byTitle[$title] } else {
        $c = Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/milestones" -Body @{ title = $title } -Token $token
        $milestones[$title] = $c.number; Write-Host "Created milestone: $title" -ForegroundColor Green
    }
}

# --- 2. Labels ---
$existingLb = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/labels" -Token $token
$lbNames = @($existingLb | ForEach-Object { $_.name })
foreach ($lb in @(@{ name = "epic"; color = "7C4DFF"; description = "Epic" }, @{ name = "bug"; color = "d73a4a"; description = "Bug" }, @{ name = "blocker"; color = "b60205"; description = "Blocker" })) {
    if ($lbNames -notcontains $lb.name) {
        Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/labels" -Body $lb -Token $token | Out-Null
        Write-Host "Created label: $($lb.name)" -ForegroundColor Green
    }
}

# --- 3. Project + fields (ensure exist) ---
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
$requiredFields = @(
    @{ name = "Status"; options = @("Backlog", "Planned", "In progress", "In review", "Done") },
    @{ name = "Milestones"; options = @("Project completion", "Framework Package 1", "Phase 2", "Technical backlog") },
    @{ name = "Area"; options = @("Framework", "FabricPowerBI", "Aurora", "Tooling", "Docs") },
    @{ name = "Priority"; options = @("P0", "P1", "P2") },
    @{ name = "Risk"; options = @("On track", "At risk") }
)
$createFieldMutation = 'mutation($input: CreateProjectV2FieldInput!) { createProjectV2Field(input: $input) { projectV2Field { ... on ProjectV2SingleSelectField { id name options { id name } } } } }'
foreach ($def in $requiredFields) {
    if (-not $fieldMap[$def.name]) {
        $optInputs = @($def.options | ForEach-Object { @{ name = $_; description = ""; color = "GRAY" } })
        try {
            Invoke-GitHubGraphQL -Payload @{ query = $createFieldMutation; variables = @{ input = @{ projectId = $projectId; name = $def.name; dataType = "SINGLE_SELECT"; singleSelectOptions = $optInputs } } } -Token $token | Out-Null
            Write-Host "Created field: $($def.name)" -ForegroundColor Green
        } catch { if ($_.Exception.Message -notmatch "already been taken|reserved") { throw } }
    }
}
# Re-fetch fields
if ($scope -eq "user") {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($login: String!, $number: Int!) { user(login: $login) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ login = $projectOwner; number = $projectNumber } } -Token $token
    $proj = $data.user.projectV2
} else {
    $data = Invoke-GitHubGraphQL -Payload @{ query = 'query($owner: String!, $repo: String!, $number: Int!) { repository(owner: $owner, name: $repo) { projectV2(number: $number) { id fields(first: 30) { nodes { __typename ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'; variables = @{ owner = $owner; repo = $name; number = $projectNumber } } -Token $token
    $proj = $data.repository.projectV2
}
$fieldMap = @{}; foreach ($node in $proj.fields.nodes) {
    if ($node.__typename -eq "ProjectV2SingleSelectField" -and $node.options) { $opts = @{}; foreach ($o in $node.options) { $opts[$o.name] = $o.id }; $fieldMap[$node.name] = @{ id = $node.id; options = $opts } }
}
$statusF = $fieldMap["Status"]; $milestoneF = $fieldMap["Milestones"]; if (-not $milestoneF) { $milestoneF = $fieldMap["Milestone"] }
$areaF = $fieldMap["Area"]; $priorityF = $fieldMap["Priority"]; $riskF = $fieldMap["Risk"]
if (-not ($statusF -and $milestoneF -and $areaF -and $priorityF)) { Write-Error "Project missing Status, Milestones, Area, or Priority. Add in Project Settings." }

# --- 4. Existing issues by title (exact match; if duplicates, keep lowest number) ---
$titleToIssue = @{}
$page = 1; $perPage = 100
do {
    $list = Invoke-GitHubRest -Method Get -Path "/repos/$owner/$name/issues?state=all&per_page=$perPage&page=$page" -Token $token
    foreach ($iss in $list) {
        if (-not $iss.pull_request -and $iss.title -ne "") {
            $t = $iss.title
            if (-not $titleToIssue[$t] -or $titleToIssue[$t].number -gt $iss.number) {
                $titleToIssue[$t] = @{ number = $iss.number; node_id = $iss.node_id }
            }
        }
    }
    $page++; if ($list.Count -lt $perPage) { break }
} while ($list.Count -eq $perPage)

# --- 5. Project items: issue number -> item id ---
$issueToItemId = @{}; $cursor = $null
do {
    $q = 'query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) { nodes { id content { ... on Issue { number } } } pageInfo { endCursor hasNextPage } } } } }'
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $q; variables = $vars } -Token $token
    $n = $out.node.items; foreach ($i in $n.nodes) { if ($i.content.number) { $issueToItemId[$i.content.number] = $i.id } }; $cursor = $n.pageInfo.endCursor; if (-not $n.pageInfo.hasNextPage) { break }
} while ($cursor)

# --- 6. Get-or-create issues, add to project, set fields ---
$addMutation = 'mutation($projectId: ID!, $contentId: ID!) { addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) { projectV2Item { id } } }'
$updateMutation = 'mutation($input: UpdateProjectV2ItemFieldValueInput!) { updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } } }'
$created = @(); $added = @(); $fieldsSet = 0
foreach ($item in $script:GranularIssues) {
    $title = $item.title
    if (-not $titleToIssue[$title]) {
        $body = "**Milestone:** $($item.milestone) | **Area:** $($item.area) | **Priority:** $($item.priority)`n`n$($item.body)"
        $payload = @{ title = $title; body = $body; labels = $item.labels; milestone = $milestones[$item.milestone] }
        $issue = Invoke-GitHubRest -Method Post -Path "/repos/$owner/$name/issues" -Body $payload -Token $token
        $titleToIssue[$title] = @{ number = $issue.number; node_id = $issue.node_id }; $created += $issue.number
        Write-Host "Created #$($issue.number): $($title.Substring(0, [Math]::Min(50, $title.Length)))..." -ForegroundColor Green
    }
    $num = $titleToIssue[$title].number; $nodeId = $titleToIssue[$title].node_id
    $itemId = $null
    $wasJustAdded = $false
    if (-not $issueToItemId[$num]) {
        $addResult = Invoke-GitHubGraphQL -Payload @{ query = $addMutation; variables = @{ projectId = $projectId; contentId = $nodeId } } -Token $token
        $itemId = $addResult.addProjectV2ItemById.projectV2Item.id; $issueToItemId[$num] = $itemId; $added += $num; $wasJustAdded = $true
        Write-Host "Added #$num to project" -ForegroundColor Cyan
    } else { $itemId = $issueToItemId[$num] }
    if ($itemId) {
        # Set Status only for newly added items (Backlog). Do not overwrite In progress / In review / Done.
        if ($wasJustAdded -and $statusF.options["Backlog"]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $statusF.id; value = @{ singleSelectOptionId = $statusF.options["Backlog"] } } } } -Token $token | Out-Null }
        if ($milestoneF.options[$item.milestone]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $milestoneF.id; value = @{ singleSelectOptionId = $milestoneF.options[$item.milestone] } } } } -Token $token | Out-Null }
        if ($areaF.options[$item.area]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $areaF.id; value = @{ singleSelectOptionId = $areaF.options[$item.area] } } } } -Token $token | Out-Null }
        if ($priorityF.options[$item.priority]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $priorityF.id; value = @{ singleSelectOptionId = $priorityF.options[$item.priority] } } } } -Token $token | Out-Null }
        if ($riskF -and $riskF.options["On track"]) { Invoke-GitHubGraphQL -Payload @{ query = $updateMutation; variables = @{ input = @{ projectId = $projectId; itemId = $itemId; fieldId = $riskF.id; value = @{ singleSelectOptionId = $riskF.options["On track"] } } } } -Token $token | Out-Null }
        $fieldsSet++
    }
}

# --- 7. Duplicate cleanup: by title, keep lowest issue number ---
$items = @(); $cursor = $null
do {
    $q = 'query($id: ID!, $after: String) { node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) { nodes { id content { ... on Issue { number title } } } pageInfo { endCursor hasNextPage } } } } }'
    $vars = @{ id = $projectId }; if ($cursor) { $vars["after"] = $cursor }
    $out = Invoke-GitHubGraphQL -Payload @{ query = $q; variables = $vars } -Token $token
    $n = $out.node.items
    foreach ($i in $n.nodes) { if ($i.content.number -and $i.content.title) { $items += @{ itemId = $i.id; issueNumber = $i.content.number; title = $i.content.title } } }
    $cursor = $n.pageInfo.endCursor; if (-not $n.pageInfo.hasNextPage) { break }
} while ($cursor)
$byTitle = @{}; foreach ($it in $items) { $t = $it.title; if (-not $byTitle[$t]) { $byTitle[$t] = @() }; $byTitle[$t] += $it }
$toRemove = @(); foreach ($entry in $byTitle.GetEnumerator()) {
    if ($entry.Value.Count -le 1) { continue }
    $list = $entry.Value | Sort-Object { $_.issueNumber }; for ($i = 1; $i -lt $list.Count; $i++) { $toRemove += $list[$i] }
}
$duplicatesRemoved = 0
if ($toRemove.Count -gt 0) {
    $deleteMutation = 'mutation($input: DeleteProjectV2ItemInput!) { deleteProjectV2Item(input: $input) { deletedItemId } }'
    foreach ($it in $toRemove) {
        try {
            Invoke-GitHubGraphQL -Payload @{ query = $deleteMutation; variables = @{ input = @{ projectId = $projectId; itemId = $it.itemId } } } -Token $token | Out-Null
            $duplicatesRemoved++; Write-Host "Removed duplicate #$($it.issueNumber) from project" -ForegroundColor Yellow
        } catch { Write-Host "Failed to remove #$($it.issueNumber): $_" -ForegroundColor Red }
    }
}

# --- 8. Summary ---
$summary = "Created issues: $(if ($created.Count) { '#' + ($created -join ', #') } else { '0' }) | Added to project: $(if ($added.Count) { $added.Count } else { 0 }) | Fields set: $fieldsSet items | Duplicates removed: $duplicatesRemoved"
Write-Host "`n$summary" -ForegroundColor Green
if ($env:GITHUB_STEP_SUMMARY) {
    $lines = @("## Sync from Backlog", "", $summary, "")
    Add-Content -Path $env:GITHUB_STEP_SUMMARY -Value ($lines -join "`n") -Encoding UTF8
}
