<#
.SYNOPSIS
  Use-case SSOT readiness: ensure every KPI referenced by use cases has all DAX ingredients in SSOTs and Aurora.
.DESCRIPTION
  For each use case (by domain), checks that:
  - Each influencing KPI exists in the KPI catalog with DAX.
  - Every [Measure] referenced in DAX has a KPI with that dax_name (or add insertable new KPI block).
  - Every table[column] referenced in DAX exists in the domain data contract and table is in AuroraDomainRequiredTables.
  Output: report with InsertableRemediation (ready-to-paste) per finding. See tooling/validation/docs/REMEDIATION_INSERTABLE_FORMAT.md.
.PARAMETER UseCasesRoot
  Path to core/usecases.
.PARAMETER KpiCatalogRoot
  Path to core/kpi_catalog.
.PARAMETER DataContractsRoot
  Path to core/data_contracts/domains.
.PARAMETER OutputDir
  Report output directory (default: tooling/validation/results).
.PARAMETER FailOnFinding
  If set, exit 1 when any finding exists.
#>
Param(
  [string]$UseCasesRoot = "core/usecases",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$DataContractsRoot = "core/data_contracts/domains",
  [string]$OutputDir = "",
  [switch]$FailOnFinding
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = if ($PSScriptRoot) {
  $p = Split-Path -Parent $PSScriptRoot   # tooling
  Split-Path -Parent $p                   # repo root
} else { Get-Location | Select-Object -ExpandProperty Path }

function Resolve-RepoPath {
  param([string]$ProvidedPath, [string]$DefaultRelative)
  $toTry = @()
  if ($ProvidedPath) {
    $toTry += if ([System.IO.Path]::IsPathRooted($ProvidedPath)) { $ProvidedPath } else { Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath }
  }
  if ($DefaultRelative) {
    $toTry += Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
  }
  foreach ($p in $toTry) {
    if ($p -and (Test-Path $p)) { return (Resolve-Path -Path $p).Path }
  }
  return $null
}

# Domain prefix -> domain display name (must match AuroraDomainMapping)
$script:PrefixToDomain = @{ COM = "Commercial"; FIN = "Finance"; OPS = "Operations"; SCM = "SupplyChain"; XD = "Experience" }
$script:DomainToContract = @{
  Commercial  = "commercial_sales.yaml"
  Finance     = "finance.yaml"
  Operations  = "operations.yaml"
  SupplyChain = "supply_chain.yaml"
  Experience  = "experience.yaml"
}

# Parse AuroraDomainRequiredTables from AuroraDomainMapping.ps1
function Get-AuroraRequiredTables {
  $mappingPath = Join-Path $script:RepoRoot "products\fabric\powerbi\orchestrator\AuroraDomainMapping.ps1"
  if (-not (Test-Path $mappingPath)) { return @{} }
  $lines = Get-Content -Path $mappingPath
  $result = @{}
  $inBlock = $false
  foreach ($line in $lines) {
    if ($line -match 'AuroraDomainRequiredTables\s*=\s*@\s*\{') { $inBlock = $true; continue }
    if ($inBlock -and $line -match '^\s*(\w+)\s*=\s*@\s*\(([^)]+)\)') {
      $domain = $Matches[1]
      $tables = $Matches[2] -split ',' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ }
      $result[$domain] = @($tables)
    }
    if ($inBlock -and $line -match '^\s*\}') { break }
  }
  return $result
}

# Extract [MeasureName] from DAX (exclude table[col])
function Get-MeasureRefsFromDax {
  param([string]$Expr)
  if (-not $Expr) { return @() }
  $refs = @()
  foreach ($m in [regex]::Matches($Expr, '\[([^\]]+)\]')) {
    $inner = $m.Groups[1].Value.Trim()
    if ($inner -and $inner -notmatch '\[') { $refs += $inner }
  }
  return $refs | Select-Object -Unique
}

# True if [refName] appears as a column reference (table[refName] or #"T"[refName]) in Expr (avoids false-positive "referenced measure missing")
function Test-RefNameIsColumnInDax {
  param([string]$Expr, [string]$RefName)
  if (-not $Expr -or -not $RefName) { return $false }
  $escaped = [regex]::Escape($RefName.Trim())
  return ($Expr -match "(?:\w+|#""[^""]+"")\s*\[\s*$escaped\s*\]")
}

