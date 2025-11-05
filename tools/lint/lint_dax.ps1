Param(
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [string]$RulesPath = "analytics-usecase-library/schemas/best_practices/bpa-rules-dax.json",
  [switch]$FailOnError
)

function Get-DaxBlocks {
  param([string]$Root)
  $files = Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' }
  foreach ($f in $files) {
    $raw = Get-Content -Raw -Path $f.FullName
    $matches = [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')
    foreach ($m in $matches) { $block = $m.Groups[1].Value; $id  = ([regex]::Match($block, 'kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value; $expr = ([regex]::Match($block, '(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value; if ($id) { [pscustomobject]@{ File=$f.FullName; Id=$id; Expr=$expr } } }
  }
}

if (-not (Test-Path $RulesPath)) { Write-Host "Rules file not found: $RulesPath" -ForegroundColor Yellow; exit 0 }
$rules = Get-Content -Raw -Path $RulesPath | ConvertFrom-Json
$items = Get-DaxBlocks -Root $KpiCatalogRoot
$errors=@(); $warnings=@(); $infos=@()

foreach($it in $items){
  $e = $it.Expr
  if (-not $e) { continue }
  foreach($r in $rules.rules){
    $hit = $false
    if ($r.match) { foreach($needle in $r.match.any){ if($e -like ('*' + $needle + '*')){ $hit=$true; break } } }
    if ($r.matchRegex) { if($e -match $r.matchRegex){ $hit=$true } }
    if (-not $r.match -and -not $r.matchRegex) { $hit = $true }
    if (-not $hit) { continue }
    if ($r.mustContain) { foreach($m in $r.mustContain){ if($e -notlike ('*'+$m+'*')){ $hit=$false; break } } }
    if ($r.forbidRegex) { if($e -match $r.forbidRegex){ $hit=$true } else { $hit=$false } }
    if ($r.allowWhenContains) { foreach($allow in $r.allowWhenContains){ if($e -like ('*'+$allow+'*')){ $hit=$false } } }
    if (-not $hit) { continue }
    $msg = "[$($r.id)] $($it.Id) in $($it.File)"
    switch($r.severity){ 'error' { $errors += $msg } 'warn'  { $warnings += $msg } default { $infos += $msg } }
  }
}

if($infos.Count){ Write-Host "DAX lint info:" -ForegroundColor Cyan; $infos | Sort-Object | ForEach-Object { Write-Host "- $_" } }
if($warnings.Count){ Write-Host "DAX lint warnings:" -ForegroundColor Yellow; $warnings | Sort-Object | ForEach-Object { Write-Host "- $_" } }
if($errors.Count){ Write-Host "DAX lint errors:" -ForegroundColor Red; $errors | Sort-Object | ForEach-Object { Write-Host "- $_" }; if($FailOnError){ exit 1 } }
if((-not $errors.Count) -and (-not $warnings.Count)){ Write-Host "DAX lint passed." -ForegroundColor Green }
