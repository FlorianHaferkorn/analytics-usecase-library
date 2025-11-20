Param(
  [string[]]$UseCase,
  [string]$UseCasesRoot = "analytics-usecase-library/usecases",
  [string]$KpiCatalogRoot = "analytics-usecase-library/_includes/kpi_catalog",
  [string]$DistRoot = "analytics-usecase-library/dist",
  [string]$MeasuresTableName = "_Measures",
  [switch]$SkipManifest,
  # When set, do not overwrite existing _Measures.tmdl files.
  # Instead, generate a sidecar file named "<table>._generated.tmdl" next to them.
  [switch]$StubOnly,
  # When set, overwrite existing _Measures.tmdl files even if they already exist.
  # Default behaviour without this switch is to skip use cases where a measures file exists.
  [switch]$OverwriteExisting
)

$script:ToolRoot = Split-Path -Parent $PSScriptRoot
$script:RepoRoot = Split-Path -Parent $script:ToolRoot

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    if ($script:RepoRoot) {
      $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
      if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    }
  }
  if ($DefaultRelative) {
    if ($script:RepoRoot) {
      $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
      if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
    }
  }
  return $null
}

function Get-FrontMatterBlock {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne '---') { return $null }
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq '---') {
      if ($i -le 1) { return @{ Text = ""; Lines = @() } }
      $blockLines = $lines[1..($i - 1)]
      return @{
        Text  = ($blockLines -join [Environment]::NewLine)
        Lines = $blockLines
      }
    }
  }
  return $null
}

function Parse-IdsFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $regex = [regex]::Match($FrontMatter, ($Field + '\s*:\s*\[(.*?)\]'), 'Singleline')
  if (-not $regex.Success) { return @() }
  $items = @()
  foreach ($match in [regex]::Matches($regex.Groups[1].Value, '"([^"]+)"')) {
    $items += $match.Groups[1].Value
  }
  return $items
}

function Get-ScalarValue {
  param([string[]]$Lines,[string]$Key)
  $pattern = "^\s*$Key\s*:\s*""?(.*?)""?\s*$"
  foreach ($line in $Lines) {
    $m = [regex]::Match($line, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
  }
  return $null
}

function Parse-StringMap {
  param([string[]]$Lines,[string]$Field)
  $map = [ordered]@{}
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match "^\s*$Field\s*:") {
      for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
        $line = $Lines[$j]
        if ($line.Trim().Length -eq 0) { continue }
        if ($line -notmatch "^\s{2,}") { break }
        $kv = [regex]::Match($line, '^\s+([^:\s]+)\s*:\s*"(.*)"\s*$')
        if ($kv.Success) { $map[$kv.Groups[1].Value] = $kv.Groups[2].Value }
        else { break }
      }
      break
    }
  }
  return $map
}

