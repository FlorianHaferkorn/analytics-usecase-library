Param(
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [switch]$FailOnError
)

$script:RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

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
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if ($match.Success) { return $match.Groups[1].Value }
  return $null
}

function Has-Field {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  return [regex]::IsMatch($FrontMatter, "^\s*$escaped\s*:", 'Multiline')
}

function Parse-ListField {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  $match = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if (-not $match.Success) { return @() }
  return ([regex]::Matches($match.Groups[1].Value, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value })
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
  if (-not $fm) {
    $errors += "Missing front-matter in $($_.FullName)"
    return
  }
  foreach ($field in $requiredScalarFields) {
    if (-not (Has-Field -FrontMatter $fm -Field $field)) {
      $errors += "$($_.FullName): missing field '$field'"
    }
  }
  foreach ($field in $requiredListFields) {
    $values = Parse-ListField -FrontMatter $fm -Field $field
    if ($values.Count -eq 0) { $errors += "$($_.FullName): list '$field' missing or empty" }
  }
  if (-not (Has-Field -FrontMatter $fm -Field 'required_kpis')) {
    $errors += "$($_.FullName): missing 'required_kpis' map"
  } else {
    $ids = Parse-ListField -FrontMatter $fm -Field 'required_kpi_ids'
    $map = Get-MapField -FrontMatter $fm -Field 'required_kpis'
    foreach ($id in $ids) {
      if (-not $map.Contains($id)) { $errors += "$($_.FullName): required_kpis missing label for '$id'" }
    }
  }
  if (-not (Has-Field -FrontMatter $fm -Field 'data_requirements')) { $warnings += "$($_.FullName): missing data_requirements block" }
  if (-not (Has-Field -FrontMatter $fm -Field 'model_mapping')) { $warnings += "$($_.FullName): missing model_mapping block" }
  if (-not (Has-Field -FrontMatter $fm -Field 'qa_asserts')) { $warnings += "$($_.FullName): missing qa_asserts" }
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
