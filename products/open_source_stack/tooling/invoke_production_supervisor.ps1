<#
.SYNOPSIS
  Kontrollierter Produktionslauf fuer den OSS Evidence/dbt Adapter.
.DESCRIPTION
  Spiegelbild zum Fabric-Supervisor: Builder unten, Qualitaetsvertrag und kontrollierter Loop oben.
  Der Supervisor baut scoped Artefakte fuer Referenz-Use-Cases aus dem Core/IR, validiert danach hart
  und wiederholt den Lauf kontrolliert bis zur geforderten Gruen-Serie oder bis das Iterationslimit erreicht ist.
#>

param(
  [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path,
  [string] $PolicyPath = "products/open_source_stack/tooling/production_quality.standard.json",
  [string] $ResultFile = ".cursor/oss_supervisor_result.json",
  [string[]] $UseCase,
  [switch] $All,
  [switch] $SkipBuild,
  [switch] $SkipStage1
)

$ErrorActionPreference = "Stop"

function Resolve-PathFromRepo {
  param([string] $Path)
  if ([System.IO.Path]::IsPathRooted($Path)) { return $Path }
  return Join-Path $RepoRoot ($Path -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Resolve-PythonLauncher {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @{ Command = "py"; Prefix = @("-3") }
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @{ Command = "python"; Prefix = @() }
  }
  throw "Python launcher not found. Install 'py' or 'python' to run the OSS supervisor."
}

function Invoke-PythonJson {
  param([hashtable]$Launcher, [string[]]$Arguments)
  $output = & $Launcher.Command @($Launcher.Prefix) @Arguments 2>&1 | Out-String
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  return @{ Output = $output; ExitCode = $exitCode }
}

$resolvedPolicyPath = Resolve-PathFromRepo -Path $PolicyPath
if (-not (Test-Path $resolvedPolicyPath)) {
  throw "Production policy not found: $resolvedPolicyPath"
}

$policy = Get-Content -Path $resolvedPolicyPath -Raw -Encoding utf8 | ConvertFrom-Json
$maxIterations = [int]$policy.supervisor.maxIterations
if ($maxIterations -lt 1) { $maxIterations = 1 }
$requiredGreenRuns = [int]$policy.slos.consecutiveGreenRuns
if ($requiredGreenRuns -lt 1) { $requiredGreenRuns = 1 }

$scopeUseCases = @()
if ($All) {
  $scopeUseCases = @()
} elseif ($UseCase -and $UseCase.Count -gt 0) {
  $scopeUseCases = @($UseCase | Where-Object { $_ })
} else {
  $scopeUseCases = @($policy.referenceUseCases | Where-Object { $_ })
}

if (-not $All -and (-not $scopeUseCases -or $scopeUseCases.Count -eq 0)) {
  throw "Specify -UseCase <id> or define referenceUseCases in the policy."
}

$launcher = Resolve-PythonLauncher
$adapterBuild = Join-Path $RepoRoot "products\open_source_stack\tooling\adapter_build.ps1"
$resolvedResultFile = Resolve-PathFromRepo -Path $ResultFile
$resultDir = Split-Path -Parent $resolvedResultFile
if ($resultDir -and -not (Test-Path $resultDir)) {
  New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
}

$scopeState = if ($All) {
  @{ type = "All"; value = "All" }
} else {
  @{ type = "UseCase"; value = $scopeUseCases }
}

$runState = [ordered]@{
  policy = $policy.name
  policyVersion = $policy.standardVersion
  repoRoot = $RepoRoot
  scope = $scopeState
  startedAt = (Get-Date).ToString("o")
  iterations = @()
}

$consecutiveSuccesses = 0

for ($iteration = 1; $iteration -le $maxIterations; $iteration++) {
  Write-Host "[OSS Supervisor] Iteration $iteration / $maxIterations" -ForegroundColor Cyan
  $iterationState = [ordered]@{
    iteration = $iteration
    build = $null
    validation = $null
    timestamp = (Get-Date).ToString("o")
  }

  if (-not $SkipBuild) {
    $buildParams = @{}
    if ($All) {
      $buildParams.All = $true
    } else {
      $buildParams.UseCaseId = $scopeUseCases
    }
    if ($SkipStage1) {
      $buildParams.SkipStage1 = $true
    }

    $buildMessages = @()
    try {
      & $adapterBuild @buildParams
      $buildExit = $LASTEXITCODE
      if ($null -eq $buildExit) { $buildExit = 0 }
      $buildMessages = @("Build completed successfully.")
    } catch {
      $buildExit = $LASTEXITCODE
      if ($null -eq $buildExit -or $buildExit -eq 0) { $buildExit = 1 }
      $buildMessages = @($_ | Out-String)
    }

    $iterationState.build = @{
      passed = ($buildExit -eq 0)
      exitCode = $buildExit
      output = $buildMessages
    }
    if ($buildExit -ne 0) {
      $consecutiveSuccesses = 0
      $runState.iterations += $iterationState
      continue
    }
  } else {
    $iterationState.build = @{
      passed = $true
      exitCode = 0
      output = @("Build skipped by caller.")
    }
  }

  $validateArgs = @(
    (Join-Path $RepoRoot "products\open_source_stack\tooling\validate_oss.py"),
    "--root", $RepoRoot,
    "--json"
  )
  if (-not $All -and $scopeUseCases.Count -gt 0) {
    $validateArgs += @("--use-cases", ($scopeUseCases -join ","))
  }
  $validationResult = Invoke-PythonJson -Launcher $launcher -Arguments $validateArgs
  $jsonStart = $validationResult.Output.IndexOf('{')
  if ($jsonStart -lt 0) {
    throw "Validator did not return JSON. Output: $($validationResult.Output)"
  }
  $validation = $validationResult.Output.Substring($jsonStart) | ConvertFrom-Json
  $iterationState.validation = $validation
  $runState.iterations += $iterationState

  if ($validation.passed) {
    $consecutiveSuccesses++
    if ($consecutiveSuccesses -ge $requiredGreenRuns) {
      $runState["completedAt"] = (Get-Date).ToString("o")
      $runState["success"] = $true
      $runState["consecutiveGreenRuns"] = $consecutiveSuccesses
      $runState | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
      Write-Host "[OSS Supervisor] Production validation successful." -ForegroundColor Green
      exit 0
    }
  } else {
    $consecutiveSuccesses = 0
  }
}

$runState["completedAt"] = (Get-Date).ToString("o")
$runState["success"] = $false
$runState["consecutiveGreenRuns"] = $consecutiveSuccesses
$runState | ConvertTo-Json -Depth 8 | Set-Content -Path $resolvedResultFile -Encoding utf8
Write-Host "[OSS Supervisor] Max iterations reached without satisfying production quality policy." -ForegroundColor Yellow
exit 1