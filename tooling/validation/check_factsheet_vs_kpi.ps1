Param(
  [string]$UseCasesRoot,
  [string]$KpiCatalogRoot,
  [switch]$FailOnMissing
)

$ScriptToolsRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptToolsRoot

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $relativeCandidate = Join-Path -Path $RepoRoot -ChildPath $ProvidedPath
    if (Test-Path $relativeCandidate) { return (Resolve-Path -Path $relativeCandidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$UseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $UseCasesRoot) { throw "Unable to resolve UseCases root folder. Provide -UseCasesRoot or run inside repository." }

$KpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
if (-not $KpiCatalogRoot) { throw "Unable to resolve KPI catalog folder. Provide -KpiCatalogRoot or run inside repository." }

function Get-FrontMatter {
  param([string]$Path,[int]$Depth = 0)
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---\s")
  if (-not $m.Success) { return $null }
  $frontMatter = $m.Groups[1].Value
  $pointer = [regex]::Match($frontMatter, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $target = Join-Path -Path (Split-Path -Parent $Path) -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      return Get-FrontMatter -Path $target -Depth ($Depth + 1)
    }
  }
  return $frontMatter
}

function Get-ListFromFrontMatter {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if ($inline.Success) {
    $items = @()
    foreach ($mm in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($mm.Groups[1].Success) { $mm.Groups[1].Value }
               elseif ($mm.Groups[2].Success) { $mm.Groups[2].Value }
               else { $mm.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    $out = @()
    foreach ($line in ($block.Groups['body'].Value -split "\r?\n")) {
      $trimmed = $line.Trim()
      if (-not $trimmed) { continue }
      if ($trimmed -match '^\s*-\s*(.*)$') {
        $value = $matches[1].Trim()
      } else {
        continue
      }
      if (-not $value) { continue }
      if ($value -match '^(?<val>[^#]+)\s*(#.*)?$') { $value = $matches['val'].TrimEnd() }
      if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Trim('"')
      } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Trim("'")
      }
      if ($value) { $out += $value }
    }
    return $out
  }
  return @()
}

function Get-RequiredMeasuresFromFrontMatter {
  param([string]$FrontMatter)
  return (Get-ListFromFrontMatter -FrontMatter $FrontMatter -Field 'required_measures' |
    Where-Object { $_ -and $_.Trim().Length -gt 0 } | Sort-Object -Unique)
}

function Get-RequiredIdsFromFrontMatter {
  param([string]$FrontMatter)
  return (Get-ListFromFrontMatter -FrontMatter $FrontMatter -Field 'required_kpi_ids' |
    Where-Object { $_ -and $_.Trim().Length -gt 0 } | Sort-Object -Unique)
}

function Get-RequiredIdsFromBody {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $m = [regex]::Match($content, "(?ms)^---\s*\r?\n.*?\r?\n---\s*")
  $body = if ($m.Success) { $content.Substring($m.Length) } else { $content }
  $ids = New-Object System.Collections.Generic.List[string]
  foreach ($line in ($body -split "\r?\n")) {
    if ($line -match '^\s*-\s*(?:id|kpi_id)\s*:\s*([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)') {
      $ids.Add($matches[1])
    }
  }
  return $ids | Sort-Object -Unique
}

function Get-KpiIdsFromUseCaseBracket {
  param([string]$FactsheetPath)
  $dir = Split-Path -Parent $FactsheetPath
  $bracket = Join-Path -Path $dir -ChildPath "UseCase_Bracket.yaml"
  if (-not (Test-Path $bracket)) { return @() }
  $lines = Get-Content -Path $bracket
  $ids = New-Object System.Collections.Generic.List[string]

  foreach ($ln in $lines) {
    if ($ln -match '^\s*strategic_kpi_id\s*:\s*"?([^"\s#]+)"?') {
      $ids.Add($matches[1]) | Out-Null
    }
  }

  $inInfluencing = $false
  foreach ($ln in $lines) {
    if ($ln -match '^\s*influencing_kpi_ids\s*:\s*$') { $inInfluencing = $true; continue }
    if ($inInfluencing) {
      if ($ln.Trim().Length -eq 0) { continue }
      if ($ln -notmatch '^\s{2,}-\s*"?([^"\s#]+)"?') { break }
      $ids.Add($matches[1]) | Out-Null
    }
  }

  return $ids | Where-Object { $_ -and $_.Trim().Length -gt 0 } | Sort-Object -Unique
}

