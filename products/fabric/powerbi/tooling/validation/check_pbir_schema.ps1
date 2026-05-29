<#
.SYNOPSIS
  Validates PBIR JSON files against cached Microsoft JSON schemas.
.DESCRIPTION
  Checks PBIR JSON files in a report definition folder against the Microsoft JSON
  Schema declared in each file's $schema property.

  Cached schemas live under tooling/schemas/pbir/microsoft/ (run cache_pbir_schemas.py
  to refresh). Legacy stub files (visual.schema.json, etc.) are used only when
  $schema is missing.

  Uses Python jsonschema (+ report_quality $ref resolution) when available,
  falling back to structural PowerShell checks when jsonschema is not installed.

  Schemas cached in: tooling/schemas/pbir/
  Schema source:     https://developer.microsoft.com/json-schemas/fabric/item/report/

.PARAMETER ReportPath
  Path to a .Report directory or its definition sub-folder. Defaults to first
  *.Report directory found under products/fabric/powerbi/dist/.
.PARAMETER SchemaDir
  Override the schema directory. Defaults to tooling/schemas/pbir/ relative to
  the repository root.
.EXAMPLE
  .\check_pbir_schema.ps1
.EXAMPLE
  .\check_pbir_schema.ps1 -ReportPath "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report"
#>
Param(
    [string]$ReportPath = "",
    [string]$SchemaDir  = ""
)

$ErrorActionPreference = "Stop"

# ── Locate repo root ──────────────────────────────────────────────────────────
$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot  = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.Parent.FullName

# ── Resolve SchemaDir ─────────────────────────────────────────────────────────
if (-not $SchemaDir) {
    $SchemaDir = Join-Path $repoRoot "tooling/schemas/pbir"
}
if (-not (Test-Path $SchemaDir)) {
    Write-Error "Schema directory not found: $SchemaDir"
    exit 1
}

# ── Resolve ReportPath ────────────────────────────────────────────────────────
if (-not $ReportPath) {
    $distDir     = Join-Path $repoRoot "products/fabric/powerbi/dist"
    $firstReport = Get-ChildItem -Path $distDir -Filter "*.Report" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
    $ReportPath  = if ($firstReport) { $firstReport.FullName } else { $distDir }
}
if (-not [System.IO.Path]::IsPathRooted($ReportPath)) {
    $ReportPath = Join-Path $repoRoot $ReportPath
}
# Accept either the .Report directory or its definition sub-folder
$defDir = if ((Split-Path -Leaf $ReportPath) -eq "definition") { $ReportPath } else { Join-Path $ReportPath "definition" }

if (-not (Test-Path $defDir)) {
    Write-Error "Report definition folder not found: $defDir"
    exit 1
}

Write-Host "PBIR schema validation: $defDir" -ForegroundColor Cyan
Write-Host "Schemas from:           $SchemaDir" -ForegroundColor Cyan
Write-Host ""

# ── Check jsonschema availability ─────────────────────────────────────────────
$script:pythonExeParts = $null
$useJsonschema = $false
foreach ($cmd in @("py -3", "python3", "python")) {
    $parts = $cmd -split " "
    try {
        $pyCheck = & $parts[0] @($parts[1..99] | Where-Object { $_ }) "-c" "import jsonschema; print('ok')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $pyCheck -eq "ok") {
            $script:pythonExeParts = $parts
            $useJsonschema = $true
            break
        }
    } catch { continue }
}

if ($useJsonschema) {
    Write-Host "  Using: Python jsonschema (full JSON Schema Draft-7)" -ForegroundColor DarkGray
} else {
    Write-Host "  Using: PowerShell structural checks (install jsonschema for full schema validation)" -ForegroundColor Yellow
}
Write-Host ""

# ── Helpers ───────────────────────────────────────────────────────────────────
$violations = [System.Collections.ArrayList]::new()

function Add-Violation([string]$RelPath, [string]$Message) {
    [void]$script:violations.Add("$RelPath : $Message")
}

