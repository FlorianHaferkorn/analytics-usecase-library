# User hierarchy definitions from Data Contract or Bracket.
# Outputs hierarchy level order (e.g. Region > Country > OrgName) for MCP or JSON export.

param(
	[ValidateSet("List", "FromContract", "FromBracket", "WriteToTmdl")]
	[string]$Operation = "List",
	[string]$DataContractPath,
	[string]$BracketPath,
	[string]$DefinitionPath,
	[string]$HierarchyJsonPath,
	[string]$RepoRoot = ".",
	[string]$OutJsonPath
)

$ErrorActionPreference = "Stop"

function Get-HierarchiesFromContract {
	param([object]$Contract)
	$hierarchies = [System.Collections.Generic.List[object]]::new()
	$dims = @($Contract.dimension)
	foreach ($dim in $dims) {
		if (-not $dim.name -or -not $dim.columns) { continue }
		# Infer hierarchy from column order: key first, then attributes that look like levels (e.g. Region, Country, Name)
		$levels = @()
		foreach ($col in $dim.columns) {
			$n = $col.name
			if ($n -match 'Key$') { continue }
			$levels += $n
		}
		if ($levels.Count -ge 2) {
			$hierarchies.Add(@{
				table    = $dim.name
				name     = "$($dim.name)_Hierarchy"
				levels   = $levels
			})
		}
	}
	return $hierarchies
}

