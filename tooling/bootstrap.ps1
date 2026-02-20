<#
.SYNOPSIS
  Bootstrap the repository toolchain (Node + Python) reproducibly.
.DESCRIPTION
  Intended for maintainers and CI runners.
  - Installs Node dependencies for schema validation (tooling/validation npm ci)
  - Optionally creates a Python virtual environment and installs minimal deps (PyYAML)

  Run from repository root.
#>
Param(
  [switch]$InstallNodeDeps,
  [switch]$CreateVenv,
  [string]$VenvPath = "tooling/.venv",
  [switch]$InstallPythonDeps
)

$ErrorActionPreference = "Stop"

Write-Host "Bootstrap (toolchain)..." -ForegroundColor Cyan

function Assert-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

# --- Node deps (Ajv + YAML for schema validation) ---
if ($InstallNodeDeps) {
  Assert-Command "npm"
  Write-Host ">> Installing Node deps (tooling/validation npm ci)" -ForegroundColor Cyan
  Push-Location "tooling/validation"
  try {
    & npm ci
  } finally {
    Pop-Location
  }
  Write-Host ""
} else {
  Write-Host ">> Node deps: skipped (use -InstallNodeDeps to run npm ci)" -ForegroundColor DarkGray
}

# --- Python venv (optional) ---
if ($CreateVenv) {
  # Prefer py -3 on Windows
  $py = $null
  if (Get-Command "py" -ErrorAction SilentlyContinue) { $py = "py -3" }
  elseif (Get-Command "python" -ErrorAction SilentlyContinue) { $py = "python" }
  else { throw "Python not found (expected 'py -3' or 'python')." }

  $venvFull = Resolve-Path -Path "." | Select-Object -ExpandProperty Path
  $venvFull = Join-Path $venvFull $VenvPath
  if (-not (Test-Path $venvFull)) {
    Write-Host ">> Creating venv: $venvFull" -ForegroundColor Cyan
    $cmdParts = $py -split " "
    & $cmdParts[0] @($cmdParts[1..($cmdParts.Length-1)] + @("-m", "venv", $venvFull))
  } else {
    Write-Host ">> venv exists: $venvFull" -ForegroundColor DarkGray
  }

  $pip = Join-Path $venvFull "Scripts\pip.exe"
  if (-not (Test-Path $pip)) { throw "pip not found in venv: $pip" }

  if ($InstallPythonDeps) {
    Write-Host ">> Installing Python deps (minimal): pyyaml" -ForegroundColor Cyan
    & $pip install --upgrade pip
    & $pip install pyyaml
  } else {
    Write-Host ">> Python deps: skipped (use -InstallPythonDeps to install pyyaml)" -ForegroundColor DarkGray
  }
} else {
  Write-Host ">> Python venv: skipped (use -CreateVenv to create tooling/.venv)" -ForegroundColor DarkGray
}

Write-Host "Bootstrap complete." -ForegroundColor Green

