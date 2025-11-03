$ErrorActionPreference = 'Stop'

param(
  [string]$StrategyPath = "..\..\_includes\strategy.yaml",
  [string]$UsecasesDir = "..\..\usecases",
  [string]$OutputPath = "..\..\_includes\Strategic_Alignment_Map.md"
)

function Get-StrategicKpiNames {
  param([string]$yaml)
  $names = @()
  foreach($line in $yaml -split "`n"){
    if ($line -match "^\s*-\s+id:\s+") { $inBlock = $true; continue }
    if ($line -match "^\s*name:\s*\"?(.+?)\"?\s*$") { $names += $Matches[1] }
  }
  return $names | Sort-Object -Unique
}

function Get-UsecaseSupportMap {
  param([string]$dir)
  $map = @{}
  $files = Get-ChildItem -Path $dir -Filter 'README.md' -Recurse | Select-Object -ExpandProperty FullName
  foreach($f in $files){
    $content = Get-Content $f -Raw
    # Extract front-matter (between first two ---)
    $fm = $null
    if ($content -match "(?s)^---(.*?)---") { $fm = $Matches[1] } else { continue }
    # id
    $id = ($fm | Select-String -Pattern "^\s*id:\s*\"?(.+?)\"?\s*$").Matches.Groups[1].Value
    $title = ($fm | Select-String -Pattern "^\s*title:\s*\"?(.+?)\"?\s*$").Matches.Groups[1].Value
    # supports_strategic_kpi list
    $skpLine = ($fm | Select-String -Pattern "^\s*supports_strategic_kpi:\s*\[(.*?)\]\s*$").Matches.Groups[1].Value
    if (-not $skpLine) { continue }
    $items = $skpLine -split "," | ForEach-Object { $_.Trim().Trim('"') }
    foreach($k in $items){
      if (-not $map.ContainsKey($k)) { $map[$k] = @() }
      $map[$k] += @{ id = $id; title = $title }
    }
  }
  return $map
}

if (!(Test-Path $StrategyPath)) { Write-Error "Strategy file not found: $StrategyPath" }
if (!(Test-Path $UsecasesDir)) { Write-Error "Usecases dir not found: $UsecasesDir" }

$strategy = Get-Content $StrategyPath -Raw
$kpis = Get-StrategicKpiNames -yaml $strategy
$supportMap = Get-UsecaseSupportMap -dir $UsecasesDir
$date = Get-Date -Format 'yyyy-MM-dd'

$out = @()
$out += "# Strategic Alignment Map (Generated)"
$out += "_Generated: $date_"
$out += ""
foreach($k in $kpis){
  $out += "## $k"
  if ($supportMap.ContainsKey($k)){
    foreach($uc in $supportMap[$k]){
      $out += "- ${($uc.id)} — ${($uc.title)}"
    }
  } else {
    $out += "- (no linked use cases found)"
  }
  $out += ""
}

$dir = Split-Path -Path $OutputPath -Parent
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$out -join "`n" | Set-Content -Path $OutputPath -Encoding UTF8
Write-Host "Alignment map written to: $OutputPath" -ForegroundColor Green
