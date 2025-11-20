Param(
  [Parameter(Mandatory = $true)]
  [string]$Id,
  [Parameter(Mandatory = $true)]
  [string]$Title
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot   = Split-Path -Parent $scriptRoot

function Get-ClusterPath {
  param([string]$UseCaseId)
  switch -Wildcard ($UseCaseId) {
    "COM-*" { return "usecases/01_Commercial" }
    "OPS-*" { return "usecases/02_Operational_Efficiency" }
    "CST-*" { return "usecases/03_Customer_and_Market" }
    "COR-*" { return "usecases/04_Corporate_and_Strategy" }
    "ESG-*" { return "usecases/05_ESG" }
    "GOV-*" { return "usecases/06_Governance" }
    "INN-*" { return "usecases/07_Innovation_and_People" }
    "HR-*"  { return "usecases/04_Corporate_and_Strategy" }
    default { return "usecases" }
  }
}

function Get-SafeName {
  param([string]$Text)
  $normalized = $Text.Trim()
  if (-not $normalized) { return $Text }
  $safe = $normalized -replace '[^0-9A-Za-z _-]', ''
  $safe = $safe -replace '\s+', '_'
  return $safe
}

$clusterRel = Get-ClusterPath -UseCaseId $Id
$clusterAbs = Join-Path $repoRoot $clusterRel

if (-not (Test-Path $clusterAbs)) {
  throw "Cluster folder '$clusterRel' not found under repo root."
}

$safeTitle = Get-SafeName -Text $Title
$folderName = "{0}_{1}" -f $Id, $safeTitle
$targetDir = Join-Path $clusterAbs $folderName

if (Test-Path $targetDir) {
  throw "Target use case folder already exists: $folderName"
}

$templatePath = Join-Path $repoRoot "usecases/UC-000_Template.md"
if (-not (Test-Path $templatePath)) {
  throw "Template not found: usecases/UC-000_Template.md"
}

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

$raw = Get-Content -Raw -Path $templatePath
$raw = $raw -replace 'id:\s*"\{\{PREFIX\}\}-000"', ('id: "' + $Id + '"')
$raw = $raw -replace 'title:\s*"\[Insert Use Case Title\]"', ('title: "' + $Title + '"')

$factSheetPath = Join-Path $targetDir "FactSheet.md"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($factSheetPath, $raw, $utf8)

Write-Host "Created new use case scaffold:" -ForegroundColor Green
Write-Host "  ID:     $Id" -ForegroundColor Green
Write-Host "  Title:  $Title" -ForegroundColor Green
Write-Host "  Folder: $clusterRel/$folderName" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1) Edit the new FactSheet:" -ForegroundColor DarkGray
Write-Host "       $clusterRel/$folderName/FactSheet.md" -ForegroundColor DarkGray
Write-Host "     - Set domain, owner, impact, supports_strategic_kpi_ids, required_kpi_ids, etc." -ForegroundColor DarkGray
Write-Host "  2) Add a row to _includes/UseCase_Inventory.md for $Id." -ForegroundColor DarkGray
Write-Host "  3) Ensure KPIs exist in _includes/kpi_catalog/* (or add them)." -ForegroundColor DarkGray
Write-Host "  4) Run ./tools/run_all_checks.ps1 to validate." -ForegroundColor DarkGray

