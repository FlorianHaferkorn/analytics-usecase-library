<#
.SYNOPSIS
  Proactive data-contract content audit: lineage alignment and cross-domain duplicate table names.
.DESCRIPTION
  Ensures KPI catalog lineage refs (table.Column) exist in domain data contracts, and flags
  tables defined in more than one domain file. Same pattern as audit_ssot_content.ps1.
.PARAMETER Root
  Repository root (default: current directory).
.PARAMETER KpiCatalogRoot
  Path to core/kpi_catalog.
.PARAMETER OutputDir
  Directory for report files (default: tooling/validation/results).
.PARAMETER FailOnFinding
  If set, exit 1 when any finding exists (for strict CI).
#>
Param(
  [string]$Root = ".",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$OutputDir = "",
  [switch]$FailOnFinding
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = if ($PSScriptRoot) {
  (Get-Item $PSScriptRoot).Parent.Parent.FullName
} else {
  (Get-Location).Path
}
if ($Root -and (Test-Path $Root)) {
  $script:RepoRoot = (Resolve-Path -Path $Root).Path
} elseif ($Root -ne ".") {
  $candidate = Join-Path -Path $script:RepoRoot -ChildPath $Root
  if (Test-Path $candidate) { $script:RepoRoot = (Resolve-Path -Path $candidate).Path }
}

function Resolve-RepoPath {
  param([string]$ProvidedPath, [string]$DefaultRelative)
  if ($ProvidedPath) {
    $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$kpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "core/kpi_catalog"
if (-not $kpiRoot) { throw "KPI catalog root not found." }

$outDir = if ($OutputDir) {
  $resolved = Resolve-RepoPath -ProvidedPath $OutputDir -DefaultRelative $null
  if ($resolved) { $resolved } else { Join-Path $script:RepoRoot $OutputDir }
} else {
  Join-Path $script:RepoRoot "tooling\validation\results"
}
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# Get contract schema via Python
$pyScript = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "get_contract_schema.py"
$schemaJson = & py -3 $pyScript $script:RepoRoot 2>$null
if (-not $schemaJson) { $schemaJson = & python3 $pyScript $script:RepoRoot 2>$null }
if (-not $schemaJson) { $schemaJson = & python $pyScript $script:RepoRoot 2>$null }
if (-not $schemaJson) { throw "Could not run get_contract_schema.py. Ensure Python 3 and PyYAML are available." }
$schema = $schemaJson | ConvertFrom-Json
$contractTables = $schema.tables
$crossDomainDuplicates = $schema.cross_domain_duplicates

# Collect lineage refs from KPI catalog (table.Column where table is dim_* or fact_*)
$catalogPath = Join-Path $kpiRoot "KPI_Catalog.md"
if (-not (Test-Path $catalogPath)) { throw "KPI_Catalog.md not found at $catalogPath" }
$raw = Get-Content -Raw -Path $catalogPath
$lineageRefs = @{}
foreach ($m in [regex]::Matches($raw, '(?m)^\s*-\s+(dim_[a-z0-9_]+|fact_[a-z0-9_]+)\.(.+)$')) {
  $table = $m.Groups[1].Value.Trim()
  $col = $m.Groups[2].Value.Trim()
  $key = "$table.$col"
  if (-not $lineageRefs[$key]) { $lineageRefs[$key] = @{ table = $table; column = $col } }
}

$findings = @()

# Cross-domain duplicate table names
foreach ($dup in $crossDomainDuplicates) {
  $tname = $dup[0]
  $files = $dup[1] -join ', '
  $findings += [pscustomobject]@{
    Severity    = 'Warning'
    Rule        = 'Contract.duplicate_table_name_cross_domain'
    Message     = "Table '$tname' is defined in multiple domain files: $files. Risk of inconsistent grain/columns."
    Location    = $tname
    Remediation = "Define the table in a single domain contract and reference it, or document shared ownership."
  }
}

# Lineage ref not in contract
foreach ($key in $lineageRefs.Keys) {
  $t = $lineageRefs[$key].table
  $c = $lineageRefs[$key].column
  $tMeta = $contractTables.PSObject.Properties[$t].Value
  if (-not $tMeta) {
    $findings += [pscustomobject]@{
      Severity    = 'Warning'
      Rule        = 'Contract.lineage_ref_not_in_contract'
      Message     = "KPI catalog lineage references table '$t' which is not defined in any domain contract."
      Location    = $key
      Remediation = "Add table '$t' to the appropriate domain contract under core/data_contracts/domains/, or fix lineage."
    }
    continue
  }
  $cols = @($tMeta.columns)
  if ($cols -notcontains $c) {
    $findings += [pscustomobject]@{
      Severity    = 'Warning'
      Rule        = 'Contract.lineage_ref_not_in_contract'
      Message     = "KPI catalog lineage references '$key' but column '$c' is not defined on table '$t' in domain contracts."
      Location    = $key
      Remediation = "Add column '$c' to table '$t' in the domain contract, or fix KPI lineage."
    }
  }
}

# Report
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$reportPath = Join-Path $outDir "data_contracts_audit_$timestamp.md"
$jsonPath = Join-Path $outDir "data_contracts_audit_$timestamp.json"

$dupCount = ($findings | Where-Object { $_.Rule -eq 'Contract.duplicate_table_name_cross_domain' }).Count
$lineageCount = ($findings | Where-Object { $_.Rule -eq 'Contract.lineage_ref_not_in_contract' }).Count

$md = @"
# Data Contracts Content Audit Report
Generated: $(Get-Date -Format 'o')
Source: core/data_contracts/domains, KPI catalog lineage
Findings: $($findings.Count)

## Summary
- **Duplicate table name (cross-domain):** $dupCount
- **Lineage ref not in contract:** $lineageCount

## Findings
"@
foreach ($f in $findings) {
  $md += "`n### [$($f.Severity)] $($f.Rule)`n$($f.Message)`n- **Remediation:** $($f.Remediation)`n"
}
if ($findings.Count -eq 0) {
  $md += "`nNo issues found.`n"
}
$md | Set-Content -Path $reportPath -Encoding UTF8

$findings | ConvertTo-Json -Depth 3 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host "Data contracts content audit: $($findings.Count) finding(s). Report: $reportPath" -ForegroundColor $(if ($findings.Count -eq 0) { 'Green' } else { 'Yellow' })
foreach ($f in $findings) {
  Write-Host "  [$($f.Severity)] $($f.Rule): $($f.Message)" -ForegroundColor Gray
}

if ($FailOnFinding -and $findings.Count -gt 0) { exit 1 }
exit 0