function Get-TmdlLevelLine {
	param([string]$ColumnName)
	$display = $ColumnName
	$quoted = if ($display -match '\s' -or $display -match "'") { "'$($display.Replace("'","''"))'" } else { $display }
	return "level $quoted"
}

if ($RepoRoot -eq ".") { $RepoRoot = (Get-Location).Path }

switch ($Operation) {
	"FromContract" {
		if (-not $DataContractPath -or -not (Test-Path $DataContractPath)) {
			throw "-DataContractPath required and must exist"
		}
		$contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
		$hierarchies = Get-HierarchiesFromContract -Contract $contract
		Write-Host "Hierarchies from contract: $($hierarchies.Count)" -ForegroundColor Cyan
		foreach ($h in $hierarchies) {
			Write-Host "  $($h.table): $($h.levels -join ' > ')" -ForegroundColor Gray
		}
		if ($OutJsonPath) {
			@{ hierarchies = $hierarchies; source = $DataContractPath; timestamp = (Get-Date -Format "o") } | ConvertTo-Json -Depth 4 | Set-Content -Path $OutJsonPath -Encoding utf8
			Write-Host "  Wrote: $OutJsonPath" -ForegroundColor Gray
		}
		return $hierarchies
	}
	"FromBracket" {
		if (-not $BracketPath -or -not (Test-Path $BracketPath)) {
			throw "-BracketPath required and must exist"
		}
		$bracket = Get-Content $BracketPath -Raw | ConvertFrom-Yaml
		$overrides = $bracket.overrides
		$contractRef = if ($overrides -and $overrides.data_contract_ref) { $overrides.data_contract_ref.Trim().Replace("/", "\") } else { $null }
		if (-not $contractRef) {
			Write-Host "  No data_contract_ref in bracket; skipping hierarchies" -ForegroundColor Yellow
			return @()
		}
		$contractPath = Join-Path $RepoRoot $contractRef
		if (-not (Test-Path $contractPath)) {
			Write-Host "  Contract not found: $contractPath" -ForegroundColor Yellow
			return @()
		}
		$contract = Get-Content $contractPath -Raw | ConvertFrom-Yaml
		$hierarchies = Get-HierarchiesFromContract -Contract $contract
		Write-Host "Hierarchies from bracket + contract: $($hierarchies.Count)" -ForegroundColor Cyan
		foreach ($h in $hierarchies) {
			Write-Host "  $($h.table): $($h.levels -join ' > ')" -ForegroundColor Gray
		}
		if ($OutJsonPath) {
			@{ hierarchies = $hierarchies; bracket = $BracketPath; source = $contractPath; timestamp = (Get-Date -Format "o") } | ConvertTo-Json -Depth 4 | Set-Content -Path $OutJsonPath -Encoding utf8
			Write-Host "  Wrote: $OutJsonPath" -ForegroundColor Gray
		}
		return $hierarchies
	}
	"WriteToTmdl" {
		if (-not $DefinitionPath -or -not (Test-Path $DefinitionPath)) {
			throw "-DefinitionPath required and must exist for WriteToTmdl"
		}
		$hierarchies = $null
		if ($DataContractPath -and (Test-Path $DataContractPath)) {
			$contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
			$hierarchies = Get-HierarchiesFromContract -Contract $contract
		} elseif ($HierarchyJsonPath -and (Test-Path $HierarchyJsonPath)) {
			$json = Get-Content $HierarchyJsonPath -Raw | ConvertFrom-Json
			$hierarchies = @($json.hierarchies)
		} else {
			throw "Provide -DataContractPath or -HierarchyJsonPath for WriteToTmdl"
		}
		$tablesDir = Join-Path $DefinitionPath "tables"
		if (-not (Test-Path $tablesDir)) {
			Write-Host "  No tables directory: $tablesDir" -ForegroundColor Yellow
			return @()
		}
		$written = 0
		foreach ($h in $hierarchies) {
			$tableName = $h.table
			$tmdlPath = Join-Path $tablesDir "$tableName.tmdl"
			if (-not (Test-Path $tmdlPath)) {
				Write-Host "  Skip (no table TMDL): $tableName" -ForegroundColor DarkGray
				continue
			}
			$name = $h.name
			$levels = @($h.levels)
			if ($levels.Count -lt 2) {
				Write-Host "  Skip (need >= 2 levels): $tableName" -ForegroundColor DarkGray
				continue
			}
			$content = [System.IO.File]::ReadAllText($tmdlPath)
			$hierarchyNameEscaped = [regex]::Escape($name)
			if ($content -match "hierarchy\s+(?:'$hierarchyNameEscaped'|$hierarchyNameEscaped)(?:\s|`$)") {
				Write-Host "  Already has hierarchy: $tableName / $name" -ForegroundColor DarkGray
				continue
			}
			$lines = $content -split "\r?\n"
			$insertAt = -1
			for ($i = 0; $i -lt $lines.Count; $i++) {
				if ($lines[$i] -match '^\tpartition\s+\w+\s*=\s*m') {
					$insertAt = $i
					break
				}
			}
			if ($insertAt -lt 0) {
				Write-Host "  No partition block in $tableName" -ForegroundColor Yellow
				continue
			}
			$hierLineage = [guid]::NewGuid().ToString("n").Substring(0, 8)
			$nameQuoted = if ($name -match '\s' -or $name -match "'") { "'$($name.Replace("'","''"))'" } else { $name }
			$block = @()
			$block += "`thierarchy $nameQuoted"
			$block += "`t`tlineageTag: $hierLineage"
			foreach ($lev in $levels) {
				$block += ""
				$block += "`t`t$(Get-TmdlLevelLine -ColumnName $lev)"
				$block += "`t`t`tlineageTag: $([guid]::NewGuid().ToString('n').Substring(0,8))"
				$block += "`t`t`tcolumn: $lev"
			}
			$block += ""
			$newLines = @()
			for ($i = 0; $i -lt $insertAt; $i++) { $newLines += $lines[$i] }
			$newLines += $block
			for ($i = $insertAt; $i -lt $lines.Count; $i++) { $newLines += $lines[$i] }
			$newContent = $newLines -join "`r`n"
			$utf8 = New-Object System.Text.UTF8Encoding $false
			[System.IO.File]::WriteAllText($tmdlPath, $newContent, $utf8)
			$written++
			Write-Host "  Wrote hierarchy $name to $tableName ($($levels -join ' > '))" -ForegroundColor Green
		}
		Write-Host "  WriteToTmdl: $written hierarchy/blocks written" -ForegroundColor Cyan
		return $hierarchies
	}
	"List" {
		Write-Host "Use -Operation FromContract -DataContractPath <path> or -Operation FromBracket -BracketPath <path> or -Operation WriteToTmdl -DefinitionPath <path> -DataContractPath|<HierarchyJsonPath>" -ForegroundColor Gray
		return @()
	}
	default {
		Write-Host "Operation '$Operation' not implemented" -ForegroundColor Yellow
		return @()
	}
}
