Param(
  [string]$UseCasesRoot = "usecases",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$ActionCodesRoot = "core/action_codes",
  [string]$UseCaseActionCodeMapPath = "usecases/UseCase_ActionCode_Map.yaml",
  [string]$MeasureDictRoot = "semantic_models/domains",
  [string]$OutputPath = "internal/reviews/missing_kpi_dependency_audit.md"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  $repo = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Get-FrontMatterText {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, '(?ms)^---\s*\r?\n(.*?)\r?\n---')
  if (-not $match.Success) { return $null }
  return $match.Groups[1].Value
}

function Get-BodyText {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  if (-not $content) { return "" }
  $withoutFrontMatter = [regex]::Replace($content, '(?ms)^---\s*\r?\n.*?\r?\n---\s*', '')
  return $withoutFrontMatter
}

function Parse-ListField {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if ($inline.Success) {
    $items = @()
    foreach ($token in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($token.Groups[1].Success) { $token.Groups[1].Value }
               elseif ($token.Groups[2].Success) { $token.Groups[2].Value }
               else { $token.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    $results = @()
    foreach ($rawLine in ($block.Groups['body'].Value -split '\r?\n')) {
      $line = $rawLine.Trim()
      if (-not $line) { continue }
      if ($line -match '^\s*-\s*(.*)$') { $value = $matches[1].Trim() } else { continue }
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

function Get-MapKeys {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  $match = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*$", 'Multiline')
  if (-not $match.Success) { return @() }
  $keys = @()
  $startIndex = $match.Index + $match.Length
  $lines = $FrontMatter.Substring($startIndex) -split '\r?\n'
  foreach ($line in $lines) {
    if ($line.Trim().Length -eq 0) { continue }
    if ($line -notmatch "^\s+") { break }
    $kv = [regex]::Match($line, '^\s*([^:]+):\s*"(.*?)"\s*$')
    if ($kv.Success) { $keys += $kv.Groups[1].Value.Trim() }
  }
  return $keys
}

function Get-KpiTokensFromText {
  param([string]$Text)
  if (-not $Text) { return @() }
  $tokens = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($match in [regex]::Matches($Text, '\b[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+\b')) {
    $null = $tokens.Add($match.Value)
  }
  return $tokens
}

function Get-KpiIdsFromCatalog {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -Filter "KPI_Catalog.md" | Where-Object {
    $_.FullName -notmatch '\\archive\\'
  } | ForEach-Object {
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*-\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[1])
      }
    }
  }
  return $ids
}

function Get-CoreUseCaseIds {
  param([string]$Root)
  $coreRoot = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $coreRoot)) { return @() }
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $coreRoot -Recurse -Filter "*Factsheet*.md" | ForEach-Object {
    $fm = Get-FrontMatterText -Path $_.FullName
    if (-not $fm) { return }
    $match = [regex]::Match($fm, "^\s*id\s*:\s*([A-Z0-9-]+)\s*$", "Multiline")
    if ($match.Success) { $null = $ids.Add($match.Groups[1].Value.Trim()) }
  }
  return $ids
}

function Get-ActionCodesForUseCases {
  param([string]$MapPath,[System.Collections.Generic.HashSet[string]]$UseCaseIds)
  if (-not (Test-Path $MapPath)) { return @() }
  $codes = [System.Collections.Generic.HashSet[string]]::new()
  $currentId = $null
  foreach ($line in Get-Content -Path $MapPath) {
    $useCaseMatch = [regex]::Match($line, '^\s{2}([A-Z0-9-]+):\s*$')
    if ($useCaseMatch.Success) {
      $currentId = $useCaseMatch.Groups[1].Value.Trim()
      continue
    }
    if (-not $currentId) { continue }
    if (-not $UseCaseIds.Contains($currentId)) { continue }
    $codesMatch = [regex]::Match($line, '^\s{4}action_codes:\s*\[(.*?)\]\s*$')
    if ($codesMatch.Success) {
      foreach ($token in ($codesMatch.Groups[1].Value -split ',')) {
        $value = $token.Trim().Trim('"').Trim("'")
        if ($value) { $null = $codes.Add($value) }
      }
    }
  }
  return $codes
}

function Get-ActionCodesFromFactsheets {
  param([string]$Root)
  $coreRoot = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $coreRoot)) { return @() }
  $codes = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $coreRoot -Recurse -Filter "*Factsheet*.md" | ForEach-Object {
    $body = Get-BodyText -Path $_.FullName
    if (-not $body) { return }
    foreach ($match in [regex]::Matches($body, '\b[A-Z]{1,3}-[A-Z][0-9]\.[0-9]\b')) {
      $null = $codes.Add($match.Value)
    }
  }
  return $codes
}

