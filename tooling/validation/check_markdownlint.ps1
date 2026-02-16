Param(
  [string]$Root = ".",
  [string[]]$ExcludeDirs = @(".git","node_modules","internal\\archive","implementations\\microsoft_fabric_powerbi\\dist"),
  [switch]$Fix,
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

function Find-Markdownlint {
  $cmd = Get-Command markdownlint -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $local = Join-Path -Path (Get-Location).Path -ChildPath "node_modules\\.bin\\markdownlint.cmd"
  if (Test-Path $local) { return $local }
  return $null
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

$markdownlint = Find-Markdownlint
if (-not $markdownlint) {
  Write-Host "markdownlint not found. Skipping markdown lint check." -ForegroundColor Yellow
  exit 0
}

Write-Host "Markdownlint check" -ForegroundColor Cyan

$args = @(
  "--ignore", ".git",
  "--ignore", "**/node_modules/**",
  "--ignore", "node_modules",
  "--ignore", "products/fabric_powerbi/dist",
  "--ignore", "internal\\archive"
)

if ($Fix) {
  $args += "--fix"
  Write-Host "Auto-fixing markdown issues..." -ForegroundColor Yellow
}

$args += $rootPath

try {
  & $markdownlint @args
  $exit = $LASTEXITCODE
} catch {
  $exit = 1
}

if ($exit -ne 0) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: markdownlint clean." -ForegroundColor Green
