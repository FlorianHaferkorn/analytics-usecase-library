<#
.SYNOPSIS
  Syncs overrides.evidence_grain_note from UseCase_Bracket.yaml into the Business Factsheet (Section 6, ### Evidence grain).
.DESCRIPTION
  Run after adding or changing overrides.evidence_grain_note in a bracket (e.g. after migration or when adding a governance note).
  Scans core/usecases/core/*/ for UseCase_Bracket.yaml + Business_Factsheet.md; updates Section "## 6. Data Requirements Summary"
  with a "### Evidence grain" subsection containing the note. Idempotent: re-run safe.
.PARAMETER Root
  Repository root path. Default: resolve from script location.
.PARAMETER WhatIf
  Report what would be updated without writing files.
.PARAMETER ValidateOnly
  Same as WhatIf: report use cases that would be updated (for validate_factsheets.ps1 integration).
.EXAMPLE
  .\sync_evidence_grain_note_to_factsheet.ps1
  .\sync_evidence_grain_note_to_factsheet.ps1 -WhatIf
#>
Param(
  [string]$Root = "",
  [switch]$WhatIf,
  [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = $null

function Resolve-RepoPath {
  param([string]$ProvidedPath, [string]$DefaultRelative)
  $here = (Get-Location).Path
  if ($ProvidedPath -and (Test-Path $ProvidedPath)) { return (Resolve-Path -Path $ProvidedPath).Path }
  if ($ProvidedPath) {
    $candidate = Join-Path -Path $here -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $here -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

# Repo root: from script path (tooling/maintenance -> two levels up)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:RepoRoot = Resolve-Path -Path (Join-Path $scriptDir "..\..")
if ($Root) {
  $resolved = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative ""
  if ($resolved) { $script:RepoRoot = $resolved }
}

$useCasesCore = Join-Path $script:RepoRoot "core\usecases\core"
if (-not (Test-Path $useCasesCore)) {
  Write-Host "Use cases root not found: $useCasesCore" -ForegroundColor Yellow
  exit 0
}

function Get-EvidenceGrainNoteFromBracket {
  param([string]$BracketPath)
  $raw = Get-Content -Raw -Path $BracketPath -Encoding UTF8
  # Match overrides.evidence_grain_note: quoted on same line
  $quoted = [regex]::Match($raw, '(?ms)overrides:\s*\r?\n\s*evidence_grain_note:\s*"([^"]*)"')
  if ($quoted.Success) { return $quoted.Groups[1].Value.Trim() }
  $single = [regex]::Match($raw, "(?ms)overrides:\s*\r?\n\s*evidence_grain_note:\s*'([^']*)'")
  if ($single.Success) { return $single.Groups[1].Value.Trim() }
  # Block scalar: evidence_grain_note: >- or > or | then indented lines (stop when next line has <4 spaces)
  $block = [regex]::Match($raw, '(?ms)overrides:\s*\r?\n\s*evidence_grain_note:\s*>-?\s*\r?\n((?:\s{4,}[^\r\n]+\r?\n?)*?)(?=\r?\n(?!\s{4,}))')
  if ($block.Success) {
    $lines = $block.Groups[1].Value -split '\r?\n'
    $trimmed = $lines | ForEach-Object { $_.TrimStart() } | Where-Object { $_ -ne '' }
    return ($trimmed -join ' ').Trim()
  }
  $blockPipe = [regex]::Match($raw, '(?ms)overrides:\s*\r?\n\s*evidence_grain_note:\s*\|\s*\r?\n((?:\s{4,}[^\r\n]+\r?\n?)*?)(?=\r?\n(?!\s{4,}))')
  if ($blockPipe.Success) {
    $lines = $blockPipe.Groups[1].Value -split '\r?\n'
    $trimmed = $lines | ForEach-Object { $_.TrimStart() } | Where-Object { $_ -ne '' }
    return ($trimmed -join ' ').Trim()
  }
  return $null
}

function Test-FactsheetContainsNote {
  param([string]$FactsheetBody, [string]$Note)
  if (-not $Note -or $Note.Length -lt 20) { return $true }
  $sub = $Note.Substring(0, [Math]::Min(40, $Note.Length))
  return $FactsheetBody -match [regex]::Escape($sub)
}

function Update-FactsheetWithEvidenceGrain {
  param([string]$FactsheetPath, [string]$Note, [bool]$DryRun)
  $content = Get-Content -Raw -Path $FactsheetPath -Encoding UTF8
  $section6Marker = "## 6. Data Requirements Summary"
  $idx6 = $content.IndexOf($section6Marker)
  if ($idx6 -lt 0) { return $false }
  $after6 = $content.Substring($idx6)
  $evidenceHeading = "### Evidence grain"
  $hasHeading = $after6 -match [regex]::Escape($evidenceHeading)

  if ($hasHeading) {
    # Replace content under ### Evidence grain until next ### or ##; preserve --- before ## 7.
    $pattern = '(?ms)(### Evidence grain)\s*\r?\n\s*\r?\n?\s*.*?(?=\r?\n###|\r?\n---\s*\r?\n\s*## 7\.|\r?\n## 7\.|\r?\n## |\z)'
    $replacement = "`$1`r`n`r`n$Note`r`n`r`n---`r`n`r`n"
    $newAfter6 = [regex]::Replace($after6, $pattern, $replacement)
    if ($newAfter6 -eq $after6) { return $false }
    $newContent = $content.Substring(0, $idx6) + $newAfter6
  } else {
    # Insert ### Evidence grain + note before --- that precedes ## 7. (or before ## 7.)
    $insertBlock = "`r`n`r`n### Evidence grain`r`n`r`n$Note`r`n`r`n"
    $hrBefore7 = [regex]::Match($after6, '(?ms)\r?\n---\s*\r?\n\s*## 7\.')
    if ($hrBefore7.Success) {
      $pos = $hrBefore7.Index
      $newAfter6 = $after6.Substring(0, $pos) + $insertBlock + $after6.Substring($pos)
    } else {
      $hr7 = [regex]::Match($after6, '\r?\n(## 7\.)')
      if ($hr7.Success) {
        $pos = $hr7.Index
        $newAfter6 = $after6.Substring(0, $pos) + $insertBlock + $after6.Substring($pos)
      } else {
        $newAfter6 = $after6 + $insertBlock
      }
    }
    $newContent = $content.Substring(0, $idx6) + $newAfter6
  }

  if (-not $DryRun) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($FactsheetPath, $newContent, $utf8NoBom)
  }
  return $true
}

$wouldUpdate = @()
$dirs = Get-ChildItem -Path $useCasesCore -Directory -ErrorAction SilentlyContinue
foreach ($dir in $dirs) {
  $bracketPath = Join-Path $dir.FullName "UseCase_Bracket.yaml"
  $factsheetPath = Join-Path $dir.FullName "Business_Factsheet.md"
  if (-not (Test-Path $bracketPath) -or -not (Test-Path $factsheetPath)) { continue }
  $note = Get-EvidenceGrainNoteFromBracket -BracketPath $bracketPath
  if (-not $note) { continue }
  $ucId = $dir.Name -replace '_.*$', ''
  $body = Get-Content -Raw -Path $factsheetPath -Encoding UTF8
  $needsUpdate = $false
  if (-not (Test-FactsheetContainsNote -FactsheetBody $body -Note $note)) {
    $needsUpdate = $true
  } else {
    if ($body -notmatch '### Evidence grain') { $needsUpdate = $true }
    if (-not $needsUpdate) {
      $after = $body -replace '(?ms).*### Evidence grain\s*\r?\n\s*\r?\n\s*', ''
      $untilNext = $after -replace '(?ms)(.*?)(?=\r?\n###|\r?\n## |\z).*', '$1'
      # First paragraph only (ignore --- and trailing blank lines)
      $firstPara = ($untilNext.Trim() -split '\r?\n')[0].Trim()
      if ($firstPara -ne $note) { $needsUpdate = $true }
    }
  }
  if (-not $needsUpdate) { continue }
  $wouldUpdate += $ucId
  if ($WhatIf -or $ValidateOnly) {
    Write-Host "$ucId`: would add/update Evidence grain" -ForegroundColor Cyan
    continue
  }
  $updated = Update-FactsheetWithEvidenceGrain -FactsheetPath $factsheetPath -Note $note -DryRun $false
  if ($updated) { Write-Host "Updated: $($dir.Name) - Evidence grain synced." -ForegroundColor Green }
}

if ($ValidateOnly -and $wouldUpdate.Count -gt 0) {
  $wouldUpdate | ForEach-Object { Write-Host $_ }
}
if ($WhatIf -or $ValidateOnly) {
  if ($wouldUpdate.Count -eq 0) { exit 0 }
  exit 0
}
exit 0
