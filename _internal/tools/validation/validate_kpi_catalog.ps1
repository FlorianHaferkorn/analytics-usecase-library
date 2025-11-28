Param(
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [switch]$FailOnError
)

$script:RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    if ($script:RepoRoot) {
      $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
      if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    }
  }
  if ($DefaultRelative -and $script:RepoRoot) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$allowedTypes = @('strategic','diagnostic','supporting')
$allowedCalc  = @('amount','rate','ratio','count')
$allowedImpact = @('growth','profitability','liquidity','efficiency','customer','esg','governance','innovation & people')
$idRegex = '^[a-z0-9]+(\.[a-z0-9_]+)*$'

function Get-KpiBlocks {
  param([string]$Root)
  $files = Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' }
  foreach ($f in $files) {
    $raw = Get-Content -Raw -Path $f.FullName
    $matches = [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')
    foreach ($m in $matches) { [pscustomobject]@{ File=$f.FullName; Block=$m.Groups[1].Value } }
  }
}

$errors = @(); $warnings = @(); $seenIds = @{}

# Path to Use Case FactSheets (for required KPI IDs)
$resolvedCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative '_includes/kpi_catalog'
if (-not $resolvedCatalogRoot) { throw "Unable to resolve KPI catalog root. Provide -KpiCatalogRoot or run inside repository." }

$UseCasesRoot = Resolve-RepoPath -ProvidedPath "analytics-usecase-library/usecases" -DefaultRelative 'usecases'

function Get-FrontMatter {
  param(
    [string]$Path,
    [int]$Depth = 0
  )
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s")
  if (-not $m.Success) { return $null }
  $frontMatter = $m.Groups[1].Value
  $pointer = [regex]::Match($frontMatter, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $parent = Split-Path -Parent $Path
    $target = Join-Path -Path $parent -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      $resolved = Resolve-Path -Path $target
      return Get-FrontMatter -Path $resolved.Path -Depth ($Depth + 1)
    }
  }
  return $frontMatter
}
function Parse-ListFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if ($inline.Success) {
    $vals = @()
    foreach ($mm in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($mm.Groups[1].Success) { $mm.Groups[1].Value }
               elseif ($mm.Groups[2].Success) { $mm.Groups[2].Value }
               else { $mm.Groups[3].Value }
      if ($value) { $vals += $value }
    }
    return $vals
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    $results = @()
    foreach ($line in ($block.Groups['body'].Value -split "\r?\n")) {
      $trimmed = $line.Trim()
      if (-not $trimmed) { continue }
      if ($trimmed -match '^\s*-\s*(.*)$') {
        $value = $matches[1].Trim()
      } else {
        continue
      }
      if (-not $value) { continue }
      if ($value -match '^(?<val>[^#]+)\s*(#.*)?$') { $value = $matches['val'].TrimEnd() }
      if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Trim('"')
      } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Trim("'")
      }
      if ($value) { $results += $value }
    }
    return $results
  }
  return @()
}

function Get-RequiredIdsFromFrontMatter {
  param([string]$FrontMatter)
  return Parse-ListFromFrontMatter -FrontMatter $FrontMatter -Field 'required_kpi_ids'
}

# Build set of KPI IDs required by FactSheets
$requiredSet = New-Object System.Collections.Generic.HashSet[string]
if ($UseCasesRoot -and (Test-Path $UseCasesRoot)) {
  Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md' | ForEach-Object {
    $fm = Get-FrontMatter -Path $_.FullName
    foreach ($rid in (Get-RequiredIdsFromFrontMatter -FrontMatter $fm)) { [void]$requiredSet.Add($rid) }
  }
}

# Build index of all IDs for cross-check
$allIds = New-Object System.Collections.Generic.HashSet[string]
Get-ChildItem -Path $resolvedCatalogRoot -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object { $r = Get-Content -Raw -Path $_.FullName; foreach($m in [regex]::Matches($r,'kpi_id\s*:\s*"([^"]+)"')){ [void]$allIds.Add($m.Groups[1].Value) } }

