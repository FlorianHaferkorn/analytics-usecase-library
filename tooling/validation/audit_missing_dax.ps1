# NOTE: As of 2026-03-29, dax_expression has been removed from the KPI Catalog (core is tool-agnostic).
# DAX expressions now live exclusively in the Fabric overlay:
#   products/fabric/powerbi/specs/fabric_measure_overlay.yaml
# This script may need updating to scan the overlay instead of the KPI Catalog.

Param(
  [string]$UseCasesRoot,
  [string]$KpiCatalogRoot,
  [string]$OutputPath
)

$ErrorActionPreference = "Stop"

$ScriptToolsRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptToolsRoot

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $relativeCandidate = Join-Path -Path $RepoRoot -ChildPath $ProvidedPath
    if (Test-Path $relativeCandidate) { return (Resolve-Path -Path $relativeCandidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Get-FrontMatterBlock {
  param([string]$Path, [int]$Depth = 0)
  if (-not (Test-Path $Path)) { return $null }
  $lines = Get-Content -Path $Path
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne '---') { return $null }
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq '---') {
      if ($i -le 1) { return @{ Text = ""; Lines = @() } }
      $blockLines = @($lines[1..($i - 1)])
      $text = ($blockLines -join [Environment]::NewLine)
      return @{
        Text  = $text
        Lines = $blockLines
      }
    }
  }
  return $null
}

function Parse-IdsFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  $items = @()
  if ($inline.Success) {
    foreach ($match in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($match.Groups[1].Success) { $match.Groups[1].Value }
               elseif ($match.Groups[2].Success) { $match.Groups[2].Value }
               else { $match.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
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
      if ($value) { $items += $value }
    }
    return $items
  }
  return @()
}

function Get-LiteralBlockValue {
  param([string]$Chunk,[string]$Key)
  # Match YAML literal block: "key: |" followed by indented lines
  $keyPattern = "(?m)^(\s*)$Key\s*:\s*\|\s*\r?\n"
  $keyMatch = [regex]::Match($Chunk, $keyPattern)
  if (-not $keyMatch.Success) { return $null }
  
  $keyIndent = $keyMatch.Groups[1].Value.Length
  $startPos = $keyMatch.Index + $keyMatch.Length
  
  # Extract lines until we hit a line with same/less indentation
  $remaining = $Chunk.Substring($startPos)
  $lines = @()
  foreach ($line in $remaining -split "\r?\n") {
    # Stop if line has same or less indentation (and is not empty)
    if ($line -match '^\s*\S' -and $line -match "^(\s*)") {
      $lineIndent = $matches[1].Length
      if ($lineIndent -le $keyIndent) { break }
    }
    $lines += $line
  }
  
  if ($lines.Count -eq 0) { return $null }
  
  # Find minimum indentation of non-empty lines
  $nonEmptyLines = $lines | Where-Object { $_ -match '\S' }
  if ($nonEmptyLines.Count -eq 0) { return $null }
  
  $minIndent = ($nonEmptyLines | ForEach-Object { 
    if ($_ -match '^(\s*)') { $matches[1].Length } else { 0 }
  } | Measure-Object -Minimum).Minimum
  
  # Remove common indentation and join
  $result = ($lines | ForEach-Object {
    if ($_ -match "^\s{$minIndent}(.*)$") { $matches[1] }
    elseif ($_ -match '^\s*$') { "" }
    else { $_ }
  }) -join [Environment]::NewLine
  
  return $result.Trim()
}

function Split-KpiChunks {
  param([string]$Block)
  $listMatches = [regex]::Matches($Block, '(?m)^\s*-\s*kpi_id\s*:\s*"?([^"\r\n]+)"?')
  $chunks = @()
  if ($listMatches.Count -gt 0) {
    for ($i = 0; $i -lt $listMatches.Count; $i++) {
      $start = $listMatches[$i].Index
      $end = if ($i -lt $listMatches.Count - 1) { $listMatches[$i + 1].Index } else { $Block.Length }
      $length = $end - $start
      if ($length -gt 0) {
        $chunks += $Block.Substring($start, $length)
      }
    }
  }
  return $chunks
}

function Parse-KpiRecord {
  param([string]$Chunk)
  $idMatch = [regex]::Match($Chunk, '(?m)^\s*-?\s*kpi_id\s*:\s*"?([^"\r\n]+)"?')
  if (-not $idMatch.Success) { return $null }
  
  $kpiId = $idMatch.Groups[1].Value.Trim()
  
  # Check for dax_expression field
  $daxExpression = Get-LiteralBlockValue -Chunk $Chunk -Key "dax_expression"
  
  return @{
    kpi_id = $kpiId
    has_dax = ($null -ne $daxExpression -and $daxExpression.Trim().Length -gt 0)
    dax_expression = $daxExpression
  }
}

function Get-UseCaseKpis {
  param([string]$BracketPath)
  if (-not (Test-Path $BracketPath)) { return @() }
  
  # Read kpi_to_measure_mapping from UseCase_Bracket.yaml
  $content = Get-Content -Path $BracketPath -Raw
  $kpiIds = @()
  
  # Extract kpi_id values from kpi_to_measure_mapping in bracket YAML
  foreach ($match in [regex]::Matches($content, '(?m)^\s*-?\s*kpi_id\s*:\s*([^\s\r\n#]+)')) {
    $kpiId = $match.Groups[1].Value.Trim()
    if ($kpiId -and $kpiIds -notcontains $kpiId) {
      $kpiIds += $kpiId
    }
  }
  
  return $kpiIds
}

