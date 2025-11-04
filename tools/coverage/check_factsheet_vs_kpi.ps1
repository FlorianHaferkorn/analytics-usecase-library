param(
  [switch]$FailOnMissing
)

# ID-only coverage checker: validates that all required_kpi_ids in Use Case FactSheets
# exist in the KPI Catalogs. Designed for pwsh (PowerShell 7+).

function Get-KpiIdsFromCatalogs {
  param([string]$CatalogRoot)
  $ids = New-Object System.Collections.Generic.HashSet[string]
  Get-ChildItem -Path $CatalogRoot -Filter *.md -File | ForEach-Object {
    $content = Get-Content -LiteralPath $_.FullName -Raw
    $matches = [regex]::Matches($content, "```yaml([\s\S]*?)```", 'Singleline')
    foreach ($m in $matches) {
      $yaml = $m.Groups[1].Value
      try {
        $items = $yaml | ConvertFrom-Yaml
      } catch {
        Write-Warning "YAML parse failed in $($_.FullName): $($_.Exception.Message)"
        continue
      }
      if ($items -is [System.Collections.IEnumerable]) {
        foreach ($it in $items) {
          if ($it.kpi_id) { [void]$ids.Add([string]$it.kpi_id) }
        }
      } elseif ($items.kpi_id) {
        [void]$ids.Add([string]$items.kpi_id)
      }
    }
  }
  return ,$ids
}

function Get-FrontMatter {
  param([string]$Path)
  $lines = Get-Content -LiteralPath $Path
  if ($lines.Count -lt 3 -or $lines[0].Trim() -ne '---') { return $null }
  $endIdx = ($lines | Select-String -Pattern '^---\s*$' -SimpleMatch | Select-Object -Skip 1 -First 1).LineNumber
  if (-not $endIdx) { return $null }
  $yaml = ($lines[1..($endIdx-2)]) -join "`n"
  try { return ($yaml | ConvertFrom-Yaml) } catch { return $null }
}

$repoRoot = Join-Path $PSScriptRoot '..' '..' '..' | Resolve-Path
$catalogRoot = Join-Path $repoRoot 'analytics-usecase-library' '_includes' 'kpi_catalog'
$usecaseRoot = Join-Path $repoRoot 'analytics-usecase-library' 'usecases'

$catalogIds = Get-KpiIdsFromCatalogs -CatalogRoot $catalogRoot

$missing = @()
$summary = @()

Get-ChildItem -Path $usecaseRoot -Recurse -Filter FactSheet.md -File | ForEach-Object {
  $fm = Get-FrontMatter -Path $_.FullName
  $ucId = if ($fm.id) { [string]$fm.id } else { $_.Directory.Name }
  $req = @()
  if ($fm.required_kpi_ids) { $req = @($fm.required_kpi_ids | ForEach-Object { [string]$_ }) }
  $missHere = @()
  foreach ($id in $req) {
    if (-not $catalogIds.Contains($id)) { $missHere += $id }
  }
  $summary += [pscustomobject]@{ UseCase=$ucId; Required=$req.Count; Missing=$missHere.Count }
  foreach ($m in $missHere) {
    $missing += [pscustomobject]@{ UseCase=$ucId; KPI_ID=$m; Path=$_.FullName }
  }
}

Write-Host "Use Case KPI Coverage (ID-only)"
$summary | Sort-Object UseCase | Format-Table -Auto

if ($missing.Count -gt 0) {
  Write-Warning "Missing KPI IDs detected: $($missing.Count)"
  $missing | Format-Table -Auto
  if ($FailOnMissing) { exit 1 }
} else {
  Write-Host "All required_kpi_ids are covered by catalogs."
}

