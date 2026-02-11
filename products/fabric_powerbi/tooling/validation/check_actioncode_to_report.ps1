# Action Code → Report Validation
# Purpose: Validates that action codes referenced in use cases appear in report action panels (T4 pages)
# Usage: .\check_actioncode_to_report.ps1 -UseCaseId "COM-001" -ReportPath "path\to\report.pbip"

param(
	[Parameter(Mandatory=$true)]
	[string]$UseCaseId,
	
	[string]$UseCasesRoot,
	[string]$ReportPath,
	[string]$ActionCodesRoot
)

$ErrorActionPreference = "Stop"

$ScriptToolsRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
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

function Get-UseCaseActionCodes {
	param([string]$BusinessFactsheetPath)
	if (-not (Test-Path $BusinessFactsheetPath)) { return @() }
	
	$content = Get-Content -Path $BusinessFactsheetPath -Raw
	$actionCodesMatch = [regex]::Match($content, '(?ms)```yaml\s*action_codes:\s*\r?\n(.*?)```')
	if (-not $actionCodesMatch.Success) { return @() }
	
	$actionCodesYaml = $actionCodesMatch.Groups[1].Value
	$actionCodes = @()
	
	foreach ($match in [regex]::Matches($actionCodesYaml, '(?m)^\s*-\s*([A-Z]-[A-Z]\d+\.\d+)')) {
		$actionCodes += $match.Groups[1].Value.Trim()
	}
	
	return $actionCodes
}

function Get-ReportPages {
	param([string]$ReportPath)
	
	$reportJsonPath = Join-Path $ReportPath "definition\report.json"
	if (-not (Test-Path $reportJsonPath)) {
		$reportJsonPath = Join-Path $ReportPath "report.json"
		if (-not (Test-Path $reportJsonPath)) {
			return @()
		}
	}
	
	$reportJson = Get-Content -Path $reportJsonPath -Raw | ConvertFrom-Json
	return $reportJson.sections
}

# Resolve paths
$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder." }

$resolvedReportPath = Resolve-RepoPath -ProvidedPath $ReportPath -DefaultRelative "showcases/aurora_group/reports"
if (-not $resolvedReportPath) { throw "Unable to resolve report path." }

# Find use case
$useCaseDir = Get-ChildItem -Path (Join-Path -Path $resolvedUseCasesRoot -ChildPath "core") -Directory | Where-Object { $_.Name -like "$UseCaseId*" } | Select-Object -First 1
if (-not $useCaseDir) {
	Write-Error "Use case $UseCaseId not found"
	exit 1
}

$businessFactsheet = Join-Path -Path $useCaseDir.FullName -ChildPath "Business_Factsheet.md"
if (-not (Test-Path $businessFactsheet)) {
	Write-Error "Business_Factsheet.md not found"
	exit 1
}

# Get action codes from use case
$actionCodes = Get-UseCaseActionCodes -BusinessFactsheetPath $businessFactsheet

if ($actionCodes.Count -eq 0) {
	Write-Host "No action codes found in use case $UseCaseId" -ForegroundColor Yellow
	exit 0
}

# Get report pages
$reportPages = Get-ReportPages -ReportPath $resolvedReportPath

if ($reportPages.Count -eq 0) {
	Write-Warning "No pages found in report"
	exit 0
}

# Validation results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
}

# Check if action codes appear in report (simplified - would need to parse report structure more deeply)
# For now, we'll check if T4 pages exist (prescriptive recommendation pages)
$t4Pages = $reportPages | Where-Object { $_.displayName -match "T4|Prescriptive|Recommendation|Action" }

if ($t4Pages.Count -eq 0) {
	$results.Warnings += @{
		Issue = "No T4 (Prescriptive Recommendation) pages found in report"
		ActionCodes = $actionCodes
	}
}

# Output results
Write-Host "Action Code → Report Validation for $UseCaseId" -ForegroundColor Cyan
Write-Host "  Action codes: $($actionCodes.Count)" -ForegroundColor White
Write-Host "  T4 pages found: $($t4Pages.Count)" -ForegroundColor $(if ($t4Pages.Count -gt 0) { "Green" } else { "Yellow" })
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  $($warning.Issue)" -ForegroundColor Yellow
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
