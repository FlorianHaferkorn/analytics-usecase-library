# Backlog migration: create GitHub Milestones and Issues from BACKLOG_MIGRATION.md.
# Requires: GITHUB_TOKEN or GH_TOKEN (repo scope). Optional: gh CLI for gh auth token.
# Run from repo root. Repo is taken from git remote origin or env GITHUB_REPOSITORY.

$ErrorActionPreference = "Stop"

function Get-GitHubToken {
    $token = $env:GITHUB_TOKEN
    if (-not $token) { $token = $env:GH_TOKEN }
    if (-not $token) {
        try {
            $token = (gh auth token 2>$null)
        } catch {}
    }
    if (-not $token) {
        Write-Error "Set GITHUB_TOKEN or GH_TOKEN, or run 'gh auth login'. Token needs 'repo' scope."
    }
    return $token
}

function Get-RepoOwnerAndName {
    $repo = $env:GITHUB_REPOSITORY
    if ($repo) {
        $parts = $repo -split "/", 2
        return @{ owner = $parts[0]; name = $parts[1] }
    }
    $remote = (git config --get remote.origin.url 2>$null)
    if ($remote -match "github\.com[:/]([^/]+)/([^/.]+)") {
        return @{ owner = $Matches[1]; name = ($Matches[2] -replace "\.git$", "") }
    }
    Write-Error "Could not determine repo. Set GITHUB_REPOSITORY to owner/repo or run from a git repo with origin pointing to GitHub."
}

function Invoke-GitHubApi {
    param([string]$Method, [string]$Path, [hashtable]$Body = $null, [string]$Token)
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Accept"        = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    $uri = "https://api.github.com$Path"
    $params = @{ Method = $Method; Uri = $uri; Headers = $headers }
    if ($Body) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress)
        $params["ContentType"] = "application/json"
    }
    try {
        return Invoke-RestMethod @params
    } catch {
        Write-Error "GitHub API $Method $Path failed: $($_.Exception.Message)"
    }
}

$token = Get-GitHubToken
$repo = Get-RepoOwnerAndName
$owner = $repo.owner
$name = $repo.name
Write-Host "Repo: $owner/$name" -ForegroundColor Cyan

# 1. Milestones
$milestoneTitles = @("Project completion", "Phase 2", "Technical backlog")
$milestones = @{}
foreach ($title in $milestoneTitles) {
    $all = Invoke-GitHubApi -Method Get -Path "/repos/$owner/$name/milestones?state=all" -Token $token
    $existing = @($all) | Where-Object { $_.title -eq $title }
    if ($existing.Count -gt 0) {
        $milestones[$title] = $existing[0].number
        Write-Host "Milestone exists: $title (#$($existing[0].number))"
    } else {
        $created = Invoke-GitHubApi -Method Post -Path "/repos/$owner/$name/milestones" -Body @{ title = $title } -Token $token
        $milestones[$title] = $created.number
        Write-Host "Created milestone: $title (#$($created.number))"
    }
}

# 2. Labels (create if missing)
$labelsToCreate = @(
    @{ name = "epic"; color = "7C4DFF"; description = "Epic-level issue" },
    @{ name = "bug"; color = "d73a4a"; description = "Something is broken" },
    @{ name = "blocker"; color = "b60205"; description = "Blocks other work" }
)
$existingLabels = @((Invoke-GitHubApi -Method Get -Path "/repos/$owner/$name/labels" -Token $token) | ForEach-Object { $_.name })
foreach ($lb in $labelsToCreate) {
    if ($existingLabels -notcontains $lb.name) {
        Invoke-GitHubApi -Method Post -Path "/repos/$owner/$name/labels" -Body $lb -Token $token | Out-Null
        Write-Host "Created label: $($lb.name)"
    }
}

# 3. Issues from BACKLOG_MIGRATION
$phase2Milestone = $milestones["Phase 2"]
$techMilestone = $milestones["Technical backlog"]