Get-KpiBlocks -Root $resolvedCatalogRoot | ForEach-Object {
  $file = $_.File; $b = $_.Block
  $id  = ([regex]::Match($b, 'kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value
  $typ = ([regex]::Match($b, 'kpi_type\s*:\s*"([^"]+)"')).Groups[1].Value.ToLower()
  $calc= ([regex]::Match($b, 'calc_type\s*:\s*"([^"]+)"')).Groups[1].Value.ToLower()
  $impact = ([regex]::Match($b, 'impact_dimension\s*:\s*"([^"]+)"')).Groups[1].Value.ToLower()
  $hasBiz = $b -match '(?m)^\s*business\s*:\s*'
  $hasTec = $b -match '(?m)^\s*technical\s*:\s*'
  $hasGov = $b -match '(?m)^\s*governance\s*:\s*'
  $bizPurpose = $b -match '(?m)^\s*purpose\s*:\s*"'
  $bizDef     = $b -match '(?m)^\s*definition\s*:\s*"'
  $bizGrain   = $b -match '(?m)^\s*grain_scope\s*:\s*"'
  $bizUnit    = $b -match '(?m)^\s*unit_format\s*:\s*"'
  $tecName    = $b -match '(?m)^\s*dax_name\s*:\s*"'
  $tecFmt     = $b -match '(?m)^\s*formatString\s*:\s*"'
  $tecDesc    = $b -match '(?m)^\s*description\s*:\s*"'
  $govBOwner  = $b -match '(?m)^\s*business_owner\s*:\s*"'
  $govDOwner  = $b -match '(?m)^\s*data_owner\s*:\s*"'
  $domTagOk   = $b -match '(?m)^\s*domain_tag\s*:\s*\[[^\]]*\]'
  if (-not $id) { return }
  if ($seenIds.ContainsKey($id)) { $errors += "duplicate kpi_id: $id ($file)" } else { $seenIds[$id]=$true }
  if ($typ -and ($allowedTypes -notcontains $typ)) { $errors += "invalid kpi_type '$typ' for $id ($file)" }
  if ($calc -and ($allowedCalc -notcontains $calc)) { $errors += "invalid calc_type '$calc' for $id ($file)" }
  if ($impact -and ($allowedImpact -notcontains $impact)) { $errors += "invalid impact_dimension '$impact' for $id ($file)" }
  if (-not $domTagOk) { $warnings += "missing or invalid domain_tag for $id ($file)" }
  $requireFull = ($typ -eq 'strategic') -or ($requiredSet.Contains($id))
  if ($requireFull) {
    if (-not $hasBiz) { $errors += "missing business block for $id ($file)" }
    if (-not $hasTec) { $errors += "missing technical block for $id ($file)" }
    if (-not $hasGov) { $errors += "missing governance block for $id ($file)" }
    if ($hasBiz -and (-not ($bizPurpose -and $bizDef -and $bizGrain -and $bizUnit))) { $errors += "incomplete business block for $id ($file)" }
    if ($hasTec -and (-not ($tecName -and $tecFmt -and $tecDesc))) { $errors += "incomplete technical block for $id ($file)" }
    if ($hasGov -and (-not ($govBOwner -and $govDOwner))) { $errors += "incomplete governance block for $id ($file)" }
  } else {
    if (-not $hasTec) { $warnings += "technical block recommended for $id ($file)" }
    if (-not $hasBiz) { $warnings += "business block recommended for $id ($file)" }
    if (-not $hasGov) { $warnings += "governance block recommended for $id ($file)" }
  }
  if ($id -notmatch $idRegex) { $errors += "invalid kpi_id format: $id ($file)" }

  # Composite dependency integrity
  $hasDepends = $b -match '(?m)^\s*depends_on\s*:\s*\[(?<inner>[^\]]*)\]'
  $hasDependsIds = $b -match '(?m)^\s*depends_on_ids\s*:\s*\[(?<inner>[^\]]*)\]'
  if ($hasDepends) {
    if (-not $hasDependsIds) { $warnings += "missing depends_on_ids for $id ($file)" }
    else {
      foreach($mm in [regex]::Matches($b,'(?m)^\s*depends_on_ids\s*:\s*\[(?<inner>[^\]]*)\]')){
        foreach($q in [regex]::Matches($mm.Groups['inner'].Value,'"([^"]+)"')){
          $depId = $q.Groups[1].Value
          if(-not $allIds.Contains($depId)){ $errors += "depends_on_ids references unknown id '$depId' for $id ($file)" }
        }
      }
    }
  }
}

if ($warnings.Count -gt 0) { Write-Host "KPI Catalog warnings:" -ForegroundColor Yellow; $warnings | Sort-Object | ForEach-Object { Write-Host "- $_" } }
if ($errors.Count -gt 0) { Write-Host "KPI Catalog validation errors:" -ForegroundColor Red; $errors | Sort-Object | ForEach-Object { Write-Host "- $_" }; if ($FailOnError) { exit 1 } else { exit 0 } }
else { Write-Host "KPI Catalog validation passed." -ForegroundColor Green }
