# TMDL Syntax Validator with Auto-Fix
# Purpose: Validate TMDL files against bpa-rules-tmdl.json and auto-fix common errors
# Usage: .\validate_tmdl.ps1 -TmdlPath "path\to\definition" -AutoFix

param(
	[Parameter(Mandatory=$true)]
	[string]$TmdlPath,
	
	[switch]$AutoFix,
	
	[string]$BpaRulesPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $BpaRulesPath) {
	$BpaRulesPath = Join-Path $PSScriptRoot "..\linters\powerbi\bpa-rules-tmdl.json"
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
	Fixed = @()
}

function Test-MeasureDocumentationWarnings {
	param([string]$Content)

	$warnings = @()
	$lines = $Content -split "`r?`n"
	for ($i = 0; $i -lt $lines.Count; $i++) {
		if ($lines[$i] -match '^\s*measure\s+') {
			$prev = $i - 1
			while ($prev -ge 0 -and $lines[$prev] -match '^\s*$') {
				$prev--
			}
			if ($prev -lt 0 -or $lines[$prev] -notmatch '^\s*///') {
				$warnings += $lines[$i]
			}
		}
	}
	return $warnings
}

function Test-CalculatedColumnWarnings {
	param([string]$Content)

	return @([regex]::Matches($Content, '(?m)^\s*column\s+[''\"]?[^''\"=\r\n]+[''\"]?\s*=\s*') | ForEach-Object { $_.Value })
}

# Helper: Convert description: property to /// comment
function Convert-DescriptionToComment {
	param([string]$Content)
	
	$lines = $Content -split "`r?`n"
	$output = @()
	$i = 0
	
	while ($i -lt $lines.Count) {
		$line = $lines[$i]
		
		# Match: "  description: "Total sales amount"
		if ($line -match '^\s+description:\s+"(.+)"') {
			$comment = $matches[1]
			if ($line -match '^(\s+)') {
				$indent = $matches[1]
			} else {
				$indent = ""
			}
			
			# Find previous non-empty line (measure/column definition)
			$prevIdx = $i - 1
			while ($prevIdx -ge 0 -and $lines[$prevIdx] -match '^\s*$') {
				$prevIdx--
			}
			
			# Insert /// comment before measure/column
			if ($prevIdx -ge 0) {
				$output += "$indent/// $comment"
			}
			# Skip description: line
			$i++
			continue
		}
		
		$output += $line
		$i++
	}
	
	return ($output -join "`n")
}

# Helper: Wrap inline M-expression in let...in block
function Wrap-InLetBlock {
	param([string]$Content)
	
	$lines = $Content -split "`r?`n"
	$output = @()
	$i = 0
	
	while ($i -lt $lines.Count) {
		$line = $lines[$i]
		
		# Match: "  source = #table(...)"
		if ($line -match '^\s+source\s*=\s*#table\(' -and $Content -notmatch 'let\s+Source') {
			if ($line -match '^(\s+)') {
				$indent = $matches[1]
			} else {
				$indent = "`t`t"
			}
			$expression = $line -replace '^\s+source\s*=\s*', ''
			
			# Reconstruct with let...in
			$output += "$indent`source ="
			$output += "$indent`t`tlet"
			$output += "$indent`t`t`tSource = $expression"
			$output += "$indent`t`tin"
			$output += "$indent`t`t`tSource"
			
			$i++
			continue
		}
		
		$output += $line
		$i++
	}
	
	return ($output -join "`n")
}

# Helper: Generate GUID for lineageTag
function Add-LineageTag {
	param([string]$Content)
	
	$lines = $Content -split "`r?`n"
	$output = @()
	$i = 0
	
	while ($i -lt $lines.Count) {
		$line = $lines[$i]
		
		# Match table/column definition without lineageTag (skip measure: DAX expression must be first; lineageTag before it causes parser error)
		if ($line -match '^\s*(table|column)\s+' -and $Content -notmatch "lineageTag:") {
			if ($line -match '^(\s+)') {
				$indent = $matches[1]
			} else {
				$indent = ""
			}
			# TMDL: table direct props = 1 tab; column (under table) = indent + 1 tab
			$propIndent = if ($indent) { $indent + "`t" } else { "`t" }
			$guid = [System.Guid]::NewGuid().ToString()
			
			$output += $line
			$output += "${propIndent}lineageTag: $guid"
			
			$i++
			continue
		}
		
		$output += $line
		$i++
	}
	
	return ($output -join "`n")
}

# Process all TMDL files
Write-Host "Validating TMDL files in: $TmdlPath" -ForegroundColor Cyan

$tmdlFiles = Get-ChildItem -Path $TmdlPath -Filter "*.tmdl" -Recurse

