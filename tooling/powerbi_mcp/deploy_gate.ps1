# Deploy Gate: Zero-Tolerance. Run before any Fabric/Power BI deploy.
# 1) Validates domain data contracts (check_validate_data_contracts.ps1)
# 2) Builds registry (registry_builder.py --strict)
# 3) Checks master_registry.json for failed_data_contracts
# Exit 0 only when all pass; exit 1 otherwise (blocks deploy).

param(
	[string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
	param([string]$ProvidedPath, [string]$DefaultRelative)
	$repo = (Get-Location).Path
	if ($ProvidedPath) {
		if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
		$candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
		if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
	}
	if ($DefaultRelative) {
		$fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
		if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
	}
	return $null
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

Push-Location $rootPath
try {
	Write-Host "Deploy Gate: Contract validation + Registry + failed_data_contracts check" -ForegroundColor Cyan

	# 1) Data contract validation (writes contract_validation.json)
	$contractCheck = Join-Path $rootPath "tooling\validation\check_validate_data_contracts.ps1"
	if (-not (Test-Path $contractCheck)) { throw "Missing: tooling/validation/check_validate_data_contracts.ps1" }
	& $contractCheck -Root $rootPath -FailOnError
	if ($LASTEXITCODE -ne 0) {
		Write-Host "Deploy Gate FAIL: Data contract validation failed." -ForegroundColor Red
		exit 1
	}

	# 2) Registry builder (reads contract_validation.json, writes master_registry.json)
	$registryCheck = Join-Path $rootPath "tooling\validation\check_registry_builder.ps1"
	if (-not (Test-Path $registryCheck)) { throw "Missing: tooling/validation/check_registry_builder.ps1" }
	& $registryCheck -Root $rootPath -FailOnError
	if ($LASTEXITCODE -ne 0) {
		Write-Host "Deploy Gate FAIL: Registry builder failed." -ForegroundColor Red
		exit 1
	}

	# 3) Zero-tolerance: no deploy if any failed_data_contracts in registry
	$masterPath = Join-Path $rootPath "tooling\ontology\out\master_registry.json"
	if (-not (Test-Path $masterPath)) {
		Write-Host "Deploy Gate FAIL: master_registry.json not found." -ForegroundColor Red
		exit 1
	}
	$registry = Get-Content -Path $masterPath -Raw -Encoding utf8 | ConvertFrom-Json
	$failed = @($registry.failed_data_contracts)
	if ($failed.Count -gt 0) {
		Write-Host "Deploy Gate FAIL: failed_data_contracts is non-empty (Zero-Tolerance)." -ForegroundColor Red
		$failed | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
		exit 1
	}

	Write-Host "Deploy Gate PASS: Contracts valid, registry built, no failed_data_contracts." -ForegroundColor Green
	exit 0
} finally {
	Pop-Location
}
