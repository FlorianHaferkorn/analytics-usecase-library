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

function Read-TemplateRaw {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return $null }
  return Get-Content -Raw -Path $Path
}

function Extract-FrontMatter {
  param([string]$Content)
  $match = [regex]::Match($Content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $front = $match.Groups[1].Value
  $bodyStart = $match.Index + $match.Length
  $body = $Content.Substring($bodyStart)
  return [pscustomobject]@{
    FrontMatter = $front
    Body        = $body
  }
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

$legacyTemplatePath = Join-Path $repoRoot "usecases/UC-000_Template.md"
if (-not (Test-Path $legacyTemplatePath)) {
  throw "Template not found: usecases/UC-000_Template.md"
}

$businessTemplatePath = Join-Path $repoRoot "usecases/Business_Factsheet_Template.md"
$technicalTemplatePath = Join-Path $repoRoot "usecases/Technical_Factsheet_Template.md"

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

$legacyRaw = Read-TemplateRaw -Path $legacyTemplatePath
$legacyRaw = $legacyRaw -replace 'id:\s*"\{\{PREFIX\}\}-000"', ('id: "' + $Id + '"')
$legacyRaw = $legacyRaw -replace 'title:\s*"\[Insert Use Case Title\]"', ('title: "' + $Title + '"')
$fmBlock = Extract-FrontMatter -Content $legacyRaw
if (-not $fmBlock) { throw "Unable to parse front-matter in UC-000 template." }
$frontMatter = $fmBlock.FrontMatter.Trim()
$legacyBody = $fmBlock.Body.TrimStart()

$businessBody = Read-TemplateRaw -Path $businessTemplatePath
if (-not $businessBody) { $businessBody = $legacyBody }
$businessBody = ($businessBody -replace '<UC-ID>', $Id).TrimStart()
$businessContent = @(
  '---'
  $frontMatter
  '---'
  ''
  $businessBody
) -join [Environment]::NewLine

$technicalBody = Read-TemplateRaw -Path $technicalTemplatePath
if (-not $technicalBody) {
  $technicalBody = "# $Id - Technical Factsheet`n`nTODO: Fill out the technical template."
} else {
  $technicalBody = $technicalBody -replace '<UC-ID>', $Id
}

$today = Get-Date -Format "dd.MM.yyyy"
$factSheetContent = @(
  '---'
  'migrated: true'
  'business_factsheet: "./Business_Factsheet.md"'
  'technical_factsheet: "./Technical_Factsheet.md"'
  ("last_update: ""$today""")
  '---'
  ''
  "# $Title"
  ''
  "Dieses FactSheet dient nur noch als Legacy-Stub. Bitte alle inhaltlichen und technischen Informationen direkt in den ausgewiesenen Business- bzw. Technical-Factsheets pflegen."
  ''
  '- [Business_Factsheet.md](./Business_Factsheet.md)'
  '- [Technical_Factsheet.md](./Technical_Factsheet.md)'
) -join [Environment]::NewLine

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $targetDir "Business_Factsheet.md"), $businessContent, $utf8)
[System.IO.File]::WriteAllText((Join-Path $targetDir "Technical_Factsheet.md"), $technicalBody, $utf8)
[System.IO.File]::WriteAllText((Join-Path $targetDir "FactSheet.md"), $factSheetContent, $utf8)

Write-Host "Created new use case scaffold:" -ForegroundColor Green
Write-Host "  ID:     $Id" -ForegroundColor Green
Write-Host "  Title:  $Title" -ForegroundColor Green
Write-Host "  Folder: $clusterRel/$folderName" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1) Complete the Business factsheet:" -ForegroundColor DarkGray
Write-Host "       $clusterRel/$folderName/Business_Factsheet.md" -ForegroundColor DarkGray
Write-Host "  2) Complete the Technical factsheet:" -ForegroundColor DarkGray
Write-Host "       $clusterRel/$folderName/Technical_Factsheet.md" -ForegroundColor DarkGray
Write-Host "  3) Keep FactSheet.md as stub (already wired to the new files)." -ForegroundColor DarkGray
Write-Host "  4) Add $Id to _includes/UseCase_Inventory.md and ensure referenced KPIs exist." -ForegroundColor DarkGray

