Param(
  [string]$UseCasesRoot = "usecases",
  [string]$BusinessTemplate = "usecases/templates/usecase_factsheet_business.md",
  [string]$TechnicalTemplate = "usecases/templates/usecase_factsheet_technical.md",
  [string]$ActionCodesRoot = "framework/action_codes",
  [string]$ActionCodeTemplate = "framework/templates/action_codes/ActionCode_TEMPLATE.md",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$KpiCatalogSchema = "framework/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md",
  [string]$DataContractsRoot = "data_contracts/domains",
  [string]$FactTemplate = "framework/templates/data_contract_templates/fact_template.yaml",
  [string]$DimTemplate = "framework/templates/data_contract_templates/dim_template.yaml",
  [string]$MeasureTemplate = "framework/templates/measure_templates/measure_template.md",
  [string]$MeasureInstancesRoot = "semantic_models/measures",
  [string]$PageTemplatesRoot = "framework/templates/page_templates/page_types",
  [string]$PageInstancesRoot = "framework/page_templates/instances",
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

function Get-Headings {
  param([string]$Path)
  Get-Content -Path $Path | Where-Object { $_ -match '^(##|###) ' } | ForEach-Object { $_.Trim() }
}

function Compare-OrderedList {
  param(
    [string[]]$Expected,
    [string[]]$Actual
  )
  $result = [ordered]@{
    matches = $true
    missing = @()
    extra = @()
    order_mismatch = $false
  }

  $expectedSet = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($h in $Expected) { $null = $expectedSet.Add($h) }
  $actualSet = [System.Collections.Generic.HashSet[string]]::new()
  foreach ($h in $Actual) { $null = $actualSet.Add($h) }

  $result.missing = $Expected | Where-Object { -not $actualSet.Contains($_) }
  $result.extra = $Actual | Where-Object { -not $expectedSet.Contains($_) }

  if ($result.missing.Count -gt 0 -or $result.extra.Count -gt 0) {
    $result.matches = $false
  } else {
    if ($Expected.Count -ne $Actual.Count) {
      $result.matches = $false
      $result.order_mismatch = $true
    } else {
      for ($i=0; $i -lt $Expected.Count; $i++) {
        if ($Expected[$i] -ne $Actual[$i]) {
          $result.matches = $false
          $result.order_mismatch = $true
          break
        }
      }
    }
  }

  return $result
}

function Get-TemplateYamlTopLevelKeys {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  $inYaml = $false
  $keys = New-Object System.Collections.Generic.List[string]
  foreach ($line in $lines) {
    if ($line -match '^```yaml') { $inYaml = $true; continue }
    if ($inYaml -and $line -match '^```') { $inYaml = $false; continue }
    if (-not $inYaml) { continue }
    if ($line -match '^\s*#' -or $line.Trim() -eq '') { continue }
    if ($line -match '^([A-Za-z0-9_]+)\s*:') {
      $keys.Add($matches[1])
    }
  }
  return $keys
}

function Get-YamlTopLevelKeysFromFile {
  param([string]$Path)
  $keys = New-Object System.Collections.Generic.List[string]
  Get-Content -Path $Path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_.Trim() -eq '') { return }
    if ($_ -match '^([A-Za-z0-9_]+)\s*:') {
      $keys.Add($matches[1])
    }
  }
  return $keys
}

function Get-YamlChildKeys {
  param([string]$Path,[string]$RootKey)
  $lines = Get-Content -Path $Path
  $keys = New-Object System.Collections.Generic.List[string]
  $inRoot = $false
  for ($i=0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match '^\s*#' -or $line.Trim() -eq '') { continue }
    if (-not $inRoot) {
      if ($line -match "^$RootKey\\s*:") { $inRoot = $true }
      continue
    }
    if ($line -match '^\S') { break }
    if ($line -match '^  ([A-Za-z0-9_]+)\s*:') {
      $keys.Add($matches[1])
    }
  }
  return $keys
}

