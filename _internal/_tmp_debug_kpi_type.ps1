$kpiType = @{}
Get-ChildItem -Path .\framework\kpi_catalog -Filter 'KPI_Catalog_*.md' | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  foreach ($block in [regex]::Matches($content, '(?ms)```yaml\\s*(?<yaml>.*?)\\s*```')) {
    $yaml = $block.Groups['yaml'].Value
    $matches = [regex]::Matches($yaml, '(?ms)^-\\s*kpi_id\\s*:\\s*\"?([^\"\\s]+)\"?\\s*(?:\\n(?!-\\s*kpi_id).*)*?^\\s*kpi_type\\s*:\\s*\"?([^\"\\s]+)\"?')
    foreach ($m in $matches) {
      $kpiType[$m.Groups[1].Value] = $m.Groups[2].Value.ToLowerInvariant()
    }
  }
}

Write-Output ("kpi_type entries: " + $kpiType.Count)
Write-Output ("sales.net_sales.amount => " + $kpiType['sales.net_sales.amount'])
Write-Output ("sales.price.realization_pct => " + $kpiType['sales.price.realization_pct'])
