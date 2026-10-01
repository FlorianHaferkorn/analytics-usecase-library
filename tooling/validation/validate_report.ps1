# Power BI Report Validator
# Purpose: Validate Power BI report visuals against bpa-rules-report.json
# Usage: .\validate_report.ps1 -ReportPath "path\to\report.pbip" -BpaRulesPath "path\to\bpa-rules-report.json"

param(
	[Parameter(Mandatory=$true)]
	[string]$ReportPath,
	
	[string]$BpaRulesPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Exit-WithError {
	param([string]$Message)
	$Host.UI.WriteErrorLine($Message)
	exit 1
}

if (-not $BpaRulesPath) {
	$BpaRulesPath = Join-Path $PSScriptRoot "..\linters\powerbi\bpa-rules-report.json"
}

# Load BPA Rules
if (-not (Test-Path $BpaRulesPath)) {
	Exit-WithError "BPA Rules not found: $BpaRulesPath"
}

$bpaRules = Get-Content $BpaRulesPath -Raw | ConvertFrom-Json

# Validation Results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
}

# Helper: Load report JSON (PBIR only)
# PBIR only (Florian, 01.10.2026). Learn power-bi/developer/projects/projects-report
# (read 01.10.2026): a root report.json holds "the Power BI Report Legacy format
# (PBIR-Legacy)"; the definition\ folder "replaces the report.json file". A root
# report.json is therefore an error, never a fallback.
function Get-ReportJson {
	param([string]$ReportPath)

	$legacyPath = Join-Path $ReportPath "report.json"
	if (Test-Path -LiteralPath $legacyPath) {
		Exit-WithError ("PBIR-Legacy wird nicht mehr akzeptiert: $legacyPath. " +
			"In Power BI Desktop als PBIR speichern (Learn power-bi/developer/projects/projects-report).")
	}

	$reportJsonPath = Join-Path $ReportPath "definition\report.json"
	if (-not (Test-Path -LiteralPath $reportJsonPath)) {
		Exit-WithError "PBIR definition\report.json not found in: $ReportPath"
	}

	$content = Get-Content -LiteralPath $reportJsonPath -Raw -Encoding utf8
	return $content | ConvertFrom-Json
}

# Basic validation checks
Write-Host "Validating Power BI report: $ReportPath" -ForegroundColor Cyan

$reportJson = Get-ReportJson -ReportPath $ReportPath

# Check pages count
# The page/visual rules below read the PBIR-Legacy shape (`sections`/`visualContainers`),
# which PBIR definition\report.json does not carry (pages live in definition\pages\).
# Say so instead of reporting "0 findings" for rules that did not run.
$pages = $null
if ($reportJson.PSObject.Properties['sections']) {
	$pages = $reportJson.sections
} else {
	Write-Warning ("Page/visual rules (REDUCE_PAGES, REDUCE_VISUALS_ON_PAGE, " +
		"ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY, ENSURE_ALTTEXT) not evaluated: " +
		"their reader expects the PBIR-Legacy 'sections' shape.")
}
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
	foreach ($err in $results.Errors) {
		Write-Host "  [$($err.RuleId)] $($err.Description)" -ForegroundColor Red
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
