$files = Get-ChildItem -Path .\framework\kpi_catalog -Filter 'KPI_Catalog_*.md'
$issues = @()
foreach ($f in $files) {
  $lines = Get-Content -Path $f.FullName
  $inYaml = $false
  $entry = $null
  foreach ($line in $lines) {
    if ($line -match '^```yaml') { $inYaml = $true; continue }
    if ($inYaml -and $line -match '^```') { $inYaml = $false; $entry = $null; continue }
    if (-not $inYaml) { continue }

    if ($line -match '^-\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
      if ($null -ne $entry) {
        if (-not $entry.kpi_role -or ($entry.kpi_role -notin @('strategic','supporting'))) {
          $issues += "$($f.FullName): $($entry.kpi_id) -> $($entry.kpi_role)"
        }
      }
      $entry = [ordered]@{ kpi_id = $matches[1]; kpi_role = $null }
      continue
    }

    if ($null -ne $entry -and $line -match '^\s*kpi_role\s*:\s*"?([^"\s]+)"?') {
      $entry.kpi_role = $matches[1]
    }

    if ($null -ne $entry -and $line -match '^\s*business\s*:') {
      if (-not $entry.kpi_role -or ($entry.kpi_role -notin @('strategic','supporting'))) {
        $issues += "$($f.FullName): $($entry.kpi_id) -> $($entry.kpi_role)"
      }
      $entry = $null
    }
  }
}
if ($issues.Count -eq 0) { 'ALL_OK' } else { $issues }
