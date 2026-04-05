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
  if(-not (Test-JsonValid -Path $pbip.FullName)){ $errors += ".pbip invalid JSON" } else {
    $pj = Get-Content -Raw -Path $pbip.FullName | ConvertFrom-Json
    $schemaVal = $pj.PSObject.Properties['$schema'].Value
    if(-not $schemaVal){ $warnings += ".pbip missing $schema (optional but recommended)" } else {
      # Power BI Desktop (Feb 2026+) requires pbip/pbipProperties; itemShortcut is rejected (KNOWN_ERRORS_AND_FIXES)
      if($schemaVal -notmatch '^https://developer\.microsoft\.com/json-schemas/fabric/pbip/pbipProperties/1\.\d+\.\d+/schema\.json$'){
        $errors += ".pbip $schema must be fabric/pbip/pbipProperties/1.x.y/schema.json (not itemShortcut). See internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md"
      }
    }
    $reportPath = $null
    if($pj.artifacts){
      foreach($a in $pj.artifacts){ if($a.report -and $a.report.path){ $reportPath = $a.report.path; break } }
    }
    if(-not $reportPath){ $errors += "Unable to resolve report path from .pbip artifacts" }
  }
}

# 2) Report definition
if($reportPath){ $pbir = Join-Path $Root (Join-Path $reportPath 'definition.pbir') } else { $pbir = $null }
if(Test-Path $pbir){
  if(-not (Test-BomFree -Path $pbir)){ $errors += "definition.pbir has BOM" }
  if(-not (Test-JsonValid -Path $pbir)){ $errors += "definition.pbir invalid JSON" } else {
    $dp = Get-Content -Raw -Path $pbir | ConvertFrom-Json
    if(-not $dp.'$schema'){ $errors += "definition.pbir missing $schema" }
  }
} else { $warnings += "Missing definition.pbir" }

$reportJson = if($reportPath){ Join-Path $Root (Join-Path $reportPath 'definition/report.json') } else { $null }
if(Test-Path $reportJson){
  if(-not (Test-BomFree -Path $reportJson)){ $errors += "report.json has BOM" }
  if(-not (Test-JsonValid -Path $reportJson)){ $errors += "report.json invalid JSON" } else {
    try {
      $rj = Get-Content -Raw -Path $reportJson | ConvertFrom-Json
      if(-not $rj.'$schema'){ $errors += "report.json missing $schema" }
      if($rj.themeCollection -and $rj.themeCollection.baseTheme){
        if(-not $rj.themeCollection.baseTheme.reportVersionAtImport){ $errors += "report.json missing themeCollection.baseTheme.reportVersionAtImport" }
      }
    } catch {}
  }
} else { $warnings += "Missing report.json" }

# 2a) version.json presence and BOM (Desktop requires it)
$verDef = if($reportPath){ Join-Path $Root (Join-Path $reportPath 'definition/version.json') } else { $null }
$verRoot = if($reportPath){ Join-Path $Root (Join-Path $reportPath 'version.json') } else { $null }
if(-not (Test-Path $verDef) -and -not (Test-Path $verRoot)){
  $errors += "Missing version.json in Report (definition or root)"
}
foreach($v in @($verDef,$verRoot)){
  if(Test-Path $v){
    if(-not (Test-BomFree -Path $v)){ $errors += "version.json has BOM: $v" }
    if(-not (Test-JsonValid -Path $v)){ $errors += "version.json invalid JSON: $v" } else {
      try {
        $vj = Get-Content -Raw -Path $v | ConvertFrom-Json
        if(-not $vj.'$schema'){ $errors += ("version.json missing `$schema: {0}" -f $v) }
        if(-not $vj.version){ $warnings += "version.json missing version: $v" }
      } catch {}
    }
  }
}

# 3) .platform displayName consistency
$repPlat = if($reportPath){ Join-Path $Root (Join-Path $reportPath '.platform') } else { $null }
$semPlat = $null
if(Test-Path $repPlat){ $rep = Get-Content -Raw -Path $repPlat | ConvertFrom-Json }
if(Test-Path $pbir){ try { $dp = Get-Content -Raw -Path $pbir | ConvertFrom-Json; $semRel = $dp.datasetReference.byPath.path } catch {} }
if($semRel){
  $repDir = if($reportPath){ Join-Path $Root $reportPath } else { $Root }
  try { $semFull = [IO.Path]::GetFullPath((Join-Path $repDir $semRel)) } catch { $semFull = Join-Path $repDir $semRel }
  $semPlat = Join-Path $semFull '.platform'
  if(Test-Path $semPlat){ $sem = Get-Content -Raw -Path $semPlat | ConvertFrom-Json }
}
if($rep -and $sem){ if($rep.metadata.displayName -ne $sem.metadata.displayName){ $warnings += "displayName mismatch: '$($rep.metadata.displayName)' vs '$($sem.metadata.displayName)'" } }

# 4) TMDL presence and basic checks
$tmdlRoot = $null; if($semFull){ $tmdlRoot = Join-Path $semFull 'definition' }
if(-not (Test-Path $tmdlRoot)){ $errors += "Missing SemanticModel definition folder" } else {
  $model = Join-Path $tmdlRoot 'model.tmdl'
  if(-not (Test-Path $model)){ $errors += "Missing model.tmdl" } else {
    $raw = Get-Content -Raw -Path $model
    if($raw -notmatch 'ref table'){ $warnings += "model.tmdl has no 'ref table' entries" }
  }
  $tables = Join-Path $tmdlRoot 'tables'
  if(-not (Test-Path $tables)){ $errors += "Missing tables folder" } else {
    $files = Get-ChildItem -Path $tables -Filter *.tmdl -File
    if($files.Count -eq 0){ $warnings += "No table .tmdl files found (empty model)" }
    $measureTables = $files | Where-Object { $_.Name -match '_Measures' }
    if($measureTables.Count -eq 0){ $warnings += "No measure table (_Measures or _All_Measures) found" }
  }
}

# 4a) Validate any *.pbism files (BOM-free + JSON)
$pbismFiles = Get-ChildItem -Path $Root -Recurse -Filter *.pbism -File -ErrorAction SilentlyContinue
foreach($f in $pbismFiles){
  if(-not (Test-BomFree -Path $f.FullName)){ $errors += "pbism has BOM: $($f.FullName)" }
  if(-not (Test-JsonValid -Path $f.FullName)){ $errors += "pbism invalid JSON: $($f.FullName)" }
}

if($warnings.Count){ Write-Host "Warnings:" -ForegroundColor Yellow; $warnings | ForEach-Object { Write-Host "- $_" } }
if($errors.Count){ Write-Host "Errors:" -ForegroundColor Red; $errors | ForEach-Object { Write-Host "- $_" }; exit 2 }
Write-Host "PBIP structure looks good (BOM-free + basic checks)." -ForegroundColor Green




