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

# Check that extended/ and industry/ directories exist and have README.md
$requiredReadmes = @(
  @{ Dir = "core\usecases\extended"; Label = "extended use cases" },
  @{ Dir = "core\usecases\industry"; Label = "industry use cases" }
)

foreach ($entry in $requiredReadmes) {
  $dir = Join-Path $rootPath $entry.Dir
  $readme = Join-Path $dir "README.md"

  if (-not (Test-Path $dir)) {
    $issues += "Directory '$($entry.Dir)' does not exist - $($entry.Label) layer is missing"
    continue
  }

  if (-not (Test-Path $readme)) {
    $issues += "$($entry.Dir)/README.md is missing - $($entry.Label) must have a README explaining scope, criteria, and roadmap"
    continue
  }

  # Check README has minimum content (Purpose/Scope section)
  $content = Get-Content -Raw -Path $readme
  if ($content.Length -lt 200) {
    $issues += "$($entry.Dir)/README.md exists but appears empty or too short (< 200 chars)"
  }
}

# Check that any subdirectories in extended/ and industry/ that contain Use Case content
# (i.e., have a UseCase_Bracket.yaml) also have a Business_Factsheet.md
$ucLayerDirs = @("core\usecases\extended", "core\usecases\industry")
foreach ($layerDir in $ucLayerDirs) {
  $fullLayerDir = Join-Path $rootPath $layerDir
  if (-not (Test-Path $fullLayerDir)) { continue }

  Get-ChildItem -Path $fullLayerDir -Recurse -Filter "UseCase_Bracket.yaml" -ErrorAction SilentlyContinue | ForEach-Object {
    $ucDir = Split-Path -Parent $_.FullName
    $factsheet = Join-Path $ucDir "Business_Factsheet.md"
    if (-not (Test-Path $factsheet)) {
      $relPath = $ucDir.Replace($rootPath, "").TrimStart("\")
      $issues += "$relPath has UseCase_Bracket.yaml but is missing Business_Factsheet.md"
    }
  }
}

if ($issues.Count -gt 0) {
  Write-Host "Extended/Industry use case structure check failed:" -ForegroundColor Red
  $issues | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: extended/ and industry/ use case directories have required README files." -ForegroundColor Green
