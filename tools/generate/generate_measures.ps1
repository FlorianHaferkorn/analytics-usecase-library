Param(
  [string]$UseCase = "",
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [string]$Out = "analytics-usecase-library/dist/dax",
  [string]$MeasuresTable = "Measures"
)

function Get-FrontMatter {
  param([string]$Path, [int]$Depth = 0)
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s")
  if (-not $m.Success) { return $null }
  $frontMatter = $m.Groups[1].Value
  $pointer = [regex]::Match($frontMatter, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $target = Join-Path -Path (Split-Path -Parent $Path) -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      return Get-FrontMatter -Path $target -Depth ($Depth + 1)
    }
  }
  return $frontMatter
}
function Parse-IdsFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $pattern = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$pattern\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  $values = @()
  if ($inline.Success) {
    foreach ($mm in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($mm.Groups[1].Success) { $mm.Groups[1].Value }
               elseif ($mm.Groups[2].Success) { $mm.Groups[2].Value }
               else { $mm.Groups[3].Value }
      if ($value) { $values += $value }
    }
    return $values | Sort-Object -Unique
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$pattern\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    foreach ($line in ($block.Groups['body'].Value -split "\r?\n")) {
      $trimmed = $line.Trim()
      if (-not $trimmed) { continue }
      if ($trimmed -match '^\s*-\s*(.*)$') {
        $value = $matches[1].Trim()
      } else {
        continue
      }
      if (-not $value) { continue }
      if ($value -match '^(?<val>[^#]+)\s*(#.*)?$') { $value = $matches['val'].TrimEnd() }
      if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Trim('"')
      } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Trim("'")
      }
      if ($value) { $values += $value }
    }
    return $values | Sort-Object -Unique
  }
  return @()
}
function Load-KpiCatalog {
  param([string]$Root)
  $map = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    foreach($m in [regex]::Matches($raw,'(?ms)```yaml\s*(.*?)\s*```')){
      $block = $m.Groups[1].Value
      $idMatches = [regex]::Matches($block, '(?m)^\s*-\s*kpi_id\s*:\s*"([^"]+)"')
      if($idMatches.Count -eq 0){
        # also support non-list style: kpi_id at top of block
        $singleId = ([regex]::Match($block,'(?m)^\s*kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value
        if($singleId){
          $name = ([regex]::Match($block,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value
          $expr = ([regex]::Match($block,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value
          $fmtMatches  = [regex]::Matches($block,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
          $fmt  = if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' }
          $folderMatches = [regex]::Matches($block,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
          $folder = if($folderMatches.Count){ $folderMatches[$folderMatches.Count-1].Groups[1].Value } else { '' }
          $map[$singleId] = [pscustomobject]@{ id=$singleId; dax_name=$name; dax_expression=$expr; formatString=$fmt; displayFolder=$folder }
        }
        continue
      }
      # when multiple items are inside one code-fence list, slice by indices
      $indices = @()
      foreach($im in $idMatches){ $indices += @{ Start=$im.Index; Id=$im.Groups[1].Value } }
      for($i=0; $i -lt $indices.Count; $i++){
        $start = $indices[$i].Start
        $end = if($i -lt $indices.Count-1){ $indices[$i+1].Start } else { $block.Length }
        $chunk = $block.Substring($start, $end - $start)
        $id = $indices[$i].Id
        $name = ([regex]::Match($chunk,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value
        $expr = ([regex]::Match($chunk,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value
        $fmtMatches  = [regex]::Matches($chunk,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
        $fmt  = if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' }
        $folderMatches = [regex]::Matches($chunk,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
        $folder = if($folderMatches.Count){ $folderMatches[$folderMatches.Count-1].Groups[1].Value } else { '' }
        $map[$id] = [pscustomobject]@{ id=$id; dax_name=$name; dax_expression=$expr; formatString=$fmt; displayFolder=$folder }
      }
    }
  }
  return $map
}

if(-not (Test-Path $Out)){ New-Item -ItemType Directory -Path $Out | Out-Null }
$targetIds = @(); if($UseCase){ $fs = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md' | Where-Object { $_.Directory.Name -like ($UseCase+'*') } | Select-Object -First 1; if(-not $fs){ Write-Host "Use Case not found: $UseCase" -ForegroundColor Red; exit 1 }; $fm = Get-FrontMatter -Path $fs.FullName; $targetIds = Parse-IdsFromFrontMatter -FrontMatter $fm -Field 'required_kpi_ids'; if($targetIds.Count -eq 0){ Write-Host "No required_kpi_ids in $($fs.FullName)." -ForegroundColor Yellow; exit 0 } } else { Write-Host "No -UseCase specified. Generating for all KPIs in catalogs." -ForegroundColor Yellow }

$catalog = Load-KpiCatalog -Root $KpiCatalogRoot
$outFile = if($UseCase){ Join-Path $Out ($UseCase + '.dax') } else { Join-Path $Out 'all_measures.dax' }
"// Generated from KPI catalogs $(Get-Date -Format s)" | Set-Content -Path $outFile -Encoding utf8
function Emit-Measure { param($rec) if(-not $rec.dax_name){ return } $name = $rec.dax_name; $expr = $rec.dax_expression; if(-not $expr){ $expr = "// TODO: define expression for $($rec.id)" } $lines = @(); $lines += "// kpi_id: $($rec.id)"; if($rec.displayFolder){ $lines += "// displayFolder: $($rec.displayFolder)" }; if($rec.formatString){ $lines += "// formatString: $($rec.formatString)" }; $lines += "MEASURE '$MeasuresTable'[$name] = $expr"; Add-Content -Path $outFile -Value ($lines -join [Environment]::NewLine); Add-Content -Path $outFile -Value "" }
if($UseCase){ foreach($id in $targetIds){ if($catalog.ContainsKey($id)){ Emit-Measure $catalog[$id] } } } else { foreach($rec in $catalog.Values){ Emit-Measure $rec } }
Write-Host ("Wrote measures to: " + $outFile)
