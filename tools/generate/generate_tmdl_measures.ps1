Param(
  [string]$UseCase = "",
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [string]$DistRoot = "analytics-usecase-library/dist",
  [string]$MeasuresTableName = "_Measures"
)

function Get-FrontMatter {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Parse-IdsFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $m = [regex]::Match($FrontMatter, ($Field + '\s*:\s*\[(.*?)\]'), 'Singleline')
  if (-not $m.Success) { return @() }
  $ids=@()
  foreach($mm in [regex]::Matches($m.Groups[1].Value,'"([^"]+)"')){ $ids += $mm.Groups[1].Value }
  return $ids | Sort-Object -Unique
}

function Get-UseCaseTitleFromFrontMatter {
  param([string]$FrontMatter)
  if (-not $FrontMatter) { return $null }
  $m = [regex]::Match($FrontMatter, '(?m)^\s*title\s*:\s*"(.*?)"')
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
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
        # support non-list style: a single KPI block
        $singleId = ([regex]::Match($block,'(?m)^\s*kpi_id\s*:\s*"([^"]+)"')).Groups[1].Value
        if($singleId){
          $rec = [pscustomobject]@{}
          $rec | Add-Member NoteProperty id $singleId
          $rec | Add-Member NoteProperty dax_name (([regex]::Match($block,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value)
          $rec | Add-Member NoteProperty dax_expression (([regex]::Match($block,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value)
          # take last occurrence to allow overrides within block
          $fmtMatches  = [regex]::Matches($block,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
          $rec | Add-Member NoteProperty formatString (if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' })
          $folderMatches = [regex]::Matches($block,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
          $rec | Add-Member NoteProperty displayFolder (if($folderMatches.Count){ $folderMatches[$folderMatches.Count-1].Groups[1].Value } else { '' })
          $rec | Add-Member NoteProperty description (([regex]::Match($block,'(?m)^\s*description\s*:\s*"(.*)"')).Groups[1].Value)
          $map[$singleId] = $rec
        }
        continue
      }
      # multiple items within one code-fence list => slice by id indices
      $indices = @()
      foreach($im in $idMatches){ $indices += @{ Start=$im.Index; Id=$im.Groups[1].Value } }
      for($i=0; $i -lt $indices.Count; $i++){
        $start = $indices[$i].Start
        $end = if($i -lt $indices.Count-1){ $indices[$i+1].Start } else { $block.Length }
        $chunk = $block.Substring($start, $end - $start)
        $id = $indices[$i].Id
        $rec = [pscustomobject]@{}
        $rec | Add-Member NoteProperty id $id
        $rec | Add-Member NoteProperty dax_name (([regex]::Match($chunk,'(?m)^\s*dax_name\s*:\s*"([^"]+)"')).Groups[1].Value)
        $rec | Add-Member NoteProperty dax_expression (([regex]::Match($chunk,'(?m)^\s*dax_expression\s*:\s*"(.*)"')).Groups[1].Value)
        $fmtMatches  = [regex]::Matches($chunk,'(?m)^\s*formatString\s*:\s*"([^"]+)"')
        $rec | Add-Member NoteProperty formatString (if($fmtMatches.Count){ $fmtMatches[$fmtMatches.Count-1].Groups[1].Value } else { '' })
        $folderMatches = [regex]::Matches($chunk,'(?m)^\s*displayFolder\s*:\s*"([^"]+)"')
        $rec | Add-Member NoteProperty displayFolder (if($folderMatches.Count){ $folderMatches[$folderMatches.Count-1].Groups[1].Value } else { '' })
        $rec | Add-Member NoteProperty description (([regex]::Match($chunk,'(?m)^\s*description\s*:\s*"(.*)"')).Groups[1].Value)
        $map[$id] = $rec
      }
    }
  }
  return $map
}

function Ensure-Dir {
  param([string]$Path)
  if(-not (Test-Path $Path)){
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Write-Utf8NoBom {
  param([string]$Path, [string]$Text)
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Build-MeasureBlock {
  param($rec, [string]$MeasuresTableName)
  if(-not $rec -or -not $rec.dax_name){ return "" }
  $name = $rec.dax_name
  $expr = if($rec.dax_expression){ $rec.dax_expression } else { "BLANK()" }
  $desc = $rec.description
  $lines = @()
  if($desc){ $lines += ("    /// " + $desc) }
  $lines += ("    measure '" + $name.Replace("'","''") + "'")
  $lines += "        expression:"
  $lines += "            '''"
  foreach($ln in ($expr -split "\r?\n")){
    $lines += ("            " + $ln)
  }
  $lines += "            '''"
  if($rec.formatString){ $lines += ("        formatString: \"" + $rec.formatString.Replace('"','\"') + "\"") }
  if($rec.displayFolder){ $lines += ("        displayFolder: \"" + $rec.displayFolder.Replace('"','\"') + "\"") }
  $lines += ""
  return ($lines -join [Environment]::NewLine)
}

function Ensure-Model-Ref {
  param([string]$ModelPath, [string]$TableName)
  if(-not (Test-Path $ModelPath)){ return }
  $raw = Get-Content -Raw -Path $ModelPath
  if($raw -match ('(?m)^ref\s+table\s+' + [regex]::Escape($TableName) + '\s*$')){ return }
  # append a new ref table line at the end
  $toWrite = if($raw.TrimEnd().EndsWith("`n")){ $raw + "ref table $TableName`n" } else { $raw + "`nref table $TableName`n" }
  Write-Utf8NoBom -Path $ModelPath -Text $toWrite
}

# Resolve target UseCase FactSheet and title
if(-not $UseCase){
  Write-Host "Please pass -UseCase (e.g., COM-001)" -ForegroundColor Yellow
  exit 1
}

$fs = Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'FactSheet.md' | Where-Object { $_.Directory.Name -like ($UseCase+'*') } | Select-Object -First 1
if(-not $fs){ Write-Host "Use Case not found: $UseCase" -ForegroundColor Red; exit 1 }
$fm = Get-FrontMatter -Path $fs.FullName
$targetIds = Parse-IdsFromFrontMatter -FrontMatter $fm -Field 'required_kpi_ids'
if($targetIds.Count -eq 0){ Write-Host "No required_kpi_ids in $($fs.FullName). Nothing to generate." -ForegroundColor Yellow; exit 0 }
$useCaseTitle = Get-UseCaseTitleFromFrontMatter -FrontMatter $fm

# Load KPI catalog
$catalog = Load-KpiCatalog -Root $KpiCatalogRoot

# Resolve dist paths
$caseRoot = Join-Path $DistRoot $UseCase
$semRoot = Join-Path $caseRoot ("$UseCase.SemanticModel")
$tmdlRoot = Join-Path $semRoot 'definition'
$tablesDir = Join-Path $tmdlRoot 'tables'
Ensure-Dir $tablesDir

$modelPath = Join-Path $tmdlRoot 'model.tmdl'
$measuresPath = Join-Path $tablesDir ("$MeasuresTableName.tmdl")

# Build TMDL content
$header = @()
if($useCaseTitle){ $header += ("/// $UseCase Measures ($useCaseTitle)") } else { $header += ("/// $UseCase Measures") }
$header += ("table $MeasuresTableName")
$header += ""

$blocks = @()
foreach($id in $targetIds){
  if($catalog.ContainsKey($id)){
    $blocks += (Build-MeasureBlock -rec $catalog[$id] -MeasuresTableName $MeasuresTableName)
  } else {
    $blocks += ("    /// MISSING in KPI catalog: $id")
    $blocks += ("    measure '" + $id.Replace("'","''") + "'")
    $blocks += "        expression:"
    $blocks += "            '''"
    $blocks += "            // TODO"
    $blocks += "            BLANK()"
    $blocks += "            '''"
    $blocks += ""
  }
}

$content = ($header + $blocks) -join [Environment]::NewLine
Write-Utf8NoBom -Path $measuresPath -Text $content

# Ensure model references the measures table
Ensure-Model-Ref -ModelPath $modelPath -TableName $MeasuresTableName

Write-Host ("Generated measures TMDL: " + $measuresPath) -ForegroundColor Green
Write-Host ("Updated model.tmdl ref (if needed): " + $modelPath) -ForegroundColor Green

