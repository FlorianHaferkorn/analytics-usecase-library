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

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  Write-Host "Node.js not found. Install Node.js to run schema validation." -ForegroundColor Red
  if ($FailOnError) { exit 1 }
  exit 0
}

$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$validator = Join-Path -Path $toolDir -ChildPath "validate_schema.js"
if (-not (Test-Path $validator)) { throw "Schema validator not found: $validator" }
if (-not (Test-Path (Join-Path $toolDir "node_modules\\ajv")) -or -not (Test-Path (Join-Path $toolDir "node_modules\\yaml"))) {
  Write-Host "Schema validator dependencies missing. Run 'npm ci' in _internal/tools/validation." -ForegroundColor Red
  if ($FailOnError) { exit 1 }
  exit 0
}

$schemaDir = Join-Path -Path $toolDir -ChildPath "schemas"
$actionCodeSchema = Join-Path -Path $schemaDir -ChildPath "action_code.schema.json"
$triggerMapTemplateSchema = Join-Path -Path $schemaDir -ChildPath "trigger_map_template.schema.json"
$triggerMapDeploySchema = Join-Path -Path $schemaDir -ChildPath "trigger_map_deploy.schema.json"
$useCaseMapSchema = Join-Path -Path $schemaDir -ChildPath "usecase_actioncode_map.schema.json"

$actionCodeFiles = Get-ChildItem -Path (Join-Path $rootPath "framework\action_codes") -Recurse -Filter "*.yaml" | Where-Object {
  $_.FullName -notmatch '\\decision_spines\\' -and $_.FullName -notmatch '\\_internal\\archive\\'
}
$triggerMapTemplateFiles = @()
$triggerTemplate = Join-Path -Path $rootPath -ChildPath "framework\templates\action_codes\ActionCode_KPI_Trigger_Map_Template.yaml"
if (Test-Path $triggerTemplate) { $triggerMapTemplateFiles += Get-Item $triggerTemplate }
$triggerMapDeployFiles = @()
$deployRoot = Join-Path -Path $rootPath -ChildPath "deployments"
if (Test-Path $deployRoot) {
  $triggerMapDeployFiles += Get-ChildItem -Path $deployRoot -Recurse -Filter "*trigger_map*.yaml"
}
$useCaseMap = Join-Path -Path $rootPath -ChildPath "usecases\UseCase_ActionCode_Map.yaml"

$hadIssues = $false

function Invoke-Validation {
  param([string]$Schema,[string[]]$Targets)
  if (-not (Test-Path $Schema)) { throw "Schema not found: $Schema" }
  if (-not $Targets -or $Targets.Count -eq 0) { return }
  & $node.Source $validator $Schema @Targets
  if ($LASTEXITCODE -ne 0) {
    $script:hadIssues = $true
  }
}

Write-Host "Schema validation" -ForegroundColor Cyan

Invoke-Validation -Schema $actionCodeSchema -Targets ($actionCodeFiles | Select-Object -ExpandProperty FullName)
Invoke-Validation -Schema $triggerMapTemplateSchema -Targets ($triggerMapTemplateFiles | Select-Object -ExpandProperty FullName)
Invoke-Validation -Schema $triggerMapDeploySchema -Targets ($triggerMapDeployFiles | Select-Object -ExpandProperty FullName)
if (Test-Path $useCaseMap) {
  Invoke-Validation -Schema $useCaseMapSchema -Targets @($useCaseMap)
}

if ($hadIssues) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: schema validation passed." -ForegroundColor Green
