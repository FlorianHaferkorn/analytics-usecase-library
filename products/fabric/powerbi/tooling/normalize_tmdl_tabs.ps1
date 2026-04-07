<#
.SYNOPSIS
  Proaktive Tab-Normalisierung aller TMDL-Dateien unter DistRoot (Spaces -> Tabs).
.DESCRIPTION
  Rekursiv alle .tmdl unter DistRoot finden und führende Leerzeichen durch Tabs ersetzen.
  Keine Validierung, nur Normalisierung. Wird in Phase 6 vor ensure_pbip und PatchAddSummarizeByNone aufgerufen.
.PARAMETER DistRoot
  Root path (e.g. products/fabric/powerbi/dist). Relative to RepoRoot if not rooted.
.PARAMETER RepoRoot
  Repository root. Default: derived from script path.
.EXAMPLE
  .\normalize_tmdl_tabs.ps1
  .\normalize_tmdl_tabs.ps1 -DistRoot products/fabric/powerbi/dist -RepoRoot C:\repo
#>
param(
  [string]$DistRoot = "products/fabric/powerbi/dist",
  [string]$RepoRoot = $null
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path $PSCommandPath -Parent
if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $scriptDir "..\..\..\..")).Path
}
$distResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) {
  $DistRoot
} else {
  Join-Path $RepoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar)
}

function Convert-LeadingSpacesToTabs {
  param([string]$Leading)
  if ($Leading -notmatch ' ') { return $Leading }
  $tabCount = [math]::Floor($Leading.Length / 4)
  if ($Leading.Length % 4 -gt 0) { $tabCount += 1 }
  if ($tabCount -eq 0) { $tabCount = 1 }
  return "`t" * $tabCount
}

function Repair-TableTmdlIndentation {
  param([string[]]$Lines)

  $tableLineIndex = -1
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match '^table\s+') {
      $tableLineIndex = $i
      break
    }
  }
  if ($tableLineIndex -lt 0) { return $Lines }

  $firstIndentedIndex = -1
  for ($i = $tableLineIndex + 1; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i].Trim().Length -eq 0) { continue }
    $firstIndentedIndex = $i
    break
  }
  if ($firstIndentedIndex -lt 0) { return $Lines }

  $fixed = @()
  $inExpressionBlock = $false
  $sourceIndent = -1
  foreach ($line in $Lines) {
    if ($line -match '^\t{2,}(lineageTag:|column\s|partition\s|annotation\s|measure\s|hierarchy\s|level\s)') {
      $fixed += ($line -replace '^\t', '')
      continue
    }

    if ($line -cmatch '^\t{2,}source\s*=') {
      $updatedLine = if ($line -cmatch '^\t{3,}source\s*=') { ($line -replace '^\t', '') } else { $line }
      $fixed += $updatedLine
      $inExpressionBlock = $true
      $sourceIndent = ([regex]::Match($updatedLine,'^\t*').Value.Length)
      continue
    }

    if ($line -match '^\t{3,}(dataType:|sourceColumn:|summarizeBy:|isHidden\b|formatString:|displayFolder:|mode:|entityName:|schemaName:|expressionSource:|description:|annotation\s)') {
      $updatedLine = ($line -replace '^\t', '')
      $fixed += $updatedLine
      continue
    }

    if ($inExpressionBlock -and $line.Trim().Length -gt 0) {
      $trimmed = $line.Trim()
      if ($trimmed -eq 'let') {
        $updatedLine = (("`t" * ($sourceIndent + 1)) + 'let')
      } elseif ($trimmed -eq 'in') {
        $updatedLine = (("`t" * ($sourceIndent + 1)) + 'in')
      } else {
        $updatedLine = (("`t" * ($sourceIndent + 2)) + $trimmed)
      }
      $fixed += $updatedLine
      continue
    }

    $fixed += $line

    if ($inExpressionBlock -and $line.Trim().Length -eq 0) {
      $inExpressionBlock = $false
      $sourceIndent = -1
    }
  }

  return $fixed
}

function Set-TmdlFileTabs {
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
  $fixed = Repair-TableTmdlIndentation -Lines $fixed
  $newContent = $fixed -join "`n"
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($FilePath, $newContent, $utf8)
}

if (-not (Test-Path $distResolved)) {
  Write-Host "DistRoot not found: $distResolved" -ForegroundColor Yellow
  exit 0
}

$tmdlFiles = Get-ChildItem -Path $distResolved -Recurse -Filter "*.tmdl" -File -ErrorAction SilentlyContinue | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
}
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No .tmdl files under $distResolved" -ForegroundColor Gray
  exit 0
}

$count = 0
foreach ($f in $tmdlFiles) {
  Set-TmdlFileTabs -FilePath $f.FullName
  $count++
}
Write-Host "  Normalized $count TMDL file(s) to tabs: $distResolved" -ForegroundColor Green
exit 0
