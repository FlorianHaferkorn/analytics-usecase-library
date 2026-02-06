# Generate Semantic Model TMDL from Blueprint YAML
# Purpose: Generate TMDL semantic model structure from domain blueprint YAML
# Usage: .\generate_semantic_model_from_blueprint.ps1 -Blueprint "showcases/aurora_group/models/Commercial.yaml" -Output "showcases/aurora_group/semantic_models/Commercial.SemanticModel"

param(
	[Parameter(Mandatory=$true)]
	[string]$Blueprint,
	
	[Parameter(Mandatory=$true)]
	[string]$Output,
	
	[string]$KpiCatalogRoot = "framework/kpi_catalog",
	[switch]$SkipMeasures
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

# Resolve paths
$blueprintPath = Resolve-RepoPath -ProvidedPath $Blueprint -DefaultRelative $Blueprint
if (-not $blueprintPath -or -not (Test-Path $blueprintPath)) {
	throw "Blueprint not found: $Blueprint"
}

$outputPath = Resolve-RepoPath -ProvidedPath $Output -DefaultRelative $Output
if (-not $outputPath) {
	$outputPath = Join-Path -Path $RepoRoot -ChildPath $Output
}

# Load blueprint YAML (simple parsing - assumes powershell-yaml module or manual parsing)
$blueprintContent = Get-Content -Path $blueprintPath -Raw

# Extract model metadata
$modelIdMatch = [regex]::Match($blueprintContent, '(?m)^model_id:\s*(.+)$')
$domainMatch = [regex]::Match($blueprintContent, '(?m)^domain:\s*(.+)$')
$descriptionMatch = [regex]::Match($blueprintContent, '(?m)^description:\s*>\s*\r?\n((?:\s+.*\r?\n?)+)')

$modelId = if ($modelIdMatch.Success) { $modelIdMatch.Groups[1].Value.Trim() } else { "model" }
$domain = if ($domainMatch.Success) { $domainMatch.Groups[1].Value.Trim() } else { "Unknown" }
$description = if ($descriptionMatch.Success) { ($descriptionMatch.Groups[1].Value -split "`r?`n" | ForEach-Object { $_.Trim() }) -join " " } else { "$domain Semantic Model" }

Write-Host "Generating semantic model from blueprint: $blueprintPath" -ForegroundColor Cyan
Write-Host "  Model ID: $modelId" -ForegroundColor Gray
Write-Host "  Domain: $domain" -ForegroundColor Gray
Write-Host "  Output: $outputPath" -ForegroundColor Gray

# Create output directory structure
$definitionPath = Join-Path -Path $outputPath -ChildPath "definition"
$tablesPath = Join-Path -Path $definitionPath -ChildPath "tables"
$relationshipsPath = Join-Path -Path $definitionPath -ChildPath "relationships"

if (-not (Test-Path $definitionPath)) {
	New-Item -ItemType Directory -Path $definitionPath -Force | Out-Null
}
if (-not (Test-Path $tablesPath)) {
	New-Item -ItemType Directory -Path $tablesPath -Force | Out-Null
}
if (-not (Test-Path $relationshipsPath)) {
	New-Item -ItemType Directory -Path $relationshipsPath -Force | Out-Null
}

# Generate model.tmdl
$modelTmdl = @"
model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: PowerBI_V3
	lineageTag: $([System.Guid]::NewGuid().ToString())

"@

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $definitionPath "model.tmdl"), $modelTmdl, $utf8)
Write-Host "  Created model.tmdl" -ForegroundColor Green

# Extract tables from blueprint
$tablesSectionMatch = [regex]::Match($blueprintContent, '(?s)tables:\s*\r?\n(.*?)(?=\r?\nrelationships:|display_folders:|security_roles:|configuration:|notes:|governance:|$)')
if ($tablesSectionMatch.Success) {
	$tablesSection = $tablesSectionMatch.Groups[1].Value
	
	# Extract dimensions
	$dimensionsMatch = [regex]::Match($tablesSection, '(?s)dimensions:\s*\r?\n((?:\s+-\s+.*\r?\n?)+)')
	if ($dimensionsMatch.Success) {
		$dimensions = $dimensionsMatch.Groups[1].Value
		foreach ($dimMatch in [regex]::Matches($dimensions, '(?m)^\s+-\s+table_name:\s*(\w+)')) {
			$tableName = $dimMatch.Groups[1].Value
			Write-Host "  Creating dimension table: $tableName" -ForegroundColor Gray
			
			# Create basic table TMDL (simplified - would need full parsing for columns)
			$tableTmdl = @"
table $tableName
	lineageTag: $([System.Guid]::NewGuid().ToString())

"@
			[System.IO.File]::WriteAllText((Join-Path $tablesPath "$tableName.tmdl"), $tableTmdl, $utf8)
		}
	}
	
	# Extract facts
	$factsMatch = [regex]::Match($tablesSection, '(?s)facts:\s*\r?\n((?:\s+-\s+.*\r?\n?)+)')
	if ($factsMatch.Success) {
		$facts = $factsMatch.Groups[1].Value
		foreach ($factMatch in [regex]::Matches($facts, '(?m)^\s+-\s+table_name:\s*(\w+)')) {
			$tableName = $factMatch.Groups[1].Value
			Write-Host "  Creating fact table: $tableName" -ForegroundColor Gray
			
			$tableTmdl = @"
table $tableName
	lineageTag: $([System.Guid]::NewGuid().ToString())

"@
			[System.IO.File]::WriteAllText((Join-Path $tablesPath "$tableName.tmdl"), $tableTmdl, $utf8)
		}
	}
}

