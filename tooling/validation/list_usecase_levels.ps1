param(
  [string]$UseCasesRoot = "core/usecases"
)

function Get-FrontMatterBlock {
  param(
    [string]$Path,
    [int]$Depth = 0
  )
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $block = $match.Groups[1].Value
  $pointer = [regex]::Match($block, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $parent = Split-Path -Parent $Path
    $target = Join-Path -Path $parent -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      $resolved = Resolve-Path -Path $target
      return Get-FrontMatterBlock -Path $resolved.Path -Depth ($Depth + 1)
    }
  }
  return [pscustomobject]@{
    Text   = $block
    Source = (Resolve-Path -Path $Path).Path
  }
}

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
    $fm = Get-FrontMatterBlock -Path $path
    if (-not ($fm -and $fm.Text)) {
      return
    }
    $meta = @{}
    foreach ($line in ($fm.Text -split "\r?\n")) {
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
