# Semantic Model Structure Validator
# Purpose: Validate semantic model structure against bpa-rules-semanticmodel.json
# Usage: .\validate_semanticmodel.ps1 -TmdlPath "path\to\definition" -BpaRulesPath "path\to\bpa-rules-semanticmodel.json"

param(
	[Parameter(Mandatory=$true)]
	[string]$TmdlPath,
	
	[string]$BpaRulesPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $BpaRulesPath) {
	$BpaRulesPath = Join-Path $PSScriptRoot "..\linters\powerbi\bpa-rules-semanticmodel.json"
}

# Load BPA Rules
if (-not (Test-Path $BpaRulesPath)) {
	Write-Error "BPA Rules not found: $BpaRulesPath"
	exit 1
}

$rawRules = Get-Content $BpaRulesPath -Raw | ConvertFrom-Json
if ($rawRules -is [System.Array]) {
	$bpaRules = [PSCustomObject]@{
		rules = @($rawRules | Where-Object { -not $_._meta })
	}
} else {
	$bpaRules = $rawRules
}

# Validation Results
$results = @{
	IsValid = $true
	Errors = @()
	Warnings = @()
	Info = @()
}

# Helper: Parse TMDL relationships
function Get-Relationships {
	param([string]$Content)
	
	$relationships = @()
	$pattern = '(?m)^relationship\s+(\w+)\s*=\s*(\w+)\[(\w+)\]\s*=>\s*(\w+)\[(\w+)\]'
	$matches = [regex]::Matches($Content, $pattern)
	
	foreach ($match in $matches) {
		$relationships += @{
			Name = $match.Groups[1].Value
			FromTable = $match.Groups[2].Value
			FromColumn = $match.Groups[3].Value
			ToTable = $match.Groups[4].Value
			ToColumn = $match.Groups[5].Value
		}
	}
	
	return $relationships
}

# Helper: Parse TMDL tables
function Get-Tables {
	param([string]$Content)
	
	$tables = @()
	$pattern = '(?m)^table\s+(\w+)'
	$matches = [regex]::Matches($Content, $pattern)
	
	foreach ($match in $matches) {
		$tables += $match.Groups[1].Value
	}
	
	return $tables
}

# Helper: Check for calculated columns
function Get-CalculatedColumns {
	param([string]$Content)
	
	$calculatedColumns = @()
	$pattern = '(?m)^\s+column\s+(\w+)\s*=\s*'
	$matches = [regex]::Matches($Content, $pattern)
	
	foreach ($match in $matches) {
		$line = $match.Value
		# Check if it's a calculated column (has expression, not just source column reference)
		if ($line -match '=\s*\{') {
			$calculatedColumns += $match.Groups[1].Value
		}
	}
	
	return $calculatedColumns
}

# Process all TMDL files
Write-Host "Validating semantic model structure in: $TmdlPath" -ForegroundColor Cyan

$tmdlFiles = Get-ChildItem -Path $TmdlPath -Filter "*.tmdl" -Recurse -ErrorAction SilentlyContinue

if (-not $tmdlFiles) {
	Write-Warning "No TMDL files found in: $TmdlPath"
	exit 0
}

$allContent = ($tmdlFiles | Get-Content -Raw) -join "`n"
$relationships = Get-Relationships -Content $allContent
$tables = Get-Tables -Content $allContent
$calculatedColumns = Get-CalculatedColumns -Content $allContent

# Rule: Star schema enforcement (simplified - check for fact tables with relationships)
# Rule: Calculated column avoidance
if ($calculatedColumns.Count -gt 5) {
	$results.Warnings += @{
		RuleId = "REDUCE_NUMBER_OF_CALCULATED_COLUMNS"
		RuleName = "Reduce number of calculated columns"
		Severity = "warning"
		Description = "Model has $($calculatedColumns.Count) calculated columns, recommended maximum is 5"
		Value = $calculatedColumns.Count
		Threshold = 5
	}
}

# Rule: Bi-directional relationship limits (TMDL: crossFilteringBehavior: bothDirections)
$bidirectionalCount = ([regex]::Matches($allContent, '(?mi)crossFilteringBehavior:\s*bothDirections')).Count
$totalRelationships = ([regex]::Matches($allContent, '(?m)^relationship\s+\S+')).Count
if ($totalRelationships -gt 0) {
	$bidirectionalPct = [math]::Round(($bidirectionalCount / $totalRelationships) * 100, 1)
	if ($bidirectionalPct -gt 30) {
		$results.Warnings += @{
			RuleId = "AVOID_EXCESSIVE_BI-DIRECTIONAL_OR_MANY-TO-MANY_RELATIONSHIPS"
			RuleName = "Avoid excessive bi-directional or many-to-many relationships"
			Severity = "warning"
			Description = "$bidirectionalPct% of relationships are bi-directional, recommended maximum is 30%"
			Value = $bidirectionalPct
			Threshold = 30
		}
	}
}

# Rule: Tables should have relationships
$tablesWithoutRelationships = @()
foreach ($table in $tables) {
	$hasRelationship = $relationships | Where-Object { $_.FromTable -eq $table -or $_.ToTable -eq $table }
	if (-not $hasRelationship) {
		$tablesWithoutRelationships += $table
	}
}

if ($tablesWithoutRelationships.Count -gt 0) {
	$results.Info += @{
		RuleId = "ENSURE_TABLES_HAVE_RELATIONSHIPS"
		RuleName = "Ensure tables have relationships"
		Severity = "info"
		Description = "Tables without relationships: $($tablesWithoutRelationships -join ', ')"
		Tables = $tablesWithoutRelationships
	}
}

# Output results
Write-Host "`nValidation Results:" -ForegroundColor Cyan
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Info: $($results.Info.Count)" -ForegroundColor Cyan

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  [$($warning.RuleId)] $($warning.Description)" -ForegroundColor Yellow
	}
}

if ($results.Info.Count -gt 0) {
	Write-Host "`nInfo:" -ForegroundColor Cyan
	foreach ($info in $results.Info) {
		Write-Host "  [$($info.RuleId)] $($info.Description)" -ForegroundColor Cyan
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
