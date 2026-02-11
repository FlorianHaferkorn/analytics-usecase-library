Param(
  [string]$Root = ".",
  [string[]]$Extensions = @("md","yaml","yml","ps1","txt"),
  [string[]]$ExcludeDirs = @(".git","node_modules","_internal\\archive","_internal\\reviews","_internal\\tools\\linters","implementations\\microsoft_fabric_powerbi\\dist"),
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

function Is-ExcludedPath {
  param([string]$Path,[string[]]$Exclude)
  $normPath = $Path.ToLowerInvariant().Replace('/', '\')
  foreach ($dir in $Exclude) {
    $normDir = "\" + ($dir.ToLowerInvariant().Replace('/', '\').Trim('\','/')) + "\"
    if ($normPath.Contains($normDir)) { return $true }
  }
  return $false
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

$patterns = @(
  ([string][char]0x00C3),
  ([string][char]0x00C2),
  ([string]::Concat([char]0x00E2,[char]0x0080,[char]0x0093)),
  ([string]::Concat([char]0x00E2,[char]0x0080,[char]0x0094)),
  ([string]::Concat([char]0x00E2,[char]0x0080,[char]0x0099)),
  ([string]::Concat([char]0x00E2,[char]0x0080,[char]0x009C)),
  ([string]::Concat([char]0x00E2,[char]0x0080)),
  ([string]::Concat([char]0x00C6,[char]0x0092,[char]0x003F))
)

$hadIssues = $false
Write-Host "Mojibake scan" -ForegroundColor Cyan

$files = Get-ChildItem -Path $rootPath -Recurse -File | Where-Object {
  $pathLower = $_.FullName.ToLowerInvariant()
  # Performance: skip node_modules, .git, dist, archive
  if ($pathLower -match '(\\node_modules\\|\\.git\\|_archive\\|\\microsoft_fabric_powerbi\\dist\\)') { return $false }
  $ext = $_.Extension.TrimStart(".")
  $Extensions -contains $ext `
    -and ($pathLower -notlike "*\internal\reviews\*") `
    -and ($pathLower -notlike "*\tooling\linters\*") `
    -and -not (Is-ExcludedPath -Path $_.FullName -Exclude $ExcludeDirs)
}

foreach ($file in $files) {
  $lines = Get-Content -Path $file.FullName
  for ($i = 0; $i -lt $lines.Count; $i++) {
    foreach ($p in $patterns) {
      if ($lines[$i] -match [Regex]::Escape($p)) {
        if (-not $hadIssues) {
          Write-Host "Potential mojibake found:" -ForegroundColor Red
        }
        $hadIssues = $true
        $rel = $file.FullName.Substring($rootPath.Length).TrimStart('\')
        Write-Host ("  - {0}:{1}: {2}" -f $rel, ($i + 1), $lines[$i].Trim())
        break
      }
    }
  }
}

if ($hadIssues) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: No mojibake patterns detected." -ForegroundColor Green


