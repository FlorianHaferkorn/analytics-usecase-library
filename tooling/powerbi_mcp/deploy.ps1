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
#   FABRIC_DATASET_ID or PBI_DATASET_ID (for refresh schedule; or pass -DatasetId)

param(
	[string]$Root = ".",
	[string]$WorkspaceName = "DM_ActionReady",
	[string]$ModelPath,
	[string]$ReportPath,
	[string]$DatasetId,
	[switch]$GateOnly,
	[switch]$SkipRefresh,
	[switch]$SkipSecurity
)

$ErrorActionPreference = "Stop"

# Get Power BI / Fabric access token (client credentials). Requires FABRIC_* or PBI_* env vars.
function Get-PowerBIAccessToken {
	$tenantId = if ($env:FABRIC_TENANT_ID) { $env:FABRIC_TENANT_ID } else { $env:PBI_TENANT_ID }
	$clientId = if ($env:FABRIC_CLIENT_ID) { $env:FABRIC_CLIENT_ID } else { $env:PBI_CLIENT_ID }
	$clientSecret = if ($env:FABRIC_CLIENT_SECRET) { $env:FABRIC_CLIENT_SECRET } else { $env:PBI_CLIENT_SECRET }
	if (-not $tenantId -or -not $clientId -or -not $clientSecret) {
		return $null
	}
	$scope = [System.Net.WebUtility]::UrlEncode("https://analysis.windows.net/powerbi/api/.default")
	$body = "grant_type=client_credentials&client_id=$([System.Net.WebUtility]::UrlEncode($clientId))&client_secret=$([System.Net.WebUtility]::UrlEncode($clientSecret))&scope=$scope"
	$uri = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
	try {
		$response = Invoke-RestMethod -Method Post -Uri $uri -Body $body -ContentType "application/x-www-form-urlencoded"
		return $response.access_token
	} catch {
		Write-Host "  Get-PowerBIAccessToken failed: $_" -ForegroundColor Red
		return $null
	}
}

# Set Power BI dataset refresh schedule via REST. See: https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/update-refresh-schedule
function Set-PowerBIRefreshSchedule {
	param(
		[Parameter(Mandatory = $true)]
		[string]$DatasetId,
		[Parameter(Mandatory = $true)]
		[string]$AccessToken,
		[string[]]$Days = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"),
		[string[]]$Times = @("07:00"),
		[string]$LocalTimeZoneId = "UTC",
		[string]$NotifyOption = "NoNotification"
	)
	$payload = @{
		value = @{
			days             = $Days
			times            = $Times
			localTimeZoneId  = $LocalTimeZoneId
			notifyOption     = $NotifyOption
		}
	} | ConvertTo-Json -Depth 4
	$uri = "https://api.powerbi.com/v1.0/myorg/datasets/$DatasetId/refreshSchedule"
	$headers = @{
		"Authorization" = "Bearer $AccessToken"
		"Content-Type"  = "application/json"
	}
	Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -Body $payload
}

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
	# TODO: GET/POST Fabric workspace API (see internal/technical_backlog.md § Power BI MCP).
	# $workspaceId = ... (from FABRIC_WORKSPACE_ID or lookup by FABRIC_WORKSPACE_NAME)
	Write-Host "  Stub: Workspace name = $WorkspaceName (configure FABRIC_WORKSPACE_ID or use Fabric REST)" -ForegroundColor Gray

	# 3) Semantic Model / Dataset import
	$modelPath = $ModelPath
	if (-not $modelPath) { $modelPath = Join-Path $repoRoot "showcases\aurora_group\semantic_models\CoreActionReady.SemanticModel" }
	Write-Host "Deploy: Semantic Model..." -ForegroundColor Cyan
	# TODO: Import PBIP/TMDL or PBIX to Fabric semantic model API (see internal/technical_backlog.md § Power BI MCP).
	Write-Host "  Stub: Model path = $modelPath" -ForegroundColor Gray

	# 4) Report publish and bind
	$reportPath = $ReportPath
	if (-not $reportPath) { $reportPath = Join-Path $repoRoot "products\fabric_powerbi\dist" }
	Write-Host "Deploy: Report..." -ForegroundColor Cyan
	# TODO: Publish report, bind to dataset (see internal/technical_backlog.md § Power BI MCP).
	Write-Host "  Stub: Report path = $reportPath" -ForegroundColor Gray

	# 5) Refresh schedule (Power BI REST: PATCH datasets/{id}/refreshSchedule)
	if (-not $SkipRefresh) {
		Write-Host "Deploy: Refresh schedule..." -ForegroundColor Cyan
		$datasetId = $DatasetId
		if (-not $datasetId) { $datasetId = if ($env:FABRIC_DATASET_ID) { $env:FABRIC_DATASET_ID } else { $env:PBI_DATASET_ID } }
		$token = Get-PowerBIAccessToken
		if ($datasetId -and $token) {
			try {
				Set-PowerBIRefreshSchedule -DatasetId $datasetId -AccessToken $token
				Write-Host "  Refresh schedule set (weekdays 07:00 UTC, NoNotification)." -ForegroundColor Green
			} catch {
				Write-Host "  Set refresh schedule failed: $_" -ForegroundColor Red
			}
		} else {
			if (-not $datasetId) { Write-Host "  Skipped: no dataset ID. Set -DatasetId or FABRIC_DATASET_ID when semantic model is deployed." -ForegroundColor Gray }
			else { Write-Host "  Skipped: no Power BI token. Set FABRIC_TENANT_ID, FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET (or PBI_*)." -ForegroundColor Gray }
		}
	}

	# 6) Security / RLS
	if (-not $SkipSecurity) {
		Write-Host "Deploy: Security/RLS..." -ForegroundColor Cyan
		# TODO: Apply RLS or security_user_org mapping via API (see internal/technical_backlog.md § Power BI MCP).
		Write-Host "  Stub: Apply RLS/security via API" -ForegroundColor Gray
	}

	Write-Host "Deploy script finished (Fabric REST steps are stubs; add auth and API calls)." -ForegroundColor Yellow
	exit 0
} finally {
	Pop-Location
}
