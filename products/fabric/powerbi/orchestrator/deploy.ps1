# Deploy Semantic Models and Reports to Microsoft Fabric / Power BI.
#
# Pipeline:
#   1) deploy_gate.ps1      – Zero-Tolerance gate (contracts + registry)
#   2) Workspace            – GET or CREATE via Fabric REST v1
#   3) Items deploy         – SemanticModel + Reports per domain via fabric-cicd (fabric_release.py)
#   4) RLS Sync             – Apply OrgAccess role members per deployed dataset
#   5) Refresh schedule     – PATCH datasets/{id}/refreshSchedule (Power BI REST)
#   6) Summary              – Per-domain result table
#
# Auth (Service Principal – set as env vars, never commit):
#   FABRIC_TENANT_ID, FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET
#   Fallback aliases: PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET
#
# Optional env vars:
#   FABRIC_WORKSPACE_ID     – skip workspace lookup (use directly)
#   FABRIC_CAPACITY_ID      – assign capacity when creating workspace
#   FABRIC_RLS_GROUP_ID     – AAD group object ID to assign to OrgAccess RLS role
#
# Usage examples:
#   .\deploy.ps1 -All -Environment dev
#   .\deploy.ps1 -Domains Commercial,Finance -Environment tst -DryRun
#   .\deploy.ps1 -GateOnly
#   .\deploy.ps1 -All -SkipSecurity -SkipRefresh

