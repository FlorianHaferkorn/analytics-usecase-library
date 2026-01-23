<#
.SYNOPSIS
  Normalizes all KPI catalog markdown files so their YAML blocks follow the schema order.

.DESCRIPTION
  Parses every ```yaml``` block inside `_includes/kpi_catalog/*.md`, loads the content via YamlDotNet,
  and writes the KPIs back with a canonical field order (kpi metadata + business/technical/governance sections).
  This keeps catalogs consistent with `/_includes/kpi_catalog/SCHEMA.md`.
#>

[CmdletBinding()]
param(
  [string]$CatalogRoot = "_includes/kpi_catalog",
  [string]$YamlVersion = "13.4.0"
)

$script:RepoRoot = Split-Path -Parent $PSScriptRoot

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    if ($script:RepoRoot) {
      $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
      if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    }
  }
  if ($DefaultRelative -and $script:RepoRoot) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  throw "Unable to resolve path for '$ProvidedPath'."
}

function Get-YamlDotNetAssembly {
  param([string]$Version = "13.4.0")
  $tempRoot = Split-Path -Parent ([IO.Path]::GetTempFileName())
  $targetDir = Join-Path $tempRoot "YamlDotNet.$Version"
  $dllPath = Join-Path $targetDir "YamlDotNet.dll"
  if (Test-Path $dllPath) { return $dllPath }

  if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }
  $zipPath = Join-Path $targetDir "YamlDotNet.zip"
  $uri = "https://www.nuget.org/api/v2/package/YamlDotNet/$Version"
  Write-Verbose "Downloading YamlDotNet $Version from $uri"
  Invoke-WebRequest -Uri $uri -OutFile $zipPath -UseBasicParsing
  Expand-Archive -Path $zipPath -DestinationPath $targetDir -Force
  Remove-Item $zipPath
  $dllCandidate = Join-Path $targetDir "lib/netstandard2.0/YamlDotNet.dll"
  if (-not (Test-Path $dllCandidate)) { throw "Unable to locate YamlDotNet.dll inside package." }
  return $dllCandidate
}

$yamlDll = Get-YamlDotNetAssembly -Version $YamlVersion
Add-Type -Path $yamlDll

$Deserializer = [YamlDotNet.Serialization.DeserializerBuilder]::new().IgnoreUnmatchedProperties().Build()

function Convert-ToPsValue {
  param($Value)
  if ($Value -is [System.Collections.IDictionary]) {
    $ordered = [ordered]@{}
    foreach ($key in $Value.Keys) { $ordered[$key] = Convert-ToPsValue $Value[$key] }
    return $ordered
  }
  elseif (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
    $list = @()
    foreach ($item in $Value) { $list += ,(Convert-ToPsValue $item) }
    return $list
  }
  return $Value
}

function Format-Scalar {
  param($Value)
  if ($null -eq $Value) { return "null" }
  if ($Value -is [bool]) { return $Value.ToString().ToLower() }
  elseif ((-not ($Value -is [string])) -and $Value -is [System.IFormattable]) {
    return ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0}", $Value))
  }
  $escaped = $Value.ToString().Replace('"','\"')
  return '"' + $escaped + '"'
}

function Write-YamlValue {
  param(
    [System.Text.StringBuilder]$Builder,
    [int]$Indent,
    $Value,
    [string[]]$PreferredOrder = @()
  )
  $indentStr = '  ' * $Indent
  if (($Value -is [System.Collections.IDictionary]) -and $Value.Keys.Count -gt 0) {
    $keys = @()
    foreach ($key in $PreferredOrder) { if ($Value.Contains($key)) { $keys += $key } }
    foreach ($key in $Value.Keys) { if ($keys -notcontains $key) { $keys += $key } }
    foreach ($key in $keys) {
      $Builder.AppendLine("$indentStr${key}:") | Out-Null
      Write-YamlValue -Builder $Builder -Indent ($Indent + 1) -Value $Value[$key]
    }
    return
  }

  if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
    foreach ($item in $Value) {
      if ($item -is [System.Collections.IDictionary]) {
        $Builder.AppendLine("$indentStr-") | Out-Null
        Write-YamlValue -Builder $Builder -Indent ($Indent + 1) -Value $item
      }
      elseif (($item -is [System.Collections.IEnumerable]) -and -not ($item -is [string])) {
        $Builder.AppendLine("$indentStr-") | Out-Null
        Write-YamlValue -Builder $Builder -Indent ($Indent + 1) -Value $item
      }
      else {
        $Builder.AppendLine("$indentStr- $(Format-Scalar $item)") | Out-Null
      }
    }
    return
  }

  $Builder.AppendLine("$indentStr$(Format-Scalar $Value)") | Out-Null
}

function Write-KeyValue {
  param(
    [System.Text.StringBuilder]$Builder,
    [int]$Indent,
    [string]$Key,
    $Value,
    [string[]]$PreferredOrder = @()
  )
  if ($null -eq $Value) { return }
  if ($Value -is [string] -and $Value.Trim().Length -eq 0) { return }
  $indentStr = '  ' * $Indent
  if (($Value -is [System.Collections.IDictionary]) -and $Value.Keys.Count -gt 0) {
    $Builder.AppendLine("$indentStr${Key}:") | Out-Null
    Write-YamlValue -Builder $Builder -Indent ($Indent + 1) -Value $Value -PreferredOrder $PreferredOrder
    return
  }
  if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
    $array = @($Value)
    if ($array.Count -eq 0) { return }
    $Builder.AppendLine("$indentStr${Key}:") | Out-Null
    foreach ($item in $array) {
      if ($item -is [System.Collections.IDictionary]) {
        $Builder.AppendLine("$indentStr  -") | Out-Null
        Write-YamlValue -Builder $Builder -Indent ($Indent + 2) -Value $item
      }
      elseif (($item -is [System.Collections.IEnumerable]) -and -not ($item -is [string])) {
        $Builder.AppendLine("$indentStr  -") | Out-Null
        Write-YamlValue -Builder $Builder -Indent ($Indent + 2) -Value $item
      }
      else {
        $Builder.AppendLine("$indentStr  - $(Format-Scalar $item)") | Out-Null
      }
    }
    return
  }
  $Builder.AppendLine("$indentStr${Key}: $(Format-Scalar $Value)") | Out-Null
}

