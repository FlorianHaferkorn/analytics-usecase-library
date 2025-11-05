Param(
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [switch]$FailOnMissing
)

function Get-FrontMatter {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Get-RequiredMeasuresFromFrontMatter {
  param([string]$FrontMatter)
  if (-not $FrontMatter) { return @() }
  $m = [regex]::Match($FrontMatter, 'required_measures\s*:\s*\[(.*?)\]', 'Singleline')
  if (-not $m.Success) { return @() }
  $inner = $m.Groups[1].Value
  $measures = @()
  foreach ($mm in [regex]::Matches($inner, '"([^"]+)"')) { $measures += $mm.Groups[1].Value }
  return $measures | Where-Object { $_ -and $_.Trim().Length -gt 0 } | Sort-Object -Unique
}

function Get-RequiredIdsFromFrontMatter {
  param([string]$FrontMatter)
  if (-not $FrontMatter) { return @() }
  $m = [regex]::Match($FrontMatter, 'required_kpi_ids\s*:\s*\[(.*?)\]', 'Singleline')
  if (-not $m.Success) { return @() }
  $inner = $m.Groups[1].Value
  $ids = @()
  foreach ($mm in [regex]::Matches($inner, '"([^"]+)"')) { $ids += $mm.Groups[1].Value }
  return $ids | Where-Object { $_ -and $_.Trim().Length -gt 0 } | Sort-Object -Unique
}

function Load-KpiCatalogIndex {
  param([string]$Root)
  $index = New-Object System.Collections.Generic.List[string]
  $names = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    $matches = [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')
    foreach ($m in $matches) {
      $block = $m.Groups[1].Value
      $idMatch = [regex]::Match($block, 'kpi_id\s*:\s*"([^"]+)"')
      $keyMatch = [regex]::Match($block, 'kpi_key\s*:\s*"([^"]+)"')
      if ($idMatch.Success) {
        $id = $idMatch.Groups[1].Value
        if (-not $index.Contains($id)) { [void]$index.Add($id) }
        if ($keyMatch.Success) { $names[$keyMatch.Groups[1].Value] = $id }
        $aliasBlock = [regex]::Match($block, 'aliases\s*:\s*\[(.*?)\]', 'Singleline')
        if ($aliasBlock.Success) {
          foreach ($nm in [regex]::Matches($aliasBlock.Groups[1].Value, '"([^"]+)"')) { $names[$nm.Groups[1].Value] = $id }
        }
      } elseif ($keyMatch.Success) { $names[$keyMatch.Groups[1].Value] = $true }
    }
  }
  return @{ ids = $index; names = $names }
}

Write-Host "Scanning FactSheets in $UseCasesRoot ..."
$catalog = Load-KpiCatalogIndex -Root $KpiCatalogRoot
$catalogIds = $catalog.ids
$catalogNames = $catalog.names
$factsheets = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md'
if ($factsheets.Count -eq 0) { Write-Host "No FactSheet.md files found." -ForegroundColor Yellow; exit 0 }

$missing = @(); $rows = @()
foreach ($fs in $factsheets) {
  $fm = Get-FrontMatter -Path $fs.FullName
  $reqIds = Get-RequiredIdsFromFrontMatter -FrontMatter $fm
  if ($reqIds.Count -gt 0) {
    foreach ($id in $reqIds) {
      $covered = $false
      if ($catalogIds.Contains($id)) { $covered = $true }
      if (-not $covered) {
        $files = Get-ChildItem -Path $KpiCatalogRoot -Filter '*.md' | Select-Object -ExpandProperty FullName
        $covered = Select-String -Path $files -Pattern $id -SimpleMatch -Quiet -ErrorAction SilentlyContinue
      }
      $rows += [pscustomobject]@{ UseCase = $fs.Directory.Name; Measure = $id; Covered = $covered }
      if (-not $covered) { $missing += "$($fs.Directory.Name): $id" }
    }
  } else {
    $req = Get-RequiredMeasuresFromFrontMatter -FrontMatter $fm
    if ($req.Count -eq 0) { $rows += [pscustomobject]@{ UseCase = $fs.Directory.Name; Measure = '(none)'; Covered = $true }; continue }
    foreach ($m in $req) {
      $covered = $false
      if ($catalogNames.ContainsKey($m)) { $covered = $true } else { $covered = Test-MeasureCovered -Measure $m -CatalogRoot $KpiCatalogRoot }
      $rows += [pscustomobject]@{ UseCase = $fs.Directory.Name; Measure = $m; Covered = $covered }
      if (-not $covered) { $missing += "$($fs.Directory.Name): $m" }
    }
  }
}

$rows | Sort-Object UseCase, Measure | Format-Table -AutoSize | Out-String | Write-Host

if ($missing.Count -gt 0) {
  Write-Host "Missing measures:" -ForegroundColor Red
  $missing | Sort-Object | ForEach-Object { Write-Host "- $_" }
  if ($FailOnMissing) { exit 1 }
} else { Write-Host "All required measures are covered in KPI Catalog." -ForegroundColor Green }