# DAX keywords that must not be treated as table names
$script:DaxKeywords = @('RETURN', 'VAR', 'BLANK', 'CALCULATE', 'FILTER', 'ALL', 'VALUES', 'DIVIDE', 'SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'IF', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'YEAR', 'MONTH', 'DATE', 'FORMAT', 'CONCATENATE', 'RELATED', 'USERELATIONSHIP', 'KEEPFILTERS', 'REMOVEFILTERS', 'ALLSELECTED', 'SELECTEDVALUE', 'HASONEVALUE', 'ISONORAFTER', 'COALESCE', 'SWITCH')

# Extract table[column] from DAX; returns @(@{table='x'; column='y'}, ...)
function Get-TableColumnRefsFromDax {
  param([string]$Expr)
  if (-not $Expr) { return @() }
  $pairs = @()
  foreach ($m in [regex]::Matches($Expr, '(?:#"([^"]+)"|(\w+))\s*\[\s*([^\]]+)\s*\]')) {
    $table = if ($m.Groups[1].Success -and $m.Groups[1].Value) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    $col = $m.Groups[3].Value.Trim()
    if ($table -and $col -and ($script:DaxKeywords -notcontains $table)) { $pairs += @{ table = $table; column = $col } }
  }
  return $pairs
}

# Get lineage entries as table.Column -> list from KPI chunk
function Get-LineageFromChunk {
  param([string]$Chunk)
  $list = @()
  $block = [regex]::Match($Chunk, "(?m)^\s*lineage\s*:\s*(?:\r?\n)(?<body>(?:\s{2,}-\s*[^\r\n]+\r?\n?)+)")
  if ($block.Success) {
    foreach ($line in ($block.Groups['body'].Value -split "`n")) {
      if ($line -match '^\s{2,}-\s*([^\s#][^\r\n]*)') { $list += $Matches[1].Trim() }
    }
  }
  return $list
}

# Parse domain contract YAML: tables and their columns
function Get-ContractTablesAndColumns {
  param([string]$ContractPath)
  if (-not (Test-Path $ContractPath)) { return @{} }
  $content = Get-Content -Path $ContractPath -Raw
  $result = @{}
  foreach ($section in @('dimension', 'fact')) {
    $sectionBlock = [regex]::Match($content, "(?ms)^$section\s*:\s*\r?\n(?<body>.*?)(?=^[\w#]|\z)")
    if (-not $sectionBlock.Success) { continue }
    $body = $sectionBlock.Groups['body'].Value
    foreach ($tMatch in [regex]::Matches($body, "(?m)^\s+-\s+name:\s+(\w+)\s*\r?\n(.*?)(?=^\s+-\s+name:|\z)", 'Singleline')) {
      $tableName = $tMatch.Groups[1].Value.Trim()
      $tableBlock = $tMatch.Groups[2].Value
      $cols = @()
      foreach ($cMatch in [regex]::Matches($tableBlock, "(?m)^\s+-\s+\{\s*name:\s*([^,}]+)[^}]*\}")) {
        $colName = $cMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
        $cols += $colName
      }
      $result[$tableName] = $cols
    }
  }
  return $result
}

# ---- Load use cases and KPIs per domain ----
$ucRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "core/usecases"
if (-not $ucRoot) {
  $fallback = Join-Path (Get-Location) "core\usecases"
  if (Test-Path $fallback) { $ucRoot = (Resolve-Path $fallback).Path } else { throw "Use cases root not found. Run from repo root or set -UseCasesRoot." }
}
$catalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "core/kpi_catalog"
if (-not $catalogRoot) { throw "KPI catalog root not found." }
$contractsRoot = Resolve-RepoPath -ProvidedPath $DataContractsRoot -DefaultRelative "core/data_contracts/domains"
if (-not $contractsRoot) { throw "Data contracts root not found." }

$outDir = if ($OutputDir) {
  $r = Resolve-RepoPath -ProvidedPath $OutputDir -DefaultRelative $null
  if ($r) { $r } else { Join-Path $script:RepoRoot $OutputDir }
} else {
  Join-Path $script:RepoRoot "tooling\validation\results"
}
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# Use case ID -> domain; bracket domain (domain: in YAML); collect KPI IDs per domain; (domain,kpiId) -> use case IDs (for Cross-Domain skip)
$ucToDomain = @{}
$ucBracketDomain = @{}
$kpiIdsByDomain = @{}
$kpiUseCases = @{}   # $kpiUseCases[$domain][$kpiId] = @(ucId1, ucId2, ...)
$corePath = Join-Path $ucRoot "core"
if (Test-Path $corePath) {
  Get-ChildItem -Path $corePath -Directory | ForEach-Object {
    if ($_.Name -match '^([A-Z]{2,3})-(\d+)') {
      $ucId = $Matches[1] + "-" + $Matches[2]
      $domain = $script:PrefixToDomain[$Matches[1]]
      if (-not $domain) { return }
      $ucToDomain[$ucId] = $domain
      if (-not $kpiIdsByDomain[$domain]) { $kpiIdsByDomain[$domain] = [System.Collections.Generic.HashSet[string]]::new() }
      if (-not $kpiUseCases[$domain]) { $kpiUseCases[$domain] = @{} }
      $bracketPath = Join-Path $_.FullName "UseCase_Bracket.yaml"
      if (Test-Path $bracketPath) {
        $content = Get-Content -Path $bracketPath -Raw
        $bracketDomainLine = [regex]::Match($content, '(?m)^\s*domain\s*:\s*(.+)$')
        if ($bracketDomainLine.Success) { $ucBracketDomain[$ucId] = $bracketDomainLine.Groups[1].Value.Trim().Trim('"').Trim("'") }
        $kpiIdsInBracket = @()
        foreach ($m in [regex]::Matches($content, '(?m)^\s*-?\s*kpi_id\s*:\s*([a-z][a-z0-9_.]+)')) {
          $kid = $m.Groups[1].Value.Trim()
          [void]$kpiIdsByDomain[$domain].Add($kid)
          $kpiIdsInBracket += $kid
        }
        foreach ($m in [regex]::Matches($content, '(?m)influencing_kpi_ids\s*:\s*(?:\r?\n)(?<body>(?:\s+-\s+[^\r\n]+\r?\n?)+)')) {
          foreach ($line in ($m.Groups['body'].Value -split "`n")) {
            if ($line -match '^\s+-\s+([a-z][a-z0-9_.]+)') {
              $kid = $Matches[1].Trim()
              [void]$kpiIdsByDomain[$domain].Add($kid)
              $kpiIdsInBracket += $kid
            }
          }
        }
        foreach ($kid in ($kpiIdsInBracket | Select-Object -Unique)) {
          if (-not $kpiUseCases[$domain][$kid]) { $kpiUseCases[$domain][$kid] = @() }
          $kpiUseCases[$domain][$kid] += $ucId
        }
      }
    }
  }
}

# Load KPI catalog (id, dax_name, dax_expression, file, lineage, depends_on_measures)
$entryRegex = '(?ms)^\s*-\s*kpi_id\s*:\s*.*?(?=^\s*-\s*kpi_id\s*:|\z)'
$catalogKpis = @{}
$daxNameToKpiId = @{}
$catalogFile = Join-Path $catalogRoot "KPI_Catalog.md"
if (Test-Path $catalogFile) {
  $raw = Get-Content -Raw -Path $catalogFile
  $yamlBlock = [regex]::Match($raw, '```yaml\s*(.*?)```', 'Singleline')
  if ($yamlBlock.Success) {
    $yaml = $yamlBlock.Groups[1].Value
    foreach ($entry in [regex]::Matches($yaml, $entryRegex)) {
      $chunk = $entry.Value
      $id = ([regex]::Match($chunk, 'kpi_id\s*:\s*([^\s"\r\n]+)')).Groups[1].Value.Trim().Trim('"')
      if (-not $id) { continue }
      $tech = [regex]::Match($chunk, "(?ms)technical\s*:\s*\r?\n(.*?)(?=^\s*(?:governance|metadata_quality|aliases|\w)\s*:|\z)")
      $daxExpr = $null; $daxName = $null; $deps = @(); $lineage = @()
      if ($tech.Success) {
        $sub = $tech.Groups[1].Value
        $lit = [regex]::Match($sub, "(?m)^(\s*)dax_expression\s*:\s*\|\s*\r?\n(?<body>(?:\s+.*\r?\n?)+)")
        if ($lit.Success) { $daxExpr = ($lit.Groups['body'].Value -split "`n" | ForEach-Object { $_.TrimEnd() }) -join "`n" }
        $daxName = ([regex]::Match($sub, 'dax_name\s*:\s*["]?([^"\r\n]+)["]?')).Groups[1].Value.Trim().Trim('"')
        if ($sub -match "(?m)depends_on_measures\s*:\s*(?:\r?\n)(?<body>(?:\s{2,}-\s+[^\r\n]+\r?\n?)+)") {
          foreach ($line in ($Matches['body'] -split "`n") ) { if ($line -match '-\s+([a-z][a-z0-9_.]+)') { $deps += $Matches[1] } }
        }
        $lineage = Get-LineageFromChunk -Chunk $chunk
      }
      $catalogKpis[$id] = @{ kpi_id = $id; dax_name = $daxName; dax_expression = $daxExpr; depends_on = $deps; lineage = $lineage; file = "KPI_Catalog.md" }
      if ($daxName) { $daxNameToKpiId[$daxName.Trim()] = $id }
    }
  }
}

# Load contracts and Aurora
$contractTables = @{}
foreach ($domain in $script:DomainToContract.Keys) {
  $contractPath = Join-Path $contractsRoot $script:DomainToContract[$domain]
  $contractTables[$domain] = Get-ContractTablesAndColumns -ContractPath $contractPath
}
$auroraRequired = Get-AuroraRequiredTables

# ---- Findings ----
$findings = @()

foreach ($domain in $kpiIdsByDomain.Keys) {
  $kpiIds = @($kpiIdsByDomain[$domain] | ForEach-Object { $_ })
  $tablesInContract = $contractTables[$domain]
  $requiredTables = $auroraRequired[$domain]
  if (-not $requiredTables) { $requiredTables = @() }
  $contractPath = Join-Path $contractsRoot $script:DomainToContract[$domain]
  $contractRelPath = "core/data_contracts/domains/$($script:DomainToContract[$domain])"
  $auroraTablesReported = @{}   # (domain, table) -> $true for deduplication across KPIs

  foreach ($kpiId in $kpiIds) {
    $k = $catalogKpis[$kpiId]
    if (-not $k) {
      $findings += [pscustomobject]@{
        Severity = 'Error'
        Rule = 'SSOT.kpi_not_in_catalog'
        Message = "Use case domain $domain references KPI '$kpiId' which is not in the KPI catalog."
        Location = $kpiId
        Domain = $domain
        Remediation = "Add KPI $kpiId to core/kpi_catalog/KPI_Catalog.md or remove from use case bracket."
        InsertableRemediation = $null
      }
      continue
    }

    $daxExpr = $k.dax_expression
    if (-not $daxExpr) {
      $findings += [pscustomobject]@{
        Severity = 'Error'
        Rule = 'SSOT.kpi_missing_dax'
        Message = "KPI '$kpiId' has no dax_expression in catalog."
        Location = $kpiId
        Domain = $domain
        Remediation = "Add technical.dax_expression for $kpiId in KPI catalog."
        InsertableRemediation = $null
      }
      continue
    }

    # Referenced measures: each [Name] must have a KPI with dax_name = Name (skip if [Name] is a column ref: table[Name])
    $measureRefs = Get-MeasureRefsFromDax -Expr $daxExpr
    foreach ($refName in $measureRefs) {
      if ($refName -eq $k.dax_name) { continue }
      if (Test-RefNameIsColumnInDax -Expr $daxExpr -RefName $refName) { continue }
      $refId = $daxNameToKpiId[$refName]
      if (-not $refId) {
        $suggestId = ($refName -replace '\s+', '_').ToLower() -replace '[^a-z0-9_.]', ''
        if (-not $suggestId) { $suggestId = "measure.$([guid]::NewGuid().ToString('N').Substring(0,8))" }
        $insertable = @"
- kpi_id: $suggestId
  kpi_key: $refName
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag: [$domain]
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: "Referenced by $($k.kpi_id). Define purpose and definition."
    definition: "TBD"
    grain_scope: "TBD"
    unit_format: "EUR (2 decimals)"
    interpretation: "TBD"
  technical:
    dax_name: "$refName"
    formatString: "#,0.00"
    description: "TBD - required by $($k.kpi_id)"
    dax_expression: |
      BLANK()
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: "TBD"
    data_owner: "BI Engineering"
    steward: "TBD"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules: []
    version: "v0.1"
  metadata_quality:
    completeness_score: 0.5
    last_review: "$(Get-Date -Format 'dd.MM.yyyy')"
"@
        $findings += [pscustomobject]@{
          Severity = 'Error'
          Rule = 'SSOT.referenced_measure_missing'
          Message = "KPI '$kpiId' references measure [$refName] but no KPI with dax_name '$refName' exists in catalog."
          Location = $kpiId
          Domain = $domain
          Remediation = "Add a new KPI with dax_name '$refName' (e.g. kpi_id: $suggestId) and wire depends_on_measures in $kpiId."
          InsertableRemediation = [pscustomobject]@{
            ssot_type = 'kpi_catalog'
            file_path = 'core/kpi_catalog/KPI_Catalog.md'
            insert_location = "Inside the ```yaml block, insert after an existing KPI block (e.g. before the KPI that references it). Replace TBD and BLANK() with real definition and DAX."
            insertable_content = $insertable
          }
        }
      }
    }

    # Cross-Domain: skip table_not_in_contract when this KPI is referenced by a use case with bracket domain Executive/Cross-Functional
    $skipTableNotInContract = $false
    if ($kpiUseCases[$domain] -and $kpiUseCases[$domain][$kpiId]) {
      foreach ($ucId in $kpiUseCases[$domain][$kpiId]) {
        if ($ucBracketDomain[$ucId] -match 'Executive|Cross-Functional') { $skipTableNotInContract = $true; break }
      }
    }

    # Table[column] in DAX: table must be in contract with that column; table must be in Aurora required
    $tcRefs = Get-TableColumnRefsFromDax -Expr $daxExpr
    foreach ($tc in $tcRefs) {
      $tbl = $tc.table
      $col = $tc.column
      if (-not $tablesInContract[$tbl]) {
        if (-not $skipTableNotInContract) {
          $findings += [pscustomobject]@{
            Severity = 'Error'
            Rule = 'SSOT.table_not_in_contract'
            Message = "KPI '$kpiId' DAX references table '$tbl' which is not in domain contract $($script:DomainToContract[$domain])."
            Location = $kpiId
            Domain = $domain
            Remediation = "Add table '$tbl' to $contractRelPath or change KPI to use tables from the contract."
            InsertableRemediation = [pscustomobject]@{
              ssot_type = 'data_contract'
              file_path = $contractRelPath
              insert_location = "Under dimension: or fact:, add a new table block with name: $tbl and columns including '$col'. Match existing table style in the file."
              insertable_content = "  - name: $tbl`n    description: `"TBD`"`n    purpose: `"TBD`"`n    grain: TBD`n    columns:`n      - {name: $col, type: decimal, agg: sum}"
            }
          }
        }
      } else {
        $cols = $tablesInContract[$tbl]
        $colNorm = $col.Trim()
        $found = $cols | Where-Object { $_ -eq $colNorm -or $_ -replace '\s+', '' -eq $colNorm -replace '\s+', '' }
        if (-not $found) {
          $findings += [pscustomobject]@{
            Severity = 'Error'
            Rule = 'SSOT.column_not_in_contract'
            Message = "KPI '$kpiId' DAX references $tbl[$col] but column '$col' is not on table '$tbl' in $contractRelPath."
            Location = $kpiId
            Domain = $domain
            Remediation = "Add column '$col' to table '$tbl' in $contractRelPath."
            InsertableRemediation = [pscustomobject]@{
              ssot_type = 'data_contract'
              file_path = $contractRelPath
              insert_location = "Under table '$tbl', columns:, add the following line (match indentation of sibling columns)."
              insertable_content = "      - {name: $col, type: currency, agg: sum}"
            }
          }
        }
      }
      if ($requiredTables -and $tbl -notin $requiredTables -and $tablesInContract[$tbl]) {
        $key = "$domain|$tbl"
        if (-not $auroraTablesReported[$key]) {
          $auroraTablesReported[$key] = $true
          $newList = $requiredTables + $tbl
          $line = "    $domain  = @(" + (($newList | ForEach-Object { '"' + $_ + '"' }) -join ', ') + ")"
          $findings += [pscustomobject]@{
            Severity = 'Error'
            Rule = 'SSOT.table_not_in_aurora_required'
            Message = "KPI '$kpiId' uses table '$tbl' which is in the domain contract but not in AuroraDomainRequiredTables for $domain."
            Location = $kpiId
            Domain = $domain
            Remediation = "Add '$tbl' to AuroraDomainRequiredTables for $domain in products/fabric/powerbi/orchestrator/AuroraDomainMapping.ps1."
            InsertableRemediation = [pscustomobject]@{
              ssot_type = 'aurora_domain_mapping'
              file_path = 'products/fabric/powerbi/orchestrator/AuroraDomainMapping.ps1'
              insert_location = "In `$script:AuroraDomainRequiredTables, for key '$domain', add '$tbl' to the array. Replace the existing line for $domain with the line below."
              insertable_content = $line
            }
          }
        }
      }
    }

    # Lineage tables (table.Column): table must be in required for domain (deduplicate per domain, table)
    foreach ($lin in $k.lineage) {
      if ($lin -match '^([^.]+)\.') {
        $tbl = $Matches[1].Trim()
        if ($requiredTables -and $tbl -notin $requiredTables -and $tablesInContract[$tbl]) {
          $key = "$domain|$tbl"
          if (-not $auroraTablesReported[$key]) {
            $auroraTablesReported[$key] = $true
            $newList = $requiredTables + $tbl
            $line = "    $domain  = @(" + (($newList | ForEach-Object { '"' + $_ + '"' }) -join ', ') + ")"
            $findings += [pscustomobject]@{
              Severity = 'Error'
              Rule = 'SSOT.lineage_table_not_in_aurora_required'
              Message = "KPI '$kpiId' lineage references table '$tbl' which is not in AuroraDomainRequiredTables for $domain."
              Location = $kpiId
              Domain = $domain
              Remediation = "Add '$tbl' to AuroraDomainRequiredTables for $domain."
              InsertableRemediation = [pscustomobject]@{
                ssot_type = 'aurora_domain_mapping'
                file_path = 'products/fabric/powerbi/orchestrator/AuroraDomainMapping.ps1'
                insert_location = "In AuroraDomainMapping.ps1, for key '$domain', add '$tbl' to the required tables array."
                insertable_content = $line
              }
            }
          }
        }
      }
    }
  }
}

# ---- Report ----
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$reportPath = Join-Path $outDir "usecase_ssot_readiness_$timestamp.md"
$jsonPath = Join-Path $outDir "usecase_ssot_readiness_$timestamp.json"

$md = @"
# Use-Case SSOT Readiness Report
Generated: $(Get-Date -Format 'o')
Findings: $($findings.Count)

## Summary
- **KPI not in catalog:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.kpi_not_in_catalog' }).Count)
- **KPI missing DAX:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.kpi_missing_dax' }).Count)
- **Referenced measure missing:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.referenced_measure_missing' }).Count)
- **Table not in contract:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.table_not_in_contract' }).Count)
- **Column not in contract:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.column_not_in_contract' }).Count)
- **Table not in Aurora required:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.table_not_in_aurora_required' }).Count)
- **Lineage table not in Aurora required:** $(($findings | Where-Object { $_.Rule -eq 'SSOT.lineage_table_not_in_aurora_required' }).Count)

## Findings
"@
foreach ($f in $findings) {
  $md += "`n### [$($f.Severity)] $($f.Rule)`n$($f.Message)`n- **Location:** $($f.Location) | Domain: $($f.Domain)`n- **Remediation:** $($f.Remediation)`n"
  if ($f.InsertableRemediation) {
    $ir = $f.InsertableRemediation
    $md += "- **Insertable (SSOT: $($ir.ssot_type)):** File ``$($ir.file_path)``.`n"
    $md += "- **Insert location:** $($ir.insert_location)`n"
    $fence = if ($ir.ssot_type -eq 'aurora_domain_mapping') { 'powershell' } else { 'yaml' }
    $md += "``````$fence`n$($ir.insertable_content)`n```````n"
  }
}
$md | Set-Content -Path $reportPath -Encoding UTF8

$findings | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host "Use-case SSOT readiness: $($findings.Count) finding(s). Report: $reportPath" -ForegroundColor $(if ($findings.Count -eq 0) { 'Green' } else { 'Yellow' })
foreach ($f in $findings) {
  Write-Host "  [$($f.Severity)] $($f.Rule): $($f.Message)" -ForegroundColor Gray
}

if ($FailOnFinding -and $findings.Count -gt 0) { exit 1 }
exit 0
