Param(
  [string]$UseCase = "",
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [string]$Out = "analytics-usecase-library/dist/dax",
  [string]$MeasuresTable = "Measures"
)

function Get-FrontMatter { param([string]$Path) $content = Get-Content -Raw -Path $Path; $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s"); if ($m.Success) { return $m.Groups[1].Value } return $null }
function Parse-IdsFromFrontMatter { param([string]$FrontMatter,[string]$Field) if (-not $FrontMatter) { return @() } $m = [regex]::Match($FrontMatter, ($Field + '\s*:\s*\[(.*?)\]'), 'Singleline'); if (-not $m.Success) { return @() } $ids=@(); foreach($mm in [regex]::Matches($m.Groups[1].Value,'"([^"]+)"')){ $ids += $mm.Groups[1].Value } return $ids | Sort-Object -Unique }
function Load-KpiCatalog { param([string]$Root) $map = @{}; Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object { $raw = Get-Content -Raw -Path $_.FullName; foreach($m in [regex]::Matches($raw,'(?ms)```yaml\s*(.*?)\s*```')){ $b = $m.Groups[1].Value; $id = ([regex]::Match($b,'kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value; if(-not $id){ continue } $name = ([regex]::Match($b,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value; $expr = ([regex]::Match($b,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value; $fmt  = ([regex]::Match($b,'(?m)^\s*formatString\s*:\s*"([^"]+)"')).Groups[1].Value; $folder = ([regex]::Match($b,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')).Groups[1].Value; $map[$id] = [pscustomobject]@{ id=$id; dax_name=$name; dax_expression=$expr; formatString=$fmt; displayFolder=$folder } } }; return $map }

if(-not (Test-Path $Out)){ New-Item -ItemType Directory -Path $Out | Out-Null }
$targetIds = @(); if($UseCase){ $fs = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md' | Where-Object { $_.Directory.Name -like ($UseCase+'*') } | Select-Object -First 1; if(-not $fs){ Write-Host "Use Case not found: $UseCase" -ForegroundColor Red; exit 1 }; $fm = Get-FrontMatter -Path $fs.FullName; $targetIds = Parse-IdsFromFrontMatter -FrontMatter $fm -Field 'required_kpi_ids'; if($targetIds.Count -eq 0){ Write-Host "No required_kpi_ids in $($fs.FullName)." -ForegroundColor Yellow; exit 0 } } else { Write-Host "No -UseCase specified. Generating for all KPIs in catalogs." -ForegroundColor Yellow }

$catalog = Load-KpiCatalog -Root $KpiCatalogRoot
$outFile = if($UseCase){ Join-Path $Out ($UseCase + '.dax') } else { Join-Path $Out 'all_measures.dax' }
"// Generated from KPI catalogs $(Get-Date -Format s)" | Set-Content -Path $outFile -Encoding utf8
function Emit-Measure { param($rec) if(-not $rec.dax_name){ return } $name = $rec.dax_name; $expr = $rec.dax_expression; if(-not $expr){ $expr = "// TODO: define expression for $($rec.id)" } $lines = @(); $lines += "// kpi_id: $($rec.id)"; if($rec.displayFolder){ $lines += "// displayFolder: $($rec.displayFolder)" }; if($rec.formatString){ $lines += "// formatString: $($rec.formatString)" }; $lines += "MEASURE '$MeasuresTable'[$name] = $expr"; Add-Content -Path $outFile -Value ($lines -join [Environment]::NewLine); Add-Content -Path $outFile -Value "" }
if($UseCase){ foreach($id in $targetIds){ if($catalog.ContainsKey($id)){ Emit-Measure $catalog[$id] } } } else { foreach($rec in $catalog.Values){ Emit-Measure $rec } }
Write-Host ("Wrote measures to: " + $outFile)
