Param(
  [string]$UseCasesRoot = "framework/usecases",
  [string]$MapPath = "framework/usecases/UseCase_ActionCode_Map.yaml",
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

function Get-MapEntries {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  $map = @{}
  $current = $null
  foreach ($line in $lines) {
    if ($line -match '^\s{2}([A-Z]{2,3}-\d{3}):\s*$') {
      $current = $matches[1]
      continue
    }
    if ($current -and $line -match '^\s{4}action_codes:\s*\[(.*?)\]\s*$') {
      $codes = $matches[1].Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
      $map[$current] = $codes
      $current = $null
    }
  }
  return $map
}

function Get-FrontMatterId {
  param([string]$Content)
  if (-not $Content) { return $null }
  $match = [regex]::Match($Content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $fm = $match.Groups[1].Value
  $idMatch = [regex]::Match($fm, '^\s*id\s*:\s*([A-Z]{2,3}-\d{3})\s*$', 'Multiline')
  if ($idMatch.Success) { return $idMatch.Groups[1].Value }
  return $null
}

function Get-BodyActionCodes {
  param([string]$Content)
  if (-not $Content) { return @() }
  $codes = @()
  $inYaml = $false
  $inActionCodes = $false
  foreach ($line in ([regex]::Split($Content, "\r?\n"))) {
    if ($line -match '^\s*```yaml\s*$') { $inYaml = $true; $inActionCodes = $false; continue }
    if ($line -match '^\s*```\s*$') { $inYaml = $false; $inActionCodes = $false; continue }
    if (-not $inYaml) { continue }
    if ($line -match '^\s*action_codes\s*:\s*$') { $inActionCodes = $true; continue }
    if (-not $inActionCodes) { continue }
    if ($line -match '^\s*-\s*id:\s*([A-Z][A-Z0-9\.-]+)\s*$') {
      $codes += $matches[1]
    }
  }
  if ($codes.Count -eq 0) {
    $sectionPattern = '^## 4\. Action Codes \(Summary\)(?<section>.*?)^## 5\.'
    $options = [Text.RegularExpressions.RegexOptions]::Singleline -bor [Text.RegularExpressions.RegexOptions]::Multiline
    $section = [regex]::Match($Content, $sectionPattern, $options)
    if ($section.Success) {
      foreach ($line in ([regex]::Split($section.Groups['section'].Value, "\r?\n"))) {
        if ($line -match '^\s*-\s*id:\s*([A-Z][A-Z0-9\.-]+)\s*$') {
          $codes += $matches[1]
        }
      }
    }
  }
  return $codes
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "framework/usecases"
$mapPath = Resolve-RepoPath -ProvidedPath $MapPath -DefaultRelative "framework/usecases/UseCase_ActionCode_Map.yaml"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $mapPath) { throw "UseCase ActionCode map not found. Provide -MapPath or run inside repository." }

Write-Host "Factsheets -> ActionCode map alignment" -ForegroundColor Cyan
$mapEntries = Get-MapEntries -Path $mapPath
$issues = @()

Get-ChildItem -Path (Join-Path $useCasesRoot "core") -Recurse -Filter "Business_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  $id = Get-FrontMatterId -Content $content
  if (-not $id) {
    $issues += "$($_.FullName): missing id in front matter"
    return
  }
  if (-not $mapEntries.ContainsKey($id)) {
    $issues += "$($_.FullName): missing map entry for $id"
    return
  }
  $expected = $mapEntries[$id] | Sort-Object -Unique
  $actual = (Get-BodyActionCodes -Content $content) | Sort-Object -Unique
  if ($actual.Count -eq 0) {
    $issues += "$($_.FullName): action_codes missing in body"
    return
  }
  $missing = $expected | Where-Object { $_ -notin $actual }
  $extra = $actual | Where-Object { $_ -notin $expected }
  if ($missing.Count -gt 0 -or $extra.Count -gt 0) {
    $details = @()
    if ($missing.Count -gt 0) { $details += ("missing: " + ($missing -join ", ")) }
    if ($extra.Count -gt 0) { $details += ("extra: " + ($extra -join ", ")) }
    $issues += ("$($_.FullName): " + ($details -join "; "))
  }
}

if ($issues.Count -gt 0) {
  Write-Host "Factsheet action_codes mismatch:" -ForegroundColor Red
  $issues | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: factsheet action_codes align with the UseCase ActionCode map." -ForegroundColor Green
