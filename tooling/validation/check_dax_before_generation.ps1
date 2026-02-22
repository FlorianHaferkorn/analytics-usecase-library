# Pre-Generation DAX Validation Check
# Purpose: Validate that all KPIs in UseCase_Bracket.yaml have DAX expressions before measure generation
# Usage: .\check_dax_before_generation.ps1 -UseCaseId "COM-001" -UseCasesRoot "core/usecases" -KpiCatalogRoot "core/kpi_catalog"

param(
    [Parameter(Mandatory = $true)]
    [string]$UseCaseId,
    [string]$UseCasesRoot,
    [string]$KpiCatalogRoot,
    [switch]$FailOnMissing
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($UseCaseId)) {
    Write-Error "UseCaseId must not be null or empty. Caller must pass a valid use case ID (e.g. COM-001)."
    exit 1
}

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

function Get-LiteralBlockValue {
    param([string]$Chunk, [string]$Key)
    $keyPattern = "(?m)^(\s*)$Key\s*:\s*\|\s*\r?\n"
    $keyMatch = [regex]::Match($Chunk, $keyPattern)
    if (-not $keyMatch.Success) { return $null }

    $keyIndent = $keyMatch.Groups[1].Value.Length
    $startPos = $keyMatch.Index + $keyMatch.Length

    $remaining = $Chunk.Substring($startPos)
    $lines = @()
    foreach ($line in $remaining -split "\r?\n") {
        if ($line -match '^\s*\S' -and $line -match "^(\s*)") {
            $lineIndent = $matches[1].Length
            if ($lineIndent -le $keyIndent) { break }
        }
        $lines += $line
    }

    if ($lines.Count -eq 0) { return $null }

    $nonEmptyLines = $lines | Where-Object { $_ -match '\S' }
    if ($nonEmptyLines.Count -eq 0) { return $null }

    $minIndent = ($nonEmptyLines | ForEach-Object {
        if ($_ -match '^(\s*)') { $matches[1].Length } else { 0 }
    } | Measure-Object -Minimum).Minimum

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

function Get-KpiRecordFromChunk {
    param([string]$Chunk)
    $idMatch = [regex]::Match($Chunk, '(?m)^\s*-?\s*kpi_id\s*:\s*"?([^"\r\n]+)"?')
    if (-not $idMatch.Success) { return $null }

    $kpiId = $idMatch.Groups[1].Value.Trim()
    $daxExpression = Get-LiteralBlockValue -Chunk $Chunk -Key "dax_expression"

    return @{
        kpi_id         = $kpiId
        has_dax        = ($null -ne $daxExpression -and $daxExpression.Trim().Length -gt 0)
        dax_expression = $daxExpression
    }
}

function Get-UseCaseKpis {
    param([string]$BracketPath)
    if (-not (Test-Path $BracketPath)) { return @() }

    # Read kpi_to_measure_mapping from UseCase_Bracket.yaml
    $content = Get-Content -Path $BracketPath -Raw
    $kpiIds = @()

    foreach ($match in [regex]::Matches($content, '(?m)^\s*-?\s*kpi_id\s*:\s*([^\s\r\n#]+)')) {
        $kpiId = $match.Groups[1].Value.Trim()
        if ($kpiId -and $kpiIds -notcontains $kpiId) {
            $kpiIds += $kpiId
        }
    }

    return $kpiIds
}

# Resolve paths
$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root folder. Provide -UseCasesRoot or run inside repository." }

$resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog folder. Provide -KpiCatalogRoot or run inside repository." }

# Find use case directory
$useCaseDir = Get-ChildItem -Path (Join-Path -Path $resolvedUseCasesRoot -ChildPath "core") -Directory | Where-Object { $_.Name -like "$UseCaseId*" } | Select-Object -First 1

if (-not $useCaseDir) {
    Write-Error "Use case $UseCaseId not found in $resolvedUseCasesRoot/core"
    exit 1
}

$bracketFile = Join-Path -Path $useCaseDir.FullName -ChildPath "UseCase_Bracket.yaml"
if (-not (Test-Path $bracketFile)) {
    Write-Error "UseCase_Bracket.yaml not found for use case $UseCaseId"
    exit 1
}

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
        $record = Get-KpiRecordFromChunk -Chunk $chunk
        if ($record) {
            $kpiData[$record.kpi_id] = $record
        }
    }
}

# Get KPIs from use case bracket
$kpiIds = Get-UseCaseKpis -BracketPath $bracketFile

if ($kpiIds.Count -eq 0) {
	Write-Warning "No KPIs found in UseCase_Bracket.yaml for $UseCaseId"
	exit 0
}

# Validate each KPI
$missingDax = @()
$notInCatalog = @()

foreach ($kpiId in $kpiIds) {
    if ($kpiData.ContainsKey($kpiId)) {
        $kpiRecord = $kpiData[$kpiId]
        if (-not $kpiRecord.has_dax) {
            $missingDax += $kpiId
        }
    } else {
        $notInCatalog += $kpiId
    }
}

# Report results
Write-Host "Pre-Generation DAX Check for $UseCaseId" -ForegroundColor Cyan
Write-Host "  Total KPIs: $($kpiIds.Count)" -ForegroundColor White
Write-Host "  With DAX: $(($kpiIds.Count - $missingDax.Count - $notInCatalog.Count))" -ForegroundColor Green

if ($notInCatalog.Count -gt 0) {
    Write-Host "  Not in catalog: $($notInCatalog.Count)" -ForegroundColor Red
    foreach ($kpiId in $notInCatalog) {
        Write-Host "    - $kpiId" -ForegroundColor Red
    }
}

if ($missingDax.Count -gt 0) {
    Write-Host "  Missing DAX: $($missingDax.Count)" -ForegroundColor $(if ($FailOnMissing) { "Red" } else { "Yellow" })
    foreach ($kpiId in $missingDax) {
        Write-Host "    - $kpiId" -ForegroundColor $(if ($FailOnMissing) { "Red" } else { "Yellow" })
    }
}

# Exit code
if ($notInCatalog.Count -gt 0 -or ($FailOnMissing -and $missingDax.Count -gt 0)) {
    if ($missingDax.Count -gt 0) {
        Write-Host "`nERROR: Cannot generate measures - missing DAX expressions. Add DAX to KPI Catalog before generation." -ForegroundColor Red
    }
    exit 1
}

Write-Host "`nOK All KPIs have DAX expressions. Ready for generation." -ForegroundColor Green
exit 0