# Extract relationships from blueprint
$relationshipsSectionMatch = [regex]::Match($blueprintContent, '(?s)relationships:\s*\r?\n(.*?)(?=\r?\ndisplay_folders:|security_roles:|configuration:|notes:|governance:|$)')
if ($relationshipsSectionMatch.Success) {
	$relationshipsSection = $relationshipsSectionMatch.Groups[1].Value
	$relCount = 0
	
	foreach ($relMatch in [regex]::Matches($relationshipsSection, '(?m)^\s+-\s+from_table:\s*(\w+)')) {
		$relCount++
		$fromTable = $relMatch.Groups[1].Value
		
		# Find corresponding to_table, from_column, to_column in the same block
		$relBlock = $relMatch.Value
		$toTableMatch = [regex]::Match($relationshipsSection, "(?s)$([regex]::Escape($relBlock)).*?to_table:\s*(\w+)")
		$fromColumnMatch = [regex]::Match($relationshipsSection, "(?s)$([regex]::Escape($relBlock)).*?from_column:\s*(\w+)")
		$toColumnMatch = [regex]::Match($relationshipsSection, "(?s)$([regex]::Escape($relBlock)).*?to_column:\s*(\w+)")
		
		if ($toTableMatch.Success -and $fromColumnMatch.Success -and $toColumnMatch.Success) {
			$toTable = $toTableMatch.Groups[1].Value
			$fromColumn = $fromColumnMatch.Groups[1].Value
			$toColumn = $toColumnMatch.Groups[1].Value
			
			$relName = "rel_$fromTable`_$toTable"
			Write-Host "  Creating relationship: $relName" -ForegroundColor Gray
			
			$relTmdl = @"
relationship $relName = $fromTable[$fromColumn] => $toTable[$toColumn]
	lineageTag: $([System.Guid]::NewGuid().ToString())

"@
			[System.IO.File]::WriteAllText((Join-Path $relationshipsPath "$relName.tmdl"), $relTmdl, $utf8)
		}
	}
	
	if ($relCount -gt 0) {
		Write-Host "  Created $relCount relationships" -ForegroundColor Green
	}
}

# Generate measures if not skipped
if (-not $SkipMeasures) {
	Write-Host "`nGenerating measures..." -ForegroundColor Cyan
	
	# Extract use cases and KPIs from blueprint
	$useCasesMatch = [regex]::Match($blueprintContent, '(?s)use_cases:\s*\r?\n(.*?)(?=\r?\ntables:|relationships:|display_folders:|$)')
	if ($useCasesMatch.Success) {
		$useCasesSection = $useCasesMatch.Groups[1].Value
		$allKpiIds = @()
		
		foreach ($kpiMatch in [regex]::Matches($useCasesSection, '(?m)^\s+-\s+([a-z]+\.[a-z_]+\.[a-z_]+)')) {
			$kpiId = $kpiMatch.Groups[1].Value
			if ($allKpiIds -notcontains $kpiId) {
				$allKpiIds += $kpiId
			}
		}
		
		if ($allKpiIds.Count -gt 0) {
			Write-Host "  Found $($allKpiIds.Count) unique KPIs in blueprint" -ForegroundColor Gray
			
			# Use existing generate_tmdl_measures.ps1 to generate measures
			$generateMeasuresScript = Join-Path $ScriptToolsRoot "generation\generate_tmdl_measures.ps1"
			if (Test-Path $generateMeasuresScript) {
				$measuresOutput = Join-Path $tablesPath "_Measures.tmdl"
				Write-Host "  Calling generate_tmdl_measures.ps1..." -ForegroundColor Gray
				
				# Note: This would need to be adapted to work with blueprint KPIs directly
				# For now, we'll create a placeholder
				$measuresTmdl = @"
/// $domain Measures
/// Generated from blueprint: $([System.IO.Path]::GetFileName($blueprintPath))
/// KPIs: $($allKpiIds.Count) total

table _Measures
	lineageTag: $([System.Guid]::NewGuid().ToString())

"@
				[System.IO.File]::WriteAllText($measuresOutput, $measuresTmdl, $utf8)
				Write-Host "  Created _Measures.tmdl placeholder" -ForegroundColor Yellow
				Write-Host "  Note: Run generate_tmdl_measures.ps1 separately to populate measures" -ForegroundColor Yellow
			}
		}
	}
}

Write-Host "`nSemantic model structure generated successfully!" -ForegroundColor Green
Write-Host "  Output directory: $outputPath" -ForegroundColor Gray
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Populate table columns from data contracts" -ForegroundColor White
Write-Host "  2. Run generate_tmdl_measures.ps1 to add measures" -ForegroundColor White
Write-Host "  3. Validate with validate_tmdl.ps1" -ForegroundColor White
