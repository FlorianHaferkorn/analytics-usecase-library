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
  Write-Host "Schema validator dependencies missing. Run 'npm ci' in tooling/validation." -ForegroundColor Red
  if ($FailOnError) { exit 1 }
  exit 0
}

$aiSchemaDir = Join-Path -Path $rootPath -ChildPath "tooling\generator\schemas"
$actionCodeSchema = Join-Path -Path $aiSchemaDir -ChildPath "action_code.schema.json"
$bracketSchema = Join-Path -Path $aiSchemaDir -ChildPath "usecase_bracket.schema.json"
$orgRolesSchema = Join-Path -Path $aiSchemaDir -ChildPath "org_roles.schema.json"
$triggerMapTemplateSchema = Join-Path -Path $aiSchemaDir -ChildPath "trigger_map_template.schema.json"
$triggerMapDeploySchema = Join-Path -Path $aiSchemaDir -ChildPath "trigger_map_deploy.schema.json"
$designRulesSchema = Join-Path -Path $aiSchemaDir -ChildPath "design_rules.schema.json"

$actionCodeFiles = Get-ChildItem -Path (Join-Path $rootPath "core\action_codes") -Recurse -Filter "*.yaml" | Where-Object {
  $_.FullName -notmatch '[\\/]decision_spines[\\/]' -and $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]' -and $_.Name -ne 'impactful_15.yaml' -and $_.Name -notlike '*_business_case.yaml'
}
$businessCaseFiles = Get-ChildItem -Path (Join-Path $rootPath "core\action_codes") -Recurse -Filter "*_business_case.yaml" | Where-Object {
  $_.FullName -notmatch '[\\/]decision_spines[\\/]' -and $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]'
}
$businessCaseSchema = Join-Path -Path $aiSchemaDir -ChildPath "business_case.schema.json"
$bracketFiles = Get-ChildItem -Path (Join-Path $rootPath "core\usecases\core") -Recurse -Filter "UseCase_Bracket.yaml" -ErrorAction SilentlyContinue
# Resolve org_roles: showcase from env ANALYTICS_SHOWCASE (default aurora_group), else core
$showcaseName = if ($env:ANALYTICS_SHOWCASE) { $env:ANALYTICS_SHOWCASE.Trim() } else { "aurora_group" }
$orgRolesShowcase = Join-Path -Path $rootPath -ChildPath "showcases\$showcaseName\organization\org_roles.yaml"
$orgRolesCore = Join-Path -Path $rootPath -ChildPath "core\organization\org_roles.yaml"
$orgRolesFile = if (Test-Path $orgRolesShowcase) { $orgRolesShowcase } else { $orgRolesCore }
$triggerMapTemplateFiles = @()
$triggerTemplate = Join-Path -Path $rootPath -ChildPath "core\templates\action_codes\ActionCode_KPI_Trigger_Map_Template.yaml"
if (Test-Path $triggerTemplate) { $triggerMapTemplateFiles += Get-Item $triggerTemplate }
$triggerMapDeployFiles = @()
$deployRoot = Join-Path -Path $rootPath -ChildPath "deployments"
if (Test-Path $deployRoot) {
  $triggerMapDeployFiles += Get-ChildItem -Path $deployRoot -Recurse -Filter "*trigger_map*.yaml"
}
$designRulesFile = Join-Path -Path $rootPath -ChildPath "core\templates\page_templates\design_rules.yaml"

$hadIssues = $false

function Invoke-Validation {
  param([string]$Schema,[string[]]$Targets)
  if (-not (Test-Path $Schema)) { throw "Schema not found: $Schema" }
  if (-not $Targets -or $Targets.Count -eq 0) { return }
  & $node.Source $validator $Schema @Targets
  if ((-not $?) -or ($LASTEXITCODE -ne 0)) {
    $script:hadIssues = $true
  }
}

Write-Host "Schema validation" -ForegroundColor Cyan

Invoke-Validation -Schema $actionCodeSchema -Targets ($actionCodeFiles | Select-Object -ExpandProperty FullName)
if ($businessCaseFiles -and $businessCaseFiles.Count -gt 0) {
  Invoke-Validation -Schema $businessCaseSchema -Targets ($businessCaseFiles | Select-Object -ExpandProperty FullName)
}
if ($bracketFiles -and $bracketFiles.Count -gt 0) {
  Invoke-Validation -Schema $bracketSchema -Targets ($bracketFiles | Select-Object -ExpandProperty FullName)
}
if (Test-Path $orgRolesFile) {
  Invoke-Validation -Schema $orgRolesSchema -Targets @($orgRolesFile)
}
Invoke-Validation -Schema $triggerMapTemplateSchema -Targets ($triggerMapTemplateFiles | Select-Object -ExpandProperty FullName)
Invoke-Validation -Schema $triggerMapDeploySchema -Targets ($triggerMapDeployFiles | Select-Object -ExpandProperty FullName)
if (Test-Path $designRulesFile) {
  Invoke-Validation -Schema $designRulesSchema -Targets @($designRulesFile)
}

if ($hadIssues) {
  exit 1
}

Write-Host "OK: schema validation passed." -ForegroundColor Green
