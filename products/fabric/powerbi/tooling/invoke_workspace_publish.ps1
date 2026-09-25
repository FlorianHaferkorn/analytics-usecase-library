<#
.SYNOPSIS
  Staged aktuelle dist-Artefakte in eine release-kompatible Struktur und ruft fabric_release.py auf.
#>

param(
  [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path,
  [string] $Environment = "tst",
  [string] $ResultFile = ".local/pbi_publish_result.json",
  [string] $StagingRoot = ".local/publish_staging",
  [string] $UseCase = "",
  [string] $Domain = "",
  [switch] $All,
  [switch] $DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-PathFromRepo {
  param([string] $Path)
  if ([System.IO.Path]::IsPathRooted($Path)) { return $Path }
  return Join-Path $RepoRoot ($Path -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Get-PythonCommand {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @{ command = "py"; prefix = @("-3") }
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @{ command = "python"; prefix = @() }
  }
  throw "Python launcher not found. Install py or python."
}

function Get-ArtifactsToStage {
  param([string] $DistRoot)

  $semanticModels = @(Get-ChildItem -Path $DistRoot -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue)
  if ($Domain) {
    $semanticModels = @($semanticModels | Where-Object { $_.Name -like "$Domain*.SemanticModel" })
  }

  $reports = @(Get-ChildItem -Path $DistRoot -Directory -Filter "*.Report" -ErrorAction SilentlyContinue)
  if ($UseCase) {
    $reports = @($reports | Where-Object { $_.Name -like "$UseCase*.Report" })
  }

  return @{ semanticModels = $semanticModels; reports = $reports }
}

$modeCount = 0
if ($UseCase) { $modeCount++ }
if ($Domain) { $modeCount++ }
if ($All) { $modeCount++ }
if ($modeCount -gt 1) {
  throw "Specify only one scope: -UseCase, -Domain, or -All"
}
if ($modeCount -eq 0) {
  $All = $true
}

$distRoot = Join-Path $RepoRoot "products\fabric\powerbi\dist"
$releaseScript = Join-Path $RepoRoot "products\fabric\powerbi\deployment\scripts\fabric_release.py"
$resolvedResultFile = Resolve-PathFromRepo -Path $ResultFile
$resultDir = Split-Path -Parent $resolvedResultFile
if ($resultDir -and -not (Test-Path $resultDir)) {
  New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
}

$artifacts = Get-ArtifactsToStage -DistRoot $distRoot
$semanticModels = @($artifacts.semanticModels)
$reports = @($artifacts.reports)

$result = [ordered]@{
  success = $false
  dryRun = [bool]$DryRun
  environment = $Environment
  stagingRoot = $StagingRoot
  stagedArtifacts = @{ semanticModels = $semanticModels.Count; reports = $reports.Count }
  command = $null
  reportFiles = @()
  errors = @()
  warnings = @()
  blockingReason = $null
  credentialStatus = @{
    configured = [bool]($env:TENANT_ID -and $env:CLIENT_ID -and $env:CLIENT_SECRET)
    missing = @(
      if (-not $env:TENANT_ID) { 'TENANT_ID' }
      if (-not $env:CLIENT_ID) { 'CLIENT_ID' }
      if (-not $env:CLIENT_SECRET) { 'CLIENT_SECRET' }
    )
  }
  timestamp = (Get-Date).ToString("o")
}

if (-not (Test-Path $releaseScript)) {
  $result.errors = @("fabric_release.py not found: $releaseScript")
  $result | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
  exit 1
}

if (($semanticModels.Count -lt 1) -or ($reports.Count -lt 1)) {
  $result.errors = @("Publish staging requires at least one semantic model and one report in dist.")
  $result | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
  exit 1
}

$resolvedStagingRoot = Resolve-PathFromRepo -Path $StagingRoot
if (Test-Path $resolvedStagingRoot) {
  Remove-Item -Path $resolvedStagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $resolvedStagingRoot -Force | Out-Null
$dmDir = Join-Path $resolvedStagingRoot "dm"
$biDir = Join-Path $resolvedStagingRoot "bi"
New-Item -ItemType Directory -Path $dmDir -Force | Out-Null
New-Item -ItemType Directory -Path $biDir -Force | Out-Null

foreach ($item in $semanticModels) {
  Copy-Item -Path $item.FullName -Destination (Join-Path $dmDir $item.Name) -Recurse -Force
}
foreach ($item in $reports) {
  Copy-Item -Path $item.FullName -Destination (Join-Path $biDir $item.Name) -Recurse -Force
}

$python = Get-PythonCommand
$commandArgs = @()
$commandArgs += $python.prefix
$commandArgs += @(
  $releaseScript,
  "--environment", $Environment,
  "--layers", "DM,BI",
  "--item_types", "SemanticModel,Report",
  "--repo_path", $resolvedStagingRoot,
  "--validate-parameters"
)
if ($DryRun) {
  $commandArgs += "--skip-framework-validation"
}

$result.command = ((@($python.command) + $commandArgs) -join ' ')

if ($DryRun) {
  if (-not ($env:TENANT_ID -and $env:CLIENT_ID -and $env:CLIENT_SECRET)) {
    $result.warnings = @("Dry-run executed because Fabric credentials are not fully configured.")
    $result.blockingReason = "workspace_publish_credentials_missing"
  }
  $result.success = $true
  $result | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
  Write-Host "[Publish] Dry-run prepared release staging only." -ForegroundColor Yellow
  exit 0
}

if (-not ($env:TENANT_ID -and $env:CLIENT_ID -and $env:CLIENT_SECRET)) {
  $result.errors = @("TENANT_ID, CLIENT_ID and CLIENT_SECRET are required for workspace publish.")
  $result.blockingReason = "workspace_publish_credentials_missing"
  $result | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
  exit 1
}

try {
  $releaseOutput = & $python.command @commandArgs 2>&1
  $releaseExit = $LASTEXITCODE
  if ($null -eq $releaseExit) { $releaseExit = 0 }
  $releaseLines = @($releaseOutput | Out-String -Width 4096 -Stream | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
  $result.executionOutput = @($releaseLines)
  $reportMatches = @($releaseLines | Where-Object { $_ -match '^Deployment report:' } | ForEach-Object { ($_ -replace '^Deployment report:\s*', '').Trim() })
  $result.reportFiles = @($reportMatches)
  if ($releaseExit -eq 0) {
    $result.success = $true
  } else {
    $result.errors = @($releaseLines)
  }
} catch {
  $result.errors = @("Workspace publish failed: $_")
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
if ($result.success) {
  Write-Host "[Publish] Workspace publish completed." -ForegroundColor Green
  exit 0
}

Write-Host "[Publish] Workspace publish failed." -ForegroundColor Red
exit 1