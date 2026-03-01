# Generate PBIR report structure from page template.
# Reads core/templates/page_templates/components/<TemplateName>.json and
# creates <OutputPath>\<UseCase>.Report\definition\report.json with sections (pages) and datasetReference.

param(
	[Parameter(Mandatory = $true)]
	[string]$UseCase,
	[string]$TemplateName = "overview_drivers_details",
	[string]$OutputPath,
	[string]$SemanticModelRelativePath = "../semantic_models/Commercial.SemanticModel"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
if (-not $OutputPath) {
	$OutputPath = Join-Path $repoRoot "products\fabric\powerbi\dist"
}

$templatesRoot = Join-Path $repoRoot "core\templates\page_templates\components"
$templatePath = Join-Path $templatesRoot "$TemplateName.json"
if (-not (Test-Path $templatePath)) {
	Write-Host "Template not found: $templatePath; using minimal default." -ForegroundColor Yellow
	$template = @{
		layout = @{
			sections = @(
				@{ id = "overview"; visuals = @("kpi_cards", "trend_main") },
				@{ id = "details"; visuals = @("ranking_table") }
			)
		}
	}
} else {
	$template = Get-Content $templatePath -Raw | ConvertFrom-Json
}

$reportFolder = Join-Path $OutputPath "$UseCase.Report"
$definitionDir = Join-Path $reportFolder "definition"
if (-not (Test-Path $definitionDir)) {
	New-Item -ItemType Directory -Path $definitionDir -Force | Out-Null
}

$sections = [System.Collections.Generic.List[object]]::new()
$sectionIds = $template.layout.sections
if (-not $sectionIds) {
	$sectionIds = @(@{ id = "Page1"; visuals = @() })
}
$pageIndex = 0
foreach ($sec in $sectionIds) {
	$pageIndex++
	$id = if ($sec.id) { $sec.id } else { "Section$pageIndex" }
	$displayName = $id -replace "_", " " -replace "(\B[A-Z])", " `$1"
	$sections.Add(@{
		id                = $id
		displayName       = $displayName
		visualContainers  = @()
	})
}

$reportJson = @{
	config    = @{
		version = 1
	}
	datasetReference = @{
		byPath = @{
			path = $SemanticModelRelativePath
		}
	}
	sections  = $sections
}

$reportPath = Join-Path $definitionDir "report.json"
$reportJson | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding utf8
Write-Host "Report structure created: $reportPath ($($sections.Count) sections)" -ForegroundColor Green
return $reportFolder