function Get-KpiIdsFromActionCodes {
  param([string]$Root,[System.Collections.Generic.HashSet[string]]$ActionCodes,[System.Collections.Generic.HashSet[string]]$CatalogIds)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  if (-not $ActionCodes -or $ActionCodes.Count -eq 0) { return $ids }
  foreach ($code in $ActionCodes) {
    $matches = Get-ChildItem -Path $Root -Recurse -Filter "$code.yaml" -File -ErrorAction SilentlyContinue
    if (-not $matches) { continue }
    $path = $matches[0].FullName
    foreach ($line in Get-Content -Path $path) {
      if ($line -match '^\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
        $value = $matches[1]
        if ($CatalogIds.Contains($value)) { $null = $ids.Add($value) }
        continue
      }
      if ($line -match '^\s*metric_kpi_id\s*:\s*"?([^"\s]+)"?') {
        $value = $matches[1]
        if ($CatalogIds.Contains($value)) { $null = $ids.Add($value) }
      }
    }
  }
  return $ids
}

function Parse-MeasureDictionary {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, '(?ms)```yaml\s*\r?\n(.*?)\r?\n```')
  if (-not $match.Success) { return @() }
  $lines = $match.Groups[1].Value -split '\r?\n'
  $measures = @()
  $current = $null
  $inDaxBlock = $false
  $daxIndent = 0
  foreach ($line in $lines) {
    if ($line -match '^\s*-\s*measure_name\s*:\s*"?([^"]+)"?\s*$') {
      if ($current) { $measures += $current }
      $current = [PSCustomObject]@{
        measure_name = $matches[1].Trim()
        kpi_id_ref = ""
        is_kpi_measure = $false
        dax = ""
      }
      $inDaxBlock = $false
      continue
    }
    if (-not $current) { continue }
    if ($line -match '^\s*is_kpi_measure\s*:\s*(true|false)\s*$') {
      $current.is_kpi_measure = ($matches[1] -eq "true")
      continue
    }
    if ($line -match '^\s*kpi_id_ref\s*:\s*"?([^"\s]+)"?\s*$') {
      $current.kpi_id_ref = $matches[1].Trim()
      continue
    }
    if ($line -match '^\s*dax\s*:\s*(.*)$') {
      $value = $matches[1].Trim()
      $value = $value.Trim('"')
      $current.dax = $value
      if ($value -eq "" -or $value -eq "|" -or $value -eq ">") {
        $inDaxBlock = $true
        $daxIndent = ($line.Length - $line.TrimStart().Length) + 2
        $current.dax = ""
      }
      continue
    }
    if ($inDaxBlock) {
      $indent = $line.Length - $line.TrimStart().Length
      if ($indent -lt $daxIndent) {
        $inDaxBlock = $false
        continue
      }
      $current.dax += ($line.Substring($daxIndent) + "`n")
      continue
    }
  }
  if ($current) { $measures += $current }
  return $measures
}

function Get-MeasureRefsFromDax {
  param([string]$Dax,[System.Collections.Generic.HashSet[string]]$KnownMeasures)
  $refs = [System.Collections.Generic.HashSet[string]]::new()
  if (-not $Dax) { return $refs }
  foreach ($match in [regex]::Matches($Dax, '\[([^\]]+)\]')) {
    $name = $match.Groups[1].Value.Trim()
    if ($KnownMeasures.Contains($name)) { $null = $refs.Add($name) }
  }
  return $refs
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "core/kpi_catalog"
$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "core/action_codes"
$actionCodeMapPath = Resolve-RepoPath -ProvidedPath $UseCaseActionCodeMapPath -DefaultRelative "usecases/UseCase_ActionCode_Map.yaml"
$measureDictRoot = Resolve-RepoPath -ProvidedPath $MeasureDictRoot -DefaultRelative "semantic_models/domains"
$outputPath = Resolve-RepoPath -ProvidedPath $OutputPath -DefaultRelative "internal/reviews/missing_kpi_dependency_audit.md"

if (-not $useCasesRoot) { throw "UseCases root not found." }
if (-not $kpiCatalogRoot) { throw "KPI catalog root not found." }
if (-not $measureDictRoot) { throw "Measure dictionary root not found." }
if (-not $outputPath) { $outputPath = (Join-Path -Path (Get-Location).Path -ChildPath "internal/reviews/missing_kpi_dependency_audit.md") }

$catalogIds = Get-KpiIdsFromCatalog -Root $kpiCatalogRoot

$coreUseCaseIds = Get-CoreUseCaseIds -Root $useCasesRoot
$actionCodes = [System.Collections.Generic.HashSet[string]]::new()
if ($coreUseCaseIds.Count -gt 0 -and $actionCodesRoot -and $actionCodeMapPath) {
  foreach ($code in (Get-ActionCodesForUseCases -MapPath $actionCodeMapPath -UseCaseIds $coreUseCaseIds)) {
    $null = $actionCodes.Add($code)
  }
}
foreach ($code in (Get-ActionCodesFromFactsheets -Root $useCasesRoot)) {
  $null = $actionCodes.Add($code)
}

$coreKpiIds = [System.Collections.Generic.HashSet[string]]::new()
Get-ChildItem -Path (Join-Path $useCasesRoot "core") -Recurse -Filter "*Factsheet*.md" | ForEach-Object {
  $fm = Get-FrontMatterText -Path $_.FullName
  if (-not $fm) { return }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "required_kpi_ids")) {
    if ($catalogIds.Contains($id)) { $null = $coreKpiIds.Add($id) }
  }
  foreach ($id in (Parse-ListField -FrontMatter $fm -Field "supports_strategic_kpi_ids")) {
    if ($catalogIds.Contains($id)) { $null = $coreKpiIds.Add($id) }
  }
  foreach ($id in (Get-MapKeys -FrontMatter $fm -Field "required_kpis")) {
    if ($catalogIds.Contains($id)) { $null = $coreKpiIds.Add($id) }
  }
  foreach ($id in (Get-KpiTokensFromText -Text (Get-BodyText -Path $_.FullName))) {
    if ($catalogIds.Contains($id)) { $null = $coreKpiIds.Add($id) }
  }
}