$issues = @(
    # Phase 2 Epics
    @{
        title = "[Epic] 3-30-300 complete: 300s page from action-code YAML"
        body = @"
## Summary
300s page in report shows action text and evidence table sourced from action-code YAML; generated from framework.

## Milestone
Phase 2

## Area
FabricPowerBI

## Priority
P1

## Definition of Done
- [ ] 300s page in report shows action text and evidence table from action-code YAML
- [ ] Generated from framework
"@
        labels = @("epic")
        milestone = $phase2Milestone
    },
    @{
        title = "[Epic] Strategy Pattern / AI urgency and automated reasoning"
        body = @"
## Summary
Strategy pattern precise enough for tooling; AI urgency and automated reasoning demonstrated or documented scope.

## Milestone
Phase 2

## Area
Framework

## Priority
P2

## Definition of Done
- [ ] Strategy pattern precise enough for tooling
- [ ] AI urgency and automated reasoning demonstrated or scope documented
"@
        labels = @("epic")
        milestone = $phase2Milestone
    },
    # Technical backlog – Power BI MCP / Fabric
    @{ title = "[Task] Call Power BI MCP table_operations from table_ops.ps1"; body = "See internal/technical_backlog.md. File: products/fabric_powerbi/orchestrator/table_ops.ps1 ~line 138.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    @{ title = "[Task] Call Power BI MCP relationship_operations from relationship_ops.ps1"; body = "See internal/technical_backlog.md. tooling/powerbi_mcp/relationship_ops.ps1 ~line 199.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    @{ title = "[Task] Fabric Workspace and semantic model API in deploy.ps1"; body = "deploy.ps1: GET/POST workspace, Import PBIP/TMDL, Publish report, Refresh schedule, RLS/security_user_org.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    @{ title = "[Task] TMDL/display folders, relationship update, visuals, REST, refresh, security in AUTOMATION_FLOW"; body = "See products/fabric_powerbi/orchestrator/AUTOMATION_FLOW.md.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    # Aurora
    @{ title = "[Task] Complete Aurora Operations and Finance domain models"; body = "relationships/measures/display folders; DAX in KPI Catalog; Measure_Dictionary per domain. See showcases/aurora_group/models/README.md.`n`n**Area:** Aurora | **Priority:** P1 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    # Synthetic data
    @{ title = "[Task] Synthetic data: Lakehouse pre-create and backbone notebook stubs"; body = "fabric_nb_generate_backbone_core_v1.py: create Lakehouse first; implement stub blocks (date range, joins, bands, schema).`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    @{ title = "[Task] Synthetic data: optional holiday logic in generate_gold_layer"; body = "generate_gold_layer.py line 121: is_holiday.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    # Page scaffold
    @{ title = "[Task] Page scaffold: BOM support in YAML scanner"; body = "scanner.py line 187.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone },
    @{ title = "[Task] Page scaffold: tab handling rules in YAML scanner"; body = "scanner.py line 761.`n`n**Area:** Tooling | **Priority:** P2 | **Milestone:** Technical backlog"; labels = @(); milestone = $techMilestone }
)

$createdIssues = @()
foreach ($issue in $issues) {
    $body = @{ title = $issue.title; body = $issue.body; labels = $issue.labels; milestone = $issue.milestone }
    $created = Invoke-GitHubApi -Method Post -Path "/repos/$owner/$name/issues" -Body $body -Token $token
    $createdIssues += [pscustomobject]@{ number = $created.number; title = $created.title; url = $created.html_url }
    Write-Host "Created issue #$($created.number): $($issue.title)"
}

Write-Host ""
Write-Host "Done. Created $($createdIssues.Count) issues." -ForegroundColor Green
$numList = ($createdIssues | ForEach-Object { $_.number }) -join ", "
Write-Host "Add them to your Project: open the Project -> Add items -> paste issue numbers: $numList"
Write-Host "Then set Status = Backlog, Milestone and Area per issue (see internal/project_mgmt/BACKLOG_MIGRATION.md)."
