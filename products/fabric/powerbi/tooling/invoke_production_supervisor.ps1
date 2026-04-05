<#
.SYNOPSIS
  Kontrollierter Produktionslauf fuer den Fabric/Power BI Report Generator.

.DESCRIPTION
  Der Supervisor ist die obere Steuerungsschicht fuer den Produktionslauf:
  - Build
  - harte Validierung gegen den Produktionsstandard
  - Fehlerklassifikation
  - deterministische Fixes
  - optional ein begrenzter LLM-Fix-Versuch
  - Workspace-Publish und Post-Publish-Smoke-Test
#>

param(
  [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path,
  [string] $PolicyPath = "products/fabric/powerbi/tooling/production_quality.standard.json",
  [string] $ResultFile = ".cursor/pbi_supervisor_result.json",
  [string] $UseCase = "",
  [string] $Domain = "",
  [switch] $All,
  [switch] $UseAuroraData,
  [switch] $SkipBuild,
  [switch] $SkipPublish,
  [switch] $DisableLlmFix,
  [string] $PublishEnvironment = ""
)

$ErrorActionPreference = "Stop"

function Resolve-PathFromRepo {
  param([string] $Path)
  if ([System.IO.Path]::IsPathRooted($Path)) { return $Path }
  return Join-Path $RepoRoot ($Path -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Get-PolicyValue {
  param(
    [object] $Root,
    [string[]] $Path,
    [object] $Default = $null
  )

  $current = $Root
  foreach ($segment in $Path) {
    if ($null -eq $current) { return $Default }
    $prop = $current.PSObject.Properties[$segment]
    if ($null -eq $prop) { return $Default }
    $current = $prop.Value
  }
  if ($null -eq $current) { return $Default }
  return $current
}

function Convert-ToLineArray {
  param([object] $Value)
  $text = if ($null -eq $Value) { "" } else { ($Value | Out-String -Width 4096) }
  return @($text -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
}

function Get-PowerShellHostPath {
  $processPath = (Get-Process -Id $PID -ErrorAction Stop).Path
  if ($processPath -and (Test-Path $processPath)) {
    return $processPath
  }

  $powershellCommand = Get-Command powershell.exe -ErrorAction SilentlyContinue
  if ($powershellCommand) {
    return $powershellCommand.Source
  }

  throw "Unable to resolve a PowerShell host executable for supervisor child process."
}

function Quote-NativeArgument {
  param([string] $Value)
  if ($null -eq $Value) { return '""' }
  if ($Value -match '^[^-\s"][^\s"]*$' -or $Value -match '^-[A-Za-z0-9][A-Za-z0-9-]*$') {
    return $Value
  }

  return ('"{0}"' -f ($Value -replace '"', '\"'))
}

function Test-PublishCredentialsConfigured {
  return [bool]($env:TENANT_ID -and $env:CLIENT_ID -and $env:CLIENT_SECRET)
}

function Test-LlmConfigured {
  return (($env:AZURE_OPENAI_API_KEY -and $env:AZURE_OPENAI_ENDPOINT -and $env:AZURE_OPENAI_DEPLOYMENT) -or $env:OPENAI_API_KEY)
}

function Invoke-LlmChatCompletion {
  param(
    [string] $SystemPrompt,
    [string] $UserPrompt
  )

  $useAzure = ($env:AZURE_OPENAI_API_KEY -and $env:AZURE_OPENAI_ENDPOINT -and $env:AZURE_OPENAI_DEPLOYMENT)
  $deployment = if ($env:AZURE_OPENAI_DEPLOYMENT) { $env:AZURE_OPENAI_DEPLOYMENT } elseif ($env:OPENAI_MODEL) { $env:OPENAI_MODEL } else { "gpt-4o" }
  $body = @{
    model = $deployment
    messages = @(
      @{ role = "system"; content = $SystemPrompt },
      @{ role = "user"; content = $UserPrompt }
    )
    response_format = @{ type = "json_object" }
    temperature = 0.1
  } | ConvertTo-Json -Depth 10

  if ($useAzure) {
    $uri = "$($env:AZURE_OPENAI_ENDPOINT.TrimEnd('/'))/openai/deployments/$deployment/chat/completions?api-version=2024-02-15-preview"
    $headers = @{ "api-key" = $env:AZURE_OPENAI_API_KEY; "Content-Type" = "application/json" }
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -Encoding utf8
    return $response.choices[0].message.content
  }

  $uri = "https://api.openai.com/v1/chat/completions"
  $headers = @{ "Authorization" = "Bearer $env:OPENAI_API_KEY"; "Content-Type" = "application/json" }
  $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -Encoding utf8
  return $response.choices[0].message.content
}

function Add-KnowledgeBaseRow {
  param(
    [string] $KbPath,
    [string] $Section,
    [string] $Symptom,
    [string] $Cause,
    [string] $Fix
  )

  if (-not (Test-Path $KbPath)) { return $false }
  $content = Get-Content -Path $KbPath -Raw -Encoding utf8
  $marker = "## $Section"
  $index = $content.IndexOf($marker)
  if ($index -lt 0) { return $false }
  $sectionText = $content.Substring($index)
  $tableEnd = $sectionText.IndexOf("`n---")
  if ($tableEnd -lt 0) { $tableEnd = $sectionText.IndexOf("`n## ") }
  if ($tableEnd -lt 0) { $tableEnd = $sectionText.Length }
  $insertAt = $index + $tableEnd
  $newRow = "`n| $Symptom | $Cause | $Fix |"
  $updated = $content.Insert($insertAt, $newRow)
  Set-Content -Path $KbPath -Value $updated -NoNewline -Encoding utf8
  return $true
}

function Get-ValidationResult {
  param([string] $ValidationResultPath)
  $null = & $validatorScript -RepoRoot $RepoRoot -PolicyPath $resolvedPolicyPath -RequirePbiToolsCompile $true -ResultFile $ValidationResultPath 2>&1
  if (-not (Test-Path $ValidationResultPath)) {
    throw "Validation result file not written: $ValidationResultPath"
  }
  return Get-Content -Path $ValidationResultPath -Raw -Encoding utf8 | ConvertFrom-Json
}

function Get-ValidationFailureClassification {
  param([object] $Validation)

  $errors = @($Validation.errors)
  $failedGates = @($Validation.failedGates)
  $combined = (($errors + $failedGates) -join "`n")
  $classifications = [System.Collections.ArrayList]::new()
  $rules = @(
    @{ name = "stage1_failure"; confidence = "high"; patterns = @("stage1"); deterministicActions = @(); description = "Stage 1 Gate fehlgeschlagen." },
    @{ name = "tmdl_indentation_or_render"; confidence = "high"; patterns = @("TMDL", "tabs_only", "ungültiger Einzug", "invalid indent", "tmdl.indent"); deterministicActions = @("normalizeTabs", "renderAndFixTmdl"); description = "TMDL Syntax-, Render- oder Einrueckungsproblem." },
    @{ name = "pbip_structure"; confidence = "high"; patterns = @("Missing SemanticModel definition folder", "Missing .pbip file", "definition.pbir", "definition.pbism", "PBIP"); deterministicActions = @("ensurePbipDesktopReady"); description = "PBIP-Struktur oder Desktop-Readiness fehlerhaft." },
    @{ name = "compile_gate_failure"; confidence = "medium"; patterns = @("pbi-tools compile", "compile failed", "compile gate"); deterministicActions = @("renderAndFixTmdl", "ensurePbipDesktopReady"); description = "Compile-Gate scheitert an Readiness oder Syntax." },
    @{ name = "dax_or_measure_logic"; confidence = "medium"; patterns = @("DAX", "invalid expression", "Measure not found", "could not be determined", "check_measures_vs_kpi"); deterministicActions = @(); description = "DAX- oder Measure-Logikfehler." },
    @{ name = "catalog_reference"; confidence = "medium"; patterns = @("check_factsheet_vs_kpi", "check_action_codes_vs_kpi", "KPI ID missing", "non-existent KPI"); deterministicActions = @(); description = "Governed KPI- oder Action-Code-Referenz fehlt." },
    @{ name = "desktop_runtime"; confidence = "medium"; patterns = @("pbi_errors.log", "Power BI Desktop"); deterministicActions = @(); description = "Desktop-Runtime-Fehler aus Bridge-Log." }
  )

  foreach ($rule in $rules) {
    $matched = $false
    foreach ($pattern in $rule.patterns) {
      if ($combined -match [regex]::Escape($pattern)) {
        $matched = $true
        break
      }
    }
    if ($matched) {
      [void]$classifications.Add([ordered]@{
        name = $rule.name
        confidence = $rule.confidence
        description = $rule.description
        deterministicActions = @($rule.deterministicActions)
      })
    }
  }

  if ($classifications.Count -eq 0) {
    [void]$classifications.Add([ordered]@{
      name = "unknown"
      confidence = "low"
      description = "Keine bekannte Fehlerklasse getroffen."
      deterministicActions = @()
    })
  }

  return @($classifications)
}

function Invoke-DeterministicFixPass {
  param(
    [object[]] $Classifications,
    [int] $MaxActions
  )

  $actionMap = [ordered]@{}
  foreach ($classification in $Classifications) {
    foreach ($action in @($classification.deterministicActions)) {
      if (-not $actionMap.Contains($action)) {
        $actionMap[$action] = $true
      }
    }
  }

  $actions = @($actionMap.Keys | Select-Object -First $MaxActions)
  $results = [System.Collections.ArrayList]::new()
  foreach ($action in $actions) {
    switch ($action) {
      "normalizeTabs" {
        $script = Join-Path $RepoRoot "products\fabric\powerbi\tooling\normalize_tmdl_tabs.ps1"
        if (Test-Path $script) {
          try {
            $output = & $script -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot 2>&1
            [void]$results.Add(@{ action = $action; success = $true; output = @(Convert-ToLineArray -Value $output) })
          } catch {
            [void]$results.Add(@{ action = $action; success = $false; output = @("normalize_tmdl_tabs failed: $_") })
          }
        }
      }
      "renderAndFixTmdl" {
        $script = Join-Path $RepoRoot "products\fabric\powerbi\tooling\tmdl_render_and_fix.ps1"
        if (Test-Path $script) {
          try {
            $output = & $script -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot -UpdateKnowledgeBase $true 2>&1
            [void]$results.Add(@{ action = $action; success = $true; output = @(Convert-ToLineArray -Value $output) })
          } catch {
            [void]$results.Add(@{ action = $action; success = $false; output = @("tmdl_render_and_fix failed: $_") })
          }
        }
      }
      "ensurePbipDesktopReady" {
        $script = Join-Path $RepoRoot "products\fabric\powerbi\tooling\ensure_pbip_desktop_ready.ps1"
        if (Test-Path $script) {
          try {
            $output = & $script -DistRoot "products/fabric/powerbi/dist" -RepoRoot $RepoRoot 2>&1
            [void]$results.Add(@{ action = $action; success = $true; output = @(Convert-ToLineArray -Value $output) })
          } catch {
            [void]$results.Add(@{ action = $action; success = $false; output = @("ensure_pbip_desktop_ready failed: $_") })
          }
        }
      }
    }
  }

  return @($results)
}

function Invoke-LlmFixAttempt {
  param(
    [object] $Validation,
    [object[]] $Classifications
  )

  if (-not (Test-LlmConfigured)) {
    return @{ attempted = $false; appliedEdits = 0; reason = "LLM not configured."; output = @() }
  }

  $knowledgePath = Join-Path $RepoRoot "internal\project_mgmt\KNOWN_ERRORS_AND_FIXES.md"
  $knowledgePreview = if (Test-Path $knowledgePath) {
    $raw = Get-Content -Path $knowledgePath -Raw -Encoding utf8
    $raw.Substring(0, [Math]::Min(12000, $raw.Length))
  } else {
    ""
  }

  $systemPrompt = @"
Du bist ein Power-BI-PBIP-Experte. Du bekommst strukturierte Validierungsfehler und bekannte Fehlerklassen.
Antworte NUR mit einem einzelnen JSON-Objekt.

Format:
{
  "file_edits": [
    { "path": "relativer Pfad ab Repo-Root", "search": "exakter Text mit \\n", "replace": "Ersatztext mit \\n" }
  ],
  "knowledge_base_row": { "section": "TMDL / PBIP oder DAX / measures oder datasetReference usw.", "symptom": "...", "cause": "...", "fix": "..." }
}

Regeln:
- Aendere nur Dateien unter products/fabric/powerbi/dist oder internal/project_mgmt.
- Nur minimale, exakte search/replace-Edits.
- Wenn kein sicherer Fix moeglich ist: leere file_edits.
"@

  $userPrompt = @"
Klassifikation:
$($Classifications | ConvertTo-Json -Depth 6)

Validierungsfehler:
$($Validation | ConvertTo-Json -Depth 8)

Auszug Wissensbasis:
$knowledgePreview
"@

  try {
    $jsonText = Invoke-LlmChatCompletion -SystemPrompt $systemPrompt -UserPrompt $userPrompt
    $cleanJson = ($jsonText -replace '(?s)^\s*```(?:json)?\s*', '' -replace '\s*```\s*$', '').Trim()
    $response = $cleanJson | ConvertFrom-Json
  } catch {
    return @{ attempted = $true; appliedEdits = 0; reason = "LLM call or parse failed: $_"; output = @() }
  }

  $editCount = 0
  $messages = [System.Collections.ArrayList]::new()
  foreach ($edit in @($response.file_edits)) {
    $fullPath = Resolve-PathFromRepo -Path $edit.path
    if (-not (Test-Path $fullPath)) {
      [void]$messages.Add("LLM edit skipped, file missing: $($edit.path)")
      continue
    }
    $content = Get-Content -Path $fullPath -Raw -Encoding utf8
    $search = ($edit.search -replace '\\n', "`n")
    $replace = ($edit.replace -replace '\\n', "`n")
    if (-not $content.Contains($search)) {
      [void]$messages.Add("LLM edit skipped, search text missing: $($edit.path)")
      continue
    }
    $updated = $content.Replace($search, $replace)
    Set-Content -Path $fullPath -Value $updated -NoNewline -Encoding utf8
    $editCount++
    [void]$messages.Add("LLM edit applied: $($edit.path)")
  }

  if ($response.knowledge_base_row -and $response.knowledge_base_row.section) {
    $added = Add-KnowledgeBaseRow -KbPath $knowledgePath -Section $response.knowledge_base_row.section -Symptom $response.knowledge_base_row.symptom -Cause $response.knowledge_base_row.cause -Fix $response.knowledge_base_row.fix
    if ($added) {
      [void]$messages.Add("Knowledge base row added: $($response.knowledge_base_row.symptom)")
    }
  }

  $reason = "No safe LLM edits returned."
  if ($editCount -gt 0) {
    $reason = "LLM edits applied."
  }

  return @{ attempted = $true; appliedEdits = $editCount; reason = $reason; output = @($messages) }
}

function Invoke-WorkspacePublishPhase {
  param()
  $publishResultPath = Resolve-PathFromRepo -Path ".cursor/pbi_publish_result.json"
  $publishArgs = @("-RepoRoot", $RepoRoot, "-Environment", $effectivePublishEnvironment, "-ResultFile", $publishResultPath)
  if ($UseCase) {
    $publishArgs += @("-UseCase", $UseCase)
  } elseif ($Domain) {
    $publishArgs += @("-Domain", $Domain)
  } else {
    $publishArgs += "-All"
  }
  $dryRunWhenCredentialsMissing = [bool](Get-PolicyValue -Root $policy -Path @("supervisor", "dryRunWhenCredentialsMissing") -Default $true)
  $hasCredentials = Test-PublishCredentialsConfigured
  if ((-not $hasCredentials) -and $dryRunWhenCredentialsMissing) {
    $publishArgs += "-DryRun"
  }
  $null = & $publishScript @publishArgs 2>&1
  if (-not (Test-Path $publishResultPath)) {
    throw "Publish result file not written: $publishResultPath"
  }
  return Get-Content -Path $publishResultPath -Raw -Encoding utf8 | ConvertFrom-Json
}

function Invoke-PostPublishSmokeTest {
  param([object] $PublishResult)
  if (-not $PublishResult.success) {
    return @{ success = $false; messages = @("Publish failed; smoke test not executed.") }
  }
  if ($PublishResult.dryRun) {
    return @{ success = $false; messages = @("Publish completed only as dry-run; smoke test cannot confirm workspace state.") }
  }
  $messages = [System.Collections.ArrayList]::new()
  $passed = $true
  if (($PublishResult.stagedArtifacts.semanticModels -lt 1) -or ($PublishResult.stagedArtifacts.reports -lt 1)) {
    $passed = $false
    [void]$messages.Add("Staging output incomplete after publish.")
  }
  foreach ($reportFile in @($PublishResult.reportFiles)) {
    $resolved = Resolve-PathFromRepo -Path $reportFile
    if (Test-Path $resolved) {
      [void]$messages.Add("Publish report generated: $reportFile")
    }
  }
  if ($messages.Count -eq 0) {
    [void]$messages.Add("Publish returned success and staging artifacts are present.")
  }
  return @{ success = $passed; messages = @($messages) }
}

$resolvedPolicyPath = Resolve-PathFromRepo -Path $PolicyPath
if (-not (Test-Path $resolvedPolicyPath)) {
  throw "Production policy not found: $resolvedPolicyPath"
}

$policy = Get-Content -Path $resolvedPolicyPath -Raw -Encoding utf8 | ConvertFrom-Json
$maxIterations = [int](Get-PolicyValue -Root $policy -Path @("supervisor", "maxIterations") -Default 1)
if ($maxIterations -lt 1) { $maxIterations = 1 }
$maxDeterministicFixes = [int](Get-PolicyValue -Root $policy -Path @("supervisor", "maxDeterministicFixPassesPerIteration") -Default 1)
if ($maxDeterministicFixes -lt 1) { $maxDeterministicFixes = 1 }
$maxLlmFixAttempts = [int](Get-PolicyValue -Root $policy -Path @("supervisor", "maxLlmFixAttempts") -Default 0)
if ($maxLlmFixAttempts -lt 0) { $maxLlmFixAttempts = 0 }
$effectivePublishEnvironment = if ($PublishEnvironment) { $PublishEnvironment } else { [string](Get-PolicyValue -Root $policy -Path @("supervisor", "publishEnvironment") -Default "tst") }

$modeCount = 0
if ($UseCase) { $modeCount++ }
if ($Domain) { $modeCount++ }
if ($All) { $modeCount++ }
if ($modeCount -eq 0) {
  throw "Specify exactly one scope: -UseCase <id>, -Domain <name>, or -All"
}
if ($modeCount -gt 1) {
  throw "Specify only one scope: -UseCase, -Domain, or -All"
}

$orchestratorScript = Join-Path $RepoRoot "products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1"
$validatorScript = Join-Path $RepoRoot "tooling\pbi_validate_after_impl.ps1"
$publishScript = Join-Path $RepoRoot "products\fabric\powerbi\tooling\invoke_workspace_publish.ps1"
$resolvedResultFile = Resolve-PathFromRepo -Path $ResultFile
$resultDir = Split-Path -Parent $resolvedResultFile
if ($resultDir -and -not (Test-Path $resultDir)) {
  New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
}

$scopeState = if ($UseCase) {
  @{ type = "UseCase"; value = $UseCase }
} elseif ($Domain) {
  @{ type = "Domain"; value = $Domain }
} else {
  @{ type = "All"; value = "All" }
}

$runState = [ordered]@{
  policy = $policy.name
  policyVersion = $policy.standardVersion
  repoRoot = $RepoRoot
  scope = $scopeState
  publishEnvironment = $effectivePublishEnvironment
  startedAt = (Get-Date).ToString("o")
  iterations = @()
}

$llmAttemptsUsed = 0
$stopOnStage1Failure = [bool](Get-PolicyValue -Root $policy -Path @("supervisor", "stopOnStage1Failure") -Default $true)
$publishRequired = [bool](Get-PolicyValue -Root $policy -Path @("requirements", "workspacePublish", "required") -Default $false)
$smokeRequired = [bool](Get-PolicyValue -Root $policy -Path @("requirements", "postPublishSmoke", "required") -Default $false)

for ($iteration = 1; $iteration -le $maxIterations; $iteration++) {
  Write-Host "[Supervisor] Iteration $iteration / $maxIterations" -ForegroundColor Cyan
  $iterationState = [ordered]@{
    iteration = $iteration
    timestamp = (Get-Date).ToString("o")
    build = $null
    validation = $null
    classifications = @()
    deterministicFixes = @()
    llmFix = $null
    publish = $null
    smokeTest = $null
  }

  if (-not $SkipBuild) {
    $buildArgs = @()
    if ($UseCase) {
      $buildArgs += @("-UseCase", $UseCase)
    } elseif ($Domain) {
      $buildArgs += @("-Domain", $Domain)
    } else {
      $buildArgs += "-All"
    }
    if ($UseAuroraData) {
      $buildArgs += "-UseAuroraData"
    }
    try {
      $powershellHost = Get-PowerShellHostPath
      $stdoutFile = [System.IO.Path]::GetTempFileName()
      $stderrFile = [System.IO.Path]::GetTempFileName()
      $buildCommand = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $orchestratorScript) + $buildArgs
      $buildCommandLine = (($buildCommand | ForEach-Object { Quote-NativeArgument -Value $_ }) -join ' ')
      $buildProcess = Start-Process -FilePath $powershellHost -ArgumentList $buildCommandLine -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
      $buildExit = $buildProcess.ExitCode
      $buildOutput = @()
      if (Test-Path $stdoutFile) {
        $buildOutput += Get-Content -Path $stdoutFile -Encoding utf8
      }
      if (Test-Path $stderrFile) {
        $buildOutput += Get-Content -Path $stderrFile -Encoding utf8
      }
      Remove-Item -Path $stdoutFile, $stderrFile -ErrorAction SilentlyContinue
      $iterationState.build = @{ passed = ($buildExit -eq 0); exitCode = $buildExit; output = @(Convert-ToLineArray -Value $buildOutput) }
      if ($buildExit -ne 0) {
        $runState.iterations += $iterationState
        $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
        continue
      }
    } catch {
      $iterationState.build = @{ passed = $false; exitCode = 1; output = @("orchestrate_full_model failed: $_") }
      $runState.iterations += $iterationState
      $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
      continue
    }
  } else {
    $iterationState.build = @{ passed = $true; exitCode = 0; output = @("Build skipped by caller.") }
  }

  $validationResultPath = Resolve-PathFromRepo -Path ".cursor/pbi_validate_result.json"
  try {
    $validation = Get-ValidationResult -ValidationResultPath $validationResultPath
    $iterationState.validation = $validation
  } catch {
    $iterationState.validation = @{ success = $false; errors = @("Validation pipeline failed: $_"); failedGates = @(); gates = @() }
  }

  $classifications = @(Get-ValidationFailureClassification -Validation $iterationState.validation)
  $iterationState.classifications = $classifications
  $hasStage1Failure = @($iterationState.validation.failedGates) -contains "stage1"

  if ($iterationState.validation.success) {
    if ($publishRequired -and -not $SkipPublish) {
      try {
        $publishResult = Invoke-WorkspacePublishPhase
        $iterationState.publish = $publishResult
        if ($publishResult.dryRun -and -not (Test-PublishCredentialsConfigured)) {
          $runState.iterations += $iterationState
          $runState.completedAt = (Get-Date).ToString("o")
          $runState.success = $false
          $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
          Write-Host "[Supervisor] Workspace publish requires TENANT_ID, CLIENT_ID and CLIENT_SECRET; only dry-run was possible." -ForegroundColor Yellow
          exit 1
        }
        if ($smokeRequired) {
          $iterationState.smokeTest = Invoke-PostPublishSmokeTest -PublishResult $publishResult
        }
      } catch {
        $iterationState.publish = @{ success = $false; errors = @("Publish phase failed: $_") }
        if ($smokeRequired) {
          $iterationState.smokeTest = @{ success = $false; messages = @("Publish phase failed before smoke test.") }
        }
      }
    }

    $publishPassed = ($SkipPublish -or -not $publishRequired -or ($iterationState.publish -and $iterationState.publish.success -and -not $iterationState.publish.dryRun))
    $smokePassed = ($SkipPublish -or -not $smokeRequired -or ($iterationState.smokeTest -and $iterationState.smokeTest.success))
    if ($publishPassed -and $smokePassed) {
      $runState.iterations += $iterationState
      $runState.completedAt = (Get-Date).ToString("o")
      $runState.success = $true
      $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
      Write-Host "[Supervisor] Production validation and publish successful." -ForegroundColor Green
      exit 0
    }

    $runState.iterations += $iterationState
    $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
    continue
  }

  if ($hasStage1Failure -and $stopOnStage1Failure) {
    $runState.iterations += $iterationState
    $runState.completedAt = (Get-Date).ToString("o")
    $runState.success = $false
    $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
    Write-Host "[Supervisor] Stage 1 failure is configured as hard stop." -ForegroundColor Yellow
    exit 1
  }

  $deterministicResults = @(Invoke-DeterministicFixPass -Classifications $classifications -MaxActions $maxDeterministicFixes)
  $iterationState.deterministicFixes = $deterministicResults
  $didDeterministicWork = ($deterministicResults.Count -gt 0)
  $didDeterministicApply = @($deterministicResults | Where-Object { $_.success }).Count -gt 0

  if ((-not $DisableLlmFix) -and ($llmAttemptsUsed -lt $maxLlmFixAttempts)) {
    $needsLlm = @($classifications | Where-Object { $_.name -in @("unknown", "dax_or_measure_logic", "catalog_reference", "desktop_runtime") }).Count -gt 0
    if ($needsLlm -or -not $didDeterministicApply) {
      $llmResult = Invoke-LlmFixAttempt -Validation $iterationState.validation -Classifications $classifications
      $iterationState.llmFix = $llmResult
      if ($llmResult.attempted) {
        $llmAttemptsUsed++
      }
    }
  }

  $runState.iterations += $iterationState
  $runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8

  $madeAnyFixAttempt = $didDeterministicWork -or ($iterationState.llmFix -and $iterationState.llmFix.attempted)
  if (-not $madeAnyFixAttempt) {
    break
  }
}

$runState.completedAt = (Get-Date).ToString("o")
$runState.success = $false
$runState | ConvertTo-Json -Depth 12 | Set-Content -Path $resolvedResultFile -Encoding utf8
Write-Host "[Supervisor] Max iterations reached without satisfying production quality policy." -ForegroundColor Yellow
exit 1