# Deploy Semantic Model and Report to Fabric (or Power BI).
# 1) Runs deploy_gate.ps1 (Zero-Tolerance: no deploy if failed_data_contracts or registry errors).
# 2) Workspace create/get (Fabric REST or Power BI groups API).
# 3) Semantic Model / Dataset import.
# 4) Report publish and bind to dataset.
# 5) Refresh schedule (optional).
# 6) Security/RLS (optional).
#
# Configuration: set env vars (do not commit secrets):
#   FABRIC_TENANT_ID, FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET (or PBI_* equivalents)
#   FABRIC_WORKSPACE_NAME or FABRIC_WORKSPACE_ID

param(
	[string]$Root = ".",
	[string]$WorkspaceName = "DM_ActionReady",
	[string]$ModelPath,
	[string]$ReportPath,
	[switch]$GateOnly,
	[switch]$SkipRefresh,
	[switch]$SkipSecurity
)

$ErrorActionPreference = "Stop"

$repoRoot = if ($Root -and (Test-Path $Root)) { (Resolve-Path $Root).Path } else { (Get-Location).Path }
Push-Location $repoRoot

try {
	# 1) Deploy Gate – must pass before any API calls
	$gateScript = Join-Path $repoRoot "tooling\powerbi_mcp\deploy_gate.ps1"
	if (-not (Test-Path $gateScript)) { throw "deploy_gate.ps1 not found." }
	& $gateScript -Root $repoRoot
	if ($LASTEXITCODE -ne 0) {
		Write-Host "Deploy aborted: gate failed (failed_data_contracts or registry error)." -ForegroundColor Red
		exit 1
	}
	if ($GateOnly) {
		Write-Host "GateOnly: gate passed; skipping deploy steps." -ForegroundColor Green
		exit 0
	}

	# 2) Workspace – Fabric REST or Power BI
	Write-Host "Deploy: Workspace (Fabric/Power BI)..." -ForegroundColor Cyan
	# TODO: GET/POST Fabric workspace API
	# $workspaceId = ... (from FABRIC_WORKSPACE_ID or lookup by FABRIC_WORKSPACE_NAME)
	Write-Host "  Stub: Workspace name = $WorkspaceName (configure FABRIC_WORKSPACE_ID or use Fabric REST)" -ForegroundColor Gray

	# 3) Semantic Model / Dataset import
	$modelPath = $ModelPath
	if (-not $modelPath) { $modelPath = Join-Path $repoRoot "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel" }
	Write-Host "Deploy: Semantic Model..." -ForegroundColor Cyan
	# TODO: Import PBIP/TMDL or PBIX to Fabric semantic model API
	Write-Host "  Stub: Model path = $modelPath" -ForegroundColor Gray

	# 4) Report publish and bind
	$reportPath = $ReportPath
	if (-not $reportPath) { $reportPath = Join-Path $repoRoot "products\fabric_powerbi\dist" }
	Write-Host "Deploy: Report..." -ForegroundColor Cyan
	# TODO: Publish report, bind to dataset
	Write-Host "  Stub: Report path = $reportPath" -ForegroundColor Gray

	# 5) Refresh schedule
	if (-not $SkipRefresh) {
		Write-Host "Deploy: Refresh schedule..." -ForegroundColor Cyan
		# TODO: Set refresh schedule via Fabric/Power BI REST
		Write-Host "  Stub: Configure refresh via API" -ForegroundColor Gray
	}

	# 6) Security / RLS
	if (-not $SkipSecurity) {
		Write-Host "Deploy: Security/RLS..." -ForegroundColor Cyan
		# TODO: Apply RLS or security_user_org mapping via API
		Write-Host "  Stub: Apply RLS/security via API" -ForegroundColor Gray
	}

	Write-Host "Deploy script finished (Fabric REST steps are stubs; add auth and API calls)." -ForegroundColor Yellow
	exit 0
} finally {
	Pop-Location
}
