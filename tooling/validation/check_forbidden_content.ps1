Param(
  [string]$Root = ".",
  [switch]$EnableUiSpecCheck,
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

# Use Case factsheets: forbidden KPI definition fields in YAML/front matter
$forbiddenKeys = @("definition","definition_short","lineage","target","unit","grain","interpretation")

Get-ChildItem -Path (Join-Path $rootPath "core\usecases") -Recurse -Filter "*Factsheet*.md" | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\' -and $_.FullName -notmatch '\\core\\usecases\\templates\\'
} | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  $front = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if ($front.Success) {
    foreach ($key in $forbiddenKeys) {
      if ($front.Groups[1].Value -match "(?m)^\s*$key\s*:") {
        $issues += "$($_.FullName): forbidden field '$key' in front matter"
      }
    }
  }
  foreach ($block in [regex]::Matches($content, '(?ms)```yaml\s*(.*?)\s*```')) {
    $yaml = $block.Groups[1].Value
    foreach ($key in $forbiddenKeys) {
      if ($yaml -match "(?m)^\s*$key\s*:") {
        $issues += "$($_.FullName): forbidden field '$key' in YAML block"
      }
    }
  }
}

# Trigger maps: forbidden keys (deployments only)
$triggerForbidden = @("threshold","comparator","condition","conditions","value","operator","if")
$triggerFiles = @()
$deployRoot = Join-Path -Path $rootPath -ChildPath "deployments"
if (Test-Path $deployRoot) {
  $triggerFiles += Get-ChildItem -Path $deployRoot -Recurse -Filter "*trigger_map*.yaml" | Select-Object -ExpandProperty FullName
}

foreach ($file in $triggerFiles) {
  $lines = Get-Content -Path $file
  for ($i = 0; $i -lt $lines.Count; $i++) {
    foreach ($key in $triggerForbidden) {
      if ($lines[$i] -match "^\s*$key\s*:") {
        $issues += "$($file):$($i + 1): forbidden key '$key' in trigger map"
        break
      }
    }
  }
}

# UI/report specs: disabled by default
if ($EnableUiSpecCheck) {
  $uiRoot = Join-Path -Path $rootPath -ChildPath "core\templates\page_templates"
  if (Test-Path $uiRoot) {
    Get-ChildItem -Path $uiRoot -Recurse -File -Filter "*.md" | ForEach-Object {
      $content = Get-Content -Raw -Path $_.FullName
      if ($content -match '\b(threshold|formula|calc|calculate|if\s*\()\b') {
        $issues += "$($_.FullName): potential business logic keyword found"
      }
    }
  }
}

if ($issues.Count -gt 0) {
  Write-Host "Forbidden content checks failed:" -ForegroundColor Red
  $max = 20
  $sorted = $issues | Sort-Object
  $sorted | Select-Object -First $max | ForEach-Object { Write-Host "  - $_" }
  if ($sorted.Count -gt $max) {
    $remaining = $sorted.Count - $max
    Write-Host "  ... and $remaining more" -ForegroundColor Yellow
  }
  exit 1
}

Write-Host "OK: no forbidden content detected." -ForegroundColor Green
