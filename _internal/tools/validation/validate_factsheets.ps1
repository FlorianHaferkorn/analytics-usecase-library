Param(
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [switch]$FailOnError
)

$script:RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
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

function Get-FrontMatter {
  param(
    [string]$Path,
    [int]$Depth = 0
  )
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $block = $match.Groups[1].Value
  $pointer = [regex]::Match($block, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $parent = Split-Path -Parent $Path
    $target = Join-Path -Path $parent -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      $resolved = Resolve-Path -Path $target
      return Get-FrontMatter -Path $resolved.Path -Depth ($Depth + 1)
    }
  }
  return [pscustomobject]@{
    Text   = $block
    Source = (Resolve-Path -Path $Path).Path
  }
}

function Has-Field {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  return [regex]::IsMatch($FrontMatter, "^\s*$escaped\s*:", 'Multiline')
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
    foreach ($rawLine in ($block.Groups['body'].Value -split "\r?\n")) {
      $line = $rawLine.Trim()
      if (-not $line) { continue }
      if ($line -match '^\s*-\s*(.*)$') {
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

function Get-MapField {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  $match = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*$", 'Multiline')
  if (-not $match.Success) { return @{} }
  $map = [ordered]@{}
  $startIndex = $match.Index + $match.Length
  $lines = $FrontMatter.Substring($startIndex) -split "\r?\n"
  foreach ($line in $lines) {
    if ($line.Trim().Length -eq 0) { continue }
    if ($line -notmatch "^\s+") { break }
    $kv = [regex]::Match($line, "^\s*([^:]+):\s*[`"'](.*?)[`"']\s*$")
    if ($kv.Success) { $map[$kv.Groups[1].Value.Trim()] = $kv.Groups[2].Value }
  }
  return $map
}

$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root. Provide -UseCasesRoot or run inside repository." }

$requiredScalarFields = @(
  'id',
  'title',
  'domain',
  'owner',
  'impact',
  'status',
  'last_update',
  'reporting_level',
  'analytics_stage',
  'maturity',
  'dataset_model',
  'page_template',
  'expected_impact'
)
$requiredListFields = @('supports_strategic_kpi','supports_strategic_kpi_ids','action_codes','segments','filters_default','required_kpi_ids')

$errors = @(); $warnings = @()

Get-ChildItem -Path $resolvedUseCasesRoot -Recurse -Filter 'FactSheet.md' | ForEach-Object {
  $fm = Get-FrontMatter -Path $_.FullName
  if (-not ($fm -and $fm.Text)) {
    $errors += "Missing front-matter in $($_.FullName)"
    return
  }
  $text = $fm.Text
  foreach ($field in $requiredScalarFields) {
    if (-not (Has-Field -FrontMatter $text -Field $field)) {
      $errors += "$($_.FullName): missing field '$field'"
    }
  }
  foreach ($field in $requiredListFields) {
    $values = Parse-ListField -FrontMatter $text -Field $field
    if ($values.Count -eq 0) { $errors += "$($_.FullName): list '$field' missing or empty" }
  }
  if (-not (Has-Field -FrontMatter $text -Field 'required_kpis')) {
    $errors += "$($_.FullName): missing 'required_kpis' map"
  } else {
    $ids = Parse-ListField -FrontMatter $text -Field 'required_kpi_ids'
    $map = Get-MapField -FrontMatter $text -Field 'required_kpis'
    foreach ($id in $ids) {
      if (-not $map.Contains($id)) { $errors += "$($_.FullName): required_kpis missing label for '$id'" }
    }
  }
  if (-not (Has-Field -FrontMatter $text -Field 'data_requirements')) { $warnings += "$($_.FullName): missing data_requirements block" }
  if (-not (Has-Field -FrontMatter $text -Field 'model_mapping')) { $warnings += "$($_.FullName): missing model_mapping block" }
  if (-not (Has-Field -FrontMatter $text -Field 'qa_asserts')) { $warnings += "$($_.FullName): missing qa_asserts" }
}

if ($warnings.Count -gt 0) {
  Write-Host "FactSheet warnings:" -ForegroundColor Yellow
  $warnings | Sort-Object | ForEach-Object { Write-Host "- $_" }
}

if ($errors.Count -gt 0) {
  Write-Host "FactSheet validation errors:" -ForegroundColor Red
  $errors | Sort-Object | ForEach-Object { Write-Host "- $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "FactSheet validation passed." -ForegroundColor Green
