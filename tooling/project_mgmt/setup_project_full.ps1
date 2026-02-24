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

# Granular issues: same as setup_project_full.py (BACKLOG_GRANULAR.md)
$script:GranularIssues = @(
    @{ title = "[Task] Resolve blockers from content review (company_strategy anchors, factsheet paths)"; milestone = "Project completion"; area = "Docs"; priority = "P0"; labels = @(); body = "From presentation_status_and_roadmap. Blocker resolution." },
    @{ title = "[Task] Remaining review adjustments (style, link-backs, encoding)"; milestone = "Project completion"; area = "Docs"; priority = "P1"; labels = @(); body = "Review adjustments for project completion." },
    @{ title = "[Task] Document CI/release without Stage-1 skip"; milestone = "Project completion"; area = "Tooling"; priority = "P1"; labels = @(); body = "Zero-tolerance documentation: CI/release without Stage-1 skip." },
    # Framework Package 1 (Demo Friday: P0 = must, P1 = should, P2 = optional)
    @{ title = "[Epic] Framework Package 1 complete: Aurora customer-ready (Fabric/Power BI)"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P1"; labels = @("epic"); body = "Abschluss erstes Framework-Paket. Aurora zeigt: bei Kunden ohne Probleme/Bugs einsetzbar; reproduzierbar inkl. neuer Use Cases. Out of Scope: Evidence, andere Tools; Fabric Capacity; Generators/Interfaces. AC: PBIP opens, no known blockers, docs, page templates." },
    @{ title = "[Task] Reproducible pipeline: Use Cases to PBIP (Aurora, configurable use-case set)"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P0"; labels = @(); body = "Script/workflow from Use Case Inventory + Brackets to Aurora PBIP (configurable use-case set). Demo Friday: must-have." },
    @{ title = "[Task] Verification: PBIP opens in Power BI Desktop; report and model load"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P0"; labels = @(); body = "Check: Aurora PBIP opens in Power BI Desktop; report and model load without error. AC: Report pages show visual placeholders (KPI, Trend, Variance) and open without error." },
    @{ title = "[Task] Report output: open generated report with CoreActionReady.SemanticModel (minimal .pbip or doc)"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P0"; labels = @(); body = "Minimal .pbip for dist/<UC>.Report + CoreActionReady.SemanticModel, or clear doc how to open generated report with showcase model. Demo Friday: must-have." },
    @{ title = "[Task] Verification: Pages align with page templates"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P0"; labels = @(); body = "Verify pages align with core/templates/page_templates." },
    @{ title = "[Task] Customer readiness checklist and known blockers"; milestone = "Framework Package 1"; area = "Docs"; priority = "P1"; labels = @(); body = "Customer readiness checklist; document prerequisites (versions, steps); capture known blockers." },
    @{ title = "[Task] Add one new use case and regenerate Aurora report (reproducibility proof)"; milestone = "Framework Package 1"; area = "FabricPowerBI"; priority = "P2"; labels = @(); body = "Add one new (or defined) use case; run pipeline; Aurora report regenerates and opens without error. Proof: works with new use cases. Demo Friday: optional." },
    @{ title = "[Epic] 3-30-300 complete: 300s page from action-code YAML"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P1"; labels = @("epic"); body = "Parent epic. 300s page shows action text and evidence from action-code YAML; generated from framework." },
    @{ title = "[Task] Define 300s page layout in page template (layout_330300)"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P1"; labels = @(); body = "core/templates/page_templates. Define 300s page layout." },
    @{ title = "[Task] Generate action text from action-code YAML in report"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P1"; labels = @(); body = "Action payload in 300s page from action-code YAML." },
    @{ title = "[Task] Generate evidence table from data contract / action payload"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P1"; labels = @(); body = "Evidence table for 300s page." },
    @{ title = "[Task] Wire 300s page into report scaffold (Aurora)"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P1"; labels = @(); body = "Report structure: 300s page in Aurora scaffold." },
    @{ title = "[Task] Integration test: 300s page end-to-end"; milestone = "Phase 2"; area = "FabricPowerBI"; priority = "P2"; labels = @(); body = "Verify full 300s flow." },
    @{ title = "[Epic] Strategy Pattern / AI urgency and automated reasoning"; milestone = "Phase 2"; area = "Framework"; priority = "P2"; labels = @("epic"); body = "Parent epic. Strategy pattern precise enough for tooling; AI urgency and automated reasoning scope." },
    @{ title = "[Task] Document urgency rules in strategy_patterns.md"; milestone = "Phase 2"; area = "Framework"; priority = "P2"; labels = @(); body = "core/strategy_operating_model/company. Urgency rules in strategy_patterns.md." },
    @{ title = "[Task] Add tooling hook for urgency derivation (stub or spec)"; milestone = "Phase 2"; area = "Tooling"; priority = "P2"; labels = @(); body = "Optional automation for urgency derivation." },
    @{ title = "[Task] Document automated reasoning scope and limits"; milestone = "Phase 2"; area = "Docs"; priority = "P2"; labels = @(); body = "internal/vision or strategy. Automated reasoning scope." },
    @{ title = "[Task] Call Power BI MCP table_operations from table_ops.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "tooling/powerbi_mcp/table_ops.ps1 ~line 138." },
    @{ title = "[Task] Call Power BI MCP relationship_operations from relationship_ops.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "relationship_ops.ps1 ~line 199." },
    @{ title = "[Task] Fabric: Workspace API (GET/POST) in deploy.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "deploy.ps1 - Workspace API." },
    @{ title = "[Task] Fabric: Import PBIP/TMDL to semantic model API in deploy.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "deploy.ps1 - Import PBIP/TMDL." },
    @{ title = "[Task] Fabric: Publish report and bind to dataset in deploy.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "deploy.ps1 - Publish report, bind to dataset." },
    @{ title = "[Task] Fabric: Set refresh schedule via REST in deploy.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "deploy.ps1 - Refresh schedule." },
    @{ title = "[Task] Fabric: Apply RLS / security_user_org mapping via API in deploy.ps1"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "deploy.ps1 - RLS/security_user_org." },
    @{ title = "[Task] TMDL: default format strings and display folders (AUTOMATION_FLOW)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "tooling/powerbi_mcp/AUTOMATION_FLOW.md." },
    @{ title = "[Task] Update relationship via MCP (AUTOMATION_FLOW)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "AUTOMATION_FLOW.md - relationship via MCP." },
    @{ title = "[Task] Generate visuals from template (AUTOMATION_FLOW)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "AUTOMATION_FLOW.md - visuals from template." },
    @{ title = "[Task] Aurora Operations model: complete relationships and measures (Operations.yaml)"; milestone = "Technical backlog"; area = "Aurora"; priority = "P1"; labels = @(); body = "showcases/aurora_group/models/Operations.yaml." },
    @{ title = "[Task] Aurora Operations model: DAX in KPI Catalog, Measure_Dictionary"; milestone = "Technical backlog"; area = "Aurora"; priority = "P1"; labels = @(); body = "Operations domain - DAX and Measure_Dictionary." },
    @{ title = "[Task] Aurora Finance model: complete relationships and measures (Finance.yaml)"; milestone = "Technical backlog"; area = "Aurora"; priority = "P1"; labels = @(); body = "showcases/aurora_group/models/Finance.yaml." },
    @{ title = "[Task] Aurora Finance model: DAX in KPI Catalog, Measure_Dictionary"; milestone = "Technical backlog"; area = "Aurora"; priority = "P1"; labels = @(); body = "Finance domain - DAX and Measure_Dictionary." },
    @{ title = "[Task] Synthetic: ensure Lakehouse exists before notebook run (create or doc)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "fabric_nb_generate_backbone_core_v1.py." },
    @{ title = "[Task] Synthetic: implement date range with Spark (backbone notebook)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "Backbone notebook - date range." },
    @{ title = "[Task] Synthetic: derive from sales + config.inventory (target_dio_range, coverage days)"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "Backbone notebook." },
    @{ title = "[Task] Synthetic: implement join + ratio, Category join + GM% band check"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "Backbone notebook." },
    @{ title = "[Task] Synthetic: RI dim_* vs facts, margin bands, DIO/CCC bands"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "Backbone notebook." },
    @{ title = "[Task] Synthetic: Lakehouse and schema exist; map dims/facts to config.lakehouse.tables"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "Backbone notebook." },
    @{ title = "[Task] Synthetic: optional holiday logic for is_holiday in generate_gold_layer.py"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "generate_gold_layer.py line 121." },
    @{ title = "[Task] Page scaffold: BOM support in YAML scanner"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "scanner.py line 187." },
    @{ title = "[Task] Page scaffold: tab handling rules in YAML scanner"; milestone = "Technical backlog"; area = "Tooling"; priority = "P2"; labels = @(); body = "scanner.py line 761." }
)

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
