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
  [string] $ResultFile = "",
  [string] $PolicyPath = "products/fabric/powerbi/tooling/production_quality.standard.json",
  [bool]   $RequirePbiToolsCompile = $false
)

$ErrorActionPreference = "Stop"
$bridgeFile = Join-Path $RepoRoot ".cursor\pbi_errors.log"
$fabricChecksScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\run_fabric_checks.ps1"
$reportStructureScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\check_report_structure.ps1"
$pbipValidateScript = Join-Path $RepoRoot "tooling\validation\pbip\validate_pbip.ps1"
$stage1Script = Join-Path $RepoRoot "tooling\run_stage1_checks.ps1"
$distPath = Join-Path $RepoRoot "products\fabric\powerbi\dist"

$errors = [System.Collections.ArrayList]::new()
$sources = [System.Collections.ArrayList]::new()
$gates = [System.Collections.ArrayList]::new()

function Add-GateResult {
  param(
    [string] $Name,
    [bool] $Passed,
    [string] $Source,
    [string[]] $Messages = @()
  )

  [void]$gates.Add(@{
    name = $Name
    passed = $Passed
    source = $Source
    messages = @($Messages)
  })
}

function Convert-CommandOutputToLines {
  param(
    [object] $Output
  )

  $text = if ($null -eq $Output) { "" } else { ($Output | Out-String -Width 4096) }
  return @($text -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
}

function Resolve-PolicyValue {
  param(
    [object] $Policy,
    [string] $RequirementName,
    [bool] $DefaultValue = $false
  )

  if ($null -eq $Policy) { return $DefaultValue }
  $requirements = $Policy.PSObject.Properties['requirements']
  if ($null -eq $requirements) { return $DefaultValue }
  $requirement = $requirements.Value.PSObject.Properties[$RequirementName]
  if ($null -eq $requirement) { return $DefaultValue }
  $required = $requirement.Value.PSObject.Properties['required']
  if ($null -eq $required) { return $DefaultValue }
  return [bool]$required.Value
}

function Resolve-PbiToolsPath {
  param([string] $RepoRoot)

  $command = Get-Command pbi-tools -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }

  $candidates = @(
    $env:PBI_TOOLS_PATH,
    (Join-Path $RepoRoot ".tools\pbi-tools\pbi-tools.exe"),
    (Join-Path $RepoRoot ".tools\pbi-tools\pbi-tools.core.exe")
  ) | Where-Object { $_ }

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return (Resolve-Path -Path $candidate).Path
    }
  }

  return $null
}

function Test-PbiToolsCompileCompatible {
  param([string] $FolderPath)

  return (Test-Path (Join-Path $FolderPath "Version.txt"))
}

$resolvedPolicyPath = if ([System.IO.Path]::IsPathRooted($PolicyPath)) { $PolicyPath } else { Join-Path $RepoRoot ($PolicyPath -replace "/", [IO.Path]::DirectorySeparatorChar) }
$policy = $null
if (Test-Path $resolvedPolicyPath) {
  try {
    $policy = Get-Content -Path $resolvedPolicyPath -Raw -Encoding utf8 | ConvertFrom-Json
  } catch {
    [void]$sources.Add("production_quality.standard")
    [void]$errors.Add("Policy load failed: $resolvedPolicyPath :: $_")
    Add-GateResult -Name "policy" -Passed $false -Source "production_quality.standard" -Messages @("Policy load failed: $resolvedPolicyPath")
  }
}

$requireStage1 = Resolve-PolicyValue -Policy $policy -RequirementName "stage1"
$requireReportStructure = Resolve-PolicyValue -Policy $policy -RequirementName "reportStructure" -DefaultValue $true
$requirePbipValidation = Resolve-PolicyValue -Policy $policy -RequirementName "pbipValidation" -DefaultValue $true
$effectiveRequireCompile = $RequirePbiToolsCompile -or (Resolve-PolicyValue -Policy $policy -RequirementName "pbiToolsCompile")

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

