Param(
  [string]$Root = ".",
  [switch]$FailOnError,
  [switch]$Strict = $true
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

Write-Host "Registry Builder governance validation"

# Locate Python 3 runner
$pyCmd = $null
$pyTestCommands = @("python", "python3", "py -3")
foreach ($cmd in $pyTestCommands) {
  try {
    $testArgs = $cmd -split " "
    $exe = $testArgs[0]
    $args = $testArgs[1..($testArgs.Length-1)]
    $versionArgs = $args + @("--version")
    $output = & $exe $versionArgs 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $output -match "Python 3") {
      $pyCmd = $cmd
      break
    }
  } catch {
    continue
  }
}

if (-not $pyCmd) {
  Write-Host "ERROR: Python 3 not found." -ForegroundColor Red
  Write-Host "Install Python 3 from python.org or Microsoft Store." -ForegroundColor Yellow
  Write-Host "On Windows: Enable Python in Settings > Apps > App Execution Aliases." -ForegroundColor Yellow
  if ($FailOnError) { exit 1 }
  return
}

Write-Host "Using Python: $pyCmd" -ForegroundColor Gray

$builderScript = Join-Path $rootPath "tooling\ontology\registry_builder.py"
if (-not (Test-Path $builderScript)) {
  Write-Host "ERROR: registry_builder.py not found at $builderScript" -ForegroundColor Red
  if ($FailOnError) { exit 1 }
  return
}

$outDir = Join-Path $rootPath "tooling\ontology\out"
if (-not (Test-Path $outDir)) {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# Run registry builder; --strict only when $Strict is true (CI); omit for local/Aurora builds with alignment warnings
$builderArgs = @($builderScript, "--out-dir", $outDir)
if ($Strict) { $builderArgs += "--strict" }
$cmdParts = $pyCmd -split " "
$exe = $cmdParts[0]
$pyArgs = $cmdParts[1..($cmdParts.Length-1)] + $builderArgs

Write-Host "Running: $pyCmd $($builderArgs -join ' ')" -ForegroundColor Gray
& $exe $pyArgs

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
  Write-Host "FAIL: Registry Builder governance validation failed (exit code: $exitCode)" -ForegroundColor Red
  if ($FailOnError) { exit $exitCode }
} else {
  Write-Host "OK: Registry Builder governance validation passed." -ForegroundColor Green
}

exit $exitCode