function Get-CoreUseCaseIds {
  param([string]$Root)
  $useCaseIds = @()
  $corePath = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $corePath)) { return $useCaseIds }
  
  Get-ChildItem -Path $corePath -Directory | ForEach-Object {
    $dirName = $_.Name
    if ($dirName -match '^([A-Z]+-\d+)') {
      $useCaseIds += $matches[1]
    }
  }
  
  return $useCaseIds | Sort-Object -Unique
}

# Resolve paths
$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder. Provide -UseCasesRoot or run inside repository." }

$resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog folder. Provide -KpiCatalogRoot or run inside repository." }

# Load KPI catalog
$kpiCatalogPath = Join-Path -Path $resolvedKpiRoot -ChildPath "KPI_Catalog.md"
if (-not (Test-Path $kpiCatalogPath)) { throw "KPI_Catalog.md not found at $kpiCatalogPath" }

$kpiCatalogContent = Get-Content -Path $kpiCatalogPath -Raw
$yamlBlocks = [regex]::Matches($kpiCatalogContent, '(?s)```yaml\r?\n(.*?)```')

$kpiData = @{}
foreach ($block in $yamlBlocks) {
  $yamlContent = $block.Groups[1].Value
  $chunks = Split-KpiChunks -Block $yamlContent
  foreach ($chunk in $chunks) {
    $record = Parse-KpiRecord -Chunk $chunk
    if ($record) {
      $kpiData[$record.kpi_id] = $record
    }
  }
}

# Get core use cases
$coreUseCaseIds = Get-CoreUseCaseIds -Root $resolvedUseCasesRoot

# Audit each use case
$results = @()
foreach ($useCaseId in $coreUseCaseIds) {
  $useCaseDir = Join-Path -Path $resolvedUseCasesRoot -ChildPath "core" | Get-ChildItem -Directory | Where-Object { $_.Name -like "$useCaseId*" } | Select-Object -First 1
  
  if (-not $useCaseDir) { continue }
  
  $bracketFile = Join-Path -Path $useCaseDir.FullName -ChildPath "UseCase_Bracket.yaml"
  if (-not (Test-Path $bracketFile)) { continue }
  
  $kpiIds = Get-UseCaseKpis -BracketPath $bracketFile
  
  foreach ($kpiId in $kpiIds) {
    if ($kpiData.ContainsKey($kpiId)) {
      $kpiRecord = $kpiData[$kpiId]
      $status = if ($kpiRecord.has_dax) { "has_dax" } else { "missing_dax" }
      
      $results += [PSCustomObject]@{
        UseCase = $useCaseId
        KpiId = $kpiId
        Status = $status
        HasDax = $kpiRecord.has_dax
      }
    } else {
      $results += [PSCustomObject]@{
        UseCase = $useCaseId
        KpiId = $kpiId
        Status = "not_in_catalog"
        HasDax = $false
      }
    }
  }
}

# Generate report
$dateStr = Get-Date -Format "yyyy-MM-dd"
$outputFile = if ($OutputPath) {
  Resolve-RepoPath -ProvidedPath $OutputPath -DefaultRelative "internal/reviews/missing_dax_audit_$dateStr.md"
} else {
  Join-Path -Path $RepoRoot -ChildPath "internal/reviews/missing_dax_audit_$dateStr.md"
}

# Ensure output directory exists
$outputDir = Split-Path -Parent $outputFile
if (-not (Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$report = @"
# Missing DAX Expression Audit

Generated: $dateStr

## Summary

- Total KPIs audited: $($results.Count)
- KPIs with DAX: $(($results | Where-Object { $_.HasDax }).Count)
- KPIs missing DAX: $(($results | Where-Object { -not $_.HasDax }).Count)
- KPIs not in catalog: $(($results | Where-Object { $_.Status -eq 'not_in_catalog' }).Count)

## By Use Case

"@

foreach ($useCaseId in ($results | Select-Object -ExpandProperty UseCase -Unique | Sort-Object)) {
  $useCaseResults = @($results | Where-Object { $_.UseCase -eq $useCaseId })
  $missing = @($useCaseResults | Where-Object { -not $_.HasDax })
  $hasDax = @($useCaseResults | Where-Object { $_.HasDax })
  
  $report += "`n### $useCaseId`n`n"
  $report += "- Total KPIs: $($useCaseResults.Count)`n"
  $report += "- With DAX: $($hasDax.Count)`n"
  $report += "- Missing DAX: $($missing.Count)`n`n"
  
  if ($missing.Count -gt 0) {
    $report += "**Missing DAX:**`n"
    foreach ($item in $missing) {
      $report += "- ``$($item.KpiId)`` ($($item.Status))`n"
    }
    $report += "`n"
  }
}

$report += @"

## Detailed Results

| Use Case | KPI ID | Status |
|----------|--------|--------|
"@

foreach ($result in ($results | Sort-Object UseCase, KpiId)) {
  $report += "| $($result.UseCase) | ``$($result.KpiId)`` | $($result.Status) |`n"
}

$report | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "Audit complete. Report written to: $outputFile" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total KPIs: $($results.Count)" -ForegroundColor White
Write-Host "  With DAX: $(($results | Where-Object { $_.HasDax }).Count)" -ForegroundColor Green
Write-Host "  Missing DAX: $(($results | Where-Object { -not $_.HasDax }).Count)" -ForegroundColor Yellow
Write-Host "  Not in catalog: $(($results | Where-Object { $_.Status -eq 'not_in_catalog' }).Count)" -ForegroundColor Red

if (($results | Where-Object { -not $_.HasDax }).Count -gt 0) {
  exit 1
}
