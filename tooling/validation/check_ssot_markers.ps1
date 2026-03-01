Param(
  [string]$Root = ".",
  [string[]]$AllowList = @(
    "core/strategy_operating_model/operating_model/reference/single_source_of_truth.md",
    "products/fabric/orchestrator/README.md",
    "products/fabric/orchestrator/config.yaml"
  ),
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

function Is-AllowListed {
  param([string]$Path,[string[]]$Allow)
  foreach ($item in $Allow) {
    $full = Resolve-RepoPath -ProvidedPath $item -DefaultRelative $item
    if ($full -and ($full -eq $Path)) { return $true }
  }
  return $false
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

$markers = @(
  "^\s*SSOT\s*:\s*",
  "^\s*Authority\s*:\s*",
  "^\s*authority\s*:\s*"
)

$hits = @()

Get-ChildItem -Path $rootPath -Recurse -File | Where-Object {
  $_.Extension -in @(".md",".yaml",".yml") -and $_.FullName -notmatch '\\internal\\archive\\'
} | ForEach-Object {
  $path = $_.FullName
  $lines = Get-Content -Path $path
  for ($i = 0; $i -lt $lines.Count; $i++) {
    foreach ($m in $markers) {
      if ($lines[$i] -match $m) {
        if (-not (Is-AllowListed -Path $path -Allow $AllowList)) {
          $hits += "$($path):$($i + 1): $($lines[$i].Trim())"
        }
        break
      }
    }
  }
}

if ($hits.Count -gt 0) {
  Write-Host "SSOT markers found outside allowlist:" -ForegroundColor Red
  $hits | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: SSOT markers only in allowlisted files." -ForegroundColor Green