function Get-KpiEntriesKeyOrders {
  param([string]$Path)
  $lines = Get-Content -Path $Path
  $inYaml = $false
  $entries = @()
  $current = $null
  $currentSection = $null

  foreach ($line in $lines) {
    if ($line -match '^```yaml') { $inYaml = $true; continue }
    if ($inYaml -and $line -match '^```') {
      if ($current) { $entries += $current; $current = $null; $currentSection = $null }
      $inYaml = $false
      continue
    }
    if (-not $inYaml) { continue }

    if ($line -match '^-\s*([A-Za-z0-9_]+)\s*:') {
      if ($current) { $entries += $current }
      $current = [ordered]@{
        top = New-Object System.Collections.Generic.List[string]
        business = New-Object System.Collections.Generic.List[string]
        technical = New-Object System.Collections.Generic.List[string]
        governance = New-Object System.Collections.Generic.List[string]
        metadata_quality = New-Object System.Collections.Generic.List[string]
      }
      $current.top.Add($matches[1])
      $currentSection = $null
      continue
    }

    if (-not $current) { continue }

    if ($line -match '^\s{2}([A-Za-z0-9_]+)\s*:') {
      $key = $matches[1]
      $current.top.Add($key)
      if ($key -in @("business","technical","governance","metadata_quality")) {
        $currentSection = $key
      } else {
        $currentSection = $null
      }
      continue
    }

    if ($currentSection -and $line -match '^\s{4}([A-Za-z0-9_]+)\s*:') {
      $key = $matches[1]
      $current.$currentSection.Add($key)
    }
  }

  if ($current) { $entries += $current }
  return $entries
}

$useCasesRoot = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative "usecases"
$businessTemplatePath = Resolve-RepoPath -ProvidedPath $BusinessTemplate -DefaultRelative "usecases/templates/usecase_factsheet_business.md"
$technicalTemplatePath = Resolve-RepoPath -ProvidedPath $TechnicalTemplate -DefaultRelative "usecases/templates/usecase_factsheet_technical.md"
$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "framework/action_codes"
$actionCodeTemplatePath = Resolve-RepoPath -ProvidedPath $ActionCodeTemplate -DefaultRelative "framework/templates/action_codes/ActionCode_TEMPLATE.md"
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "framework/kpi_catalog"
$kpiCatalogSchemaPath = Resolve-RepoPath -ProvidedPath $KpiCatalogSchema -DefaultRelative "framework/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md"
$dataContractsRoot = Resolve-RepoPath -ProvidedPath $DataContractsRoot -DefaultRelative "data_contracts/domains"
$factTemplatePath = Resolve-RepoPath -ProvidedPath $FactTemplate -DefaultRelative "framework/templates/data_contract_templates/fact_template.yaml"
$dimTemplatePath = Resolve-RepoPath -ProvidedPath $DimTemplate -DefaultRelative "framework/templates/data_contract_templates/dim_template.yaml"
$measureTemplatePath = Resolve-RepoPath -ProvidedPath $MeasureTemplate -DefaultRelative "framework/templates/measure_templates/measure_template.md"
$measureInstancesRoot = Resolve-RepoPath -ProvidedPath $MeasureInstancesRoot -DefaultRelative $MeasureInstancesRoot
$pageTemplatesRoot = Resolve-RepoPath -ProvidedPath $PageTemplatesRoot -DefaultRelative "framework/templates/page_templates/page_types"
$pageInstancesRoot = Resolve-RepoPath -ProvidedPath $PageInstancesRoot -DefaultRelative $PageInstancesRoot

if (-not $useCasesRoot) { throw "UseCases root not found. Provide -UseCasesRoot or run inside repository." }
if (-not $businessTemplatePath) { throw "Business template not found. Provide -BusinessTemplate or run inside repository." }
if (-not $technicalTemplatePath) { throw "Technical template not found. Provide -TechnicalTemplate or run inside repository." }

$expectedBusiness = @(Get-Headings -Path $businessTemplatePath)
$expectedTechnical = @(Get-Headings -Path $technicalTemplatePath)

Write-Host "Template layout checks" -ForegroundColor Cyan

$issues = @()

Get-ChildItem -Path $useCasesRoot -Recurse -Filter "Business_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $actual = @(Get-Headings -Path $_.FullName)
  $cmp = Compare-OrderedList -Expected $expectedBusiness -Actual $actual
  if (-not $cmp.matches) {
    $issues += [PSCustomObject]@{
      file = $_.FullName
      type = "business"
      missing = ($cmp.missing -join "; ")
      extra = ($cmp.extra -join "; ")
      order_mismatch = $cmp.order_mismatch
    }
  }
}

