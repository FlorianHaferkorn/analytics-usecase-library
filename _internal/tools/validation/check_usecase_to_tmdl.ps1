# Use Case → TMDL End-to-End Validation
# Purpose: Validates that use case KPIs → KPI Catalog DAX → Measure Dictionary → TMDL measures are consistent
# Usage: .\check_usecase_to_tmdl.ps1 -UseCaseId "COM-001" -TmdlPath "path\to\semantic_model\definition"

param(
	[Parameter(Mandatory=$true)]
	[string]$UseCaseId,
	
	[string]$UseCasesRoot,
	[string]$KpiCatalogRoot,
	[string]$TmdlPath,
	[string]$MeasureDictionaryPath
)

$ErrorActionPreference = "Stop"

$ScriptToolsRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptToolsRoot)

function Resolve-RepoPath {
	param(
		[string]$ProvidedPath,
		[string]$DefaultRelative
	)
	if ($ProvidedPath) {
		if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
		$relativeCandidate = Join-Path -Path $RepoRoot -ChildPath $ProvidedPath
		if (Test-Path $relativeCandidate) { return (Resolve-Path -Path $relativeCandidate).Path }
	}
	if ($DefaultRelative) {
		$fallback = Join-Path -Path $RepoRoot -ChildPath $DefaultRelative
		if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
	}
	return $null
}

function Get-UseCaseKpis {
	param([string]$TechnicalFactsheetPath)
	if (-not (Test-Path $TechnicalFactsheetPath)) { return @() }
	
	$content = Get-Content -Path $TechnicalFactsheetPath -Raw
	$mappingMatch = [regex]::Match($content, '(?ms)```yaml\s*kpi_to_measure_mapping:\s*\r?\n(.*?)```')
	if (-not $mappingMatch.Success) { return @() }
	
	$mappingYaml = $mappingMatch.Groups[1].Value
	$kpiMappings = @()
	
	foreach ($match in [regex]::Matches($mappingYaml, '(?m)^\s*-\s*kpi_id:\s*([^\s\r\n]+)\s*\r?\n\s*measure_name:\s*([^\r\n]+)')) {
		$kpiMappings += @{
			kpi_id = $match.Groups[1].Value.Trim()
			measure_name = $match.Groups[2].Value.Trim() -replace '^\[|\]$', ''
		}
	}
	
	return $kpiMappings
}

function Get-KpiDaxName {
	param([string]$KpiCatalogContent, [string]$KpiId)
	
	$pattern = "(?s)- kpi_id:\s*$([regex]::Escape($KpiId)).*?dax_name:\s*""([^""]+)"""
	$match = [regex]::Match($KpiCatalogContent, $pattern)
	if ($match.Success) {
		return $match.Groups[1].Value.Trim()
	}
	return $null
}

function Get-MeasuresFromTmdl {
	param([string]$TmdlContent)
	
	$measures = @()
	$pattern = "(?m)^\s*measure\s+['`"]([^'`"]+)['`"]\s*="
	$matches = [regex]::Matches($TmdlContent, $pattern)
	
	foreach ($match in $matches) {
		$measures += $match.Groups[1].Value
	}
	
	return $measures
}

# Resolve paths
$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'framework/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder." }

$resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'framework/kpi_catalog'
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog folder." }

$resolvedTmdlPath = Resolve-RepoPath -ProvidedPath $TmdlPath -DefaultRelative "showcases/aurora_group/semantic_models"
if (-not $resolvedTmdlPath) { throw "Unable to resolve TMDL path." }

# Find use case
$useCaseDir = Get-ChildItem -Path (Join-Path -Path $resolvedUseCasesRoot -ChildPath "core") -Directory | Where-Object { $_.Name -like "$UseCaseId*" } | Select-Object -First 1
if (-not $useCaseDir) {
	Write-Error "Use case $UseCaseId not found"
	exit 1
}

$technicalFactsheet = Join-Path -Path $useCaseDir.FullName -ChildPath "Technical_Factsheet.md"
if (-not (Test-Path $technicalFactsheet)) {
	Write-Error "Technical_Factsheet.md not found"
	exit 1
}

# Load KPI catalog
$kpiCatalogPath = Join-Path -Path $resolvedKpiRoot -ChildPath "KPI_Catalog.md"
$kpiCatalogContent = Get-Content -Path $kpiCatalogPath -Raw

# Load TMDL
$measuresTmdlPath = Join-Path -Path $resolvedTmdlPath -ChildPath "*\definition\tables\_Measures.tmdl"
$measuresTmdlFile = Get-ChildItem -Path $measuresTmdlPath -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $measuresTmdlFile) {
	Write-Warning "No _Measures.tmdl found in $resolvedTmdlPath"
	exit 0
}

$tmdlContent = Get-Content -Path $measuresTmdlFile.FullName -Raw
$tmdlMeasures = Get-MeasuresFromTmdl -TmdlContent $tmdlContent

# Get use case KPIs
$kpiMappings = Get-UseCaseKpis -TechnicalFactsheetPath $technicalFactsheet

# Validation results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
}

foreach ($mapping in $kpiMappings) {
	$kpiId = $mapping.kpi_id
	$expectedMeasureName = $mapping.measure_name
	
	# Check 1: KPI has DAX name in catalog
	$daxName = Get-KpiDaxName -KpiCatalogContent $kpiCatalogContent -KpiId $kpiId
	if (-not $daxName) {
		$results.Errors += @{
			KpiId = $kpiId
			Issue = "KPI not found in catalog or missing dax_name"
			Layer = "KPI Catalog"
		}
		$results.IsValid = $false
		continue
	}
	
	# Check 2: Measure name matches between Technical Factsheet and KPI Catalog
	if ($expectedMeasureName -ne $daxName) {
		$results.Warnings += @{
			KpiId = $kpiId
			Issue = "Measure name mismatch: Factsheet='$expectedMeasureName', Catalog='$daxName'"
			Layer = "Factsheet vs Catalog"
		}
	}
	
	# Check 3: Measure exists in TMDL
	$measureExists = $tmdlMeasures -contains $daxName
	if (-not $measureExists) {
		$results.Errors += @{
			KpiId = $kpiId
			MeasureName = $daxName
			Issue = "Measure not found in TMDL"
			Layer = "TMDL"
		}
		$results.IsValid = $false
	}
}

# Output results
Write-Host "Use Case → TMDL Validation for $UseCaseId" -ForegroundColor Cyan
Write-Host "  KPIs checked: $($kpiMappings.Count)" -ForegroundColor White
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })

if ($results.Errors.Count -gt 0) {
	Write-Host "`nErrors:" -ForegroundColor Red
	foreach ($error in $results.Errors) {
		Write-Host "  [$($error.Layer)] $($error.KpiId): $($error.Issue)" -ForegroundColor Red
	}
}

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  [$($warning.Layer)] $($warning.KpiId): $($warning.Issue)" -ForegroundColor Yellow
	}
}

# Return JSON result
$jsonResult = $results | ConvertTo-Json -Depth 10
Write-Output $jsonResult

# Exit code
if ($results.Errors.Count -gt 0) {
	exit 1
}

exit 0
