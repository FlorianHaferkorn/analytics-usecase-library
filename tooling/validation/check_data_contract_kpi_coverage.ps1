Param(
  [string]$Root = ".",
  [switch]$FailOnError
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

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

$issues = @()
$warnings = @()
$checkedBrackets = 0

# Collect all fact table names declared in data contracts
$contractFactTables = @{}
$contractDir = Join-Path $rootPath "core\data_contracts\domains"
Get-ChildItem -Path $contractDir -Recurse -Filter "*.yaml" -ErrorAction SilentlyContinue | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  # Match fact table names under facts: sections
  foreach ($m in [regex]::Matches($content, '(?m)^\s+- name:\s+(fact_\w+)')) {
    $contractFactTables[$m.Groups[1].Value] = $_.Name
  }
}

Write-Host "Found $($contractFactTables.Count) fact tables across data contracts."

# Check each UseCase Bracket for data_contract references
$bracketsDir = Join-Path $rootPath "core\usecases\core"
Get-ChildItem -Path $bracketsDir -Recurse -Filter "UseCase_Bracket.yaml" -ErrorAction SilentlyContinue | ForEach-Object {
  $checkedBrackets++
  $bracketFile = $_.FullName
  $content = Get-Content -Raw -Path $bracketFile
  $ucId = "unknown"
  if ($content -match '^\s*id\s*:\s*"?([^"\s]+)"?') { $ucId = $matches[1] }

  $dataContractRef = $null
  if ($content -match '(?ms)overrides\s*:\s*.*?data_contract_ref\s*:\s*"?([^"\r\n]+)"?') {
    $dataContractRef = $matches[1].Trim()
  }

  # Legacy factsheet-style required_facts are optional for brackets. If a bracket already
  # points to a governed data contract via overrides.data_contract_ref, treat that as the
  # canonical linkage and do not warn about missing required_facts.
  $factsSection = [regex]::Match($content, '(?ms)required_facts\s*:(.*?)(?=required_dimensions|$)')
  if (-not $factsSection.Success) {
    if ($dataContractRef) {
      $resolvedContractPath = Join-Path $rootPath $dataContractRef
      if (-not (Test-Path $resolvedContractPath)) {
        $issues += "${ucId}: referenced data contract '$dataContractRef' does not exist"
      }
    } else {
      $warnings += "$ucId ($($_.Name)): neither required_facts nor overrides.data_contract_ref found"
    }
    return
  }

  $factsBlock = $factsSection.Groups[1].Value
  foreach ($m in [regex]::Matches($factsBlock, '(?m)-\s+(fact_\w+)')) {
    $factName = $m.Groups[1].Value
    if (-not $contractFactTables.ContainsKey($factName)) {
      $issues += "${ucId}: required fact table '$factName' not found in any data contract domain file"
    }
  }
}

Write-Host "Checked $checkedBrackets UseCase Bracket files against $($contractFactTables.Count) data contract fact tables."

if ($warnings.Count -gt 0) {
  Write-Host "Warnings (non-blocking):" -ForegroundColor Yellow
  $warnings | ForEach-Object { Write-Host "  WARN: $_" }
}

if ($issues.Count -gt 0) {
  Write-Host "Data contract KPI coverage check failed:" -ForegroundColor Red
  $issues | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all required_facts in UseCase Brackets are covered by data contracts." -ForegroundColor Green