if ($actionCodesRoot) {
  foreach ($id in (Get-KpiIdsFromActionCodes -Root $actionCodesRoot -ActionCodes $actionCodes -CatalogIds $catalogIds)) {
    $null = $coreKpiIds.Add($id)
  }
}

$allMeasures = @()
Get-ChildItem -Path $measureDictRoot -Recurse -Filter "Measure_Dictionary_*.md" -File | Where-Object {
  $_.FullName -notmatch '\\archive\\' -and $_.Name -notmatch '_Archive\.md$'
} | ForEach-Object {
  $allMeasures += (Parse-MeasureDictionary -Path $_.FullName)
}

$measureNameSet = [System.Collections.Generic.HashSet[string]]::new()
$measureByName = @{}
foreach ($measure in $allMeasures) {
  if (-not $measure.measure_name) { continue }
  $null = $measureNameSet.Add($measure.measure_name)
  if (-not $measureByName.ContainsKey($measure.measure_name)) {
    $measureByName[$measure.measure_name] = New-Object System.Collections.Generic.List[object]
  }
  $measureByName[$measure.measure_name].Add($measure) | Out-Null
}

$missingById = @{}
foreach ($measure in $allMeasures) {
  if (-not $measure.is_kpi_measure) { continue }
  if (-not $measure.kpi_id_ref) { continue }
  if ($catalogIds.Contains($measure.kpi_id_ref)) { continue }
  if (-not $missingById.ContainsKey($measure.kpi_id_ref)) {
    $missingById[$measure.kpi_id_ref] = New-Object System.Collections.Generic.List[string]
  }
  if (-not $missingById[$measure.kpi_id_ref].Contains($measure.measure_name)) {
    $missingById[$measure.kpi_id_ref].Add($measure.measure_name) | Out-Null
  }
}

$dependencies = @{}
foreach ($measure in $allMeasures) {
  $refs = Get-MeasureRefsFromDax -Dax $measure.dax -KnownMeasures $measureNameSet
  $dependencies[$measure.measure_name] = $refs
}

$requiredMissing = [System.Collections.Generic.HashSet[string]]::new()
$visited = [System.Collections.Generic.HashSet[string]]::new()
$queue = New-Object System.Collections.Generic.Queue[string]
foreach ($name in $measureByName.Keys) {
  foreach ($entry in $measureByName[$name]) {
    if ($entry.kpi_id_ref -and $coreKpiIds.Contains($entry.kpi_id_ref)) {
      $queue.Enqueue($name)
      break
    }
  }
}

while ($queue.Count -gt 0) {
  $current = $queue.Dequeue()
  if ($visited.Contains($current)) { continue }
  $null = $visited.Add($current)
  if ($measureByName.ContainsKey($current)) {
    foreach ($entry in $measureByName[$current]) {
      if ($entry.kpi_id_ref -and $missingById.ContainsKey($entry.kpi_id_ref)) {
        $null = $requiredMissing.Add($entry.kpi_id_ref)
      }
    }
  }
  if ($dependencies.ContainsKey($current)) {
    foreach ($next in $dependencies[$current]) { $queue.Enqueue($next) }
  }
}

$lines = @()
$lines += "# Missing KPI Dependency Audit"
$lines += ""
$lines += ("- Timestamp: {0}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"))
$lines += ("- Core KPI ids (factsheets + action codes): {0}" -f $coreKpiIds.Count)
$lines += ("- Missing KPI ids (measure dictionaries not in KPI catalogs): {0}" -f $missingById.Keys.Count)
$lines += ""
$lines += "| Missing KPI ID | Measure Name(s) | Required for Core KPIs? |"
$lines += "|---|---|---|"
foreach ($id in ($missingById.Keys | Sort-Object)) {
  $names = ($missingById[$id] | Sort-Object) -join ", "
  $required = if ($requiredMissing.Contains($id)) { "yes" } else { "no" }
  $lines += ("| {0} | {1} | {2} |" -f $id, $names, $required)
}

$dir = Split-Path -Path $outputPath -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$lines | Set-Content -Path $outputPath

Write-Host ("Wrote audit: {0}" -f $outputPath) -ForegroundColor Green

