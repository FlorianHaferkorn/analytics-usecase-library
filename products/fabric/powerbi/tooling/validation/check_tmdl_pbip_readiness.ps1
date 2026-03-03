<#
.SYNOPSIS
  Validates TMDL for PBIP load readiness: duplicate relationship IDs, duplicate measures, RLS behavior, data source parameterization.
.DESCRIPTION
  Ensures previously fixed issues do not recur: (1) duplicate relationship GUIDs/names,
  (2) relationship fromColumn/toColumn use dot-quoted form (table.''Col''), not bracket (table[''Col'']),
  (3) RLS relationships use securityFilteringBehavior: oneDirection,
  (4) duplicate measure names in _Measures.tmdl,
  (5) all numeric columns (int64, int32, double, decimal) have summarizeBy: none to prevent unintentional summarization,
  (6) table partition Source uses a parameter (e.g. GoldDataPath) instead of hardcoded paths.
  Run from repository root. DistRoot can be a tables dir (e.g. .../definition/tables) or dist root.
.PARAMETER DistRoot
  Root path: either .../definition/tables (single semantic model) or products/fabric/powerbi/dist (multiple).
#>
Param(
  [string]$DistRoot = "products/fabric/powerbi/dist"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$rootResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot ($DistRoot -replace '/', [System.IO.Path]::DirectorySeparatorChar) }

if (-not (Test-Path $rootResolved)) {
  Write-Host "DistRoot not found: $rootResolved. Skipping PBIP readiness check." -ForegroundColor Yellow
  exit 0
}

# Resolve definition folder(s): one if root is .../tables, else all .../definition under root
$definitionDirs = @()
if ((Get-Item $rootResolved).Name -eq "tables" -and (Test-Path (Join-Path $rootResolved "_Measures.tmdl"))) {
  $definitionDirs = @((Resolve-Path (Join-Path $rootResolved "..")).Path)
} else {
  $defDirs = Get-ChildItem -Path $rootResolved -Recurse -Directory -Filter "definition" -ErrorAction SilentlyContinue | Where-Object {
    Test-Path (Join-Path $_.FullName "tables")
  }
  $definitionDirs = @($defDirs | ForEach-Object { $_.FullName })
}

if ($definitionDirs.Count -eq 0) {
  Write-Host "No semantic model definition folder found under $rootResolved. Skipping PBIP readiness check." -ForegroundColor Yellow
  exit 0
}

$errors = @()
$relIdPattern = [regex]'(?m)^relationship\s+([^\s\r\n]+)'
$measureNamePattern = [regex]"(?m)^\s*measure\s+'([^']+)'\s*="
$securityFilterPattern = [regex]'securityFilteringBehavior\s*:\s*(\w+)'
$folderFilesPattern = [regex]'Folder\.Files\s*\(\s*([^)]+)\s*\)'

