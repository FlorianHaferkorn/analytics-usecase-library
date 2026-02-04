<#
.SYNOPSIS
  Validates DAX expressions in _Measures.tmdl files against best-practice rules (DIVIDE, VAR/RETURN, no FORMAT, etc.).
.DESCRIPTION
  Extracts measure definitions from TMDL under DistRoot, then applies rules from bpa-rules-dax.json.
  Run from repository root. Rules file lives in _internal/tools/linters/powerbi/.
.PARAMETER FailOnWarning
  If set, exit 1 when any warning-level rule fails (default: only errors fail).
#>
Param(
  [string]$DistRoot = "implementations/microsoft_fabric_powerbi/dist",
  [string]$RulesPath = "_internal/tools/linters/powerbi/bpa-rules-dax.json",
  [switch]$FailOnWarning
)

$ErrorActionPreference = "Stop"

# Callers (run_fabric_checks, run_all_checks) run from repo root.
$repoRoot = (Get-Location).Path
$distResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }
$rulesResolved = if ([System.IO.Path]::IsPathRooted($RulesPath)) { $RulesPath } else { Join-Path $repoRoot $RulesPath }

if (-not (Test-Path $rulesResolved)) {
  Write-Host "Rules file not found: $rulesResolved. Skipping DAX best-practice check." -ForegroundColor Yellow
  exit 0
}
$rules = Get-Content -Raw -Path $rulesResolved | ConvertFrom-Json

$tmdlFiles = Get-ChildItem -Path $distResolved -Recurse -Filter "_Measures.tmdl" -ErrorAction SilentlyContinue | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
}
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No _Measures.tmdl under DistRoot. Skipping DAX best-practice check." -ForegroundColor Yellow
  exit 0
}

function Get-DaxFromTmdl {
  param([string]$FilePath)
  $items = @()
  $raw = Get-Content -Raw -Path $FilePath
  # measure 'Name' = ... until formatString: or displayFolder: or next measure
  $pattern = [regex]::new("(?ms)measure\s+['""]([^'""]+)['""]\s*=\s*(.*?)(?=\s+formatString\s*:|\s+displayFolder\s*:|\r?\n\s*measure\s+['""])")
  foreach ($m in $pattern.Matches($raw)) {
    $name = $m.Groups[1].Value.Trim()
    $expr = $m.Groups[2].Value.Trim()
    if ($name -and $expr) {
      $items += [PSCustomObject]@{ File = $FilePath; Name = $name; Expr = $expr }
    }
  }
  return $items
}

$allItems = @()
foreach ($f in $tmdlFiles) {
  $allItems += Get-DaxFromTmdl -FilePath $f.FullName
}

$errors = @()
$warnings = @()
$infos = @()

foreach ($it in $allItems) {
  $e = $it.Expr
  $eSingleLine = $e -replace '[\r\n]+', ' '
  if (-not $e) { continue }
  foreach ($r in $rules.rules) {
    $hit = $false
    if ($r.match -and $r.match.any) {
      foreach ($needle in $r.match.any) { if ($e -like ('*' + $needle + '*')) { $hit = $true; break } }
    }
    if ($r.matchRegex -and ($eSingleLine -match $r.matchRegex)) { $hit = $true }
    if (-not $r.match -and -not $r.matchRegex) { $hit = $true }
    if (-not $hit) { continue }
    if ($r.mustContain) {
      foreach ($m in $r.mustContain) { if ($e -notlike ('*' + $m + '*')) { $hit = $false; break } }
    }
    if ($r.forbidRegex) {
      if ($eSingleLine -match $r.forbidRegex) { $hit = $true } else { $hit = $false }
    }
    if ($r.allowWhenContains) {
      foreach ($allow in $r.allowWhenContains) { if ($e -like ('*' + $allow + '*')) { $hit = $false } }
    }
    if (-not $hit) { continue }
    $shortFile = $it.File
    if ($shortFile.StartsWith($repoRoot)) { $shortFile = $shortFile.Substring($repoRoot.Length).TrimStart('\', '/') }
    $msg = "[$($r.id)] $($it.Name) in $shortFile"
    switch ($r.severity) {
      'error' { $errors += $msg }
      'warn'  { $warnings += $msg }
      default { $infos += $msg }
    }
  }
}

if ($infos.Count) { Write-Host "DAX best-practice info:" -ForegroundColor Cyan; $infos | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" } }
if ($warnings.Count) { Write-Host "DAX best-practice warnings:" -ForegroundColor Yellow; $warnings | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" } }
if ($errors.Count) { Write-Host "DAX best-practice errors:" -ForegroundColor Red; $errors | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" } }

if ($errors.Count -gt 0) {
  Write-Host "DAX best-practice check failed ($($errors.Count) error(s))." -ForegroundColor Red
  exit 1
}
if ($FailOnWarning -and $warnings.Count -gt 0) {
  Write-Host "DAX best-practice check failed ($($warnings.Count) warning(s)) with -FailOnWarning." -ForegroundColor Red
  exit 1
}
Write-Host "DAX best-practice check passed." -ForegroundColor Green
exit 0
