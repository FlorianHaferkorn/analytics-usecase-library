Param(
  [string]$UseCasesRoot = "framework/usecases",
  [string]$MapPath = "framework/action_codes/decision_spines/DecisionSpine_UseCase_Map.yaml",
  [string]$DecisionSpinesRoot = "framework/action_codes/decision_spines",
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

function Get-CoreUseCaseIds {
  param([string]$Root)
  $coreRoot = Join-Path -Path $Root -ChildPath "core"
  if (-not (Test-Path $coreRoot)) { return @() }
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  $factsheets = Get-ChildItem -Path $coreRoot -Recurse -File -Filter "Business_Factsheet.md"
  foreach ($file in $factsheets) {
    $id = $null
    $lines = Get-Content -Path $file.FullName -TotalCount 40
    foreach ($line in $lines) {
      if ($line -match '^id:\s*"?([^"\s]+)"?') {
        $id = $matches[1]
        break
      }
    }
    if (-not $id) {
      $id = $file.Directory.Name.Split('_')[0]
    }
    if ($id) { $null = $ids.Add($id) }
  }
  return $ids | Sort-Object
}

function Get-DecisionSpineMap {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  $map = @{}
  $current = $null
  $inSection = $false
  foreach ($line in $lines) {
    if ($line -match '^\s*decision_spines:\s*$') {
      $inSection = $true
      continue
    }
    if (-not $inSection) { continue }
    if ($line -match '^\s{2}([A-Z0-9-_]+):\s*$') {
      $current = $matches[1]
      continue
    }
    if ($current -and $line -match '^\s{4}use_cases:\s*\[(.*?)\]\s*$') {
      $cases = $matches[1].Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
      $map[$current] = $cases
      $current = $null
    }
  }
  return $map
}

function Get-DecisionSpineIds {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -File | Where-Object {
    $_.Extension -in @(".yaml", ".yml") -and $_.Name -ne "DecisionSpine_UseCase_Map.yaml"
  } | ForEach-Object {
    $basename = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)
    if ($basename) { $null = $ids.Add($basename) }
  }
  return $ids
}

function Get-Indent {
  param([string]$Line)
  if ($Line -match '^(\s*)') { return $matches[1].Length }
  return 0
}

function SectionHasList {
  param(
    [string[]]$Lines,
    [string]$KeyPattern
  )
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match $KeyPattern) {
      $baseIndent = Get-Indent -Line $Lines[$i]
      for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
        if ($Lines[$j] -match '^\s*$') { continue }
        $indent = Get-Indent -Line $Lines[$j]
        if ($indent -le $baseIndent) { break }
        if ($Lines[$j] -match '^\s*-\s+.+') { return $true }
      }
      return $false
    }
  }
  return $false
}

function Get-EscalationLevels {
  param([string[]]$Lines)
  $levels = @()
  $inEscalationPath = $false
  $baseIndent = 0
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    $line = $Lines[$i]
    if ($line -match '^\s*escalation_path:\s*$') {
      $inEscalationPath = $true
      $baseIndent = Get-Indent -Line $line
      continue
    }
    if ($inEscalationPath) {
      $indent = Get-Indent -Line $line
      if ($indent -le $baseIndent) { break }
      if ($line -match '^\s*-\s*level:\s*\"?([^\"\s]+)\"?') {
        $levels += $matches[1]
      }
    }
  }
  return $levels
}

function Get-ScalarValue {
  param(
    [string[]]$Lines,
    [string]$KeyPattern
  )
  foreach ($line in $Lines) {
    if ($line -match $KeyPattern) { return $matches[1] }
  }
  return $null
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "framework/usecases"
$mapPath = Resolve-RepoPath -ProvidedPath $MapPath -DefaultRelative "framework/action_codes/decision_spines/DecisionSpine_UseCase_Map.yaml"
$decisionSpinesRoot = Resolve-RepoPath -ProvidedPath $DecisionSpinesRoot -DefaultRelative "framework/action_codes/decision_spines"

if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $mapPath) { throw "Decision spine map not found. Provide -MapPath or run inside repository." }
if (-not $decisionSpinesRoot) { throw "Decision spines root not found. Provide -DecisionSpinesRoot or run inside repository." }

Write-Host "Decision Spine map consistency" -ForegroundColor Cyan

$coreUseCases = Get-CoreUseCaseIds -Root $useCasesRoot
$mapEntries = Get-DecisionSpineMap -Path $mapPath
$spineIds = Get-DecisionSpineIds -Root $decisionSpinesRoot

$mapSpines = $mapEntries.Keys | Sort-Object
$mappedUseCases = @()
foreach ($entry in $mapEntries.GetEnumerator()) {
  $mappedUseCases += $entry.Value
}
$mappedUseCases = $mappedUseCases | Where-Object { $_ } | Sort-Object

$missingSpines = $mapSpines | Where-Object { -not $spineIds.Contains($_) }
$unmappedSpines = $spineIds | Where-Object { $_ -notin $mapSpines }

$missingCore = $coreUseCases | Where-Object { $_ -notin $mappedUseCases }
$nonCore = $mappedUseCases | Where-Object { $_ -notin $coreUseCases }

$duplicateUseCases = @()
$caseCounts = @{}
foreach ($uc in $mappedUseCases) {
  if (-not $caseCounts.ContainsKey($uc)) { $caseCounts[$uc] = 0 }
  $caseCounts[$uc]++
}
foreach ($kv in $caseCounts.GetEnumerator()) {
  if ($kv.Value -gt 1) { $duplicateUseCases += $kv.Key }
}