foreach ($defDir in $definitionDirs) {
  $relPathBase = $defDir.Replace($repoRoot, "").TrimStart([System.IO.Path]::DirectorySeparatorChar)
  $tablesDir = Join-Path $defDir "tables"
  $relationshipsFile = Join-Path $defDir "relationships.tmdl"
  $relationshipsDir = Join-Path $defDir "relationships"

  # --- 1) Duplicate relationship IDs ---
  $allRelIds = @()
  if (Test-Path $relationshipsFile) {
    $content = Get-Content -Path $relationshipsFile -Raw
    foreach ($m in $relIdPattern.Matches($content)) { $allRelIds += $m.Groups[1].Value }
  }
  if (Test-Path $relationshipsDir) {
    Get-ChildItem -Path $relationshipsDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | ForEach-Object {
      $content = Get-Content -Path $_.FullName -Raw
      foreach ($m in $relIdPattern.Matches($content)) { $allRelIds += $m.Groups[1].Value }
    }
  }
  $dupRels = $allRelIds | Group-Object | Where-Object { $_.Count -gt 1 }
  foreach ($g in $dupRels) {
    $errors += [PSCustomObject]@{ File = "$relPathBase (relationships)"; Line = 0; Rule = "pbip.relationship.duplicate_id"; Message = "Duplicate relationship ID: $($g.Name)" }
  }

  # --- 2) Relationship columns: no bracket notation; use dot-quoted (table.'Column Name') ---
  $relColBracketPattern = [regex]'(?m)^\s*(fromColumn|toColumn)\s*:\s*[^\r\n]*\[\s*''[^'']+''\s*\]'
  $relFilesToScan = @()
  if (Test-Path $relationshipsFile) { $relFilesToScan += $relationshipsFile }
  if (Test-Path $relationshipsDir) {
    $relFilesToScan += @(Get-ChildItem -Path $relationshipsDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  }
  foreach ($rf in $relFilesToScan) {
    $content = Get-Content -Path $rf -Raw
    $fname = if ($rf -eq $relationshipsFile) { "$relPathBase/relationships.tmdl" } else { "$relPathBase/relationships/$(Split-Path -Leaf $rf)" }
    foreach ($m in $relColBracketPattern.Matches($content)) {
      $errors += [PSCustomObject]@{ File = $fname; Line = 0; Rule = "pbip.relationship.column_bracket"; Message = "Relationship column must use dot-quoted form (e.g. table.''Column Name''), not bracket form (table[''Column Name'']): $($m.Value.Trim())" }
    }
  }

  # --- 3) RLS: security relationships must use oneDirection ---
  $securityRelFiles = @()
  if (Test-Path $relationshipsDir) {
    $securityRelFiles = @(Get-ChildItem -Path $relationshipsDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^security_' })
  }
  foreach ($rf in $securityRelFiles) {
    $content = Get-Content -Path $rf.FullName -Raw
    $sfMatch = $securityFilterPattern.Match($content)
    if ($sfMatch.Success -and $sfMatch.Groups[1].Value -ne "oneDirection") {
      $errors += [PSCustomObject]@{ File = (Join-Path $relPathBase "relationships\$($rf.Name)"); Line = 0; Rule = "pbip.rls.one_direction"; Message = "RLS relationship must use securityFilteringBehavior: oneDirection (found: $($sfMatch.Groups[1].Value))" }
    }
  }
  # Monolith relationships.tmdl: security_* relationship blocks must have securityFilteringBehavior: oneDirection
  if (Test-Path $relationshipsFile) {
    $content = Get-Content -Path $relationshipsFile -Raw
    $securityBlockPattern = [regex]'(?ms)^relationship\s+(security_\S+)\s*$(.*?)(?=^relationship\s|\z)'
    foreach ($m in $securityBlockPattern.Matches($content)) {
      $relName = $m.Groups[1].Value
      $block = $m.Groups[2].Value
      $sfMatch = $securityFilterPattern.Match($block)
      if (-not $sfMatch.Success) {
        $errors += [PSCustomObject]@{ File = "$relPathBase/relationships.tmdl"; Line = 0; Rule = "pbip.rls.one_direction"; Message = "RLS relationship '$relName' must have securityFilteringBehavior: oneDirection (missing)" }
      } elseif ($sfMatch.Groups[1].Value -ne "oneDirection") {
        $errors += [PSCustomObject]@{ File = "$relPathBase/relationships.tmdl"; Line = 0; Rule = "pbip.rls.one_direction"; Message = "RLS relationship '$relName' must use securityFilteringBehavior: oneDirection (found: $($sfMatch.Groups[1].Value))" }
      }
    }
  }

  # --- 4) Duplicate measure names (in _Measures.tmdl and any .tmdl under tables) ---
  $allMeasureNames = @()
  if (Test-Path $tablesDir) {
    Get-ChildItem -Path $tablesDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | ForEach-Object {
      $content = Get-Content -Path $_.FullName -Raw
      foreach ($m in $measureNamePattern.Matches($content)) { $allMeasureNames += $m.Groups[1].Value }
    }
  }
  $dupMeasures = $allMeasureNames | Group-Object | Where-Object { $_.Count -gt 1 }
  foreach ($g in $dupMeasures) {
    $errors += [PSCustomObject]@{ File = "$relPathBase/tables"; Line = 0; Rule = "pbip.measure.duplicate_name"; Message = "Duplicate measure name: '$($g.Name)'" }
  }

  # --- 5) Numeric columns: all summarizable types (Int64, Decimal, Double, etc.) must have summarizeBy: none ---
  $numericDataTypePattern = [regex]'(?mi)^\s*dataType:\s*(int64|int32|double|decimal)'
  $summarizeByPattern = [regex]'(?m)^\s*summarizeBy:\s*none'
  $columnPattern = [regex]'(?m)^\s*column\s+([^\s\r\n]+)'
  if (Test-Path $tablesDir) {
    Get-ChildItem -Path $tablesDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | ForEach-Object {
      $content = Get-Content -Path $_.FullName -Raw
      $lines = $content -split "`r?`n"
      $currentColumn = $null
      $currentDataType = $null
      $hasSummarizeBy = $false
      $inColumnBlock = $false
      $columnStartLine = 0
      
      for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $indentLevel = 0
        if ($line -match '^(\t+)') {
          $indentLevel = $matches[1].Length
        }
        
        # Detect column start (1 tab indent)
        $colMatch = $columnPattern.Match($line)
        if ($colMatch.Success -and $indentLevel -eq 1) {
          # Check previous column if we were in one
          if ($inColumnBlock -and $currentColumn -and $currentDataType -and -not $hasSummarizeBy) {
            $errors += [PSCustomObject]@{ File = "$relPathBase/tables/$($_.Name)"; Line = $columnStartLine + 1; Rule = "pbip.column.summarize_by_none"; Message = "Numeric column '$currentColumn' (dataType: $currentDataType) must have 'summarizeBy: none' to prevent unintentional summarization" }
          }
          $currentColumn = $colMatch.Groups[1].Value.Trim("'")
          $currentDataType = $null
          $hasSummarizeBy = $false
          $inColumnBlock = $true
          $columnStartLine = $i
          continue
        }
        
        if ($inColumnBlock) {
          # Check for dataType (2 tabs indent)
          $dtMatch = $numericDataTypePattern.Match($line)
          if ($dtMatch.Success -and $indentLevel -eq 2) {
            $currentDataType = $dtMatch.Groups[1].Value
          }
          # Check for summarizeBy: none (2 tabs indent)
          if ($summarizeByPattern.Match($line).Success -and $indentLevel -eq 2) {
            $hasSummarizeBy = $true
          }
          # Detect end of column block: next top-level element (1 tab) that's not a column property
          if ($indentLevel -eq 1 -and ($line -match '^\t(column|measure|partition|hierarchy|table)\s+' -or $line -match '^\t///')) {
            # Check current column before moving on
            if ($currentDataType -and -not $hasSummarizeBy) {
              $errors += [PSCustomObject]@{ File = "$relPathBase/tables/$($_.Name)"; Line = $columnStartLine + 1; Rule = "pbip.column.summarize_by_none"; Message = "Numeric column '$currentColumn' (dataType: $currentDataType) must have 'summarizeBy: none' to prevent unintentional summarization" }
            }
            $inColumnBlock = $false
            $currentColumn = $null
            $currentDataType = $null
            $hasSummarizeBy = $false
            # If this is a new column, process it
            if ($line -match '^\tcolumn\s+') {
              $i--  # Re-process this line as column start
            }
          }
        }
      }
      # Check last column if file ends with a column block
      if ($inColumnBlock -and $currentColumn -and $currentDataType -and -not $hasSummarizeBy) {
        $errors += [PSCustomObject]@{ File = "$relPathBase/tables/$($_.Name)"; Line = $columnStartLine + 1; Rule = "pbip.column.summarize_by_none"; Message = "Numeric column '$currentColumn' (dataType: $currentDataType) must have 'summarizeBy: none' to prevent unintentional summarization" }
      }
    }
  }

  # --- 6) Partition Source: Folder.Files must use parameter (GoldDataPath or similar), not hardcoded path ---
  if (Test-Path $tablesDir) {
    Get-ChildItem -Path $tablesDir -Filter "*.tmdl" -ErrorAction SilentlyContinue | ForEach-Object {
      $content = Get-Content -Path $_.FullName -Raw
      $folderMatches = $folderFilesPattern.Matches($content)
      foreach ($fm in $folderMatches) {
        $arg = $fm.Groups[1].Value.Trim()
        # Parameterized: contains GoldDataPath or ampersand + quote (e.g. GoldDataPath & "/facts/...")
        if ($arg -match 'GoldDataPath' -or $arg -match '&\s*"' -or $arg -match "&\s*'") { continue }
        # Hardcoded: argument is a single quoted path (e.g. "C:/foo" or '..\gold\facts')
        $isQuotedPath = ($arg -match '^"[^"]*"\s*$' -or $arg -match '^''[^'']*''\s*$') -and $arg -match '[/\\]'
        if ($isQuotedPath) {
          $snip = if ($arg.Length -gt 55) { $arg.Substring(0, 52) + "..." } else { $arg }
          $errors += [PSCustomObject]@{ File = "$relPathBase/tables/$($_.Name)"; Line = 0; Rule = "pbip.partition.hardcoded_path"; Message = ("Partition Source must use a parameter (e.g. GoldDataPath and path), not hardcoded path: " + $snip) }
        }
      }
    }
  }
}

if ($errors.Count -gt 0) {
  foreach ($e in $errors) {
    $loc = if ($e.Line -gt 0) { "$($e.File):$($e.Line)" } else { $e.File }
    Write-Host "$loc [ERROR] $($e.Rule) - $($e.Message)" -ForegroundColor Red
  }
  Write-Host "PBIP readiness: $($errors.Count) error(s)." -ForegroundColor Red
  exit 1
}
Write-Host "PBIP readiness check passed (relationships, measures, RLS, summarizeBy, partition paths)." -ForegroundColor Green
exit 0
