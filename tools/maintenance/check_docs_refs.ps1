Param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path   # .../tools/maintenance
$toolsRoot  = Split-Path -Parent $scriptRoot                    # .../tools
$repoRoot   = Split-Path -Parent $toolsRoot                     # repo root

Write-Host "Checking documentation and tooling references..." -ForegroundColor Cyan

$items = @(
  @{ Path = "docs/Concept_and_Conventions.md";       Kind = "file"; Description = "Concept & Conventions" },
  @{ Path = "docs/Business_Playbook.md";             Kind = "file"; Description = "Business Playbook" },
  @{ Path = "docs/Quickstart_1-Pager.md";            Kind = "file"; Description = "Quickstart 1-Pager" },
  @{ Path = "docs/Instructions.md";                  Kind = "file"; Description = "Instructions" },
  @{ Path = "usecases/UC-000_Template.md";           Kind = "file"; Description = "Use Case template" },
  @{ Path = "_includes/UseCase_Inventory.md";        Kind = "file"; Description = "Use Case Inventory" },
  @{ Path = "_includes/Strategic_KPIs.md";           Kind = "file"; Description = "Strategic KPIs" },
  @{ Path = "_includes/Strategic_Alignment_Map.md";  Kind = "file"; Description = "Strategic Alignment Map" },
  @{ Path = "_includes/kpi_catalog/SCHEMA.md";       Kind = "file"; Description = "KPI Catalog Schema" },
  @{ Path = "tools/run_all_checks.ps1";              Kind = "file"; Description = "Run all checks script" },
  @{ Path = "tools/new_usecase.ps1";                 Kind = "file"; Description = "New usecase helper" },
  @{ Path = "tools/generate/generate_tmdl_measures.ps1"; Kind = "file"; Description = "TMDL measures generator" },
  @{ Path = "tools/generate_all_measures.ps1";       Kind = "file"; Description = "Generate all measures wrapper" }
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