function Get-RelPath([string]$AbsPath) {
    $AbsPath.Replace($repoRoot, "").TrimStart("/\")
}

function Validate-WithJsonschema([string]$JsonFile) {
    $relJson = Get-RelPath $JsonFile
    $pyHelper = Join-Path $scriptDir "validate_pbir_jsonschema.py"
    if (-not (Test-Path $pyHelper)) {
        Add-Violation $relJson "validate_pbir_jsonschema.py not found beside check_pbir_schema.ps1"
        return
    }
    $env:PYTHONPATH = @(
        (Join-Path $repoRoot "tooling"),
        $env:PYTHONPATH
    ) -join [System.IO.Path]::PathSeparator
    $pyArgs = @($script:pythonExeParts[1..99] | Where-Object { $_ }) + @($pyHelper, $JsonFile, $SchemaDir)
    $output = & $script:pythonExeParts[0] @pyArgs 2>&1
    if ($LASTEXITCODE -eq 2) {
        foreach ($line in @($output)) {
            Add-Violation $relJson "$line"
        }
        return
    }

    foreach ($line in @($output)) {
        $text = "$line"
        if ($text -and $text -match "\|") {
            $parts   = $text -split "\|", 2
            $path    = $parts[0]
            $message = $parts[1]
            Add-Violation $relJson "[$path] $message"
        }
    }
}

function Validate-Structural-Visual([string]$JsonFile) {
    $relJson = Get-RelPath $JsonFile
    try {
        $obj = Get-Content $JsonFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Add-Violation $relJson "JSON parse error: $_"
        return
    }
    if (-not $obj.'$schema') { Add-Violation $relJson 'missing required: $schema' }
    if (-not $obj.name)      { Add-Violation $relJson "missing required: name" }
    if (-not $obj.position)  { Add-Violation $relJson "missing required: position" }
    if (-not ($obj.visual -or $obj.visualGroup)) {
        Add-Violation $relJson "missing required: visual or visualGroup"
    }
    if ($obj.name -and $obj.name -match "[^a-zA-Z0-9_\-]") {
        Add-Violation $relJson "name '$($obj.name)' contains invalid characters (use a-z, A-Z, 0-9, _, -)"
    }
    if ($obj.position) {
        foreach ($field in @("x","y","height","width")) {
            if ($null -eq $obj.position.$field) {
                Add-Violation $relJson "position missing required field: $field"
            }
        }
    }
}

function Validate-Structural-Page([string]$JsonFile) {
    $relJson = Get-RelPath $JsonFile
    try {
        $obj = Get-Content $JsonFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Add-Violation $relJson "JSON parse error: $_"
        return
    }
    if (-not $obj.'$schema')   { Add-Violation $relJson 'missing required: $schema' }
    if (-not $obj.name)        { Add-Violation $relJson "missing required: name" }
    if (-not $obj.displayName) { Add-Violation $relJson "missing required: displayName" }
    if ($obj.displayOption -and ($obj.displayOption -is [int])) {
        Add-Violation $relJson "displayOption must be a string (e.g. 'FitToPage'), not an integer"
    }
}

function Validate-Structural-Pbir([string]$JsonFile) {
    $relJson = Get-RelPath $JsonFile
    try {
        $obj = Get-Content $JsonFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Add-Violation $relJson "JSON parse error: $_"
        return
    }
    if (-not $obj.'$schema')        { Add-Violation $relJson 'missing required: $schema' }
    if (-not $obj.version)          { Add-Violation $relJson "missing required: version" }
    if (-not $obj.datasetReference) { Add-Violation $relJson "missing required: datasetReference" }
    if ($obj.datasetReference) {
        $hasByPath       = $null -ne $obj.datasetReference.byPath
        $hasByConnection = $null -ne $obj.datasetReference.byConnection
        if (-not $hasByPath -and -not $hasByConnection) {
            Add-Violation $relJson "datasetReference must have either byPath or byConnection"
        }
        if ($hasByPath -and -not $obj.datasetReference.byPath.path) {
            Add-Violation $relJson "datasetReference.byPath.path is required"
        }
        if ($hasByConnection) {
            $bc = $obj.datasetReference.byConnection
            if (-not $bc.pbiModelDatabaseName) {
                Add-Violation $relJson "datasetReference.byConnection.pbiModelDatabaseName is required (Fabric SemanticModel GUID)"
            } elseif ($bc.pbiModelDatabaseName.Length -ne 36) {
                Add-Violation $relJson "datasetReference.byConnection.pbiModelDatabaseName should be a 36-char GUID"
            }
        }
    }
}

# ── Folder name validation ────────────────────────────────────────────────────
# Power BI Desktop silently ignores pages/visuals/bookmarks whose folder names
# contain characters outside [a-zA-Z0-9_-]. No error dialog is shown -- the
# object simply vanishes from the loaded report. This is the hardest-to-debug
# class of PBIR errors. Validate early to catch it before opening in Desktop.
function Validate-FolderNames([string]$PagesDir) {
    $validNameRe = [regex]'^[\w\-]+$'
    Get-ChildItem -Path $PagesDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        # strip optional .Page suffix before checking
        $pageName = $_.Name -replace '\.Page$', ''
        if (-not $validNameRe.IsMatch($pageName)) {
            Add-Violation (Get-RelPath $_.FullName) "Page folder '$pageName' contains invalid characters. Only a-z, A-Z, 0-9, _ and - are allowed. Desktop silently ignores pages with invalid names."
        }
        $visualsDir = Join-Path $_.FullName "visuals"
        if (Test-Path $visualsDir) {
            Get-ChildItem -Path $visualsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                if (-not $validNameRe.IsMatch($_.Name)) {
                    Add-Violation (Get-RelPath $_.FullName) "Visual folder '$($_.Name)' contains invalid characters. Only a-z, A-Z, 0-9, _ and - are allowed. Desktop silently ignores visuals with invalid names."
                }
            }
        }
    }
    # bookmarks
    $bookmarksDir = Join-Path (Split-Path -Parent $PagesDir) "bookmarks"
    if (Test-Path $bookmarksDir) {
        Get-ChildItem -Path $bookmarksDir -Filter "*.bookmark.json" -ErrorAction SilentlyContinue | ForEach-Object {
            $bName = $_.BaseName -replace '\.bookmark$', ''
            if (-not $validNameRe.IsMatch($bName)) {
                Add-Violation (Get-RelPath $_.FullName) "Bookmark '$bName' contains invalid characters. Only a-z, A-Z, 0-9, _ and - are allowed."
            }
        }
    }
}

