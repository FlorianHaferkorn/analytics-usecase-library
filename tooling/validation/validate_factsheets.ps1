Param(
  [string]$UseCasesRoot = "core/usecases",
  [switch]$FailOnError
)

$script:RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    if ($script:RepoRoot) {
      $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
      if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
    }
  }
  if ($DefaultRelative -and $script:RepoRoot) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Get-FrontMatter {
  param(
    [string]$Path,
    [int]$Depth = 0
  )
  if (-not (Test-Path $Path)) { return $null }
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $block = $match.Groups[1].Value
  $pointer = [regex]::Match($block, 'business_factsheet\s*:\s*"([^"]+)"')
  if ($pointer.Success -and $Depth -lt 5) {
    $parent = Split-Path -Parent $Path
    $target = Join-Path -Path $parent -ChildPath $pointer.Groups[1].Value
    if (Test-Path $target) {
      $resolved = Resolve-Path -Path $target
      return Get-FrontMatter -Path $resolved.Path -Depth ($Depth + 1)
    }
  }
  return [pscustomobject]@{
    Text   = $block
    Source = (Resolve-Path -Path $Path).Path
  }
}

function Has-Field {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  return [regex]::IsMatch($FrontMatter, "^\s*$escaped\s*:", 'Multiline')
}

function Parse-ListField {
  param([string]$FrontMatter,[string]$Field)
  if (-not $FrontMatter) { return @() }
  $escaped = [regex]::Escape($Field)
  $inline = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*\[(.*?)\]", 'Multiline,Singleline')
  if ($inline.Success) {
    $items = @()
    foreach ($token in [regex]::Matches($inline.Groups[1].Value, '"([^"]+)"|''([^'']+)''|([^,\s\]]+)')) {
      $value = if ($token.Groups[1].Success) { $token.Groups[1].Value }
               elseif ($token.Groups[2].Success) { $token.Groups[2].Value }
               else { $token.Groups[3].Value }
      if ($value) { $items += $value }
    }
    return $items
  }
  $block = [regex]::Match($FrontMatter, "(?ms)^\s*$escaped\s*:\s*(?:#.*)?\r?\n(?<body>(?:\s{2,}-\s*[^\r\n]*\r?\n?)+)")
  if ($block.Success) {
    $results = @()
    foreach ($rawLine in ($block.Groups['body'].Value -split '\r?\n')) {
      $line = $rawLine.Trim()
      if (-not $line) { continue }
      if ($line -match '^\s*-\s*(.*)$') {
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
      if ($value) { $results += $value }
    }
    return $results
  }
  return @()
}

function Get-MapField {
  param([string]$FrontMatter,[string]$Field)
  $escaped = [regex]::Escape($Field)
  $match = [regex]::Match($FrontMatter, "^\s*$escaped\s*:\s*$", 'Multiline')
  if (-not $match.Success) { return @{} }
  $map = [ordered]@{}
  $startIndex = $match.Index + $match.Length
  $lines = $FrontMatter.Substring($startIndex) -split '\r?\n'
  foreach ($line in $lines) {
    if ($line.Trim().Length -eq 0) { continue }
    if ($line -notmatch "^\s+") { break }
    $kv = [regex]::Match($line, '^\s*([^:]+):\s*(.+?)\s*$')
    if ($kv.Success) {
      $value = $kv.Groups[2].Value.Trim().Trim('"').Trim("'")
      $map[$kv.Groups[1].Value.Trim()] = $value
    }
  }
  return $map
}

$resolvedUseCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'core/usecases'
if (-not $resolvedUseCasesRoot) { throw "Unable to resolve UseCases root. Provide -UseCasesRoot or run inside repository." }

$errors = @(); $warnings = @()

function Get-ContentBody {
  param([string]$Path)
  $content = Get-Content -Raw -Path $Path
  $match = [regex]::Match($content, "(?ms)^---\s*\r?\n.*?\r?\n---\s*")
  if ($match.Success) { return $content.Substring($match.Length) }
  return $content
}

function Get-MetadataValue {
  param([string]$Body,[string]$Label)
  $pattern = '^\s*-\s*\*\*' + [regex]::Escape($Label) + ':\*\*\s*(.+?)\s*$'
  foreach ($line in ($Body -split '\r?\n')) {
    if ($line -match $pattern) { return $matches[1].Trim() }
  }
  return $null
}

function Get-YamlBlock {
  param([string]$Body,[string]$Key)
  $pattern = '(?ms)```yaml\s*(?<block>.*?)\s*```'
  foreach ($m in [regex]::Matches($Body, $pattern)) {
    $keyPattern = '^\s*' + [regex]::Escape($Key) + '\s*:'
    if ($m.Groups['block'].Value -match $keyPattern) { return $m.Groups['block'].Value }
  }
  return $null
}

function Get-UseCaseBracketPath {
  param([string]$FactsheetPath)
  $dir = Split-Path -Parent $FactsheetPath
  $bracket = Join-Path -Path $dir -ChildPath "UseCase_Bracket.yaml"
  if (Test-Path $bracket) { return (Resolve-Path -Path $bracket).Path }
  return $null
}

function Test-UseCaseBracket {
  param([string]$BracketPath,[string]$FactsheetPath)
  if (-not $BracketPath) { return $false }
  $lines = Get-Content -Path $BracketPath
  $text = ($lines -join "`n")

  if ($text -notmatch '(?m)^\s*schema_version\s*:\s*["'']?2\.0["'']?\s*$') {
    $errors += "$($FactsheetPath): UseCase_Bracket.yaml missing schema_version: ""2.0"" ($BracketPath)"
    return $false
  }

  if ($text -notmatch '(?m)^\s*owner_role\s*:\s*\S+') {
    $errors += "$($FactsheetPath): UseCase_Bracket.yaml missing governance.owner_role ($BracketPath)"
    return $false
  }
  if ($text -notmatch '(?m)^\s*steward_role\s*:\s*\S+') {
    $errors += "$($FactsheetPath): UseCase_Bracket.yaml missing governance.steward_role ($BracketPath)"
    return $false
  }
  if ($text -notmatch '(?m)^\s*strategic_kpi_id\s*:\s*\S+') {
    $errors += "$($FactsheetPath): UseCase_Bracket.yaml missing orchestration.strategic_kpi_id ($BracketPath)"
    return $false
  }

  # action_code_ids list required (>= 1)
  $actionCount = 0
  $inActions = $false
  foreach ($ln in $lines) {
    if ($ln -match '^\s*action_code_ids\s*:\s*$') { $inActions = $true; continue }
    if ($inActions) {
      if ($ln.Trim().Length -eq 0) { continue }
      if ($ln -notmatch '^\s{2,}-\s+') { break }
      $actionCount++
    }
  }
  if ($actionCount -lt 1) {
    $errors += "$($FactsheetPath): UseCase_Bracket.yaml action_code_ids missing or empty ($BracketPath)"
    return $false
  }
  return $true
}

function Count-ListItems {
  param([string]$YamlBlock,[string]$ItemKey)
  if (-not $YamlBlock) { return 0 }
  $count = 0
  foreach ($line in ($YamlBlock -split '\r?\n')) {
    if ($line -match ('^\s*-\s*' + [regex]::Escape($ItemKey) + '\s*:\s*.+$')) { $count++ }
  }
  return $count
}

function Require-TechnicalRefs {
  param([string]$Body,[string]$Path)
  $techFields = @(
    "Domain Data Contract",
    "Source Data Contract",
    "Semantic Model Definition",
    "KPI Catalog",
    "Measure Dictionary",
    "Action Codes"
  )
  foreach ($label in $techFields) {
    $value = Get-MetadataValue -Body $Body -Label $label
    if (-not $value) { $errors += "${Path}: missing '$label' reference" }
  }
}

Get-ChildItem -Path $resolvedUseCasesRoot -Recurse -Filter 'Business_Factsheet.md' | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $fm = Get-FrontMatter -Path $_.FullName
  if (-not ($fm -and $fm.Text)) { $errors += "Missing front-matter in $($_.FullName)"; return }
  $body = Get-ContentBody -Path $_.FullName

  $domain = Get-MetadataValue -Body $body -Label "Domain"
  if (-not $domain) { $errors += "$($_.FullName): missing Domain" }

  $bracketPath = Get-UseCaseBracketPath -FactsheetPath $_.FullName
  if (-not $bracketPath) {
    $errors += "$($_.FullName): UseCase_Bracket.yaml not found (required for every Business_Factsheet.md)"
  } else {
    $hasBracket = Test-UseCaseBracket -BracketPath $bracketPath -FactsheetPath $_.FullName
    if (-not $hasBracket) {
      $errors += "$($_.FullName): UseCase_Bracket.yaml does not pass minimum validation ($bracketPath)"
    }
  }
}

if ($warnings.Count -gt 0) {
  Write-Host "FactSheet warnings:" -ForegroundColor Yellow
  $warnings | Sort-Object | ForEach-Object { Write-Host "- $_" }
}

if ($errors.Count -gt 0) {
  Write-Host "FactSheet validation errors:" -ForegroundColor Red
  $errors | Sort-Object | ForEach-Object { Write-Host "- $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host 'FactSheet validation passed.' -ForegroundColor Green
