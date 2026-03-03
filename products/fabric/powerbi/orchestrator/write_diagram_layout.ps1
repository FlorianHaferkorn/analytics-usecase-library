# products/fabric/powerbi/orchestrator/write_diagram_layout.ps1
# Generates diagramLayout.json (Model View) per spaghetti principle: _Measures (0,0), facts horizontal, dims vertical.
# Full Desktop schema: version, selectedDiagram, defaultDiagram, nodeLineageTag, size, zIndex, expandedHeight.
# Run from repo root or pass -DefinitionPath to the domain definition folder.

Param(
    [string]$DefinitionPath,
    [string]$SemanticModelRoot
)

$ErrorActionPreference = "Stop"

$defPath = $DefinitionPath
if (-not $defPath -and $SemanticModelRoot) {
    $defPath = Join-Path $SemanticModelRoot "definition"
}
if (-not $defPath -or -not (Test-Path $defPath)) {
    Write-Host "DefinitionPath or SemanticModelRoot required and must exist." -ForegroundColor Red
    exit 1
}

$smRoot = if ($SemanticModelRoot) { $SemanticModelRoot } else { (Split-Path $defPath -Parent) }
$tablesDir = Join-Path $defPath "tables"
if (-not (Test-Path $tablesDir)) {
    Write-Host "Tables directory not found: $tablesDir" -ForegroundColor Yellow
    exit 0
}

function Get-LineageTagFromTmdl {
    param([string]$TmdlPath)
    if (-not (Test-Path $TmdlPath)) { return $null }
    $content = Get-Content -Path $TmdlPath -Raw -Encoding utf8 -ErrorAction SilentlyContinue
    if (-not $content) { return $null }
    if ($content -match 'lineageTag:\s*([^\s\r\n]+)') {
        return $matches[1].Trim()
    }
    return $null
}

$tableNames = @(Get-ChildItem $tablesDir -Filter "*.tmdl" -File -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName } | Sort-Object -Unique)
$measures = @($tableNames | Where-Object { $_ -eq "_Measures" })
$facts = @($tableNames | Where-Object { $_ -like "fact_*" } | Sort-Object)
$dimsAndSecurity = @($tableNames | Where-Object { ($_ -like "dim_*") -or ($_ -like "security_*") } | Sort-Object)
$other = @($tableNames | Where-Object { $_ -notin @("_Measures") -and $_ -notlike "fact_*" -and $_ -notlike "dim_*" -and $_ -notlike "security_*" } | Sort-Object)

$defaultLineageMeasures = "a3000000-2000-4000-8000-000000000000"
$diagramName = "Alle Tabellen"
$nodes = [System.Collections.ArrayList]::new()

# _Measures at (0, 0), zIndex 0
foreach ($t in $measures) {
    $tmdlPath = Join-Path $tablesDir "$t.tmdl"
    $tag = Get-LineageTagFromTmdl -TmdlPath $tmdlPath
    if (-not $tag) { $tag = $defaultLineageMeasures }
    [void]$nodes.Add(@{
        location       = @{ x = 0; y = 0 }
        nodeIndex      = $t
        nodeLineageTag = $tag
        size           = @{ height = 72; width = 234 }
        zIndex         = 0
        expandedHeight = 104
    })
}

# Facts horizontal at y=0, zIndex 5
$xFact = 280
foreach ($t in $facts) {
    $tmdlPath = Join-Path $tablesDir "$t.tmdl"
    $tag = Get-LineageTagFromTmdl -TmdlPath $tmdlPath
    if (-not $tag) { $tag = [guid]::NewGuid().ToString() }
    [void]$nodes.Add(@{
        location       = @{ x = $xFact; y = 0 }
        nodeIndex      = $t
        nodeLineageTag = $tag
        size           = @{ height = 128; width = 234 }
        zIndex         = 5
        expandedHeight = 152
    })
    $xFact += 250
}

# Dims and security vertical at x=0, zIndex 10
$yDim = 120
foreach ($t in $dimsAndSecurity) {
    $tmdlPath = Join-Path $tablesDir "$t.tmdl"
    $tag = Get-LineageTagFromTmdl -TmdlPath $tmdlPath
    if (-not $tag) { $tag = [guid]::NewGuid().ToString() }
    [void]$nodes.Add(@{
        location       = @{ x = 0; y = $yDim }
        nodeIndex      = $t
        nodeLineageTag = $tag
        size           = @{ height = 104; width = 234 }
        zIndex         = 10
        expandedHeight = 152
    })
    $yDim += 120
}

# Other tables (e.g. _ActionReady_Logic)
foreach ($t in $other) {
    $tmdlPath = Join-Path $tablesDir "$t.tmdl"
    $tag = Get-LineageTagFromTmdl -TmdlPath $tmdlPath
    if (-not $tag) { $tag = [guid]::NewGuid().ToString() }
    [void]$nodes.Add(@{
        location       = @{ x = 0; y = $yDim }
        nodeIndex      = $t
        nodeLineageTag = $tag
        size           = @{ height = 104; width = 234 }
        zIndex         = 10
        expandedHeight = 152
    })
    $yDim += 120
}

$diagram = @{
    ordinal                  = 0
    scrollPosition           = @{ x = 0; y = 0 }
    name                     = $diagramName
    zoomValue                = 22.850503485670025
    pinKeyFieldsToTop        = $false
    showExtraHeaderInfo      = $false
    hideKeyFieldsWhenCollapsed = $false
    tablesLocked             = $false
    nodes                    = @($nodes)
}

$layout = @{
    version          = "1.1.0"
    diagrams         = @($diagram)
    selectedDiagram  = $diagramName
    defaultDiagram   = $diagramName
}

$json = $layout | ConvertTo-Json -Depth 6 -Compress:$false
$outPath = Join-Path $smRoot "diagramLayout.json"
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($outPath, $json, $utf8)
$nodeCount = $nodes.Count
Write-Host "  Wrote: $outPath ($nodeCount nodes)" -ForegroundColor Green
