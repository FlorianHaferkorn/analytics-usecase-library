param(
  [string]$KpiCatalogRoot = (Join-Path $PSScriptRoot "..\..\..\core\kpi_catalog"),
  [string]$MeasureDictRoot = (Join-Path $PSScriptRoot "..\..\..\semantic_models\domains")
)

$ErrorActionPreference = "Stop"

function Get-KpiIdsFromCatalog {
  param([string]$Root)
  $ids = New-Object System.Collections.Generic.List[string]
  Get-ChildItem -Path $Root -Filter "KPI_Catalog.md" | ForEach-Object {
    Get-Content $_.FullName | ForEach-Object {
      if ($_ -match '^\s*-\s*kpi_id:\s*"?([A-Za-z0-9_.-]+)"?\s*$') {
        $ids.Add($Matches[1]) | Out-Null
      }
    }
  }
  return $ids
}

function Get-KpiIdsFromMeasureDictionaries {
  param([string]$Root)
  $ids = New-Object System.Collections.Generic.List[string]
  $warnings = New-Object System.Collections.Generic.List[string]
  Get-ChildItem -Path $Root -Recurse -Filter "Measure_Dictionary_*.md" | Where-Object {
    $_.FullName -notmatch '\\archive\\' -and $_.Name -notmatch '_Archive\.md$' -and $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    $file = $_.FullName
    $measureName = $null
    $isKpi = $null
    $kpiId = $null

    function Flush-Measure {
      if ($isKpi -eq $true) {
        if (-not $kpiId) {
          $warnings.Add("${file}: KPI measure without kpi_id_ref (${measureName})") | Out-Null
        } else {
          $ids.Add($kpiId) | Out-Null
        }
      } elseif ($isKpi -eq $false -and $kpiId) {
        $warnings.Add("${file}: Non-KPI measure has kpi_id_ref (${measureName} -> ${kpiId})") | Out-Null
      }
      $measureName = $null
      $isKpi = $null
      $kpiId = $null
    }

    Get-Content $file | ForEach-Object {
      if ($_ -match '^\s*-\s*measure_name:\s*"?(.+?)"?\s*$') {
        Flush-Measure
        $measureName = $Matches[1].Trim()
      }
      if ($_ -match '^\s*is_kpi_measure:\s*(true|false)\s*$') {
        $isKpi = ($Matches[1] -eq 'true')
      }
      if ($_ -match '^\s*kpi_id_ref:\s*(.*)\s*$') {
        $raw = $Matches[1].Trim()
        $raw = $raw.Trim('"').Trim("'").Trim()
        if ([string]::IsNullOrWhiteSpace($raw) -or $raw -eq 'null') {
          $kpiId = $null
        } else {
          $kpiId = $raw
        }
      }
    }
    Flush-Measure
  }
  return @{ ids = $ids; warnings = $warnings }
}

$kpiCatalogIds = Get-KpiIdsFromCatalog -Root $KpiCatalogRoot
$dictResult = Get-KpiIdsFromMeasureDictionaries -Root $MeasureDictRoot
$measureIds = $dictResult.ids
$dictWarnings = $dictResult.warnings

$missingInDict = $kpiCatalogIds | Where-Object { $_ -notin $measureIds } | Sort-Object -Unique
$missingInCatalog = $measureIds | Where-Object { $_ -notin $kpiCatalogIds } | Sort-Object -Unique

$dupDict = $measureIds | Group-Object | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name
$dupCatalog = $kpiCatalogIds | Group-Object | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name

Write-Host "KPI Catalog <-> Measure Dictionary consistency"

if ($dictWarnings.Count -gt 0) {
  Write-Host "Warnings:"
  $dictWarnings | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($dupCatalog.Count -gt 0) {
  Write-Host "Duplicate kpi_id in KPI catalogs:"
  $dupCatalog | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($dupDict.Count -gt 0) {
  Write-Host "Duplicate kpi_id_ref in Measure Dictionaries:"
  $dupDict | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($missingInDict.Count -eq 0 -and $missingInCatalog.Count -eq 0) {
  Write-Host "OK: KPI IDs are consistent."
  exit 0
}

if ($missingInDict.Count -gt 0) {
  Write-Host "Missing in Measure Dictionaries (present in KPI catalogs):"
  $missingInDict | ForEach-Object { Write-Host "  - $_" }
}

if ($missingInCatalog.Count -gt 0) {
  Write-Host "Missing in KPI catalogs (present in Measure Dictionaries):"
  $missingInCatalog | ForEach-Object { Write-Host "  - $_" }
}

exit 1

