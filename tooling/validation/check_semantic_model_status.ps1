Param(
  [string]$Root = ".",
  [int]$DraftWarningDaysThreshold = 90,
  [switch]$FailOnError
)

# NOTE: This check is always non-failing (warnings only) unless -FailOnError is set.
# It surfaces Measure Dictionaries that have been in "draft" status for too long.
# Intended use: informational warning in Stage 1, not a hard gate.

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

$warnings = @()
$checked = 0
$now = Get-Date

$dictDir = Join-Path $rootPath "core\semantic_models\domains"
Get-ChildItem -Path $dictDir -Recurse -Filter "Measure_Dictionary_*.md" -ErrorAction SilentlyContinue | ForEach-Object {
  $checked++
  $filePath = $_.FullName
  $content = Get-Content -Raw -Path $filePath

  # Extract governance.status value
  $statusMatch = [regex]::Match($content, '(?m)^\s*status\s*:\s*"?(\w+)"?')
  if (-not $statusMatch.Success) {
    $warnings += "$($_.Name): no status field found in governance block"
    return
  }
  $status = $statusMatch.Groups[1].Value.ToLowerInvariant()

  if ($status -ne "draft") { return }

  # If draft: try to find last_review date
  $reviewMatch = [regex]::Match($content, '(?m)last_review\s*:\s*"?(\d{4}-\d{2}-\d{2})"?')
  if (-not $reviewMatch.Success) {
    $warnings += "$($_.Name): status=draft and no parseable last_review date - cannot determine how long it has been in draft"
    return
  }

  $lastReview = [datetime]::ParseExact($reviewMatch.Groups[1].Value, "yyyy-MM-dd", $null)
  $daysDraft = ($now - $lastReview).Days

  if ($daysDraft -ge $DraftWarningDaysThreshold) {
    $warnings += "$($_.Name): status=draft for $daysDraft days (last_review: $($reviewMatch.Groups[1].Value)) - exceeds $DraftWarningDaysThreshold-day threshold"
  }
}

Write-Host "Checked $checked Measure Dictionary files for draft status."

if ($warnings.Count -gt 0) {
  Write-Host "Semantic model draft status warnings:" -ForegroundColor Yellow
  $warnings | ForEach-Object { Write-Host "  WARN: $_" }
  if ($FailOnError) {
    Write-Host "Failing due to -FailOnError flag." -ForegroundColor Red
    exit 1
  }
  # Always exit 0 unless FailOnError - this check is advisory
  Write-Host "Note: draft status warnings are non-blocking. Resolve by updating governance.status to 'active'." -ForegroundColor Yellow
  exit 0
}

Write-Host "OK: no Measure Dictionary files in long-term draft status." -ForegroundColor Green
