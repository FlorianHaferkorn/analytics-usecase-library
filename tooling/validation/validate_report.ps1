# Power BI Report Validator
# Purpose: Validate Power BI report visuals against bpa-rules-report.json
# Usage: .\validate_report.ps1 -ReportPath "path\to\report.pbip" -BpaRulesPath "path\to\bpa-rules-report.json"

param(
	[Parameter(Mandatory=$true)]
	[string]$ReportPath,
	
	[string]$BpaRulesPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $BpaRulesPath) {
	$BpaRulesPath = Join-Path $PSScriptRoot "..\linters\powerbi\bpa-rules-report.json"
}

# Load BPA Rules
if (-not (Test-Path $BpaRulesPath)) {
	Write-Error "BPA Rules not found: $BpaRulesPath"
	exit 1
}

$bpaRules = Get-Content $BpaRulesPath -Raw | ConvertFrom-Json

# Validation Results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
}

# Helper: Load report JSON (from PBIP structure)
function Get-ReportJson {
	param([string]$ReportPath)
	
	# PBIP structure: report/definition/report.json
	$reportJsonPath = Join-Path $ReportPath "definition\report.json"
	if (-not (Test-Path $reportJsonPath)) {
		# Try alternative: report.json at root
		$reportJsonPath = Join-Path $ReportPath "report.json"
		if (-not (Test-Path $reportJsonPath)) {
			return $null
		}
	}
	
	$content = Get-Content -Path $reportJsonPath -Raw
	return $content | ConvertFrom-Json
}

# Basic validation checks
Write-Host "Validating Power BI report: $ReportPath" -ForegroundColor Cyan

$reportJson = Get-ReportJson -ReportPath $ReportPath

if (-not $reportJson) {
	Write-Error "Could not find report.json in: $ReportPath"
	exit 1
}

# Check pages count
$pages = $reportJson.sections
if ($pages) {
	$pageCount = $pages.Count
	
	# Rule: REDUCE_PAGES (max 10 pages)
	$maxPages = 10
	if ($pageCount -gt $maxPages) {
		$results.IsValid = $false
		$results.Errors += @{
			RuleId = "REDUCE_PAGES"
			RuleName = "Reduce number of pages per report"
			Severity = "error"
			Description = "Report has $pageCount pages, maximum allowed is $maxPages"
			Value = $pageCount
			Threshold = $maxPages
		}
	}
	
	# Check each page
	foreach ($page in $pages) {
		$visuals = $page.visualContainers
		if ($visuals) {
			$visibleVisuals = $visuals | Where-Object { -not $_.isHidden }
			$visualCount = $visibleVisuals.Count
			
			# Rule: REDUCE_VISUALS_ON_PAGE (max 20 visuals)
			$maxVisuals = 20
			if ($visualCount -gt $maxVisuals) {
				$results.Warnings += @{
					RuleId = "REDUCE_VISUALS_ON_PAGE"
					RuleName = "Reduce the number of visible visuals on the page"
					Severity = "warning"
					Page = $page.displayName
					Description = "Page has $visualCount visible visuals, recommended maximum is $maxVisuals"
					Value = $visualCount
					Threshold = $maxVisuals
				}
			}
			
			# Rule: ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY (max height 720px)
			if ($page.height -gt 720) {
				$results.Warnings += @{
					RuleId = "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"
					RuleName = "Ensure pages do not scroll vertically"
					Severity = "warning"
					Page = $page.displayName
					Description = "Page height is $($page.height)px, recommended maximum is 720px"
					Value = $page.height
					Threshold = 720
				}
			}
			
			# Check for alt-text (accessibility)
			foreach ($visual in $visibleVisuals) {
				if (-not $visual.config.altText) {
					$results.Info += @{
						RuleId = "ENSURE_ALTTEXT"
						RuleName = "Ensure alternativeText has been defined for all visuals"
						Severity = "info"
						Page = $page.displayName
						Visual = $visual.name
						Description = "Visual missing alt-text for accessibility"
					}
				}
			}
		}
	}
}

# Output results
Write-Host "`nValidation Results:" -ForegroundColor Cyan
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Info: $($results.Info.Count)" -ForegroundColor Cyan

if ($results.Errors.Count -gt 0) {
	Write-Host "`nErrors:" -ForegroundColor Red
	foreach ($error in $results.Errors) {
		Write-Host "  [$($error.RuleId)] $($error.Description)" -ForegroundColor Red
	}
}

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  [$($warning.RuleId)] $($warning.Page): $($warning.Description)" -ForegroundColor Yellow
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
