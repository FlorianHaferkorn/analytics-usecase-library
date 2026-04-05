# Deploy Semantic Model and Report to Fabric (or Power BI).
# 1) Runs deploy_gate.ps1 (Zero-Tolerance: no deploy if failed_data_contracts or registry errors).
# 2) Workspace create/get (Fabric REST or Power BI groups API).
# 3) Semantic Model import — via `fab` if available, az rest fallback otherwise.
# 4) Report publish and bind to dataset.
# 5) Refresh schedule (optional).
# 6) Security/RLS (optional).
#
# Configuration: set env vars (do not commit secrets):
#   FABRIC_TENANT_ID, FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET (or PBI_* equivalents)
#   FABRIC_WORKSPACE_NAME or FABRIC_WORKSPACE_ID
#   FABRIC_DATASET_ID or PBI_DATASET_ID (for refresh schedule; or pass -DatasetId)
#
# Deploy strategy:
#   Primary:  fab import (fast, supports byPath, requires fab CLI authenticated)
#   Fallback: az rest createItemWithDefinition (requires az login, base64 TMDL encoding)
#   Use -ForceFabCli or -ForceAzRest to override auto-detection.

param(
	[string]$Root = ".",
	[string]$WorkspaceName = "DM_ActionReady",
	[string]$WorkspaceId,
	[string]$ModelPath,
	[string]$ReportPath,
	[string]$DatasetId,
	[switch]$GateOnly,
	[switch]$SkipRefresh,
	[switch]$SkipSecurity,
	[switch]$ForceFabCli,
	[switch]$ForceAzRest
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

function Test-Command([string]$Name) {
	return ($null -ne (Get-Command $Name -ErrorAction SilentlyContinue))
}

function Get-FabricToken {
	<#
	.SYNOPSIS
	  Return a Fabric API bearer token using az cli or client credentials.
	#>
	# Try az cli first (interactive sessions)
	if (Test-Command "az") {
		try {
			$token = az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken --output tsv 2>$null
			if ($token) { return $token }
		} catch { }
	}
	# Fall back to client credentials via env vars
	return Get-PowerBIAccessToken
}

function Invoke-FabricRestDeploy {
	<#
	.SYNOPSIS
	  Deploy a PBIP semantic model to Fabric via az rest createItemWithDefinition.
	  Fallback when `fab` CLI is unavailable.
	.PARAMETER ModelPath
	  Path to the .SemanticModel directory (containing definition/).
	.PARAMETER WorkspaceId
	  Target Fabric workspace GUID.
	#>
	param(
		[Parameter(Mandatory)][string]$ModelPath,
		[Parameter(Mandatory)][string]$WorkspaceId
	)

	$defPath = Join-Path $ModelPath "definition"
	if (-not (Test-Path $defPath)) {
		throw "definition/ folder not found in: $ModelPath"
	}

	$modelName = (Get-Item $ModelPath).BaseName -replace "\.SemanticModel$", ""
	Write-Host "  az rest deploy: $modelName → workspace $($WorkspaceId.Substring(0,8))…" -ForegroundColor Cyan

	# Build base64-encoded part list for createItemWithDefinition
	$parts = [System.Collections.ArrayList]::new()
	Get-ChildItem -Path $defPath -Recurse -File | ForEach-Object {
		$relPath = $_.FullName.Replace($defPath, "").TrimStart("/\").Replace("\", "/")
		$bytes   = [System.IO.File]::ReadAllBytes($_.FullName)
		$b64     = [System.Convert]::ToBase64String($bytes)
		[void]$parts.Add(@{
			path    = $relPath
			payload = $b64
			payloadType = "InlineBase64"
		})
	}

	$pbismPath = Join-Path $ModelPath "definition.pbism"
	$pbismPart = $null
	if (Test-Path $pbismPath) {
		$bytes    = [System.IO.File]::ReadAllBytes($pbismPath)
		$b64      = [System.Convert]::ToBase64String($bytes)
		$pbismPart = @{ path = "definition.pbism"; payload = $b64; payloadType = "InlineBase64" }
		[void]$parts.Insert(0, $pbismPart)
	}

	$body = @{
		displayName = $modelName
		type        = "SemanticModel"
		definition  = @{
			parts = $parts.ToArray()
		}
	} | ConvertTo-Json -Depth 10

	$bodyFile = [System.IO.Path]::GetTempFileName()
	$body | Set-Content -Path $bodyFile -Encoding UTF8

	try {
		$apiUrl  = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items"
		$result  = az rest --method POST --url $apiUrl --headers "Content-Type=application/json" --body "@$bodyFile" 2>&1
		if ($LASTEXITCODE -ne 0) {
			throw "az rest failed (exit $LASTEXITCODE): $result"
		}
		$resultObj = $result | ConvertFrom-Json -ErrorAction SilentlyContinue
		$operationId = $resultObj.operationId
		if ($operationId) {
			Write-Host "  LRO started: $operationId — polling..." -ForegroundColor DarkGray
			Invoke-PollLro -WorkspaceId $WorkspaceId -OperationId $operationId
		}
		Write-Host "  az rest deploy: success." -ForegroundColor Green
		return $resultObj
	} finally {
		Remove-Item $bodyFile -ErrorAction SilentlyContinue
	}
}

function Invoke-PollLro {
	<#
	.SYNOPSIS
	  Poll a Fabric LRO operation until it completes (Succeeded) or fails.
	#>
	param(
		[string]$WorkspaceId,
		[string]$OperationId,
		[int]$TimeoutSeconds = 300,
		[int]$PollIntervalSeconds = 5
	)
	$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
	$pollUrl  = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/operations/$OperationId/result"

	while ((Get-Date) -lt $deadline) {
		Start-Sleep -Seconds $PollIntervalSeconds
		$raw = az rest --method GET --url $pollUrl 2>&1
		if ($LASTEXITCODE -ne 0) { break }
		$status = ($raw | ConvertFrom-Json -ErrorAction SilentlyContinue).status
		Write-Host "    LRO status: $status" -ForegroundColor DarkGray
		if ($status -in @("Succeeded", "Completed")) { return }
		if ($status -in @("Failed", "Cancelled")) {
			throw "LRO $OperationId ended with status: $status"
		}
	}
	throw "LRO $OperationId did not complete within $TimeoutSeconds seconds"
}

# ─── Main ─────────────────────────────────────────────────────────────────────

$repoRoot = if ($Root -and (Test-Path $Root)) { (Resolve-Path $Root).Path } else { (Get-Location).Path }
Push-Location $repoRoot

try {
	# 1) Deploy Gate – must pass before any API calls
	$gateScript = Join-Path $repoRoot "products\fabric\powerbi\orchestrator\deploy_gate.ps1"
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

	# 3) Semantic Model import — fab primary, az rest fallback
	$modelPath = $ModelPath
	if (-not $modelPath) { $modelPath = Join-Path $repoRoot "products\fabric\powerbi\dist\Commercial.SemanticModel" }
	Write-Host "Deploy: Semantic Model..." -ForegroundColor Cyan

	$wsId = if ($WorkspaceId) { $WorkspaceId } else { $env:FABRIC_WORKSPACE_ID }

	$fabAvailable = (Test-Command "fab") -and (-not $ForceAzRest)
	$azAvailable  = (Test-Command "az")  -and (-not $ForceFabCli)

	if ($fabAvailable) {
		Write-Host "  Strategy: fab import (primary)" -ForegroundColor DarkGray
		if (-not $wsId) {
			Write-Host "  Skipped: no workspace ID (set -WorkspaceId or FABRIC_WORKSPACE_ID)." -ForegroundColor Yellow
		} else {
			$modelName = (Get-Item $modelPath -ErrorAction SilentlyContinue)?.BaseName
			& fab import "$wsId/$modelName.SemanticModel" -i $modelPath -f
			if ($LASTEXITCODE -ne 0) {
				Write-Host "  fab import failed; trying az rest fallback..." -ForegroundColor Yellow
				if ($azAvailable -and $wsId) {
					Invoke-FabricRestDeploy -ModelPath $modelPath -WorkspaceId $wsId
				} else {
					Write-Host "  No fallback available (az not found or no workspace ID)." -ForegroundColor Red
					exit 1
				}
			} else {
				Write-Host "  fab import: success." -ForegroundColor Green
			}
		}
	} elseif ($azAvailable -and $wsId) {
		Write-Host "  Strategy: az rest createItemWithDefinition (fallback — fab not found)" -ForegroundColor Yellow
		Invoke-FabricRestDeploy -ModelPath $modelPath -WorkspaceId $wsId
	} else {
		Write-Host "  Skipped: neither fab nor az available, or no workspace ID." -ForegroundColor Gray
		Write-Host "    Install fab: https://aka.ms/fabric-cli" -ForegroundColor Gray
		Write-Host "    Install az:  https://aka.ms/azcli" -ForegroundColor Gray
	}

	# 4) Report publish and bind
	$reportPath = $ReportPath
	if (-not $reportPath) { $reportPath = Join-Path $repoRoot "products\fabric\powerbi\dist" }
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