param(
    [string]$Root          = ".",
    [string]$WorkspaceName = "DM_ActionReady",
    [string]$Environment   = "dev",
    [string[]]$Domains     = @("Commercial","Finance","Operations","SupplyChain","Experience"),
    [switch]$All,
    [string]$CapacityId,
    [switch]$GateOnly,
    [switch]$SkipRefresh,
    [switch]$SkipSecurity,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$script:FabricApiBase  = "https://api.fabric.microsoft.com/v1"
$script:PbiApiBase     = "https://api.powerbi.com/v1.0/myorg"

# ────────────────────────────────────────────────────────────────────────────────
# HELPERS – Paths
# ────────────────────────────────────────────────────────────────────────────────

function Resolve-RepoRoot {
    param([string]$Provided)
    $candidate = if ($Provided -and (Test-Path $Provided)) {
        (Resolve-Path $Provided).Path
    } else { (Get-Location).Path }
    # Walk up until core/ + products/ exist (repo root)
    $cur = $candidate
    while ($cur) {
        if ((Test-Path (Join-Path $cur "core")) -and (Test-Path (Join-Path $cur "products"))) {
            return $cur
        }
        $parent = Split-Path -Parent $cur
        if ($parent -eq $cur) { break }
        $cur = $parent
    }
    return $candidate
}

# ────────────────────────────────────────────────────────────────────────────────
# HELPERS – Authentication
# ────────────────────────────────────────────────────────────────────────────────

function Get-SPCredentials {
    return @{
        TenantId     = if ($env:FABRIC_TENANT_ID)     { $env:FABRIC_TENANT_ID }     else { $env:PBI_TENANT_ID }
        ClientId     = if ($env:FABRIC_CLIENT_ID)     { $env:FABRIC_CLIENT_ID }     else { $env:PBI_CLIENT_ID }
        ClientSecret = if ($env:FABRIC_CLIENT_SECRET) { $env:FABRIC_CLIENT_SECRET } else { $env:PBI_CLIENT_SECRET }
    }
}

function Get-OAuthToken {
    # Returns bearer token for Power BI / Fabric API (client credentials flow).
    param([string]$Scope = "https://analysis.windows.net/powerbi/api/.default")
    $creds = Get-SPCredentials
    if (-not $creds.TenantId -or -not $creds.ClientId -or -not $creds.ClientSecret) {
        Write-Host "  [WARN] No service-principal credentials found." `
            + " Set FABRIC_TENANT_ID / FABRIC_CLIENT_ID / FABRIC_CLIENT_SECRET." -ForegroundColor Yellow
        return $null
    }
    $body = "grant_type=client_credentials" +
            "&client_id=$([Uri]::EscapeDataString($creds.ClientId))" +
            "&client_secret=$([Uri]::EscapeDataString($creds.ClientSecret))" +
            "&scope=$([Uri]::EscapeDataString($Scope))"
    $uri = "https://login.microsoftonline.com/$($creds.TenantId)/oauth2/v2.0/token"
    try {
        $resp = Invoke-RestMethod -Method Post -Uri $uri -Body $body `
            -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
        return $resp.access_token
    } catch {
        Write-Host "  [ERROR] Token request failed: $_" -ForegroundColor Red
        return $null
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# HELPERS – REST wrappers
# ────────────────────────────────────────────────────────────────────────────────

function Invoke-FabricREST {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Token,
        [object]$Body   = $null,
        [switch]$Silent
    )
    $uri     = "$script:FabricApiBase$Path"
    $headers = @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" }
    $params  = @{ Method = $Method; Uri = $uri; Headers = $headers; ErrorAction = "Stop" }
    if ($Body) { $params["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress) }
    try {
        return Invoke-RestMethod @params
    } catch {
        if (-not $Silent) {
            Write-Host "  [ERROR] Fabric REST $Method $Path -> $_" -ForegroundColor Red
        }
        return $null
    }
}

function Invoke-PBIREST {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Token,
        [object]$Body   = $null,
        [switch]$Silent
    )
    $uri     = "$script:PbiApiBase$Path"
    $headers = @{ "Authorization" = "Bearer $Token"; "Content-Type" = "application/json" }
    $params  = @{ Method = $Method; Uri = $uri; Headers = $headers; ErrorAction = "Stop" }
    if ($Body) { $params["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress) }
    try {
        return Invoke-RestMethod @params
    } catch {
        if (-not $Silent) {
            Write-Host "  [ERROR] Power BI REST $Method $Path -> $_" -ForegroundColor Red
        }
        return $null
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# STEP 2 – Workspace: GET or CREATE
# ────────────────────────────────────────────────────────────────────────────────

function Get-OrCreate-FabricWorkspace {
    param([string]$Name, [string]$Token, [string]$CapacityId)

    # Short-circuit: workspace ID already provided via env var
    if ($env:FABRIC_WORKSPACE_ID) {
        Write-Host "  Using FABRIC_WORKSPACE_ID from env: $($env:FABRIC_WORKSPACE_ID)" -ForegroundColor Gray
        return $env:FABRIC_WORKSPACE_ID
    }

    if (-not $Token) {
        Write-Host "  [SKIP] No token available – workspace step skipped." -ForegroundColor Yellow
        return $null
    }

    # List workspaces (paginated – Fabric REST v1 does not support OData $filter on displayName)
    Write-Host "  Searching for workspace '$Name'..." -ForegroundColor Gray
    $continuationToken = $null
    do {
        $path = "/workspaces"
        if ($continuationToken) {
            $path += "?continuationToken=$([Uri]::EscapeDataString($continuationToken))"
        }
        $page = Invoke-FabricREST -Method Get -Path $path -Token $Token -Silent
        if (-not $page) { break }
        $match = $page.value | Where-Object { $_.displayName -eq $Name } | Select-Object -First 1
        if ($match) {
            Write-Host "  Found existing workspace: $($match.id)" -ForegroundColor Gray
            return $match.id
        }
        $continuationToken = $page.continuationToken
    } while ($continuationToken)

    # Not found – create
    Write-Host "  Workspace '$Name' not found – creating..." -ForegroundColor Gray
    if ($DryRun) {
        Write-Host "  [DRY-RUN] Would POST /workspaces { displayName: '$Name' }" -ForegroundColor Cyan
        return "dry-run-workspace-id"
    }

    $createBody = @{ displayName = $Name }
    if ($CapacityId) { $createBody["capacityId"] = $CapacityId }

    $created = Invoke-FabricREST -Method Post -Path "/workspaces" -Token $Token -Body $createBody
    if (-not $created) { throw "Failed to create Fabric workspace '$Name'." }

    Write-Host "  Created workspace: $($created.id)" -ForegroundColor Green
    return $created.id
}

# ────────────────────────────────────────────────────────────────────────────────
# STEP 3 – Items deploy: delegate to fabric_release.py (fabric-cicd)
# ────────────────────────────────────────────────────────────────────────────────

function Invoke-FabricRelease {
    param(
        [string]$RepoRoot,
        [string]$WorkspaceId,
        [string]$Environment,
        [string]$Domain         # e.g. "Commercial"; empty = all domains
    )

    $releaseScript = Join-Path $RepoRoot "products\fabric\powerbi\deployment\scripts\fabric_release.py"
    if (-not (Test-Path $releaseScript)) {
        Write-Host "  [WARN] fabric_release.py not found: $releaseScript" -ForegroundColor Yellow
        return $false
    }

    # Dist root contains all PBIP folders (SemanticModel + Report subfolders)
    $distRoot = Join-Path $RepoRoot "products\fabric\powerbi\dist"

    # Pass SP credentials to Python via azure-identity expected env vars
    $creds = Get-SPCredentials
    if ($creds.TenantId)     { $env:AZURE_TENANT_ID     = $creds.TenantId }
    if ($creds.ClientId)     { $env:AZURE_CLIENT_ID     = $creds.ClientId }
    if ($creds.ClientSecret) { $env:AZURE_CLIENT_SECRET = $creds.ClientSecret }

    $pyArgs = @(
        $releaseScript,
        "--environment", $Environment,
        "--repo_path",   $distRoot,
        "--item_types",  "SemanticModel,Report",
        "--layers",      "DM"
    )
    if ($WorkspaceId)  { $pyArgs += @("--workspace_id", $WorkspaceId) }
    if ($Domain)       { $pyArgs += @("--domain_filter", $Domain) }
    if ($DryRun)       { $pyArgs += "--dry_run" }

    Write-Host "  fabric_release.py (domain=$(if ($Domain) { $Domain } else { 'all' }), env=$Environment)..." -ForegroundColor Gray

    if ($DryRun) {
        Write-Host "  [DRY-RUN] python $($pyArgs -join ' ')" -ForegroundColor Cyan
        return $true
    }

    try {
        $output = & python @pyArgs 2>&1
        $output | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] fabric_release.py exited with code $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
        return $true
    } catch {
        Write-Host "  [ERROR] fabric_release.py invocation failed: $_" -ForegroundColor Red
        return $false
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# STEP 3b – Resolve deployed item IDs from workspace (for RLS + refresh)
# ────────────────────────────────────────────────────────────────────────────────

function Get-WorkspaceDatasetMap {
    # Returns @{ DisplayName -> datasetId }
    param([string]$WorkspaceId, [string]$Token)
    if (-not $Token -or -not $WorkspaceId) { return @{} }
    $resp = Invoke-PBIREST -Method Get -Path "/groups/$WorkspaceId/datasets" -Token $Token -Silent
    if (-not $resp) { return @{} }
    $map = @{}
    $resp.value | ForEach-Object { $map[$_.name] = $_.id }
    return $map
}

# ────────────────────────────────────────────────────────────────────────────────
# STEP 4 – RLS Sync: read blueprint security_roles, assign members via Power BI REST
# ────────────────────────────────────────────────────────────────────────────────

function Read-BlueprintRoles {
    # Parse security_roles from domain Blueprint YAML via Python (avoids PowerShell-Yaml dependency)
    param([string]$RepoRoot, [string]$DomainName)
    $blueprintPath = Join-Path $RepoRoot "products\fabric\powerbi\blueprints\$DomainName.yaml"
    if (-not (Test-Path $blueprintPath)) { return @() }
    $safePath = $blueprintPath -replace "\\", "/"
    $pyScript = "import yaml,json,sys; d=yaml.safe_load(open(r'$safePath',encoding='utf-8')); print(json.dumps(d.get('security_roles',[])))"
    try {
        $json = & python -c $pyScript 2>$null
        if ($json) { return ($json | ConvertFrom-Json) }
    } catch {}
    return @()
}

function Sync-RLSRoles {
    param(
        [string]$WorkspaceId,
        [string]$DatasetId,
        [string]$DomainName,
        [string]$Token,
        [string]$RepoRoot,
        [string]$RlsGroupId    # AAD group object ID for OrgAccess
    )

    if (-not $Token -or -not $WorkspaceId -or -not $DatasetId) {
        Write-Host "  [SKIP] RLS sync skipped – missing token, workspace, or dataset ID." -ForegroundColor Yellow
        return
    }

    $roles = Read-BlueprintRoles -RepoRoot $RepoRoot -DomainName $DomainName
    if (-not $roles -or $roles.Count -eq 0) {
        Write-Host "  No security_roles in $DomainName blueprint – nothing to sync." -ForegroundColor Gray
        return
    }

    foreach ($role in $roles) {
        $roleName = $role.id
        if (-not $roleName) { continue }

        # Collect members: from FABRIC_RLS_GROUP_ID env var + blueprint members list
        $members = [System.Collections.Generic.List[hashtable]]::new()

        $effectiveGroupId = if ($RlsGroupId) { $RlsGroupId } `
                            elseif ($env:FABRIC_RLS_GROUP_ID) { $env:FABRIC_RLS_GROUP_ID } `
                            else { $null }
        if ($effectiveGroupId) {
            $members.Add(@{ memberType = "Group"; memberName = $effectiveGroupId })
        }

        # Blueprint-defined members (optional; format: {type: "Group"|"User", id: "..."})
        if ($role.PSObject.Properties.Name -contains 'members' -and $role.members) {
            foreach ($m in $role.members) {
                $mType = if ($m.PSObject.Properties.Name -contains 'type') { $m.type } else { "User" }
                $mName = if ($m.PSObject.Properties.Name -contains 'id')   { $m.id }   else { $m.name }
                if ($mName) { $members.Add(@{ memberType = $mType; memberName = $mName }) }
            }
        }

        if ($members.Count -eq 0) {
            Write-Host "  Role '$roleName': no members configured (set FABRIC_RLS_GROUP_ID)." -ForegroundColor Gray
            continue
        }

        if ($DryRun) {
            Write-Host "  [DRY-RUN] Would PUT /groups/$WorkspaceId/datasets/$DatasetId/security { role=$roleName, members=$($members.Count) }" -ForegroundColor Cyan
            continue
        }

        # PUT /groups/{workspaceId}/datasets/{datasetId}/security
        # Power BI REST: replaces current member list for the specified role
        $body   = @{ role = $roleName; members = @($members) }
        $result = Invoke-PBIREST -Method Put `
            -Path "/groups/$WorkspaceId/datasets/$DatasetId/security" `
            -Token $Token -Body $body -Silent

        if ($null -ne $result) {
            Write-Host "  Role '$roleName': $($members.Count) member(s) synced." -ForegroundColor Green
        } else {
            # 204 No Content returns $null; treat as success if no exception was thrown
            Write-Host "  Role '$roleName': PUT returned null (may be 204 OK or permission issue)." -ForegroundColor Yellow
        }
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# STEP 5 – Refresh schedule: PATCH datasets/{id}/refreshSchedule
# ────────────────────────────────────────────────────────────────────────────────

function Set-RefreshSchedule {
    param(
        [string]$WorkspaceId,
        [string]$DatasetId,
        [string]$Token,
        [string[]]$Days   = @("Monday","Tuesday","Wednesday","Thursday","Friday"),
        [string[]]$Times  = @("05:00","13:00"),
        [string]$TimeZone = "UTC"
    )
    if (-not $Token -or -not $DatasetId) {
        Write-Host "  [SKIP] Refresh schedule: no token or dataset ID." -ForegroundColor Gray
        return
    }

    $body = @{
        value = @{
            enabled         = $true
            days            = $Days
            times           = $Times
            localTimeZoneId = $TimeZone
            notifyOption    = "NoNotification"
        }
    }

    if ($DryRun) {
        Write-Host "  [DRY-RUN] Would PATCH refreshSchedule for $DatasetId ($($Days -join ',') @ $($Times -join ',') $TimeZone)" -ForegroundColor Cyan
        return
    }

    # Use group-scoped path when workspaceId is available (avoids "My workspace" ambiguity)
    $path = if ($WorkspaceId) {
        "/groups/$WorkspaceId/datasets/$DatasetId/refreshSchedule"
    } else {
        "/datasets/$DatasetId/refreshSchedule"
    }

    $result = Invoke-PBIREST -Method Patch -Path $path -Token $Token -Body $body -Silent
    if ($null -ne $result) {
        Write-Host "  Set: $($Days -join ',') @ $($Times -join ', ') $TimeZone" -ForegroundColor Green
    } else {
        # PATCH refreshSchedule returns 200 with body; null usually means permission issue
        Write-Host "  [WARN] refreshSchedule PATCH returned null – check Build permissions on dataset." -ForegroundColor Yellow
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────────

$repoRoot = Resolve-RepoRoot -Provided $Root
Push-Location $repoRoot

# Domain -> SemanticModel display name mapping (mirrors AuroraDomainMapping.ps1)
$domainToModelName = @{
    Commercial  = "Commercial"
    Finance     = "Finance"
    Operations  = "Operations"
    SupplyChain = "SupplyChain"
    Experience  = "Experience"
}

$deployDomains = if ($All) {
    $domainToModelName.Keys | Sort-Object
} else {
    $Domains
}

try {
    $deployResults  = @{}
    $datasetMap     = @{}

    # ── 1. Deploy Gate ──────────────────────────────────────────────────────────
    Write-Host "`n[1/6] Deploy Gate" -ForegroundColor Cyan
    $gateScript = Join-Path $repoRoot "products\fabric\powerbi\orchestrator\deploy_gate.ps1"
    if (Test-Path $gateScript) {
        & $gateScript -Root $repoRoot
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Deploy aborted: gate failed (failed_data_contracts or registry error)." -ForegroundColor Red
            exit 1
        }
        Write-Host "  Gate PASSED." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] deploy_gate.ps1 not found – gate skipped." -ForegroundColor Yellow
    }

    if ($GateOnly) {
        Write-Host "GateOnly mode – exiting after gate." -ForegroundColor Green
        exit 0
    }

    # ── 2. Authentication ───────────────────────────────────────────────────────
    Write-Host "`n[2/6] Authentication" -ForegroundColor Cyan
    $token = Get-OAuthToken
    if ($token) {
        Write-Host "  Bearer token acquired (client credentials)." -ForegroundColor Green
    } else {
        Write-Host "  No token – API steps (workspace, RLS, refresh) will be skipped." -ForegroundColor Yellow
    }

    # ── 3. Workspace ────────────────────────────────────────────────────────────
    Write-Host "`n[3/6] Workspace: '$WorkspaceName'" -ForegroundColor Cyan
    $effectiveCapacityId = if ($CapacityId) { $CapacityId } else { $env:FABRIC_CAPACITY_ID }
    $workspaceId = Get-OrCreate-FabricWorkspace `
        -Name $WorkspaceName -Token $token -CapacityId $effectiveCapacityId
    if ($workspaceId) {
        Write-Host "  Workspace ID: $workspaceId" -ForegroundColor Green
    } else {
        Write-Host "  Workspace ID unavailable – RLS and refresh steps will be skipped." -ForegroundColor Yellow
    }

    # ── 4. Items deploy ─────────────────────────────────────────────────────────
    Write-Host "`n[4/6] Items deploy (SemanticModel + Reports per domain)" -ForegroundColor Cyan
    foreach ($domain in $deployDomains) {
        Write-Host "  -> $domain" -ForegroundColor White
        $ok = Invoke-FabricRelease `
            -RepoRoot    $repoRoot `
            -WorkspaceId (if ($workspaceId) { $workspaceId } else { "" }) `
            -Environment $Environment `
            -Domain      $domain
        $deployResults[$domain] = $ok
        Write-Host "  $domain: $(if ($ok) { 'SUCCESS' } else { 'FAILED' })" `
            -ForegroundColor (if ($ok) { "Green" } else { "Red" })
    }

    # Refresh item maps (dataset display names from Power BI REST)
    if ($token -and $workspaceId) {
        $datasetMap = Get-WorkspaceDatasetMap -WorkspaceId $workspaceId -Token $token
    }

    # ── 5. RLS Sync ─────────────────────────────────────────────────────────────
    if (-not $SkipSecurity) {
        Write-Host "`n[5/6] RLS Sync" -ForegroundColor Cyan
        foreach ($domain in $deployDomains) {
            $modelName = $domainToModelName[$domain]
            $datasetId = if ($datasetMap -and $modelName) { $datasetMap[$modelName] } else { $null }
            Write-Host "  $domain (dataset: $(if ($datasetId) { $datasetId } else { 'not found' }))" -ForegroundColor White
            if (-not $datasetId -and -not $DryRun) {
                Write-Host "  [SKIP] Dataset '$modelName' not found in workspace – deploy may have failed or be async." -ForegroundColor Yellow
                continue
            }
            $rlsWsId  = if ($workspaceId) { $workspaceId } else { "" }
            $rlsDsId  = if ($datasetId)   { $datasetId }   else { "" }
            $rlsToken = if ($token)        { $token }       else { "" }
            Sync-RLSRoles `
                -WorkspaceId  $rlsWsId `
                -DatasetId    $rlsDsId `
                -DomainName   $domain `
                -Token        $rlsToken `
                -RepoRoot     $repoRoot `
                -RlsGroupId   $env:FABRIC_RLS_GROUP_ID
        }
    } else {
        Write-Host "`n[5/6] RLS Sync – SKIPPED (-SkipSecurity)" -ForegroundColor Gray
    }

    # ── 6. Refresh schedule ─────────────────────────────────────────────────────
    if (-not $SkipRefresh) {
        Write-Host "`n[6/6] Refresh schedule" -ForegroundColor Cyan
        foreach ($domain in $deployDomains) {
            $modelName = $domainToModelName[$domain]
            $datasetId = if ($datasetMap -and $modelName) { $datasetMap[$modelName] } else { $null }
            Write-Host "  $domain" -ForegroundColor White
            if (-not $datasetId -and -not $DryRun) {
                Write-Host "  [SKIP] No dataset ID for '$domain'." -ForegroundColor Gray
                continue
            }
            $rfWsId  = if ($workspaceId) { $workspaceId } else { "" }
            $rfDsId  = if ($datasetId)   { $datasetId }   else { "dry-run" }
            $rfToken = if ($token)        { $token }       else { "" }
            Set-RefreshSchedule `
                -WorkspaceId $rfWsId `
                -DatasetId   $rfDsId `
                -Token       $rfToken
        }
    } else {
        Write-Host "`n[6/6] Refresh schedule – SKIPPED (-SkipRefresh)" -ForegroundColor Gray
    }

    # ── Summary ─────────────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host " DEPLOY SUMMARY" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host ("  Environment  : " + $Environment)
    Write-Host ("  Workspace    : $WorkspaceName" + $(if ($workspaceId) { " [$workspaceId]" } else { " [—]" }))
    Write-Host ("  DryRun       : " + $DryRun.IsPresent)
    Write-Host "  Domains      :"
    foreach ($domain in $deployDomains) {
        $ok     = $deployResults[$domain]
        $dsId   = if ($datasetMap[$domainToModelName[$domain]]) { $datasetMap[$domainToModelName[$domain]] } else { "—" }
        $status = if ($null -eq $ok) { "—" } elseif ($ok) { "OK" } else { "FAIL" }
        Write-Host ("    {0,-14} [{1}]   dataset: {2}" -f $domain, $status, $dsId)
    }
    Write-Host "=====================================================" -ForegroundColor Cyan

    exit 0

} finally {
    Pop-Location
}
