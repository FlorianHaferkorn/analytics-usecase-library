<#
.SYNOPSIS
  Validates TMDL files for syntax best practices (tabs-only indentation, no description property).
.DESCRIPTION
  Scans .tmdl files under DistRoot for: (1) indentation using spaces instead of tabs; (2) forbidden "description:" property.
  Sources: products/fabric_powerbi/docs/tmdl_best_practices.md, Microsoft Learn TMDL overview.
.PARAMETER DistRoot
  Root path to search for .tmdl files (e.g. products/fabric_powerbi/dist or a PBIP definition folder).
#>
Param(
  [string]$DistRoot = "products/fabric_powerbi/dist"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$distResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }

if (-not (Test-Path $distResolved)) {
  Write-Host "DistRoot not found: $distResolved. Skipping TMDL syntax check." -ForegroundColor Yellow
  exit 0
}

$tmdlFiles = Get-ChildItem -Path $distResolved -Recurse -Filter "*.tmdl" -ErrorAction SilentlyContinue | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
}
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No .tmdl files under DistRoot. Skipping TMDL syntax check." -ForegroundColor Yellow
  exit 0
}

$errors = @()

foreach ($f in $tmdlFiles) {
  $relPath = $f.FullName.Replace($distResolved, "").TrimStart([System.IO.Path]::DirectorySeparatorChar)
  $lines = Get-Content -Path $f.FullName -ErrorAction SilentlyContinue
  $lineNum = 0
  foreach ($line in $lines) {
    $lineNum++
    # Forbidden: description property (TMDL does not support it; use /// comments)
    if ($line -match '^\s*description\s*:') {
      $errors += [PSCustomObject]@{ File = $relPath; Line = $lineNum; Rule = "tmdl.description.forbidden"; Message = "Property 'description:' is not supported; use /// comments above the object." }
    }
    # Forbidden: spaces used for indentation (TMDL requires tabs only)
    $leading = $line -replace '^(\s*).*', '$1'
    if ($leading -and $leading.Length -gt 0 -and $leading -match ' ') {
      $errors += [PSCustomObject]@{ File = $relPath; Line = $lineNum; Rule = "tmdl.indent.tabs_only"; Message = "Use TABs only for indentation; spaces cause parser errors." }
    }
  }
}

if ($errors.Count -gt 0) {
  foreach ($e in $errors) {
    Write-Host "$($e.File):$($e.Line) [ERROR] $($e.Rule) - $($e.Message)" -ForegroundColor Red
  }
  Write-Host "TMDL syntax: $($errors.Count) error(s)." -ForegroundColor Red
  exit 1
}
Write-Host "TMDL syntax check passed (tabs only, no description property)." -ForegroundColor Green
exit 0