# ── Scan files (validate against each file's $schema URL) ─────────────────────
$scannedFiles = 0

function Invoke-PbirJsonCheck([string]$JsonFile, [scriptblock]$StructuralCheck) {
    $script:scannedFiles++
    if ($useJsonschema) {
        Validate-WithJsonschema $JsonFile
    } else {
        & $StructuralCheck $JsonFile
    }
}

# definition.pbir + report.json at definition root
$pbirFile = Join-Path $defDir "definition.pbir"
if (Test-Path $pbirFile) {
    Invoke-PbirJsonCheck $pbirFile { param($f) Validate-Structural-Pbir $f }
}
$reportJson = Join-Path $defDir "report.json"
if (Test-Path $reportJson) {
    Invoke-PbirJsonCheck $reportJson {
        param($f)
        $relJson = Get-RelPath $f
        try {
            $obj = Get-Content $f -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            Add-Violation $relJson "JSON parse error: $_"
            return
        }
        if (-not $obj.'$schema') { Add-Violation $relJson 'missing required: $schema' }
    }
}

# pages/**/page.json and visuals/**/visual.json
$pagesDir = Join-Path $defDir "pages"
if (Test-Path $pagesDir) {
    Validate-FolderNames $pagesDir
    Get-ChildItem -Path $pagesDir -Recurse -File -Filter "page.json" | ForEach-Object {
        Invoke-PbirJsonCheck $_.FullName { param($f) Validate-Structural-Page $f }
    }

    Get-ChildItem -Path $pagesDir -Recurse -File -Filter "visual.json" | ForEach-Object {
        Invoke-PbirJsonCheck $_.FullName { param($f) Validate-Structural-Visual $f }
    }
}

# ── Report results ────────────────────────────────────────────────────────────
Write-Host "Scanned $scannedFiles file(s)." -ForegroundColor DarkGray

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "PBIR schema violations ($($violations.Count)):" -ForegroundColor Red
    foreach ($v in $violations) {
        Write-Host "  ✗ $v" -ForegroundColor Red
    }
    exit 1
}

Write-Host "PBIR schema check passed -- no violations found." -ForegroundColor Green
exit 0