foreach ($file in $tmdlFiles) {
	Write-Host "`nProcessing: $($file.Name)" -ForegroundColor Gray
	
	$content = Get-Content $file.FullName -Raw
	$modified = $false
	$fixedRules = @()
	
	# Apply BPA Rules
	foreach ($rule in $bpaRules.rules) {
		$ruleMatches = $false
		$specialMatches = @()

		switch ($rule.id) {
			"TMDL-006" {
				$specialMatches = Test-MeasureDocumentationWarnings -Content $content
				$ruleMatches = ($specialMatches.Count -gt 0)
			}
			"TMDL-007" {
				$specialMatches = Test-CalculatedColumnWarnings -Content $content
				$ruleMatches = ($specialMatches.Count -gt 0)
			}
			default {
		
				# Check pattern match
				if ($rule.pattern -and $content -match $rule.pattern) {
					# Check negative pattern (must NOT match)
					if ($rule.negativePattern -and $content -match $rule.negativePattern) {
						continue
					}
					$ruleMatches = $true
				}
			}
		}
		
		if ($ruleMatches) {
			$issue = @{
				RuleId = $rule.id
				RuleName = $rule.name
				Severity = $rule.severity
				File = $file.Name
				Description = $rule.description
			}
			
			# Categorize by severity
			switch ($rule.severity) {
				"error" { 
					$results.Errors += $issue
					$results.IsValid = $false
				}
				"warning" { $results.Warnings += $issue }
				"info" { $results.Info += $issue }
			}
			
			# Auto-fix if enabled and rule is fixable
			if ($AutoFix -and $rule.autoFixable) {
				Write-Host "  ↻ Auto-fixing: $($rule.id) - $($rule.name)" -ForegroundColor Yellow
				
				switch ($rule.id) {
					"TMDL-001" {
						# Replace Tab+Space with pure TAB
						$content = $content -replace '\t ', "`t"
						$modified = $true
						$fixedRules += $rule.id
					}
					"TMDL-002" {
						# Convert description: to ///
						$content = Convert-DescriptionToComment $content
						$modified = $true
						$fixedRules += $rule.id
					}
					"TMDL-003" {
						# Wrap in let...in
						$content = Wrap-InLetBlock $content
						$modified = $true
						$fixedRules += $rule.id
					}
					"TMDL-010" {
						# Add lineageTag
						$content = Add-LineageTag $content
						$modified = $true
						$fixedRules += $rule.id
					}
				}
			}
		}
	}
	
	# Save fixed content (UTF8 no BOM; PowerShell 5.1 has no UTF8NoBOM enum)
	if ($modified) {
		$utf8NoBom = New-Object System.Text.UTF8Encoding $false
		[System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
		Write-Host "  OK Fixed and saved: $($fixedRules -join ', ')" -ForegroundColor Green
		$results.Fixed += @{
			File = $file.Name
			Rules = $fixedRules
		}
	}
}

# Report Results
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "TMDL Validation Results" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

if ($results.Errors.Count -gt 0) {
	Write-Host "`nERRORS ($($results.Errors.Count)):" -ForegroundColor Red
	foreach ($err in $results.Errors) {
		Write-Host "  [$($err.RuleId)] $($err.File): $($err.RuleName)" -ForegroundColor Red
		Write-Host "    $($err.Description)" -ForegroundColor Gray
	}
}

if ($results.Warnings.Count -gt 0) {
	Write-Host "`nWARNINGS ($($results.Warnings.Count)):" -ForegroundColor Yellow
	foreach ($warn in $results.Warnings) {
		Write-Host "  [$($warn.RuleId)] $($warn.File): $($warn.RuleName)" -ForegroundColor Yellow
	}
}

if ($results.Info.Count -gt 0) {
	Write-Host "`nINFO ($($results.Info.Count)):" -ForegroundColor Cyan
	foreach ($info in $results.Info) {
		Write-Host "  [$($info.RuleId)] $($info.File): $($info.RuleName)" -ForegroundColor Cyan
	}
}

if ($results.Fixed.Count -gt 0) {
	Write-Host "`nAUTO-FIXED ($($results.Fixed.Count) files):" -ForegroundColor Green
	foreach ($fix in $results.Fixed) {
		Write-Host "  $($fix.File): $($fix.Rules -join ', ')" -ForegroundColor Green
	}
}

if ($results.IsValid) {
	Write-Host "`nOK All TMDL files valid!" -ForegroundColor Green
	exit 0
} else {
	Write-Host "`nERROR TMDL validation failed. Fix errors before deployment." -ForegroundColor Red
	
	if (-not $AutoFix -and $results.Errors.Any({ $bpaRules.rules | Where-Object { $_.id -eq $_.RuleId -and $_.autoFixable } })) {
		Write-Host "`nHint: Run with -AutoFix to automatically correct fixable errors." -ForegroundColor Cyan
	}
	
	exit 1
}