function Get-ChunkValue {
  param([string]$Chunk,[string]$Key)
  $m = [regex]::Match($Chunk, "(?m)^\s*$Key\s*:\s*""([^""]*)""")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Get-ListValue {
  param([string]$Chunk,[string]$Key)
  $m = [regex]::Match($Chunk, "(?m)^\s*$Key\s*:\s*\[(.*?)\]", 'Singleline')
  if (-not $m.Success) { return @() }
  $list = @()
  foreach ($match in [regex]::Matches($m.Groups[1].Value, '"([^"]+)"')) {
    $list += $match.Groups[1].Value
  }
  return $list
}

function Get-QARules {
  param([string]$Chunk)
  $m = [regex]::Match($Chunk, "(?ms)qa_rules\s*:\s*(?:\r?\n\s*-\s*""[^""]*""\s*)+")
  if (-not $m.Success) { return @() }
  $rules = @()
  foreach ($match in [regex]::Matches($m.Value, '\s*-\s*"(.*?)"', 'Singleline')) {
    $rules += $match.Groups[1].Value
  }
  return $rules
}

function Split-KpiChunks {
  param([string]$Block)
  $listMatches = [regex]::Matches($Block, '(?m)^\s*-\s*kpi_id\s*:\s*"([^"]+)"')
  $chunks = @()
  if ($listMatches.Count -gt 0) {
    for ($i = 0; $i -lt $listMatches.Count; $i++) {
      $start = $listMatches[$i].Index
      $end = if ($i -lt $listMatches.Count - 1) { $listMatches[$i + 1].Index } else { $Block.Length }
      $chunks += $Block.Substring($start, $end - $start)
    }
  } elseif ([regex]::IsMatch($Block, '(?m)^\s*kpi_id\s*:\s*"([^"]+)"')) {
    $chunks += $Block
  }
  return $chunks
}

function Parse-KpiRecord {
  param([string]$Chunk,[string]$SourcePath)
  $idMatch = [regex]::Match($Chunk, '(?m)^\s*-?\s*kpi_id\s*:\s*"([^"]+)"')
  if (-not $idMatch.Success) { return $null }
  $rec = [ordered]@{}
  $rec.id = $idMatch.Groups[1].Value
  $rec.kpi_key = Get-ChunkValue -Chunk $Chunk -Key 'kpi_key'
  $rec.dax_name = Get-ChunkValue -Chunk $Chunk -Key 'dax_name'
  $rec.dax_expression = Get-ChunkValue -Chunk $Chunk -Key 'dax_expression'
  $fmtMatches = [regex]::Matches($Chunk, '(?m)^\s*formatString\s*:\s*"([^"]*)"')
  $rec.formatString = if ($fmtMatches.Count) { $fmtMatches[$fmtMatches.Count - 1].Groups[1].Value } else { "" }
  $folderMatches = [regex]::Matches($Chunk, '(?m)^\s*displayFolder\s*:\s*"([^"]*)"')
  $rec.displayFolder = if ($folderMatches.Count) { $folderMatches[$folderMatches.Count - 1].Groups[1].Value } else { "" }
  $rec.description = Get-ChunkValue -Chunk $Chunk -Key 'description'
  $rec.kpi_type = Get-ChunkValue -Chunk $Chunk -Key 'kpi_type'
  $rec.impact_dimension = Get-ChunkValue -Chunk $Chunk -Key 'impact_dimension'
  $rec.calc_type = Get-ChunkValue -Chunk $Chunk -Key 'calc_type'
  $rec.refresh = Get-ChunkValue -Chunk $Chunk -Key 'refresh'
  $rec.status = Get-ChunkValue -Chunk $Chunk -Key 'status'
  $purposeMatch = [regex]::Match($Chunk, '(?m)^\s+purpose\s*:\s*"([^"]*)"')
  $rec.purpose = if ($purposeMatch.Success) { $purposeMatch.Groups[1].Value } else { "" }
  $rec.domain_tags = Get-ListValue -Chunk $Chunk -Key 'domain_tag'
  $rec.depends_on = Get-ListValue -Chunk $Chunk -Key 'depends_on'
  $rec.depends_on_ids = Get-ListValue -Chunk $Chunk -Key 'depends_on_ids'
  $rec.business_owner = Get-ChunkValue -Chunk $Chunk -Key 'business_owner'
  $rec.data_owner = Get-ChunkValue -Chunk $Chunk -Key 'data_owner'
  $rec.steward = Get-ChunkValue -Chunk $Chunk -Key 'steward'
  $rec.qa_rules = Get-QARules -Chunk $Chunk
  $rec.source = $SourcePath
  return $rec
}

function Load-KpiCatalog {
  param([string]$Root)
  $map = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    foreach ($match in [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')) {
      foreach ($chunk in (Split-KpiChunks -Block $match.Groups[1].Value)) {
        $rec = Parse-KpiRecord -Chunk $chunk -SourcePath $_.FullName
        if ($rec) { $map[$rec.id] = $rec }
      }
    }
  }
  return $map
}

function Ensure-Dir {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Write-Utf8NoBom {
  param([string]$Path,[string]$Text)
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8)
}

function Get-SafeName {
  param([string]$Name)
  $safe = $Name
  foreach ($ch in [System.IO.Path]::GetInvalidFileNameChars()) {
    $safe = $safe.Replace($ch, '_')
  }
  return $safe
}

function Resolve-SemanticModelPath {
  param(
    [string]$CaseRoot,
    [string]$DatasetModel,
    [string]$UseCaseId
  )
  $candidates = New-Object System.Collections.Generic.List[string]
  if ($DatasetModel) {
    $candidates.Add((Join-Path $CaseRoot $DatasetModel))
    $safeName = Get-SafeName -Name $DatasetModel
    if ($safeName -ne $DatasetModel) {
      $candidates.Add((Join-Path $CaseRoot $safeName))
    }
  }
  $candidates.Add((Join-Path $CaseRoot ("$UseCaseId.SemanticModel")))
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  $target = $candidates[0]
  Ensure-Dir $CaseRoot
  Ensure-Dir $target
  return (Resolve-Path -Path $target).Path
}

function Build-MeasureObject {
  param(
    [string]$KpiId,
    $CatalogRecord,
    [System.Collections.Specialized.OrderedDictionary]$LabelMap
  )
  $label = if ($LabelMap -and $LabelMap.Contains($KpiId)) { $LabelMap[$KpiId] }
  elseif ($CatalogRecord -and $CatalogRecord.kpi_key) { $CatalogRecord.kpi_key }
  elseif ($CatalogRecord -and $CatalogRecord.dax_name) { $CatalogRecord.dax_name }
  else { $KpiId }

  if (-not $CatalogRecord) {
    return [ordered]@{
      kpi_id       = $KpiId
      name         = $label
      missing      = $true
      purpose      = $null
      description  = $null
      dax_expression = $null
    }
  }

  $domainTags = @()
  if ($CatalogRecord.domain_tags) { $domainTags = @($CatalogRecord.domain_tags) }
  $dependsOn = @()
  if ($CatalogRecord.depends_on) { $dependsOn = @($CatalogRecord.depends_on) }
  $dependsOnIds = @()
  if ($CatalogRecord.depends_on_ids) { $dependsOnIds = @($CatalogRecord.depends_on_ids) }
  $qaRules = @()
  if ($CatalogRecord.qa_rules) { $qaRules = @($CatalogRecord.qa_rules) }
  $purpose = $CatalogRecord.purpose

  return [ordered]@{
    kpi_id          = $KpiId
    name            = $label
    kpi_key         = $CatalogRecord.kpi_key
    kpi_type        = $CatalogRecord.kpi_type
    impact_dimension= $CatalogRecord.impact_dimension
    domain_tags     = $domainTags
    calc_type       = $CatalogRecord.calc_type
    refresh         = $CatalogRecord.refresh
    status          = $CatalogRecord.status
    format_string   = $CatalogRecord.formatString
    display_folder  = $CatalogRecord.displayFolder
    purpose         = $purpose
    description     = if ($purpose) { $purpose } else { $CatalogRecord.description }
    technical_description = $CatalogRecord.description
    dax_expression  = $CatalogRecord.dax_expression
    depends_on      = $dependsOn
    depends_on_ids  = $dependsOnIds
    business_owner  = $CatalogRecord.business_owner
    data_owner      = $CatalogRecord.data_owner
    steward         = $CatalogRecord.steward
    qa_rules        = $qaRules
    catalog_source  = $CatalogRecord.source
  }
}

function Build-MeasureBlock {
  param($Measure)
  $lines = @()
  if ($Measure.kpi_id -or $Measure.kpi_key) {
    $label = $Measure.kpi_key
    if (-not $label) { $label = $Measure.name }
    $lines += ("    /// " + $Measure.kpi_id + " - " + $label)
  }
  if ($Measure.purpose) { $lines += ("    /// " + $Measure.purpose) }
  elseif ($Measure.description) { $lines += ("    /// " + $Measure.description) }
  $name = $Measure.name.Replace("'", "''")
  $expressionLines = @()
  if ($Measure.missing) {
    $lines += ("    /// MISSING in KPI catalog: " + $Measure.kpi_id)
    $expressionLines = @("// TODO", "BLANK()")
  } else {
    $expr = if ($Measure.dax_expression) { $Measure.dax_expression } else { "BLANK()" }
    $expressionLines = $expr -split "\r?\n"
  }
  $lines += ("    measure '$name' =")
  foreach ($ln in $expressionLines) {
    $lines += ("            " + $ln)
  }
  if ($Measure.format_string) { $lines += ("        formatString: """ + $Measure.format_string.Replace('"', '\"') + """") }
  if ($Measure.display_folder) { $lines += ("        displayFolder: """ + $Measure.display_folder.Replace('"', '\"') + """") }
  $lines += ""
  return $lines
}

function Write-Manifest {
  param([string]$Path,$Manifest)
  $json = $Manifest | ConvertTo-Json -Depth 10
  Write-Utf8NoBom -Path $Path -Text $json
}

$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder. Provide -UseCasesRoot or run inside repository." }
$resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative '_includes/kpi_catalog'
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog root. Provide -KpiCatalogRoot or run inside repository." }
$resolvedDistRoot = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'dist'
if (-not $resolvedDistRoot) { throw "Unable to resolve dist root. Provide -DistRoot or run inside repository." }

$factSheets = Get-ChildItem -Path $resolvedUseCasesRoot -Recurse -Filter 'FactSheet.md'
if ($UseCase -and $UseCase.Count -gt 0) {
  $filters = $UseCase | Where-Object { $_ -and $_.Trim().Length -gt 0 }
  if ($filters.Count -gt 0) {
    $factSheets = foreach ($fs in $factSheets) {
      $frontMatter = Get-FrontMatterBlock -Path $fs.FullName
      if (-not $frontMatter) { continue }
      $lines = $frontMatter.Lines
      $useCaseId = Get-ScalarValue -Lines $lines -Key 'id'
      if (-not $useCaseId) { $useCaseId = $fs.Directory.Name.Split('_')[0] }
      if ($filters | Where-Object { $useCaseId -like ($_ + '*') }) { $fs }
    }
  }
}

if ($factSheets.Count -eq 0) {
  Write-Host "No FactSheets matched the provided filters." -ForegroundColor Yellow
  exit 0
}

$catalog = Load-KpiCatalog -Root $resolvedKpiRoot
$generated = 0

foreach ($fs in $factSheets) {
  $frontMatter = Get-FrontMatterBlock -Path $fs.FullName
  if (-not $frontMatter) { continue }
  $lines = $frontMatter.Lines
  $text = $frontMatter.Text

  $useCaseId = Get-ScalarValue -Lines $lines -Key 'id'
  if (-not $useCaseId) { $useCaseId = $fs.Directory.Name.Split('_')[0] }
  if ($UseCase -and $UseCase.Count -gt 0) {
    $matchesFilter = $false
    foreach ($filter in $UseCase) {
      if ($useCaseId -like ($filter + '*')) { $matchesFilter = $true; break }
    }
    if (-not $matchesFilter) { continue }
  }

  $title = Get-ScalarValue -Lines $lines -Key 'title'
  $datasetModel = Get-ScalarValue -Lines $lines -Key 'dataset_model'
  if (-not $datasetModel) { $datasetModel = "$useCaseId.SemanticModel" }

  $targetIds = Parse-IdsFromFrontMatter -FrontMatter $text -Field 'required_kpi_ids'
  if ($targetIds.Count -eq 0) {
    Write-Host "Skipping $useCaseId - no required_kpi_ids defined." -ForegroundColor Yellow
    continue
  }
  $labelMap = Parse-StringMap -Lines $lines -Field 'required_kpis'
  if (-not $labelMap) { $labelMap = [ordered]@{} }

  $manifest = [ordered]@{
    usecase_id    = $useCaseId
    title         = $title
    dataset_model = $datasetModel
    table_name    = $MeasuresTableName
    fact_sheet    = (Resolve-Path -Path $fs.FullName).Path
    measures      = @()
  }

  foreach ($id in $targetIds) {
    $record = if ($catalog.ContainsKey($id)) { $catalog[$id] } else { $null }
    $measure = Build-MeasureObject -KpiId $id -CatalogRecord $record -LabelMap $labelMap
    $manifest.measures += $measure
    if (-not $record) {
      Write-Host "Warning: KPI '$id' missing in catalog for $useCaseId" -ForegroundColor Yellow
    }
  }

  $caseRoot = Join-Path $resolvedDistRoot $useCaseId
  $semRoot = Resolve-SemanticModelPath -CaseRoot $caseRoot -DatasetModel $datasetModel -UseCaseId $useCaseId
  $definitionRoot = Join-Path $semRoot 'definition'
  $tablesDir = Join-Path $definitionRoot 'tables'
  Ensure-Dir $tablesDir

  $measuresPath = Join-Path $tablesDir ("$MeasuresTableName.tmdl")
  $generatedPath = Join-Path $tablesDir ("$MeasuresTableName.generated.tmdl")
  $modelPath = Join-Path $definitionRoot 'model.tmdl'

  if (-not $StubOnly -and -not $OverwriteExisting -and (Test-Path $measuresPath)) {
    Write-Host "Skipping $useCaseId - measures file already exists (use -OverwriteExisting or -StubOnly)." -ForegroundColor Yellow
    continue
  }

  $header = @()
  if ($title) { $header += ("/// $useCaseId Measures ($title)") } else { $header += ("/// $useCaseId Measures") }
  $header += ("table $MeasuresTableName")
  $header += ""

  $blocks = @()
  foreach ($measure in $manifest.measures) {
    $blocks += (Build-MeasureBlock -Measure $measure)
  }

  $content = ($header + $blocks) -join [Environment]::NewLine

  if ($StubOnly) {
    Write-Utf8NoBom -Path $generatedPath -Text $content
  } else {
    Write-Utf8NoBom -Path $measuresPath -Text $content
  }

  if (-not $StubOnly -and (Test-Path $modelPath)) {
    $modelRaw = Get-Content -Raw -Path $modelPath
    if ($modelRaw -notmatch ("(?m)^ref\s+table\s+" + [regex]::Escape($MeasuresTableName) + '\s*$')) {
      $append = "ref table $MeasuresTableName"
      if ($modelRaw.TrimEnd().Length -gt 0) {
        Write-Utf8NoBom -Path $modelPath -Text ($modelRaw.TrimEnd() + [Environment]::NewLine + $append + [Environment]::NewLine)
      } else {
        Write-Utf8NoBom -Path $modelPath -Text ($append + [Environment]::NewLine)
      }
    }
  }

  if (-not $SkipManifest) {
    $manifestPath = Join-Path $semRoot 'measures_manifest.json'
    Write-Manifest -Path $manifestPath -Manifest $manifest
  }

  if ($StubOnly) {
    Write-Host ("Generated stub measures for $useCaseId -> " + $generatedPath) -ForegroundColor Green
  } else {
    Write-Host ("Generated measures for $useCaseId -> " + $measuresPath) -ForegroundColor Green
  }
  $generated++
}

if ($generated -eq 0) {
  Write-Host "No measures were generated. Ensure the requested UseCase IDs exist." -ForegroundColor Yellow
} else {
  Write-Host ("Completed measure generation for $generated use case(s).") -ForegroundColor Cyan
}
