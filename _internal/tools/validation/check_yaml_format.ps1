Param(
  [string]$Root = ".",
  [string[]]$ExcludeDirs = @(".git","node_modules","dist","_internal\\archive"),
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
  foreach ($dir in $Exclude) {
    if ($Path -match [Regex]::Escape([IO.Path]::DirectorySeparatorChar + $dir + [IO.Path]::DirectorySeparatorChar)) {
      return $true
    }
    if ($Path -match [Regex]::Escape($dir + [IO.Path]::DirectorySeparatorChar)) {
      return $true
    }
  }
  return $false
}

function Get-PythonCommand {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

Write-Host "YAML format check" -ForegroundColor Cyan

$python = Get-PythonCommand
if (-not $python) {
  Write-Host "Python not found. Skipping YAML format check." -ForegroundColor Yellow
  exit 0
}

$canImportYaml = $false
try {
  & $python -c "import yaml" 2>$null
  if ($LASTEXITCODE -eq 0) { $canImportYaml = $true }
} catch {
  $canImportYaml = $false
}

if (-not $canImportYaml) {
  Write-Host "PyYAML not available. Skipping YAML format check." -ForegroundColor Yellow
  exit 0
}

$files = Get-ChildItem -Path $rootPath -Recurse -File | Where-Object {
  ($_.Extension -in @(".yaml",".yml")) -and -not (Is-ExcludedPath -Path $_.FullName -Exclude $ExcludeDirs)
}

$hadIssues = $false
foreach ($file in $files) {
  $rel = $file.FullName.Substring($rootPath.Length).TrimStart('\')
  try {
    & $python -c "import sys,yaml; yaml.safe_load(open(sys.argv[1], 'rb'))" $file.FullName 2>$null
    if ($LASTEXITCODE -ne 0) {
      $hadIssues = $true
      Write-Host "Invalid YAML: $rel" -ForegroundColor Red
    }
  } catch {
    $hadIssues = $true
    Write-Host "Invalid YAML: $rel" -ForegroundColor Red
  }
}

if ($hadIssues) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: All YAML files parsed successfully." -ForegroundColor Green
