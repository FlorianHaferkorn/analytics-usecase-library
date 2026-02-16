param(
  [string]$MeasureDictRoot = (Join-Path $PSScriptRoot "..\..\..\semantic_models\domains"),
  [string]$GoldRoot = (Join-Path $PSScriptRoot "..\..\..\data_contracts\domains")
)

$ErrorActionPreference = "Stop"

function Get-GoldTables {
  param([string]$Root)
  $tables = @{}
  Get-ChildItem -Path $Root -Filter "*.yaml" | ForEach-Object {
    $currentTable = $null
    $inColumns = $false
    Get-Content $_.FullName | ForEach-Object {
      $line = $_.Trim()
      if ($line -match '^-\\s+name:\\s*([A-Za-z0-9_]+)\\s*$') {
        $currentTable = $Matches[1]
        if (-not $tables.ContainsKey($currentTable)) {
          $tables[$currentTable] = New-Object System.Collections.Generic.HashSet[string]
        }
        $inColumns = $false
        return
      }
      if ($line -eq 'columns:') { $inColumns = $true; return }
      if ($inColumns -and $currentTable) {
        if ($line -match '^-\\s*\\{name:\\s*([^,}]+)') {
          $col = $Matches[1].Trim()
          $tables[$currentTable].Add($col) | Out-Null
          return
        }
        if ($line -like 'qa:*') { $inColumns = $false; return }
      }
    }
  }
  return $tables
}

function Get-ColumnToTables {
  param($Tables)
  $map = @{}
  foreach ($t in $Tables.Keys) {
    foreach ($c in $Tables[$t]) {
      if (-not $map.ContainsKey($c)) { $map[$c] = New-Object System.Collections.Generic.HashSet[string] }
      $map[$c].Add($t) | Out-Null
    }
  }
  return $map
}

$goldTables = Get-GoldTables -Root $GoldRoot
$colToTables = Get-ColumnToTables -Tables $goldTables

$errors = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

Get-ChildItem -Path $MeasureDictRoot -Recurse -Filter "Measure_Dictionary_*.md" | Where-Object {
  $_.FullName -notmatch '\\internal\\archive\\'
} | ForEach-Object {
  $text = Get-Content $_.FullName -Raw
  $refs = New-Object System.Collections.Generic.HashSet[string]

  foreach ($m in [regex]::Matches($text, "(fact|dim)_[A-Za-z0-9_]+\\[[^\\]]+\\]", [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
    $token = $m.Value
    $table = $token.Split('[')[0].Trim()
    $col = $token.Substring($token.IndexOf('[') + 1).TrimEnd(']').Trim()
    $refs.Add("$table|||$col") | Out-Null
  }

  foreach ($m in [regex]::Matches($text, "(fact|dim)_[A-Za-z0-9_]+\\.[A-Za-z0-9 _%/\\-]+", [Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
    $token = $m.Value
    $parts = $token.Split('.', 2)
    $table = $parts[0].Trim()
    $col = $parts[1].Trim().Trim('"').Trim("'").TrimEnd(')').Trim()
    $refs.Add("$table|||$col") | Out-Null
  }

  foreach ($ref in $refs) {
    $parts = $ref -split '\\|\\|\\|'
    $table = $parts[0]
    $col = $parts[1]
    if (-not $goldTables.ContainsKey($table)) {
      $errors.Add("$($_.Name): $table not found in gold contracts") | Out-Null
      continue
    }
    if (-not $goldTables[$table].Contains($col)) {
      if ($colToTables.ContainsKey($col)) {
        $alt = ($colToTables[$col] | Sort-Object) -join ', '
        $warnings.Add("$($_.Name): $table[$col] missing; column exists in: $alt") | Out-Null
      } else {
        $errors.Add("$($_.Name): $table[$col] not found in gold contracts") | Out-Null
      }
    }
  }
}

Write-Host "Measure Dictionary -> Gold Data Contracts consistency"

if ($warnings.Count -gt 0) {
  Write-Host "Warnings (possible mapping needed):"
  $warnings | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($errors.Count -eq 0) {
  Write-Host "OK: all referenced tables/columns exist in gold contracts."
  exit 0
}

Write-Host "Errors:"
$errors | Sort-Object | ForEach-Object { Write-Host "  - $_" }
exit 1
