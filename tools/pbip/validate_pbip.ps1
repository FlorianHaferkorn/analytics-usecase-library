Param(
  [Parameter(Mandatory=$true)][string]$Root
)

function Test-BomFree {
  param([string]$Path)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  return -not ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
}

function Test-JsonValid {
  param([string]$Path)
  try { Get-Content -Raw -Path $Path | ConvertFrom-Json | Out-Null; return $true } catch { return $false }
}

Write-Host ("Validating PBIP at: " + $Root) -ForegroundColor Cyan

$errors=@(); $warnings=@()

# 1) PBIP root
$pbip = Get-ChildItem -Path $Root -Filter *.pbip -File | Select-Object -First 1
if(-not $pbip){ $errors += "Missing .pbip file" } else {
  if(-not (Test-BomFree -Path $pbip.FullName)){ $errors += ".pbip has BOM" }
  if(-not (Test-JsonValid -Path $pbip.FullName)){ $errors += ".pbip invalid JSON" }
}

# 2) Report definition
$pbir = Join-Path $Root 'COM-001.Report/definition.pbir'
if(Test-Path $pbir){ if(-not (Test-BomFree -Path $pbir)){ $errors += "definition.pbir has BOM" }; if(-not (Test-JsonValid -Path $pbir)){ $errors += "definition.pbir invalid JSON" } } else { $warnings += "Missing definition.pbir" }

$reportJson = Join-Path $Root 'COM-001.Report/definition/report.json'
if(Test-Path $reportJson){ if(-not (Test-BomFree -Path $reportJson)){ $errors += "report.json has BOM" }; if(-not (Test-JsonValid -Path $reportJson)){ $errors += "report.json invalid JSON" } } else { $warnings += "Missing report.json" }

# 3) .platform displayName consistency
$repPlat = Join-Path $Root 'COM-001.Report/.platform'
$semPlat = Join-Path $Root 'COM-001.SemanticModel/.platform'
if(Test-Path $repPlat){ $rep = Get-Content -Raw -Path $repPlat | ConvertFrom-Json } else { $warnings += "Missing Report .platform" }
if(Test-Path $semPlat){ $sem = Get-Content -Raw -Path $semPlat | ConvertFrom-Json } else { $warnings += "Missing SemanticModel .platform" }
if($rep -and $sem){ if($rep.metadata.displayName -ne $sem.metadata.displayName){ $warnings += "displayName mismatch: '$($rep.metadata.displayName)' vs '$($sem.metadata.displayName)'" } }

# 4) TMDL presence and basic checks
$tmdlRoot = Join-Path $Root 'COM-001.SemanticModel/definition'
if(-not (Test-Path $tmdlRoot)){ $errors += "Missing SemanticModel definition folder" } else {
  $model = Join-Path $tmdlRoot 'model.tmdl'
  if(-not (Test-Path $model)){ $errors += "Missing model.tmdl" } else {
    $raw = Get-Content -Raw -Path $model
    if($raw -notmatch 'ref table'){ $warnings += "model.tmdl has no 'ref table' entries" }
  }
  $tables = Join-Path $tmdlRoot 'tables'
  if(-not (Test-Path $tables)){ $errors += "Missing tables folder" } else {
    $files = Get-ChildItem -Path $tables -Filter *.tmdl -File
    if($files.Count -eq 0){ $errors += "No table .tmdl files found" }
    $measureTables = $files | Where-Object { $_.Name -match '_Measures' }
    if($measureTables.Count -eq 0){ $warnings += "No measure table (_Measures or _All_Measures) found" }
  }
}

if($warnings.Count){ Write-Host "Warnings:" -ForegroundColor Yellow; $warnings | ForEach-Object { Write-Host "- $_" } }
if($errors.Count){ Write-Host "Errors:" -ForegroundColor Red; $errors | ForEach-Object { Write-Host "- $_" }; exit 2 }
Write-Host "PBIP structure looks good (BOM-free + basic checks)." -ForegroundColor Green



