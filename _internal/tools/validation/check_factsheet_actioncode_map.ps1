Param(
  [string]$UseCasesRoot = "usecases",
  [string]$MapPath = "usecases/UseCase_ActionCode_Map.yaml",
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

function Get-FrontMatterText {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  return $match.Groups[1].Value
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
  param([string]$FrontMatter)
  if (-not $FrontMatter) { return $null }
  $match = [regex]::Match($FrontMatter, '^\s*id\s*:\s*([A-Z]{2,3}-\d{3})\s*$', 'Multiline')
  if ($match.Success) { return $match.Groups[1].Value }
  return $null
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
$mapPath = Resolve-RepoPath -ProvidedPath $MapPath -DefaultRelative "usecases/UseCase_ActionCode_Map.yaml"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $mapPath) { throw "UseCase ActionCode map not found. Provide -MapPath or run inside repository." }

Write-Host "Factsheets -> ActionCode map alignment" -ForegroundColor Cyan
$mapEntries = Get-MapEntries -Path $mapPath
$issues = @()

Get-ChildItem -Path (Join-Path $useCasesRoot "core") -Recurse -Filter "Business_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $fm = Get-FrontMatterText -Path $_.FullName
  $id = Get-FrontMatterId -FrontMatter $fm
  if (-not $id) {
    $issues += "$($_.FullName): missing id in front matter"
    return
  }
  if (-not $mapEntries.ContainsKey($id)) {
    $issues += "$($_.FullName): missing map entry for $id"
    return
  }
  $expected = $mapEntries[$id] | Sort-Object -Unique
  $actual = (Parse-ListField -FrontMatter $fm -Field "action_codes") | Sort-Object -Unique
  if ($actual.Count -eq 0) {
    $issues += "$($_.FullName): action_codes missing in front matter"
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
