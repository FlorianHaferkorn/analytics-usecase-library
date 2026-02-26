<#
.SYNOPSIS
  TMDL Script Renderer: Validiert TMDL, befüllt bei Fehlern das Fehlerlog, wendet Auto-Fixes an und trägt
  erfolgreiche Lösungen in KNOWN_ERRORS_AND_FIXES.md ein (Learning Loop).

.DESCRIPTION
  1) Führt TMDL-Validierung aus (check_tmdl_syntax, check_tmdl_pbip_readiness; optional pbi-tools compile).
  2) Bei Fehlern: schreibt in .cursor/tmdl_errors.log, wendet bekannte Auto-Fixes an (z. B. Spaces→Tabs, description entfernen), wiederholt.
  3) Nach erfolgreicher Validierung, wenn in dieser Runde ein Fix angewendet wurde: fügt eine Zeile (Symptom | Cause | Fix) in internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md unter "TMDL / PBIP" ein.

.PARAMETER DistRoot
  Pfad zum Dist-Root (z. B. products/fabric_powerbi/dist).

.PARAMETER RepoRoot
  Repo-Root (Standard: aus Skriptpfad ermittelt).

.PARAMETER MaxIterations
  Maximale Validierungs-/Fix-Runden (Standard: 5).

.PARAMETER ErrorLogPath
  Datei für TMDL-Fehler (Standard: .cursor/tmdl_errors.log).

.PARAMETER UpdateKnowledgeBase
  Bei Erfolg nach Fix eine Zeile in KNOWN_ERRORS_AND_FIXES eintragen (Standard: true).

.PARAMETER TryPbiToolsCompile
  Falls pbi-tools im PATH: nach den Checks noch compile ausführen (Standard: false, da oft nicht installiert).

.EXAMPLE
  .\products\fabric_powerbi\tooling\tmdl_render_and_fix.ps1
  .\products\fabric_powerbi\tooling\tmdl_render_and_fix.ps1 -DistRoot products/fabric_powerbi/dist -UpdateKnowledgeBase $true
#>

param(
  [string] $DistRoot = "products/fabric_powerbi/dist",
  [string] $RepoRoot = $null,
  [int]    $MaxIterations = 5,
  [string] $ErrorLogPath = ".cursor/tmdl_errors.log",
  [bool]   $UpdateKnowledgeBase = $true,
  [bool]   $TryPbiToolsCompile = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path $PSCommandPath -Parent
if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
}
$distResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $RepoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }
$errorLogResolved = if ([System.IO.Path]::IsPathRooted($ErrorLogPath)) { $ErrorLogPath } else { Join-Path $RepoRoot ($ErrorLogPath -replace '/', [System.IO.Path]::DirectorySeparatorChar) }
$knowledgePath = Join-Path $RepoRoot "internal\project_mgmt\KNOWN_ERRORS_AND_FIXES.md"

$checkSyntax = Join-Path $scriptDir "validation\check_tmdl_syntax.ps1"
$checkReadiness = Join-Path $scriptDir "validation\check_tmdl_pbip_readiness.ps1"

function Write-TmdlLog {
  param([string]$Message, [string]$Level = "ERROR")
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
  $cursorDir = Split-Path $errorLogResolved -Parent
  if (-not (Test-Path $cursorDir)) { New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null }
  $line | Out-File -FilePath $errorLogResolved -Append -Encoding utf8
  Write-Host $line
}

function Invoke-TmdlValidation {
  $allOutput = @()
  $failed = $false
  if (Test-Path $checkSyntax) {
    $out = & $checkSyntax -DistRoot $distResolved 2>&1
    $allOutput += $out
    if ($LASTEXITCODE -ne 0) { $failed = $true }
  }
  if (Test-Path $checkReadiness) {
    $out = & $checkReadiness -DistRoot $distResolved 2>&1
    $allOutput += $out
    if ($LASTEXITCODE -ne 0) { $failed = $true }
  }
  if ($TryPbiToolsCompile) {
    $pbitools = Get-Command pbi-tools -ErrorAction SilentlyContinue
    if ($pbitools) {
      $modelDirs = Get-ChildItem -Path $distResolved -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue
      foreach ($m in $modelDirs) {
        $out = & pbi-tools compile -pbipPath $m.FullName 2>&1
        $allOutput += $out
        if ($LASTEXITCODE -ne 0) { $failed = $true }
      }
    }
  }
  return @{ Failed = $failed; Output = $allOutput }
}

function Convert-LeadingSpacesToTabs {
  param([string]$Leading)
  if ($Leading -notmatch ' ') { return $Leading }
  $tabCount = [math]::Floor($Leading.Length / 4)
  if ($Leading.Length % 4 -gt 0) { $tabCount += 1 }
  if ($tabCount -eq 0) { $tabCount = 1 }
  return "`t" * $tabCount
}

function Apply-AutoFixTabs {
  param([string]$FilePath)
  $content = Get-Content -Path $FilePath -Raw -Encoding utf8
  $lines = $content -split "`r?`n"
  $fixed = @()
  foreach ($line in $lines) {
    if ($line -match '^(\s+)(.*)$') {
      $leading = Convert-LeadingSpacesToTabs -Leading $matches[1]
      $fixed += $leading + $matches[2]
    } else {
      $fixed += $line
    }
  }
  $newContent = $fixed -join "`n"
  [System.IO.File]::WriteAllText($FilePath, $newContent, (New-Object System.Text.UTF8Encoding $false))
}

