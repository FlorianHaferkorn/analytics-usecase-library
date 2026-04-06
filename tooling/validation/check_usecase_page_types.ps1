Param(
  [string]$Root = ".",
  [switch]$FailOnError
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  $repo = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

$rootPath = Resolve-RepoPath -ProvidedPath $Root -DefaultRelative "."
if (-not $rootPath) { throw "Root path not found." }

# Valid page types as defined in core/templates/page_templates/page_types/
$validPageTypes = @("T1_Strategic_Overview", "T2_Tactical_Variance", "T3_Operational_Monitoring", "T4_Prescriptive_Recommendation")

$issues = @()
$checked = 0

$bracketsDir = Join-Path $rootPath "core\usecases\core"
Get-ChildItem -Path $bracketsDir -Recurse -Filter "UseCase_Bracket.yaml" -ErrorAction SilentlyContinue | ForEach-Object {
  $checked++
  $bracketFile = $_.FullName
  $content = Get-Content -Raw -Path $bracketFile
  $ucId = "unknown"
  if ($content -match '(?m)^\s*id\s*:\s*"?([^"\s]+)"?') { $ucId = $matches[1] }

  # Look for page_type declarations in the bracket
  $pageTypeMatches = [regex]::Matches($content, '(?m)page_type\s*:\s*"?([^"\s\r\n]+)"?')

  if ($pageTypeMatches.Count -eq 0) {
    $issues += "${ucId} ($($_.Name)): no page_type declared - at least one page_type is required"
    return
  }

  foreach ($m in $pageTypeMatches) {
    $pt = $m.Groups[1].Value.Trim('"')
    if ($pt -notin $validPageTypes) {
      $issues += "${ucId}: invalid page_type '$pt' (valid: $($validPageTypes -join ', '))"
    }
  }
}

Write-Host "Checked $checked UseCase Bracket files for page_type declarations."

if ($issues.Count -gt 0) {
  Write-Host "UseCase page type check failed:" -ForegroundColor Red
  $issues | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all UseCase Brackets declare valid page types." -ForegroundColor Green
