Param(
  [Parameter(Mandatory=$true)][string]$Root
)

$errors=@(); $warnings=@();

function Get-TmdlFiles { param([string]$Dir) if(Test-Path $Dir){ Get-ChildItem -Path $Dir -Filter *.tmdl -File -Recurse } }

function Test-BomFree { param([string]$Path) $b=[System.IO.File]::ReadAllBytes($Path); return -not ($b.Length -ge 3 -and $b[0]-eq 0xEF -and $b[1]-eq 0xBB -and $b[2]-eq 0xBF) }

Write-Host ("BPA on: " + $Root) -ForegroundColor Cyan

# 1) JSON artifacts BOM-free
Get-ChildItem -Path $Root -Recurse -Include *.json,*.pbip,*.pbir -File | ForEach-Object {
  if(-not (Test-BomFree -Path $_.FullName)){ $errors += "BOM present: $($_.FullName)" }
}

# 2) TMDL style checks (procurement-like)
$tmdlRoot = Join-Path $Root 'COM-001.SemanticModel/definition'
if(Test-Path $tmdlRoot){
  $model = Join-Path $tmdlRoot 'model.tmdl'
  if(-not (Test-Path $model)){ $errors += "Missing model.tmdl" } else {
    $raw = Get-Content -Raw -Path $model
    if($raw -notmatch 'ref table'){ $warnings += "model.tmdl has no 'ref table' entries" }
  }
  $tablesDir = Join-Path $tmdlRoot 'tables'
  if(-not (Test-Path $tablesDir)){ $errors += "Missing tables dir" } else {
    $files = Get-TmdlFiles -Dir $tablesDir
    $measureTbl = $files | Where-Object { $_.Name -match '^_[A-Za-z].*\.tmdl$' }
    if(-not $measureTbl){ $warnings += "No measure table starting with '_' found" }
    foreach($f in $measureTbl){
      $raw = Get-Content -Raw -Path $f.FullName
      # Each measure block should have formatString and displayFolder
      $measures = Select-String -InputObject $raw -Pattern '(?m)^\s*measure\s+''([^'']+)''' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value }
      foreach($m in $measures){
        $pattern = '(?ms)measure\s+''' + [regex]::Escape($m) + '''\s*.*?formatString\s*:.*?displayFolder\s*:'
        if(-not ([regex]::IsMatch($raw,$pattern))){ $warnings += "Measure missing formatString or displayFolder: '$m' in $($f.Name)" }
        # Check for preceding /// comment
        $lineIndex = 0
        $lines = Get-Content -Path $f.FullName
        for($i=0;$i -lt $lines.Count;$i++){
          if($lines[$i] -match ('^\s*measure\s+''' + [regex]::Escape($m) + '''')){ $lineIndex=$i; break }
        }
        if($lineIndex -gt 0){ if(-not ($lines[$lineIndex-1].TrimStart().StartsWith('///'))){ $warnings += "Measure missing /// description: '$m' in $($f.Name)" } }
      }
    }
  }
} else { $errors += "Missing SemanticModel/definition" }

if($warnings.Count){ Write-Host "BPA warnings:" -ForegroundColor Yellow; $warnings | Sort-Object | ForEach-Object { Write-Host "- $_" } }
if($errors.Count){ Write-Host "BPA errors:" -ForegroundColor Red; $errors | Sort-Object | ForEach-Object { Write-Host "- $_" }; exit 2 }
Write-Host "BPA checks passed (basic style + BOM)." -ForegroundColor Green

