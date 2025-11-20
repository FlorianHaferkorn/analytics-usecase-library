param(
  [string]$UseCasesRoot = "usecases"
)

Write-Host "Listing reporting levels and analytics stages for all FactSheets..." -ForegroundColor Cyan
Write-Host "UseCases root: $UseCasesRoot" -ForegroundColor DarkGray
Write-Host ""

if (-not (Test-Path $UseCasesRoot)) {
  Write-Error "UseCases root '$UseCasesRoot' not found."
  exit 1
}

$items = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter "FactSheet.md" |
  Sort-Object FullName |
  ForEach-Object {
    $path = $_.FullName
    $lines = Get-Content -Path $path
    if (-not $lines -or $lines[0].Trim() -ne "---") {
      return
    }

    $metaLines = @()
    for ($i = 1; $i -lt $lines.Count; $i++) {
      if ($lines[$i].Trim() -eq "---") { break }
      $metaLines += $lines[$i]
    }

    $meta = @{}
    foreach ($line in $metaLines) {
      if ($line -match '^\s*([^:]+):\s*(.+)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"')
        $meta[$key] = $value
      }
    }

    [pscustomobject]@{
      Id              = $meta['id']
      Title           = $meta['title']
      Domain          = $meta['domain']
      ReportingLevel  = $meta['reporting_level']
      AnalyticsStage  = $meta['analytics_stage']
      Maturity        = $meta['maturity']
      File            = ($path -replace [regex]::Escape((Get-Location).Path + '\'), '')
    }
  }

if (-not $items) {
  Write-Warning "No FactSheet.md files found under '$UseCasesRoot'."
  exit 0
}

$items | Format-Table Id, Title, Domain, ReportingLevel, AnalyticsStage, Maturity, File -AutoSize