$kpiOrder = @('kpi_id','kpi_key','kpi_type','kpi_role','strategic_ref','impact_dimension','domain_tag','use_case_ref','depends_on','depends_on_ids','calc_type','refresh','status','business','technical','governance','metadata_quality','aliases')
$businessOrder = @('purpose','definition','grain_scope','unit_format','interpretation')
$technicalOrder = @('dax_name','dax_expression','displayFolder','formatString','description','lineage','source_grain','source_column_ref','source_system','verified')
$governanceOrder = @('business_owner','data_owner','steward','review_cycle','validation_process','qa_rules','version','last_review')
$metadataOrder = @('completeness_score','lineage_verified','copilot_ready')

function Format-KpiEntry {
  param($Entry)
  $listKeys = @('domain_tag','use_case_ref','depends_on','depends_on_ids','lineage','source_column_ref','qa_rules','aliases')
  foreach ($listKey in $listKeys) {
    if ($Entry.Contains($listKey) -and $null -ne $Entry[$listKey]) {
      $value = $Entry[$listKey]
      if (($value -is [System.Collections.IEnumerable]) -and -not ($value -is [string])) {
        $Entry[$listKey] = @($value)
      }
      else {
        $Entry[$listKey] = @($value)
      }
    }
  }
  $sb = New-Object System.Text.StringBuilder
  $written = New-Object System.Collections.Generic.HashSet[string]
  Write-KeyValue -Builder $sb -Indent 0 -Key "- kpi_id" -Value $Entry['kpi_id']
  $written.Add('kpi_id') | Out-Null
  foreach ($key in $kpiOrder) {
    if ($key -eq 'kpi_id') { continue }
    if ($Entry.Contains($key)) {
      $value = $Entry[$key]
      switch ($key) {
        'business' { Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $value -PreferredOrder $businessOrder }
        'technical' { Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $value -PreferredOrder $technicalOrder }
        'governance' { Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $value -PreferredOrder $governanceOrder }
        'metadata_quality' { Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $value -PreferredOrder $metadataOrder }
        Default { Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $value }
      }
      $written.Add($key) | Out-Null
    }
  }
  foreach ($key in $Entry.Keys) {
    if (-not $written.Contains($key)) {
      Write-KeyValue -Builder $sb -Indent 1 -Key $key -Value $Entry[$key]
    }
  }
  return $sb.ToString().TrimEnd()
}

function Convert-YamlBlock {
  param([string]$BlockText)
  $trimmed = $BlockText.Trim()
  if (-not $trimmed) { return "" }
  $parsed = $Deserializer.Deserialize([string]$trimmed)
  if (-not ($parsed -is [System.Collections.IEnumerable])) { return $trimmed }
  $entries = @()
  foreach ($item in $parsed) { $entries += ,(Convert-ToPsValue $item) }
  $sb = New-Object System.Text.StringBuilder
  for ($i = 0; $i -lt $entries.Count; $i++) {
    $sb.AppendLine((Format-KpiEntry $entries[$i])) | Out-Null
    if ($i -lt $entries.Count - 1) { $sb.AppendLine() | Out-Null }
  }
  return $sb.ToString().TrimEnd()
}

$resolvedCatalogRoot = Resolve-RepoPath -ProvidedPath $CatalogRoot -DefaultRelative '_includes/kpi_catalog'
$fenceOpen = (New-Object string([char]0x60,3)) + "yaml"
$fenceClose = New-Object string([char]0x60,3)
$catalogFiles = Get-ChildItem -Path $resolvedCatalogRoot -Filter 'KPI_Catalog.md'
if ($catalogFiles.Count -eq 0) { Write-Warning "No catalog files found."; return }

foreach ($file in $catalogFiles) {
  $content = Get-Content -Raw -Path $file.FullName
  $regex = [regex]::new('```yaml(?<content>.*?)```', [System.Text.RegularExpressions.RegexOptions]::Singleline)
  $sb = New-Object System.Text.StringBuilder
  $lastIndex = 0
  foreach ($match in $regex.Matches($content)) {
    $sb.Append($content.Substring($lastIndex, $match.Index - $lastIndex)) | Out-Null
    $converted = Convert-YamlBlock $match.Groups['content'].Value
    $sb.AppendLine($fenceOpen) | Out-Null
    if ($converted) { $sb.AppendLine($converted.TrimEnd()) | Out-Null }
    $sb.AppendLine($fenceClose) | Out-Null
    $lastIndex = $match.Index + $match.Length
  }
  $sb.Append($content.Substring($lastIndex)) | Out-Null
  $resultText = $sb.ToString()
  $tickPattern = [regex]::Escape([string][char]0x60)
  $resultText = $resultText -replace "(?m)^${tickPattern}yaml$", '```yaml'
  $resultText = $resultText -replace "(?m)^${tickPattern}$", '```'
  Set-Content -Path $file.FullName -Value $resultText -Encoding UTF8
  $message = 'Normalized {0}' -f $file.Name
  Write-Host $message
}