function Load-KpiCatalogIndex {
  param([string]$Root)
  $index = New-Object System.Collections.Generic.List[string]
  $names = @{}
  Get-ChildItem -Path $Root -Filter '*.md' | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    $matches = [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')
    foreach ($m in $matches) {
      $block = $m.Groups[1].Value
      $idMatch = [regex]::Match($block, 'kpi_id\s*:\s*"([^"]+)"')
      $keyMatch = [regex]::Match($block, 'kpi_key\s*:\s*"([^"]+)"')
      if ($idMatch.Success) {
        $id = $idMatch.Groups[1].Value
        if (-not $index.Contains($id)) { [void]$index.Add($id) }
        if ($keyMatch.Success) { $names[$keyMatch.Groups[1].Value] = $id }
        $aliasBlock = [regex]::Match($block, 'aliases\s*:\s*\[(.*?)\]', 'Singleline')
        if ($aliasBlock.Success) {
          foreach ($nm in [regex]::Matches($aliasBlock.Groups[1].Value, '"([^"]+)"')) { $names[$nm.Groups[1].Value] = $id }
        }
      } elseif ($keyMatch.Success) { $names[$keyMatch.Groups[1].Value] = $true }
    }
  }
  return @{ ids = $index; names = $names }
}

function Test-MeasureCovered {
  param(
    [string]$Measure,
    [string]$CatalogRoot
  )
  if (-not $Measure) { return $false }
  $files = Get-ChildItem -Path $CatalogRoot -Filter '*.md' -Recurse | Where-Object {
    $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]'
  }
  foreach ($file in $files) {
    if (Select-String -Path $file.FullName -Pattern ([regex]::Escape($Measure)) -SimpleMatch -Quiet -ErrorAction SilentlyContinue) {
      return $true
    }
  }
  return $false
}

Write-Host "Scanning Business Factsheets in $UseCasesRoot ..."
$catalog = Load-KpiCatalogIndex -Root $KpiCatalogRoot
$catalogIds = $catalog.ids
$catalogNames = $catalog.names
$factsheets = @(
  Get-ChildItem -Path $UseCasesRoot -Recurse -Filter 'Business_Factsheet.md' | Where-Object {
    $_.FullName -notmatch '[\\/]internal[\\/]archive[\\/]'
  }
) | Sort-Object FullName -Unique
if ($factsheets.Count -eq 0) { Write-Host "No Business_Factsheet.md files found." -ForegroundColor Yellow; exit 0 }

$missing = @(); $rows = @(); $noKpiRefs = @()
foreach ($fs in $factsheets) {
  $fm = Get-FrontMatter -Path $fs.FullName
  $reqIds = Get-RequiredIdsFromFrontMatter -FrontMatter $fm
  if ($reqIds.Count -eq 0) {
    # Prefer ontology bracket (SSOT) when present
    $reqIds = Get-KpiIdsFromUseCaseBracket -FactsheetPath $fs.FullName
  }
  if ($reqIds.Count -eq 0) {
    # Legacy fallback: parse body YAML blocks
    $reqIds = Get-RequiredIdsFromBody -Path $fs.FullName
  }
  if ($reqIds.Count -gt 0) {
    foreach ($id in $reqIds) {
      $covered = $false
      if ($catalogIds.Contains($id)) { $covered = $true }
      if (-not $covered) {
        $files = Get-ChildItem -Path $KpiCatalogRoot -Filter '*.md' | Select-Object -ExpandProperty FullName
        $covered = Select-String -Path $files -Pattern $id -SimpleMatch -Quiet -ErrorAction SilentlyContinue
      }
      $rows += [pscustomobject]@{ UseCase = $fs.Directory.Name; Measure = $id; Covered = $covered }
      if (-not $covered) { $missing += "$($fs.Directory.Name): $id" }
    }
  } else {
    $req = Get-RequiredMeasuresFromFrontMatter -FrontMatter $fm
    if ($req.Count -eq 0) {
      $noKpiRefs += $fs.FullName
      continue
    }
    foreach ($m in $req) {
      $covered = $false
      if ($catalogNames.ContainsKey($m)) { $covered = $true } else { $covered = Test-MeasureCovered -Measure $m -CatalogRoot $KpiCatalogRoot }
      $rows += [pscustomobject]@{ UseCase = $fs.Directory.Name; Measure = $m; Covered = $covered }
      if (-not $covered) { $missing += "$($fs.Directory.Name): $m" }
    }
  }
}

$rows | Sort-Object UseCase, Measure -Unique | Format-Table -AutoSize | Out-String | Write-Host
if ($noKpiRefs.Count -gt 0) {
  Write-Host "Factsheets without KPI references in front matter or body:" -ForegroundColor Yellow
  $noKpiRefs | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

if ($missing.Count -gt 0) {
  Write-Host "Missing measures:" -ForegroundColor Red
  $missing | Sort-Object | ForEach-Object { Write-Host "- $_" }
  if ($FailOnMissing) { exit 1 }
} else { Write-Host "All required measures are covered in KPI Catalog." -ForegroundColor Green }
