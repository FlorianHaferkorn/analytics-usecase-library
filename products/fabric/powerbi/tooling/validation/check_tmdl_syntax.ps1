<#
.SYNOPSIS
  Validates TMDL files for syntax best practices (tabs-only indentation, no description property).
.DESCRIPTION
  Scans .tmdl files under DistRoot for: (1) indentation using spaces instead of tabs; (2) forbidden "description:" property.
  Sources: products/fabric/powerbi/docs/tmdl_best_practices.md, Microsoft Learn TMDL overview.
.PARAMETER DistRoot
  Root path to search for .tmdl files (e.g. products/fabric/powerbi/dist or a PBIP definition folder).
#>
Param(
  [string]$DistRoot = "products/fabric/powerbi/dist"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$distResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }

if (-not (Test-Path $distResolved)) {
  Write-Host "DistRoot not found: $distResolved. Skipping TMDL syntax check." -ForegroundColor Yellow
  exit 0
}

$tmdlFiles = Get-ChildItem -Path $distResolved -Recurse -Filter "*.tmdl" -ErrorAction SilentlyContinue | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
}
if (-not $tmdlFiles -or $tmdlFiles.Count -eq 0) {
  Write-Host "No .tmdl files under DistRoot. Skipping TMDL syntax check." -ForegroundColor Yellow
  exit 0
}

$errors = @()

foreach ($f in $tmdlFiles) {
  $relPath = $f.FullName.Replace($distResolved, "").TrimStart([System.IO.Path]::DirectorySeparatorChar)
  $lines = Get-Content -Path $f.FullName -ErrorAction SilentlyContinue
  $lineNum = 0
  $currentObjectIndent = $null
  foreach ($line in $lines) {
    $lineNum++
    if ($line -match '^\s*$' -or $line -match '^\s*///') {
      continue
    }

    if ($line -match '^(\t*)(table|column|partition|measure|hierarchy|level|annotation)\b') {
      $currentObjectIndent = $matches[1].Length
    } elseif ($null -ne $currentObjectIndent -and $line -match '^(\t*)([^\s].*?)(:|\s*=)') {
      $propertyIndent = $matches[1].Length
      if ($propertyIndent -le $currentObjectIndent) {
        $errors += [PSCustomObject]@{ File = $relPath; Line = $lineNum; Rule = "tmdl.indent.child_scope"; Message = "Child properties must be indented deeper than their parent object; Desktop otherwise fails with invalid indentation." }
      }
    }

    # Forbidden: description property (TMDL does not support it; use /// comments)
    if ($line -match '^\s*description\s*:') {
      $errors += [PSCustomObject]@{ File = $relPath; Line = $lineNum; Rule = "tmdl.description.forbidden"; Message = "Property 'description:' is not supported; use /// comments above the object." }
    }
    # Forbidden: spaces used for indentation (TMDL requires tabs only)
    $leading = $line -replace '^(\s*).*', '$1'
    if ($leading -and $leading.Length -gt 0 -and $leading -match ' ') {
      $errors += [PSCustomObject]@{ File = $relPath; Line = $lineNum; Rule = "tmdl.indent.tabs_only"; Message = "Use TABs only for indentation; spaces cause parser errors." }
    }
  }
}

# ── M-expression vs table name collision ─────────────────────────────────────
# If an M shared expression and a table share the same name, Desktop fails:
# "Microsoft.Data.Mashup.Preview; This document contains a duplicate member '<name>'."
# This is a silent-blocker class error with no helpful error message in Desktop.
$defDirsForCollision = @()
if (Test-Path $distResolved) {
  $defDirsForCollision = @(Get-ChildItem -Path $distResolved -Recurse -Directory -Filter "definition" -ErrorAction SilentlyContinue | Where-Object {
    Test-Path (Join-Path $_.FullName "tables")
  } | Select-Object -ExpandProperty FullName)
}
foreach ($defDir in $defDirsForCollision) {
  $expressionsFile = Join-Path $defDir "expressions.tmdl"
  $tablesDir       = Join-Path $defDir "tables"
  $expressionNames = @{}
  $tableNames      = @{}
  $relBase         = $defDir.Replace($distResolved, "").TrimStart([System.IO.Path]::DirectorySeparatorChar)

  if (Test-Path $expressionsFile) {
    $content = Get-Content -Path $expressionsFile -Raw
    # Handles: expression Name =, expression 'Name' =, expression #"Name" =
    $exprRe = [regex]"(?m)^\s*expression\s+(?:'([^']+)'|#`"([^`"]+)`"|([A-Za-z0-9_\- ]+))\s*="
    foreach ($m in $exprRe.Matches($content)) {
      $name = ($m.Groups[1].Value + $m.Groups[2].Value + $m.Groups[3].Value).Trim()
      if ($name) { $expressionNames[$name] = $true }
    }
  }
  if (Test-Path $tablesDir) {
    Get-ChildItem -Path $tablesDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | ForEach-Object {
      $raw = Get-Content -Path $_.FullName -TotalCount 10 -ErrorAction SilentlyContinue
      foreach ($line in $raw) {
        $tableRe = [regex]"^\s*table\s+(?:'([^']+)'|#`"([^`"]+)`"|([A-Za-z0-9_\-]+))\s*$"
        $tm = $tableRe.Match($line)
        if ($tm.Success) {
          $name = ($tm.Groups[1].Value + $tm.Groups[2].Value + $tm.Groups[3].Value).Trim()
          if ($name) { $tableNames[$name] = $_.Name }
        }
      }
    }
  }
  foreach ($name in $expressionNames.Keys) {
    if ($tableNames.ContainsKey($name)) {
      $errors += [PSCustomObject]@{
        File    = "$relBase/expressions.tmdl"
        Line    = 0
        Rule    = "tmdl.m_table_name_collision"
        Message = "M expression '$name' shares its name with table '$($tableNames[$name])'. Desktop fails with 'duplicate member'. Rename the M expression (e.g. append ' Query' or ' Source')."
      }
    }
  }
}

if ($errors.Count -gt 0) {
  foreach ($e in $errors) {
    Write-Host "$($e.File):$($e.Line) [ERROR] $($e.Rule) - $($e.Message)" -ForegroundColor Red
  }
  Write-Host "TMDL syntax: $($errors.Count) error(s)." -ForegroundColor Red
  exit 1
}
Write-Host "TMDL syntax check passed (tabs only, no description property, no M/table name collisions)." -ForegroundColor Green
exit 0
