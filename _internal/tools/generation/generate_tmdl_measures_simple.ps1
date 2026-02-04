Param(
  [string]$UseCase,
  [string]$UseCasesRoot = "framework/usecases",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$DistRoot = "implementations/microsoft_fabric_powerbi/dist",
  [string]$MeasuresTableName = "_Measures"
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
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
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
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
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

function Get-UseCaseTitleFromFrontMatter { param([string]$FrontMatter)
  if (-not $FrontMatter) { return $null }
  $m = [regex]::Match($FrontMatter, '(?m)^\s*title\s*:\s*"(.*?)"')
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Load-KpiCatalog { param([string]$Root)
  $map = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    foreach($m in [regex]::Matches($raw,'(?ms)```yaml\s*(.*?)\s*```')){
      $block = $m.Groups[1].Value
      $idMatches = [regex]::Matches($block, '(?m)^\s*-\s*kpi_id\s*:\s*"([^"]+)"')
      if($idMatches.Count -eq 0){
        $singleId = ([regex]::Match($block,'(?m)^\s*kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value
        if($singleId){
          $fmtMatches  = [regex]::Matches($block,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
          $folderMatches = [regex]::Matches($block,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
          $descMatches = [regex]::Matches($block,'(?m)^\s*description\s*:\s*"(.*)"')
          $fmt = if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' }
          if($folderMatches.Count){ $folder = $folderMatches[$folderMatches.Count-1].Groups[1].Value } else {
            $fm2 = [regex]::Matches($block,'displayFolder\s*:\s*"([^"]+)"','Singleline')
            $folder = if($fm2.Count){ $fm2[$fm2.Count-1].Groups[1].Value } else { '' }
          }
          $desc = if($descMatches.Count){ $descMatches[$descMatches.Count-1].Groups[1].Value } else { '' }
          $map[$singleId] = [pscustomobject]@{
            id=$singleId;
            dax_name=([regex]::Match($block,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value;
            dax_expression=([regex]::Match($block,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value;
            formatString=$fmt;
            displayFolder=$folder;
            description=$desc
          }
        }
        continue
      }
      $indices = @(); foreach($im in $idMatches){ $indices += @{ Start=$im.Index; Id=$im.Groups[1].Value } }
      for($i=0; $i -lt $indices.Count; $i++){
        $start = $indices[$i].Start; $end = if($i -lt $indices.Count-1){ $indices[$i+1].Start } else { $block.Length }
        $chunk = $block.Substring($start, $end - $start); $id = $indices[$i].Id
        $fmtMatches  = [regex]::Matches($chunk,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
        $folderMatches = [regex]::Matches($chunk,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
        $descMatches = [regex]::Matches($chunk,'(?m)^\s*description\s*:\s*"(.*)"')
        $fmt = if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' }
        if($folderMatches.Count){ $folder = $folderMatches[$folderMatches.Count-1].Groups[1].Value } else {
          $fm2 = [regex]::Matches($chunk,'displayFolder\s*:\s*"([^"]+)"','Singleline')
          $folder = if($fm2.Count){ $fm2[$fm2.Count-1].Groups[1].Value } else { '' }
        }
        $desc = if($descMatches.Count){ $descMatches[$descMatches.Count-1].Groups[1].Value } else { '' }
        $map[$id] = [pscustomobject]@{
          id=$id;
          dax_name=([regex]::Match($chunk,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value;
          dax_expression=([regex]::Match($chunk,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value;
          formatString=$fmt;
          displayFolder=$folder;
          description=$desc
        }
      }
    }
  }
  return $map
}

function Ensure-Dir { param([string]$Path) if(-not (Test-Path $Path)){ New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

function Write-Utf8NoBom { param([string]$Path, [string]$Text)
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

if(-not $UseCase){ Write-Host "Please pass -UseCase (e.g., COM-001)" -ForegroundColor Yellow; exit 1 }

$fs = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md' | Where-Object { $_.Directory.Name -like ($UseCase+'*') } | Select-Object -First 1
if(-not $fs){ Write-Host "Use Case not found: $UseCase" -ForegroundColor Red; exit 1 }
$fm = Get-FrontMatter -Path $fs.FullName
$targetIds = Parse-IdsFromFrontMatter -FrontMatter $fm -Field 'required_kpi_ids'
if($targetIds.Count -eq 0){ Write-Host "No required_kpi_ids in $($fs.FullName)." -ForegroundColor Yellow; exit 0 }
$useCaseTitle = Get-UseCaseTitleFromFrontMatter -FrontMatter $fm

$catalog = Load-KpiCatalog -Root $KpiCatalogRoot

$caseRoot = Join-Path $DistRoot $UseCase
$semRoot = Join-Path $caseRoot ("$UseCase.SemanticModel")
$tmdlRoot = Join-Path $semRoot 'definition'
$tablesDir = Join-Path $tmdlRoot 'tables'
Ensure-Dir $tablesDir
$modelPath = Join-Path $tmdlRoot 'model.tmdl'
$measuresPath = Join-Path $tablesDir ("$MeasuresTableName.tmdl")

$buf = @()
if($useCaseTitle){ $buf += "/// $UseCase Measures ($useCaseTitle)" } else { $buf += "/// $UseCase Measures" }
$buf += "table $MeasuresTableName"
$buf += ""

foreach($id in $targetIds){
  if($catalog.ContainsKey($id)){
    $rec = $catalog[$id]
    $name = if($rec.dax_name){ $rec.dax_name } else { $id }
    $expr = if($rec.dax_expression){ $rec.dax_expression } else { 'BLANK()' }
    if($rec.description){ $buf += ("    /// " + $rec.description) }
    $safeName = $name -replace "'","''"
    $buf += ("    measure '" + $safeName + "' =")
    foreach($ln in ($expr -split "\r?\n")) { $buf += ("            " + $ln) }
    if($rec.formatString){ $buf += ('        formatString: "' + $rec.formatString + '"') }
    if($rec.displayFolder){ $buf += ('        displayFolder: "' + $rec.displayFolder + '"') }
    $buf += ""
  } else {
    $buf += ("    /// MISSING in KPI catalog: $id")
    $buf += ("    measure '" + ($id -replace "'","''") + "' =")
    $buf += "            // TODO"
    $buf += "            BLANK()"
    $buf += ""
  }
}

Write-Utf8NoBom -Path $measuresPath -Text ($buf -join [Environment]::NewLine)

if(Test-Path $modelPath){
  $raw = Get-Content -Raw -Path $modelPath
  if($raw -notmatch ('(?m)^ref\s+table\s+' + [regex]::Escape($MeasuresTableName) + '\s*$')){
    $toWrite = if($raw.TrimEnd().EndsWith("`n")){ $raw + "ref table $MeasuresTableName`n" } else { $raw + "`nref table $MeasuresTableName`n" }
    Write-Utf8NoBom -Path $modelPath -Text $toWrite
  }
}

Write-Host ("Generated measures TMDL: " + $measuresPath) -ForegroundColor Green
