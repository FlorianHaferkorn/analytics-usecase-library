<#
.SYNOPSIS
  Post-Implementation-Validierung für PBIP: Fabric-Checks + optionale Desktop-Fehler aus pbi_errors.log.
  Gibt ein maschinenlesbares JSON-Ergebnis aus; der Agent wartet darauf und entscheidet: Loop (Fix + Learning) oder Ende.

.DESCRIPTION
  Wird vom Agent nach Abschluss einer MCP- oder manuellen Implementierung ausgeführt.
  - Führt run_fabric_checks.ps1 aus und erfasst Ausgabe und Exit-Code.
  - Falls .cursor/pbi_errors.log in den letzten N Minuten geändert wurde, werden die letzten Zeilen als weitere Fehlerquelle einbezogen.
  - Schreibt Ergebnis als JSON (stdout + optional .cursor/pbi_validate_result.json) für den Agent.

.PARAMETER RepoRoot
  Repo-Root (Standard: über tooling ermittelt).

.PARAMETER IncludeDesktopLogMinutes
  Wenn pbi_errors.log innerhalb der letzten N Minuten geändert wurde, dessen Inhalt in errors aufnehmen (0 = aus).

.PARAMETER ResultFile
  Zusätzlich JSON in diese Datei schreiben (z. B. .cursor/pbi_validate_result.json).

.EXAMPLE
  .\tooling\pbi_validate_after_impl.ps1
  .\tooling\pbi_validate_after_impl.ps1 -IncludeDesktopLogMinutes 15 -ResultFile .cursor/pbi_validate_result.json
#>

param(
  [string] $RepoRoot = (Split-Path $PSScriptRoot -Parent),
  [int]    $IncludeDesktopLogMinutes = 10,
  [string] $ResultFile = ""
)

$ErrorActionPreference = "Stop"
$bridgeFile = Join-Path $RepoRoot ".cursor\pbi_errors.log"
$fabricChecksScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\run_fabric_checks.ps1"

$errors = [System.Collections.ArrayList]::new()
$sources = [System.Collections.ArrayList]::new()

# 0a) Normalize TMDL tabs (all .tmdl under dist) before ensure and patch
$normalizeTabsScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\normalize_tmdl_tabs.ps1"
if (Test-Path $normalizeTabsScript) {
  try { & $normalizeTabsScript -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot 2>&1 | Out-Null } catch {}
}

# 0) PBIP Desktop-tauglich + TMDL render & fix
$ensureScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\ensure_pbip_desktop_ready.ps1"
if (Test-Path $ensureScript) {
  try { & $ensureScript -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot 2>&1 | Out-Null } catch {}
}
$tmdlRenderScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\tmdl_render_and_fix.ps1"
if (Test-Path $tmdlRenderScript) {
  try { & $tmdlRenderScript -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot -UpdateKnowledgeBase $true 2>&1 | Out-Null } catch {}
}

# 0b) Auto-fix best practices: summarizeBy: none + diagram layout (Spaghetti) for each semantic model in dist
$distPath = Join-Path $RepoRoot "products\fabric\powerbi\dist"
$orchestratorRoot = Join-Path $RepoRoot "products\fabric\powerbi\orchestrator"
$tableOpsScript = Join-Path $orchestratorRoot "table_ops.ps1"
$writeDiagramScript = Join-Path $orchestratorRoot "write_diagram_layout.ps1"
if (Test-Path $distPath) {
  Get-ChildItem -Path $distPath -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue | ForEach-Object {
    $defPath = Join-Path $_.FullName "definition"
    if (Test-Path $defPath) {
      if (Test-Path $tableOpsScript) { try { & $tableOpsScript -Operation "PatchAddSummarizeByNone" -DefinitionPath $defPath 2>&1 | Out-Null } catch {} }
      if (Test-Path $writeDiagramScript) { try { & $writeDiagramScript -DefinitionPath $defPath 2>&1 | Out-Null } catch {} }
    }
  }
}

# 1) Fabric-Checks ausführen
if (Test-Path $fabricChecksScript) {
  try {
    $fabricOutput = & $fabricChecksScript 2>&1
    $fabricExit = $LASTEXITCODE
    if ($null -eq $fabricExit) { $fabricExit = 0 }
    $fabricLines = @($fabricOutput | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ -ne "" })
    [void]$sources.Add("run_fabric_checks")
    $fabricFailed = ($fabricExit -ne 0) -or ($fabricOutput -match "Fabric checks:\s*\d+\s+failed")
    if ($fabricFailed) {
      foreach ($line in $fabricLines) { [void]$errors.Add($line) }
    }
  } catch {
    [void]$sources.Add("run_fabric_checks")
    [void]$errors.Add("run_fabric_checks failed: $_")
  }
} else {
  [void]$sources.Add("run_fabric_checks")
  [void]$errors.Add("run_fabric_checks.ps1 not found: $fabricChecksScript")
}

# 2) Optionale Desktop-Log-Fehler (wenn kürzlich geändert)
if ($IncludeDesktopLogMinutes -gt 0 -and (Test-Path $bridgeFile)) {
  $lastWrite = (Get-Item $bridgeFile).LastWriteTime
  $cutoff = (Get-Date).AddMinutes(-$IncludeDesktopLogMinutes)
  if ($lastWrite -ge $cutoff) {
    [void]$sources.Add("pbi_errors.log")
    $tail = Get-Content -Path $bridgeFile -Tail 50 -Encoding utf8 -ErrorAction SilentlyContinue
    foreach ($line in $tail) {
      $t = $line.Trim()
      if ($t -ne "") { [void]$errors.Add($t) }
    }
  }
}

$success = ($errors.Count -eq 0)
$result = @{
  success   = $success
  errors    = @($errors)
  sources   = @($sources)
  timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json -Depth 3

if ($ResultFile) {
  $resolved = if ([System.IO.Path]::IsPathRooted($ResultFile)) { $ResultFile } else { Join-Path $RepoRoot ($ResultFile -replace "/", [IO.Path]::DirectorySeparatorChar) }
  $dir = Split-Path $resolved -Parent
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $result | Set-Content -Path $resolved -Encoding utf8
}

Write-Output $result
if (-not $success) { exit 1 }
exit 0