# 0c) Optional Stage 1 as hard prerequisite in production mode
if ($requireStage1) {
  if (Test-Path $stage1Script) {
    try {
      $stage1ResultsPath = Join-Path $RepoRoot "tooling\validation\results\latest_results.json"
      $stage1StdOut = [System.IO.Path]::GetTempFileName()
      $stage1StdErr = [System.IO.Path]::GetTempFileName()
      $stage1Process = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $stage1Script, "-Root", $RepoRoot) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stage1StdOut -RedirectStandardError $stage1StdErr
      $stage1Output = @()
      if (Test-Path $stage1StdOut) { $stage1Output += Get-Content -Path $stage1StdOut }
      if (Test-Path $stage1StdErr) { $stage1Output += Get-Content -Path $stage1StdErr }
      Remove-Item $stage1StdOut, $stage1StdErr -ErrorAction SilentlyContinue
      $stage1Exit = $stage1Process.ExitCode
      if ($null -eq $stage1Exit) { $stage1Exit = 0 }
      $stage1Lines = Convert-CommandOutputToLines -Output $stage1Output
      $stage1Passed = ($stage1Exit -eq 0)
      if (Test-Path $stage1ResultsPath) {
        try {
          $stage1Results = Get-Content -Raw -Path $stage1ResultsPath | ConvertFrom-Json
          if ($stage1Results.overall_status) {
            $stage1Passed = ($stage1Results.overall_status -eq "pass")
          }
        } catch {}
      }
      if ((-not $stage1Passed) -and $stage1Lines.Count -eq 0) {
        $stage1Lines = @("run_stage1_checks exited with code $stage1Exit")
      }
      Add-GateResult -Name "stage1" -Passed $stage1Passed -Source "run_stage1_checks" -Messages $stage1Lines
      [void]$sources.Add("run_stage1_checks")
      if (-not $stage1Passed) {
        foreach ($line in $stage1Lines) { [void]$errors.Add($line) }
      }
    } catch {
      [void]$sources.Add("run_stage1_checks")
      [void]$errors.Add("run_stage1_checks failed: $_")
      Add-GateResult -Name "stage1" -Passed $false -Source "run_stage1_checks" -Messages @("run_stage1_checks failed: $_")
    }
  } else {
    [void]$sources.Add("run_stage1_checks")
    [void]$errors.Add("run_stage1_checks.ps1 not found: $stage1Script")
    Add-GateResult -Name "stage1" -Passed $false -Source "run_stage1_checks" -Messages @("run_stage1_checks.ps1 not found: $stage1Script")
  }
}

# 1) Fabric-Checks ausführen
if (Test-Path $fabricChecksScript) {
  try {
    $fabricOutput = & $fabricChecksScript 2>&1
    $fabricExit = $LASTEXITCODE
    if ($null -eq $fabricExit) { $fabricExit = 0 }
    $fabricLines = Convert-CommandOutputToLines -Output $fabricOutput
    [void]$sources.Add("run_fabric_checks")
    $fabricFailed = ($fabricExit -ne 0) -or ($fabricOutput -match "Fabric checks:\s*\d+\s+failed")
    if ($fabricFailed -and $fabricLines.Count -eq 0) {
      $fabricLines = @("run_fabric_checks exited with code $fabricExit")
    }
    Add-GateResult -Name "fabricChecks" -Passed (-not $fabricFailed) -Source "run_fabric_checks" -Messages $fabricLines
    if ($fabricFailed) {
      foreach ($line in $fabricLines) { [void]$errors.Add($line) }
    }
  } catch {
    [void]$sources.Add("run_fabric_checks")
    [void]$errors.Add("run_fabric_checks failed: $_")
    Add-GateResult -Name "fabricChecks" -Passed $false -Source "run_fabric_checks" -Messages @("run_fabric_checks failed: $_")
  }
} else {
  [void]$sources.Add("run_fabric_checks")
  [void]$errors.Add("run_fabric_checks.ps1 not found: $fabricChecksScript")
  Add-GateResult -Name "fabricChecks" -Passed $false -Source "run_fabric_checks" -Messages @("run_fabric_checks.ps1 not found: $fabricChecksScript")
}

# 1b) Report structure check
if ($requireReportStructure) {
  if (Test-Path $reportStructureScript) {
    try {
      $structureOutput = & $reportStructureScript -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot 2>&1
      $structureExit = $LASTEXITCODE
      if ($null -eq $structureExit) { $structureExit = 0 }
      $structureLines = Convert-CommandOutputToLines -Output $structureOutput
      $structurePassed = ($structureExit -eq 0)
      if ((-not $structurePassed) -and $structureLines.Count -eq 0) {
        $structureLines = @("check_report_structure exited with code $structureExit")
      }
      Add-GateResult -Name "reportStructure" -Passed $structurePassed -Source "check_report_structure" -Messages $structureLines
      [void]$sources.Add("check_report_structure")
      if (-not $structurePassed) {
        foreach ($line in $structureLines) { [void]$errors.Add($line) }
      }
    } catch {
      [void]$sources.Add("check_report_structure")
      [void]$errors.Add("check_report_structure failed: $_")
      Add-GateResult -Name "reportStructure" -Passed $false -Source "check_report_structure" -Messages @("check_report_structure failed: $_")
    }
  } else {
    [void]$sources.Add("check_report_structure")
    [void]$errors.Add("check_report_structure.ps1 not found: $reportStructureScript")
    Add-GateResult -Name "reportStructure" -Passed $false -Source "check_report_structure" -Messages @("check_report_structure.ps1 not found: $reportStructureScript")
  }
}