Get-ChildItem -Path $useCasesRoot -Recurse -Filter "Technical_Factsheet.md" | Where-Object {
  $_.FullName -notmatch '\\_internal\\archive\\'
} | ForEach-Object {
  $actual = @(Get-Headings -Path $_.FullName)
  $cmp = Compare-OrderedList -Expected $expectedTechnical -Actual $actual
  if (-not $cmp.matches) {
    $issues += [PSCustomObject]@{
      file = $_.FullName
      type = "technical"
      missing = ($cmp.missing -join "; ")
      extra = ($cmp.extra -join "; ")
      order_mismatch = $cmp.order_mismatch
    }
  }
}

if ($actionCodesRoot -and $actionCodeTemplatePath) {
  $expectedActionKeys = @(Get-TemplateYamlTopLevelKeys -Path $actionCodeTemplatePath)
  $optionalActionKeys = @("inherits_decision_spine")
  $actionFiles = Get-ChildItem -Path $actionCodesRoot -Recurse -Filter "*.yaml" | Where-Object {
    $_.FullName -notmatch 'decision_spines' -and $_.FullName -notmatch '\\_internal\\archive\\'
  }
  if ($actionFiles.Count -eq 0) {
    Write-Host "Note: no Action Code YAML files found under $actionCodesRoot." -ForegroundColor Yellow
  } else {
    $actionFiles | ForEach-Object {
      $actual = @(Get-YamlTopLevelKeysFromFile -Path $_.FullName)
      $expected = if ($actual | Where-Object { $_ -in $optionalActionKeys }) { $expectedActionKeys } else { $expectedActionKeys | Where-Object { $_ -notin $optionalActionKeys } }
      $cmp = Compare-OrderedList -Expected $expected -Actual $actual
      if (-not $cmp.matches) {
        $issues += [PSCustomObject]@{
          file = $_.FullName
          type = "action_code"
          missing = ($cmp.missing -join "; ")
          extra = ($cmp.extra -join "; ")
          order_mismatch = $cmp.order_mismatch
        }
      }
    }
  }
}

if ($kpiCatalogRoot -and $kpiCatalogSchemaPath) {
  $kpiFiles = Get-ChildItem -Path $kpiCatalogRoot -Filter "KPI_Catalog_*.md"
  if ($kpiFiles.Count -eq 0) {
    Write-Host "Note: no KPI Catalog files found under $kpiCatalogRoot." -ForegroundColor Yellow
  } else {
    $mandatoryTop = @("kpi_id","kpi_key","kpi_type","impact_dimension","domain_tag","use_case_ref","action_code_ref","calc_type","business","technical","governance","metadata_quality")
    $optionalTop = @("aliases")
    $expectedBusiness = @("purpose","definition","grain_scope","unit_format","interpretation")
    $expectedTechnical = @("dax_name","depends_on_measures","lineage")
    $expectedMeta = @("completeness_score","last_review")

    $kpiFiles | ForEach-Object {
      $entries = @(Get-KpiEntriesKeyOrders -Path $_.FullName)
      if ($entries.Count -eq 0) { return }
      foreach ($entry in $entries) {
        $actualTop = @($entry.top)
        $expectedTop = @()
        $expectedTop += $mandatoryTop[0..2]
        $expectedTop += "kpi_role"
        $expectedTop += "impact_dimension","domain_tag","use_case_ref","action_code_ref"
        $expectedTop += "calc_type","business","technical","governance","metadata_quality"
        if ($actualTop -contains "aliases") { $expectedTop += "aliases" }

        $cmpTop = Compare-OrderedList -Expected $expectedTop -Actual $actualTop
        if (-not $cmpTop.matches) {
          $issues += [PSCustomObject]@{
            file = $_.FullName
            type = "kpi_catalog"
            missing = ($cmpTop.missing -join "; ")
            extra = ($cmpTop.extra -join "; ")
            order_mismatch = $cmpTop.order_mismatch
          }
        }

        $cmpBusiness = Compare-OrderedList -Expected $expectedBusiness -Actual @($entry.business)
        if (-not $cmpBusiness.matches) {
          $issues += [PSCustomObject]@{
            file = $_.FullName
            type = "kpi_catalog_business"
            missing = ($cmpBusiness.missing -join "; ")
            extra = ($cmpBusiness.extra -join "; ")
            order_mismatch = $cmpBusiness.order_mismatch
          }
        }

        $cmpTechnical = Compare-OrderedList -Expected $expectedTechnical -Actual @($entry.technical)
        if (-not $cmpTechnical.matches) {
          $issues += [PSCustomObject]@{
            file = $_.FullName
            type = "kpi_catalog_technical"
            missing = ($cmpTechnical.missing -join "; ")
            extra = ($cmpTechnical.extra -join "; ")
            order_mismatch = $cmpTechnical.order_mismatch
          }
        }

        $actualGov = @($entry.governance)
        $expectedGov = @("business_owner","data_owner")
        if ($actualGov -contains "steward") { $expectedGov += "steward" }
        $expectedGov += "review_cycle","validation_process","qa_rules","version"
        $cmpGovernance = Compare-OrderedList -Expected $expectedGov -Actual $actualGov
        if (-not $cmpGovernance.matches) {
          $issues += [PSCustomObject]@{
            file = $_.FullName
            type = "kpi_catalog_governance"
            missing = ($cmpGovernance.missing -join "; ")
            extra = ($cmpGovernance.extra -join "; ")
            order_mismatch = $cmpGovernance.order_mismatch
          }
        }

        $cmpMeta = Compare-OrderedList -Expected $expectedMeta -Actual @($entry.metadata_quality)
        if (-not $cmpMeta.matches) {
          $issues += [PSCustomObject]@{
            file = $_.FullName
            type = "kpi_catalog_metadata_quality"
            missing = ($cmpMeta.missing -join "; ")
            extra = ($cmpMeta.extra -join "; ")
            order_mismatch = $cmpMeta.order_mismatch
          }
        }
      }
    }
  }
}

