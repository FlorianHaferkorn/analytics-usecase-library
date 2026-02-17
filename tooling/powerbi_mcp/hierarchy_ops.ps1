# User hierarchy definitions from Data Contract or Bracket.
# Outputs hierarchy level order (e.g. Region > Country > OrgName) for MCP or JSON export.

param(
	[ValidateSet("List", "FromContract", "FromBracket")]
	[string]$Operation = "List",
	[string]$DataContractPath,
	[string]$BracketPath,
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
	"List" {
		Write-Host "Use -Operation FromContract -DataContractPath <path> or -Operation FromBracket -BracketPath <path>" -ForegroundColor Gray
		return @()
	}
	default {
		Write-Host "Operation '$Operation' not implemented" -ForegroundColor Yellow
		return @()
	}
}
