<#
.SYNOPSIS
  Proactive action-code content audit: duplicate display names and optional consistency checks.
.DESCRIPTION
  Scans core/action_codes (excluding decision_spines) for duplicate 'name' (display name)
  across different action code IDs. Same pattern as audit_ssot_content.ps1; report-only by default.
.PARAMETER ActionCodesRoot
  Path to core/action_codes.
.PARAMETER OutputDir
  Directory for report files (default: tooling/validation/results).
.PARAMETER FailOnFinding
  If set, exit 1 when any finding exists (for strict CI).
#>
Param(
  [string]$ActionCodesRoot = "core/action_codes",
  [string]$OutputDir = "",
  [switch]$FailOnFinding
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = if ($PSScriptRoot) {
  (Get-Item $PSScriptRoot).Parent.Parent.FullName
} else {
  (Get-Location).Path
}

function Resolve-RepoPath {
  param([string]$ProvidedPath, [string]$DefaultRelative)
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$actionRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "core/action_codes"
if (-not $actionRoot) { throw "Action codes root not found. Use -ActionCodesRoot or run from repo." }

$outDir = if ($OutputDir) {
  $resolved = Resolve-RepoPath -ProvidedPath $OutputDir -DefaultRelative $null
  if ($resolved) { $resolved } else { Join-Path $script:RepoRoot $OutputDir }
} else {
  Join-Path $script:RepoRoot "tooling\validation\results"
}
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# Collect id -> name from action code YAML (exclude decision_spines and map file)
$actions = @()
Get-ChildItem -Path $actionRoot -Recurse -Filter "*.yaml" | Where-Object {
  $_.FullName -notmatch '\\decision_spines\\' -and $_.Name -ne 'DecisionSpine_UseCase_Map.yaml'
} | ForEach-Object {
  $content = Get-Content -Raw -Path $_.FullName
  $id = $null
  $name = $null
  foreach ($line in ($content -split "`n")) {
    if ($line -match '^\s*id\s*:\s*(.+)') { $id = $matches[1].Trim().Trim('"').Trim("'") }
    if ($line -match '^\s*name\s*:\s*(.+)') { $name = $matches[1].Trim().Trim('"').Trim("'"); break }
  }
  if ($id -and $name) {
    $actions += [pscustomobject]@{ id = $id; name = $name; file = $_.FullName.Replace($script:RepoRoot + [IO.Path]::DirectorySeparatorChar, '') }
  }
}

# Duplicate display name
$byName = @{}
foreach ($a in $actions) {
  $n = $a.name.Trim()
  if (-not $byName[$n]) { $byName[$n] = @() }
  $byName[$n] += $a
}

$findings = @()
foreach ($n in $byName.Keys) {
  $list = $byName[$n]
  if ($list.Count -gt 1) {
    $ids = ($list | ForEach-Object { $_.id }) -join ', '
    $findings += [pscustomobject]@{
      Severity  = 'Warning'
      Rule      = 'ActionCode.duplicate_display_name'
      Message   = "Display name '$n' used by multiple action codes: $ids. UI/reports may be ambiguous."
      Location  = $n
      Remediation = "Use distinct names per action code (e.g. prefix with domain or outcome)."
    }
  }
}

# Report
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$reportPath = Join-Path $outDir "action_codes_audit_$timestamp.md"
$jsonPath = Join-Path $outDir "action_codes_audit_$timestamp.json"

$md = @"
# Action Codes Content Audit Report
Generated: $(Get-Date -Format 'o')
Source: $actionRoot (excluding decision_spines)
Findings: $($findings.Count)

## Summary
- **Duplicate display name (name):** $($findings.Count)

## Findings
"@
foreach ($f in $findings) {
  $md += "`n### [$($f.Severity)] $($f.Rule)`n$($f.Message)`n- **Remediation:** $($f.Remediation)`n"
}
if ($findings.Count -eq 0) {
  $md += "`nNo issues found.`n"
}
$md | Set-Content -Path $reportPath -Encoding UTF8

$findings | ConvertTo-Json -Depth 3 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host "Action codes content audit: $($findings.Count) finding(s). Report: $reportPath" -ForegroundColor $(if ($findings.Count -eq 0) { 'Green' } else { 'Yellow' })
foreach ($f in $findings) {
  Write-Host "  [$($f.Severity)] $($f.Rule): $($f.Message)" -ForegroundColor Gray
}

if ($FailOnFinding -and $findings.Count -gt 0) { exit 1 }
exit 0
