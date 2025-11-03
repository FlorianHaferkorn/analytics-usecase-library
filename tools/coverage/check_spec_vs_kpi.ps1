$ErrorActionPreference = 'Stop'

param(
  [Parameter(Position=0)] [string]$SpecPath = "..\..\usecases\01_Commercial\COM-001_Sales_Performance\spec.yaml",
  [Parameter(Position=1)] [string]$KpiDir = "..\..\_includes\kpi_catalog"
)

if (!(Test-Path $SpecPath)) { Write-Error "Spec not found: $SpecPath" }
if (!(Test-Path $KpiDir)) { Write-Error "KPI dir not found: $KpiDir" }

$spec = Get-Content $SpecPath -Raw
$required = @()
foreach($line in $spec -split "`n"){
  if ($line -match "^\s*-\s+(.+)$" -and $line -match "required_measures:") { }
}

# naive parse: collect lines under 'required_measures:' until next top-level key
$collect = $false
foreach($line in $spec -split "`n"){
  if ($line -match "^\s*required_measures:\s*$") { $collect = $true; continue }
  if ($collect -and $line -match "^\s*[a-zA-Z]" ) { $collect = $false }
  if ($collect -and $line -match "^\s*-\s+(.+)$"){
    $m = $Matches[1].Trim()
    $required += $m
  }
}

Write-Host "Required measures in spec:" -ForegroundColor Cyan
$required | ForEach-Object { Write-Host " - $_" }

$catalogFiles = Get-ChildItem -Path $KpiDir -Filter '*.md' -File -Recurse
$found = @{}
foreach($r in $required){ $found[$r] = $false }

foreach($file in $catalogFiles){
  $content = Get-Content $file.FullName -Raw
  foreach($r in $required){
    if ($content -match [regex]::Escape("kpi_key: \"$r\"")){
      $found[$r] = $true
    }
  }
}

Write-Host "\nCoverage:" -ForegroundColor Cyan
foreach($k in $found.Keys){
  $status = if($found[$k]){"OK"} else {"MISSING"}
  Write-Host (" - {0}: {1}" -f $k,$status)
}

if ($found.Values -contains $false){ exit 2 } else { exit 0 }