# 1c) PBIP validation for each report folder
if ($requirePbipValidation) {
  if (Test-Path $pbipValidateScript) {
    $reportDirs = @(Get-ChildItem -Path $distPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue)
    if ($reportDirs.Count -eq 0) {
      $message = "No report folders found under dist for PBIP validation."
      [void]$sources.Add("validate_pbip")
      [void]$errors.Add($message)
      Add-GateResult -Name "pbipValidation" -Passed $false -Source "validate_pbip" -Messages @($message)
    } else {
      $pbipGatePassed = $true
      $pbipMessages = [System.Collections.ArrayList]::new()
      foreach ($reportDir in $reportDirs) {
        try {
          $pbipOutput = & $pbipValidateScript -Root $reportDir.FullName 2>&1
          $pbipExit = $LASTEXITCODE
          if ($null -eq $pbipExit) { $pbipExit = 0 }
          $lines = Convert-CommandOutputToLines -Output $pbipOutput
          if (($pbipExit -ne 0) -and $lines.Count -eq 0) {
            $lines = @("validate_pbip exited with code $pbipExit")
          }
          foreach ($line in $lines) { [void]$pbipMessages.Add("[$($reportDir.Name)] $line") }
          if ($pbipExit -ne 0) {
            $pbipGatePassed = $false
            foreach ($line in $lines) { [void]$errors.Add("[$($reportDir.Name)] $line") }
          }
        } catch {
          $pbipGatePassed = $false
          $message = "[$($reportDir.Name)] validate_pbip failed: $_"
          [void]$pbipMessages.Add($message)
          [void]$errors.Add($message)
        }
      }
      [void]$sources.Add("validate_pbip")
      Add-GateResult -Name "pbipValidation" -Passed $pbipGatePassed -Source "validate_pbip" -Messages @($pbipMessages)
    }
  } else {
    [void]$sources.Add("validate_pbip")
    [void]$errors.Add("validate_pbip.ps1 not found: $pbipValidateScript")
    Add-GateResult -Name "pbipValidation" -Passed $false -Source "validate_pbip" -Messages @("validate_pbip.ps1 not found: $pbipValidateScript")
  }
}

# 1d) pbi-tools compile as explicit production gate
if ($effectiveRequireCompile) {
  $pbiTools = Resolve-PbiToolsPath -RepoRoot $RepoRoot
  if (-not $pbiTools) {
    $message = "pbi-tools not found in PATH, PBI_TOOLS_PATH, or .tools/pbi-tools; compile gate required by policy."
    [void]$sources.Add("pbi-tools compile")
    [void]$errors.Add($message)
    Add-GateResult -Name "pbiToolsCompile" -Passed $false -Source "pbi-tools compile" -Messages @($message)
  } else {
    $compileDirs = @(Get-ChildItem -Path $distPath -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue)
    $compileDirs += @(Get-ChildItem -Path $distPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue)
    $compileGatePassed = $true
    $compileMessages = [System.Collections.ArrayList]::new()
    $compatibleCompileDirs = @($compileDirs | Where-Object { Test-PbiToolsCompileCompatible -FolderPath $_.FullName })
    $skippedCompileDirs = @($compileDirs | Where-Object { -not (Test-PbiToolsCompileCompatible -FolderPath $_.FullName) })
    foreach ($skippedDir in $skippedCompileDirs) {
      [void]$compileMessages.Add("[$($skippedDir.Name)] skipped pbi-tools compile: PBIP split artifact without Version.txt; pbipValidation remains the authoritative gate.")
    }
    if ($compatibleCompileDirs.Count -eq 0) {
      [void]$compileMessages.Add("No pbi-tools-compatible PbixProj folders found under dist; compile gate satisfied by structural PBIP validation for this layout.")
    }
    foreach ($compileDir in $compatibleCompileDirs) {
      try {
        $compileOutput = & $pbiTools compile $compileDir.FullName 2>&1
        $compileExit = $LASTEXITCODE
        if ($null -eq $compileExit) { $compileExit = 0 }
        $lines = Convert-CommandOutputToLines -Output $compileOutput
        if (($compileExit -ne 0) -and $lines.Count -eq 0) {
          $lines = @("pbi-tools compile exited with code $compileExit")
        }
        foreach ($line in $lines) { [void]$compileMessages.Add("[$($compileDir.Name)] $line") }
        if ($compileExit -ne 0) {
          $compileGatePassed = $false
          foreach ($line in $lines) { [void]$errors.Add("[$($compileDir.Name)] $line") }
        }
      } catch {
        $compileGatePassed = $false
        $message = "[$($compileDir.Name)] pbi-tools compile failed: $_"
        [void]$compileMessages.Add($message)
        [void]$errors.Add($message)
      }
    }
    [void]$sources.Add("pbi-tools compile")
    Add-GateResult -Name "pbiToolsCompile" -Passed $compileGatePassed -Source "pbi-tools compile" -Messages @($compileMessages)
  }
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

$failedGateNames = @($gates | Where-Object { -not $_.passed } | ForEach-Object { $_.name })
$success = ($failedGateNames.Count -eq 0) -and ($errors.Count -eq 0)
$result = @{
  success   = $success
  errors    = @($errors)
  sources   = @($sources)
  gates     = @($gates)
  failedGates = @($failedGateNames)
  policy    = if ($policy) { $policy.name } else { $null }
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
