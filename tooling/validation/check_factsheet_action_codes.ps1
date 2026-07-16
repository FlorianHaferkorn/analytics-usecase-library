Param(
  [string]$UseCasesRoot = "usecases",
  [string]$ActionCodesRoot = "core/action_codes",
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

function Get-BracketActionCodes {
  <#
  .SYNOPSIS
    Fall back to UseCase_Bracket.yaml for action_code_ids when factsheet
    frontmatter has no action_codes field (SSOT = bracket).
  #>
  param([string]$FactsheetPath)
  $dir = Split-Path -Parent $FactsheetPath
  $bracketPath = Join-Path -Path $dir -ChildPath "UseCase_Bracket.yaml"
  if (-not (Test-Path $bracketPath)) { return @() }
  $ids = @()
  $inActionCodeIds = $false
  $sectionIndent = $null
  foreach ($line in (Get-Content -Path $bracketPath)) {
    if ($line -match '^\s*action_code_ids\s*:') {
      $inActionCodeIds = $true
      $sectionIndent = ($line.Length - $line.TrimStart().Length)
      continue
    }
    if ($inActionCodeIds) {
      if ($line -match '^\s*$' -or $line -match '^\s*#') {
        continue
      }
      $currentIndent = ($line.Length - $line.TrimStart().Length)
      if ($currentIndent -le $sectionIndent) {
        break
      }
      if ($line -match '^\s*-\s*"?([^"\s]+)"?') {
        $ids += $matches[1]
      }
    }
  }
  return $ids
}

function Get-ActionCodeIds {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -File | Where-Object {
    $_.Extension -in @(".yaml",".yml") -and $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]'
  } | ForEach-Object {
    $basename = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
    if ($basename) { $null = $ids.Add($basename) }
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*id\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[1])
      }
    }
  }
  return $ids
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "core/usecases"
$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "core/action_codes"
if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $actionCodesRoot) { throw "Action codes root not found. Provide -ActionCodesRoot or run inside repository." }

Write-Host "Factsheets -> Action Codes consistency" -ForegroundColor Cyan
$actionCodeIds = Get-ActionCodeIds -Root $actionCodesRoot
$missing = @()

Get-ChildItem -Path $useCasesRoot -Recurse -Filter "Business_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]' -and
  $_.FullName -notmatch '[\\/]extended[\\/]' -and
  $_.FullName -notmatch '[\\/]industry[\\/]'
} | ForEach-Object {
  $fm = Get-FrontMatterText -Path $_.FullName
  $refs = @()
  if ($fm) {
    $refs = Parse-ListField -FrontMatter $fm -Field "action_codes"
  }
  # Bracket fallback: if factsheet has no action_codes, use UseCase_Bracket.yaml (SSOT)
  if ($refs.Count -eq 0) {
    $refs = Get-BracketActionCodes -FactsheetPath $_.FullName
  }
  foreach ($ref in $refs) {
    if (-not $actionCodeIds.Contains($ref)) {
      $missing += "$($_.FullName): $ref"
    }
  }
}

if ($missing.Count -gt 0) {
  Write-Host "Missing Action Codes (referenced in factsheets or brackets):" -ForegroundColor Red
  $missing | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: factsheet/bracket action codes are consistent." -ForegroundColor Green