$hadIssues = $false
if ($missingSpines.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Missing Decision Spine files (referenced in map):" -ForegroundColor Red
  $missingSpines | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($unmappedSpines.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Decision Spine files not present in map:" -ForegroundColor Red
  $unmappedSpines | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($missingCore.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Core use cases missing in Decision Spine map:" -ForegroundColor Red
  $missingCore | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($nonCore.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Non-core use cases referenced in Decision Spine map:" -ForegroundColor Red
  $nonCore | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}
if ($duplicateUseCases.Count -gt 0) {
  $hadIssues = $true
  Write-Host "Use cases mapped to multiple Decision Spines:" -ForegroundColor Red
  $duplicateUseCases | Sort-Object | ForEach-Object { Write-Host "  - $_" }
}

Write-Host "Decision Spine content validation" -ForegroundColor Cyan
$requiredScalarPatterns = @(
  '^\s*schema_version:\s*\"?([^\"\s]+)\"?',
  '^\s*id:\s*\"?([^\"\s]+)\"?',
  '^\s*name:\s*\"?(.+?)\"?\s*$',
  '^\s*impact_dimension:\s*\"?(.+?)\"?\s*$'
)

$requiredSectionPatterns = @(
  '^\s*purpose:\s*$',
  '^\s*decision_context:\s*$',
  '^\s*decision_tradeoffs:\s*$',
  '^\s*when_not_to_act:\s*$',
  '^\s*escalation_logic:\s*$',
  '^\s*decision_confidence:\s*$',
  '^\s*governance:\s*$',
  '^\s*quality_rules:\s*$'
)

$requiredListKeys = @(
  '^\s*decision_owner_roles:\s*$',
  '^\s*improves:\s*$',
  '^\s*risks:\s*$',
  '^\s*conditions:\s*$',
  '^\s*escalation_path:\s*$',
  '^\s*rationale:\s*$',
  '^\s*consulted_roles:\s*$',
  '^\s*change_policy:\s*$',
  '^\s*quality_rules:\s*$'
)

$expectedEscalationLevels = @("EarlyWarning","RequiredIntervention","PrescriptiveExecution")
$allowedDecisionTypes = @("Descriptive","Diagnostic","Prescriptive")

Get-ChildItem -Path $decisionSpinesRoot -File | Where-Object {
  $_.Extension -in @(".yaml",".yml") -and $_.Name -ne "DecisionSpine_UseCase_Map.yaml"
} | ForEach-Object {
  $path = $_.FullName
  $lines = Get-Content -Path $path
  $content = $lines -join "`n"
  $fileId = [System.IO.Path]::GetFileNameWithoutExtension($_.Name)

  foreach ($pattern in $requiredScalarPatterns) {
    if (-not ($lines | Where-Object { $_ -match $pattern })) {
      $hadIssues = $true
      Write-Host "Missing required field in $($_.Name): $pattern" -ForegroundColor Red
    }
  }
  foreach ($pattern in $requiredSectionPatterns) {
    if (-not ($lines | Where-Object { $_ -match $pattern })) {
      $hadIssues = $true
      Write-Host "Missing required section in $($_.Name): $pattern" -ForegroundColor Red
    }
  }
  foreach ($pattern in $requiredListKeys) {
    if (-not (SectionHasList -Lines $lines -KeyPattern $pattern)) {
      $hadIssues = $true
      Write-Host "Missing or empty list in $($_.Name): $pattern" -ForegroundColor Red
    }
  }

  $idValue = Get-ScalarValue -Lines $lines -KeyPattern '^\s*id:\s*\"?([^\"\s]+)\"?'
  if ($idValue -and $idValue -ne $fileId) {
    $hadIssues = $true
    Write-Host "ID mismatch in $($_.Name): id='$idValue' expected '$fileId'" -ForegroundColor Red
  }

  $decisionType = Get-ScalarValue -Lines $lines -KeyPattern '^\s*decision_type:\s*\"?([^\"\s]+)\"?'
  if ($decisionType -and ($decisionType -notin $allowedDecisionTypes)) {
    $hadIssues = $true
    Write-Host "Invalid decision_type in $($_.Name): $decisionType" -ForegroundColor Red
  }

  $ownerDomainsInline = $lines | Where-Object { $_ -match '^\s*owner_domains:\s*\[.+\]' }
  if (-not $ownerDomainsInline) {
    $hadIssues = $true
    Write-Host "owner_domains must be a non-empty list in $($_.Name)" -ForegroundColor Red
  }

  $levels = Get-EscalationLevels -Lines $lines
  if ($levels.Count -ne $expectedEscalationLevels.Count -or ($levels -join ',') -ne ($expectedEscalationLevels -join ',')) {
    $hadIssues = $true
    Write-Host "Invalid escalation_path levels in $($_.Name): $($levels -join ', ')" -ForegroundColor Red
  }

  if ($content -match '\bkpi_id\b' -or $content -match '\bkpi_id_ref\b') {
    $hadIssues = $true
    Write-Host "KPI ID references detected in $($_.Name) (not allowed)" -ForegroundColor Red
  }
}

if ($hadIssues) {
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: Decision Spines map matches core use cases and files." -ForegroundColor Green


