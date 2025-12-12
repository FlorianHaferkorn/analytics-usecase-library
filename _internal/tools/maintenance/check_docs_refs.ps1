Param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path   # .../_internal/tools/maintenance
$toolsRoot  = Split-Path -Parent $scriptRoot                    # .../_internal/tools
$repoRoot   = Split-Path -Parent (Split-Path -Parent $toolsRoot) # repo root

Write-Host "Checking documentation and tooling references..." -ForegroundColor Cyan

$items = @(
  @{ Path = "docs/README.md";                                    Kind = "file"; Description = "Docs overview" },
  @{ Path = "docs/company/company_strategy.md";                  Kind = "file"; Description = "Business Strategy / Strategic KPIs / Alignment Map (canonical)" },
  @{ Path = "docs/operating_model/semantic_layer.md";            Kind = "file"; Description = "Semantic Layer blueprint" },
  @{ Path = "docs/operating_model/distribution_architecture.md"; Kind = "file"; Description = "Distribution architecture" },
  @{ Path = "usecases/templates/usecase_factsheet_business.md";  Kind = "file"; Description = "Use Case factsheet (business) template" },
  @{ Path = "usecases/templates/usecase_factsheet_technical.md"; Kind = "file"; Description = "Use Case factsheet (technical) template" },
  @{ Path = "usecases/UseCase_Inventory.md";                     Kind = "file"; Description = "Use Case Inventory" },
  @{ Path = "framework/kpi_catalog/SCHEMA.md";                   Kind = "file"; Description = "KPI Catalog Schema" },
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

if ($missing.Count -gt 0) {
  Write-Host ""
  Write-Host "Documentation/tooling references out of sync. See missing items above." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Documentation and tooling references look consistent." -ForegroundColor Green