function Apply-AutoFixDescription {
  param([string]$FilePath)
  $content = Get-Content -Path $FilePath -Raw -Encoding utf8
  $lines = $content -split "`r?`n"
  $fixed = @()
  foreach ($line in $lines) {
    if ($line -match '^\s*description\s*:') { continue }
    $fixed += $line
  }
  $newContent = $fixed -join "`n"
  [System.IO.File]::WriteAllText($FilePath, $newContent, (New-Object System.Text.UTF8Encoding $false))
}

function Apply-AutoFixesFromOutput {
  param([array]$Output)
  $tmdlFilesFixed = @{}
  foreach ($line in $Output) {
    $s = $line.ToString()
    if ($s -match '([^\s:]+\.tmdl):(\d+)\s*\[ERROR\]\s*(tmdl\.\w+)\s*-') {
      $filePart = $matches[1]
      $rule = $matches[3]
      $fullPath = Join-Path $distResolved $filePart
      if (-not (Test-Path $fullPath)) { continue }
      if (-not $tmdlFilesFixed[$fullPath]) { $tmdlFilesFixed[$fullPath] = @{} }
      if ($rule -eq "tmdl.indent.tabs_only") { $tmdlFilesFixed[$fullPath]["tabs"] = $true }
      if ($rule -eq "tmdl.description.forbidden") { $tmdlFilesFixed[$fullPath]["description"] = $true }
    }
  }
  foreach ($path in $tmdlFilesFixed.Keys) {
    $opts = $tmdlFilesFixed[$path]
    if ($opts["tabs"]) { Apply-AutoFixTabs -FilePath $path; Write-Host "  Auto-fix (tabs): $path" -ForegroundColor Yellow }
    if ($opts["description"]) { Apply-AutoFixDescription -FilePath $path; Write-Host "  Auto-fix (description): $path" -ForegroundColor Yellow }
  }
  return ($tmdlFilesFixed.Count -gt 0)
}

function Add-KnowledgeBaseRow {
  param([string]$Symptom, [string]$Cause, [string]$Fix)
  if (-not (Test-Path $knowledgePath)) { return }
  $escape = { param($s) ($s -replace '\|', '\|') -replace "`r?`n", ' ' }
  $s = & $escape $Symptom
  $c = & $escape $Cause
  $f = & $escape $Fix
  $content = Get-Content -Path $knowledgePath -Raw -Encoding utf8
  $section = "## TMDL / PBIP"
  $idx = $content.IndexOf($section)
  if ($idx -lt 0) { return }
  $after = $content.Substring($idx)
  $endTable = $after.IndexOf("`n---")
  if ($endTable -lt 0) { $endTable = $after.IndexOf("`n## ") }
  if ($endTable -lt 0) { $endTable = $after.Length }
  $insertPos = $idx + $endTable
  $newRow = "`n| $s | $c | $f |"
  $content = $content.Insert($insertPos, $newRow)
  [System.IO.File]::WriteAllText($knowledgePath, $content, (New-Object System.Text.UTF8Encoding $false))
  Write-Host "  Learning Loop: Zeile in KNOWN_ERRORS_AND_FIXES.md (TMDL / PBIP) eingetragen." -ForegroundColor Green
}

# --- Main ---
if (-not (Test-Path $distResolved)) {
  Write-Host "DistRoot nicht gefunden: $distResolved" -ForegroundColor Red
  exit 2
}

Write-Host "TMDL Render & Fix: Validierung + Fehlerlog + Auto-Fix + Learning Loop (max $MaxIterations Runden)" -ForegroundColor Cyan
$lastErrorSummary = $null
$appliedFixInRun = $false
$iteration = 0

while ($iteration -lt $MaxIterations) {
  $iteration++
  Write-Host "`n--- Runde $iteration ---" -ForegroundColor Cyan
  $result = Invoke-TmdlValidation
  if (-not $result.Failed) {
    if ($appliedFixInRun -and $UpdateKnowledgeBase -and $lastErrorSummary) {
      $symptom = ($lastErrorSummary -split "`n")[0]
      if ($symptom.Length -gt 200) { $symptom = $symptom.Substring(0, 197) + "..." }
      Add-KnowledgeBaseRow -Symptom $symptom -Cause "TMDL syntax/readiness (tabs or description)." -Fix "tmdl_render_and_fix.ps1 Auto-Fix (Spaces→Tabs, description entfernt); bei Indentation in Spaltenamen: column ''Name'' verwenden."
    }
    Write-Host "`nTMDL-Validierung bestanden." -ForegroundColor Green
    exit 0
  }

  $outputText = $result.Output | ForEach-Object { $_.ToString() } | Where-Object { $_ -ne "" }
  $lastErrorSummary = $outputText -join "`n"
  foreach ($line in $outputText) { Write-TmdlLog -Message $line }
  Write-TmdlLog -Message "--- End of validation output ---" -Level "INFO"

  $fixed = Apply-AutoFixesFromOutput -Output $result.Output
  if ($fixed) { $appliedFixInRun = $true }
  if (-not $fixed) {
    Write-Host "`nKeine Auto-Fixes anwendbar; verbleibende Fehler siehe $errorLogResolved" -ForegroundColor Yellow
    exit 1
  }
}

Write-Host "`nMax Runden ($MaxIterations) erreicht. Fehlerlog: $errorLogResolved" -ForegroundColor Yellow
exit 1
