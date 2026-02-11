Param(
  [string]$Root = ".",
  [string[]]$ExcludeDirs = @(".git","node_modules","_internal\\archive","_internal\\reviews","implementations\\microsoft_fabric_powerbi\\dist")
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path   # .../_internal/tools/maintenance
$toolsRoot  = Split-Path -Parent $scriptRoot                    # .../_internal/tools
$repoRoot   = Split-Path -Parent (Split-Path -Parent $toolsRoot) # repo root

Write-Host "Checking documentation and tooling references..." -ForegroundColor Cyan

$items = @(
  @{ Path = "framework/strategy_operating_model/README.md";                                    Kind = "file"; Description = "Docs overview" },
  @{ Path = "framework/strategy_operating_model/company/company_strategy.md";                  Kind = "file"; Description = "Business Strategy / Strategic KPIs / Alignment Map (canonical)" },
  @{ Path = "framework/strategy_operating_model/operating_model/semantic_layer.md";            Kind = "file"; Description = "Semantic Layer blueprint" },
  @{ Path = "framework/strategy_operating_model/operating_model/distribution_architecture.md"; Kind = "file"; Description = "Distribution architecture" },
  @{ Path = "framework/usecases/templates/usecase_factsheet_business.md";  Kind = "file"; Description = "Use Case factsheet (business) template" },
  @{ Path = "framework/usecases/templates/usecase_factsheet_technical.md"; Kind = "file"; Description = "Use Case factsheet (technical) template" },
  @{ Path = "framework/usecases/UseCase_Inventory.md";                     Kind = "file"; Description = "Use Case Inventory" },
  @{ Path = "framework/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md"; Kind = "file"; Description = "KPI Catalog Schema (canonical)" },
  @{ Path = "framework/kpi_catalog/README.md";                   Kind = "file"; Description = "KPI Catalog overview" },
  @{ Path = "_internal/tools/run_all_checks.ps1";                Kind = "file"; Description = "Run all checks script" },
  @{ Path = "_internal/tools/generation/new_usecase.ps1";        Kind = "file"; Description = "New usecase helper" },
  @{ Path = "_internal/tools/generation/generate_tmdl_measures.ps1"; Kind = "file"; Description = "TMDL measures generator" },
  @{ Path = "_internal/tools/generation/generate_all_measures.ps1";  Kind = "file"; Description = "Generate all measures wrapper" }
)

$missing = @()

foreach ($item in $items) {
  $full = Join-Path $repoRoot $item.Path
  $exists = Test-Path $full
  if ($exists) {
    Write-Host ("  OK   {0} ({1})" -f $item.Path, $item.Description) -ForegroundColor DarkGreen
  } else {
    Write-Host ("  MISS {0} ({1})" -f $item.Path, $item.Description) -ForegroundColor Red
    $missing += $item
  }
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

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repoRoot -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Test-RelativePath {
  param([string]$BasePath,[string]$Target)
  if (-not $Target) { return $true }
  if ($Target -match '^(https?://|mailto:|#)') { return $true }
  $clean = $Target.Split('#')[0].Trim()
  if (-not $clean) { return $true }
  $full = Join-Path -Path (Split-Path -Parent $BasePath) -ChildPath $clean
  return (Test-Path $full)
}

function Get-MarkdownLinks {
  param([string]$Content)
  $links = @()
  foreach ($m in [regex]::Matches($Content, '\[[^\]]*\]\(([^)]+)\)')) {
    $links += $m.Groups[1].Value.Trim()
  }
  return $links
}

function Get-YamlPathRefs {
  param([string]$Content)
  $refs = @()
  foreach ($line in ($Content -split "\r?\n")) {
    if ($line -match '^\s*([A-Za-z0-9_]+_path)\s*:\s*"?([^"\s#]+)"?\s*$') {
      $value = $matches[2]
      if (-not $value) { continue }
      if ($value -match '^(null|~)$') { continue }
      $refs += $value
    }
  }
  return $refs
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

$brokenRefs = @()

Get-ChildItem -Path $rootPath -Recurse -File | Where-Object {
  ($_.Extension -in @(".md",".yaml",".yml")) -and -not (Is-ExcludedPath -Path $_.FullName -Exclude $ExcludeDirs)
} | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  if ($_.Extension -eq ".md") {
    foreach ($link in (Get-MarkdownLinks -Content $content)) {
      if (-not (Test-RelativePath -BasePath $_.FullName -Target $link)) {
        $brokenRefs += "$($_.FullName): $link"
      }
    }
  } else {
    foreach ($ref in (Get-YamlPathRefs -Content $content)) {
      if (-not (Test-RelativePath -BasePath $_.FullName -Target $ref)) {
        $brokenRefs += "$($_.FullName): $ref"
      }
    }
  }
}

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host "Documentation/tooling references out of sync. See missing items above." -ForegroundColor Red
  exit 1
}

if ($brokenRefs.Count -gt 0) {
  Write-Host ""
  Write-Host "Broken relative references detected:" -ForegroundColor Red
  $brokenRefs | Sort-Object | ForEach-Object { Write-Host "  - $_" }
  exit 1
}

Write-Host ""
Write-Host "Documentation and tooling references look consistent." -ForegroundColor Green
