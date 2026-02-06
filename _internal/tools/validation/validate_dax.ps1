# DAX Expression Validator with Auto-Fix
# Purpose: Validate DAX measure expressions against bpa-rules-dax.json and auto-fix common errors
# Usage: .\validate_dax.ps1 -TmdlPath "path\to\definition" -AutoFix

param(
	[Parameter(Mandatory=$true)]
	[string]$TmdlPath,
	
	[switch]$AutoFix,
	
	[string]$BpaRulesPath = "$PSScriptRoot\..\linters\powerbi\bpa-rules-dax.json"
)

$ErrorActionPreference = "Stop"

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
	Fixed = @()
}

# Helper: Extract DAX expression from TMDL measure
function Get-DaxExpression {
	param([string]$Content, [string]$MeasureName)
	
	# Match measure definition: measure 'MeasureName' = <expression>
	$pattern = "(?s)measure\s+['`"]$([regex]::Escape($MeasureName))['`"]\s*=\s*(.+?)(?=\s+formatString|\s+displayFolder|\s+lineageTag|\s*$|\r?\n\s*(?:measure|table|column|//))"
	$match = [regex]::Match($Content, $pattern)
	
	if ($match.Success) {
		return $match.Groups[1].Value.Trim()
	}
	
	return $null
}