if ($dataContractsRoot -and $factTemplatePath -and $dimTemplatePath) {
  $expectedFactKeys = @(Get-YamlChildKeys -Path $factTemplatePath -RootKey "fact")
  $expectedDimKeys = @(Get-YamlChildKeys -Path $dimTemplatePath -RootKey "dimension")
  $contractFiles = Get-ChildItem -Path $dataContractsRoot -Recurse -Filter "*.yaml" | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  }
  if ($contractFiles.Count -eq 0) {
    Write-Host "Note: no data contracts found under $dataContractsRoot." -ForegroundColor Yellow
  } else {
    $contractFiles | ForEach-Object {
      $content = Get-Content -Path $_.FullName
      $rootKey = $null
      foreach ($line in $content) {
        if ($line -match '^\s*#' -or $line.Trim() -eq '') { continue }
        if ($line -match '^(fact|dimension)\s*:') { $rootKey = $matches[1]; break }
      }
      if (-not $rootKey) {
        $issues += [PSCustomObject]@{
          file = $_.FullName
          type = "data_contract"
          missing = "<missing root key: fact or dimension>"
          extra = ""
          order_mismatch = $false
        }
        return
      }
      $actual = @(Get-YamlChildKeys -Path $_.FullName -RootKey $rootKey)
      $expected = if ($rootKey -eq "fact") { $expectedFactKeys } else { $expectedDimKeys }
      $cmp = Compare-OrderedList -Expected $expected -Actual $actual
      if (-not $cmp.matches) {
        $issues += [PSCustomObject]@{
          file = $_.FullName
          type = "data_contract"
          missing = ($cmp.missing -join "; ")
          extra = ($cmp.extra -join "; ")
          order_mismatch = $cmp.order_mismatch
        }
      }
    }
  }
}

if ($measureTemplatePath) {
  if (-not $measureInstancesRoot -or -not (Test-Path $measureInstancesRoot)) {
    Write-Host "Note: no measure documents found for template at $measureTemplatePath (no instances under semantic_models/measures)." -ForegroundColor Yellow
  }
}

if ($pageTemplatesRoot) {
  if (-not $pageInstancesRoot -or -not (Test-Path $pageInstancesRoot)) {
    Write-Host "Note: no page instance documents found for templates under $pageTemplatesRoot." -ForegroundColor Yellow
  }
}

if ($issues.Count -gt 0) {
  Write-Host "Layout mismatches found:" -ForegroundColor Red
  $issues | ForEach-Object {
    Write-Host ("- [{0}] {1}" -f $_.type, $_.file)
    if ($_.missing) { Write-Host ("  Missing: {0}" -f $_.missing) }
    if ($_.extra) { Write-Host ("  Extra: {0}" -f $_.extra) }
    if ($_.order_mismatch) { Write-Host "  Order mismatch: headings are present but in different order." }
  }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: all checked documents match their template layout." -ForegroundColor Green