# Helper: Extract all measure names and expressions from TMDL
function Get-MeasuresFromTmdl {
	param([string]$Content)
	
	$measures = @()
	
	# Match: measure 'Name' = expression
	$pattern = "(?m)^\s*measure\s+['`"]([^'`"]+)['`"]\s*=\s*(.+?)(?=\s+formatString|\s+displayFolder|\s+lineageTag|\r?\n\s*(?:measure|table|column|//)|$)"
	$matches = [regex]::Matches($Content, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
	
	foreach ($match in $matches) {
		$measureName = $match.Groups[1].Value
		$expression = $match.Groups[2].Value.Trim()
		
		# Remove trailing properties if captured
		$expression = $expression -replace '\s+(formatString|displayFolder|lineageTag):.*$', ''
		
		$measures += @{
			Name = $measureName
			Expression = $expression
		}
	}
	
	return $measures
}

# Helper: Auto-fix DIVIDE (replace / with DIVIDE)
function Fix-DivideOperator {
	param([string]$Expression)
	
	$fixed = $Expression
	
	# Match division operator: number / number (but not in comments or strings)
	# Simple pattern: avoid / in strings, comments, or already DIVIDE()
	$pattern = '(\w+|\])\s*/\s*(\w+|\[)'
	$fixed = [regex]::Replace($fixed, $pattern, {
		param($m)
		$left = $m.Groups[1].Value
		$right = $m.Groups[2].Value
		return "DIVIDE($left, $right)"
	})
	
	return $fixed
}

# Helper: Auto-fix REMOVEFILTERS (replace ALL with REMOVEFILTERS where appropriate)
function Fix-RemoveFilters {
	param([string]$Expression)
	
	$fixed = $Expression
	
	# Replace ALL(table) with REMOVEFILTERS(table) when not in VALUES/ALLSELECTED/ALLEXCEPT/ALLNOBLANKROW context
	# This is a simplified heuristic - full context analysis would be more complex
	$pattern = '(?i)ALL\s*\(\s*([^)]+)\s*\)'
	$fixed = [regex]::Replace($fixed, $pattern, {
		param($m)
		$table = $m.Groups[1].Value
		# Check if it's in a context where ALL is appropriate
		if ($m.Value -match '(VALUES|ALLSELECTED|ALLEXCEPT|ALLNOBLANKROW)') {
			return $m.Value
		}
		return "REMOVEFILTERS($table)"
	})
	
	return $fixed
}

# Validate DAX expression against rules
function Test-DaxExpression {
	param(
		[string]$Expression,
		[string]$MeasureName,
		[string]$FilePath
	)
	
	$violations = @()
	
	foreach ($rule in $bpaRules.rules) {
		$violated = $false
		$message = ""
		
		# Check forbidRegex (error/warn)
		if ($rule.forbidRegex) {
			$forbidMatch = [regex]::Match($Expression, $rule.forbidRegex)
			if ($forbidMatch.Success) {
				# Check allowWhenContains exception
				if ($rule.allowWhenContains) {
					$allowed = $false
					foreach ($allow in $rule.allowWhenContains) {
						if ($Expression -match [regex]::Escape($allow)) {
							$allowed = $true
							break
						}
					}
					if ($allowed) { continue }
				}
				
				$violated = $true
				$message = $rule.description
			}
		}
		
		# Check matchRegex (warn/info)
		if ($rule.matchRegex -and -not $violated) {
			$matchResult = [regex]::Match($Expression, $rule.matchRegex)
			if ($matchResult.Success) {
				# Check allowWhenContains exception
				if ($rule.allowWhenContains) {
					$allowed = $false
					foreach ($allow in $rule.allowWhenContains) {
						if ($Expression -match [regex]::Escape($allow)) {
							$allowed = $true
							break
						}
					}
					if ($allowed) { continue }
				}
				
				$violated = $true
				$message = $rule.description
			}
		}
		
		# Check mustContain (warn)
		if ($rule.mustContain -and -not $violated) {
			$hasMatch = $false
			foreach ($matchItem in $rule.match.any) {
				if ($Expression -match [regex]::Escape($matchItem)) {
					$hasMatch = $true
					break
				}
			}
			
			if ($hasMatch) {
				$hasRequired = $false
				foreach ($required in $rule.mustContain) {
					if ($Expression -match [regex]::Escape($required)) {
						$hasRequired = $true
						break
					}
				}
				
				if (-not $hasRequired) {
					$violated = $true
					$message = $rule.description
				}
			}
		}
		
		if ($violated) {
			$violations += @{
				RuleId = $rule.id
				RuleName = $rule.id
				Severity = $rule.severity
				Description = $message
				MeasureName = $MeasureName
				FilePath = $FilePath
			}
		}
	}
	
	return $violations
}

# Process all TMDL files
Write-Host "Validating DAX expressions in: $TmdlPath" -ForegroundColor Cyan

$tmdlFiles = Get-ChildItem -Path $TmdlPath -Filter "*.tmdl" -Recurse -ErrorAction SilentlyContinue

if (-not $tmdlFiles) {
	Write-Warning "No TMDL files found in: $TmdlPath"
	exit 0
}

foreach ($file in $tmdlFiles) {
	$content = Get-Content -Path $file.FullName -Raw
	$measures = Get-MeasuresFromTmdl -Content $content
	
	if ($measures.Count -eq 0) {
		continue
	}
	
	$fileFixed = $false
	$fixedRules = @()
	
	foreach ($measure in $measures) {
		$violations = Test-DaxExpression -Expression $measure.Expression -MeasureName $measure.Name -FilePath $file.Name
		
		foreach ($violation in $violations) {
			$results.IsValid = $false
			
			$violationObj = @{
				RuleId = $violation.RuleId
				RuleName = $violation.RuleName
				Severity = $violation.Severity
				File = $file.Name
				Measure = $violation.MeasureName
				Description = $violation.Description
			}
			
			if ($violation.Severity -eq "error") {
				$results.Errors += $violationObj
			} elseif ($violation.Severity -eq "warn") {
				$results.Warnings += $violationObj
			} else {
				$results.Info += $violationObj
			}
			
			# Auto-fix if enabled
			if ($AutoFix) {
				$originalExpression = $measure.Expression
				$fixedExpression = $originalExpression
				
				# Fix DIVIDE
				if ($violation.RuleId -eq "dax.divide.preferred") {
					$fixedExpression = Fix-DivideOperator -Expression $fixedExpression
					if ($fixedExpression -ne $originalExpression) {
						$fixedRules += "dax.divide.preferred"
						$fileFixed = $true
					}
				}
				
				# Fix REMOVEFILTERS
				if ($violation.RuleId -eq "dax.removefilters.preferred") {
					$fixedExpression = Fix-RemoveFilters -Expression $fixedExpression
					if ($fixedExpression -ne $originalExpression) {
						$fixedRules += "dax.removefilters.preferred"
						$fileFixed = $true
					}
				}
				
				# Update content if fixed
				if ($fixedExpression -ne $originalExpression) {
					$pattern = "(?s)(measure\s+['`"]$([regex]::Escape($measure.Name))['`"]\s*=\s*)([^\r\n]+)"
					$content = [regex]::Replace($content, $pattern, {
						param($m)
						return $m.Groups[1].Value + $fixedExpression
					})
				}
			}
		}
	}
	
	# Write fixed content
	if ($fileFixed -and $AutoFix) {
		Set-Content -Path $file.FullName -Value $content -NoNewline
		$results.Fixed += @{
			File = $file.Name
			Rules = $fixedRules | Select-Object -Unique
		}
		Write-Host "  Fixed: $($file.Name)" -ForegroundColor Green
	}
}

# Output results
Write-Host "`nValidation Results:" -ForegroundColor Cyan
Write-Host "  Errors: $($results.Errors.Count)" -ForegroundColor $(if ($results.Errors.Count -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $($results.Warnings.Count)" -ForegroundColor $(if ($results.Warnings.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Info: $($results.Info.Count)" -ForegroundColor Cyan
Write-Host "  Fixed: $($results.Fixed.Count)" -ForegroundColor Green

if ($results.Errors.Count -gt 0) {
	Write-Host "`nErrors:" -ForegroundColor Red
	foreach ($error in $results.Errors) {
		Write-Host "  [$($error.RuleId)] $($error.File)::$($error.Measure): $($error.Description)" -ForegroundColor Red
	}
}

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWarnings:" -ForegroundColor Yellow
	foreach ($warning in $results.Warnings) {
		Write-Host "  [$($warning.RuleId)] $($warning.File)::$($warning.Measure): $($warning.Description)" -ForegroundColor Yellow
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
