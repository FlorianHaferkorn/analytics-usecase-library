# Install pre-commit hook for ontology registry validation.
# Validates Python 3 availability before installing.
# Run from repository root.

$ErrorActionPreference = "Stop"

# Resolve repo root (run from repo root or tooling/git-hooks)
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    $repoRoot = if ($PSScriptRoot) {
        (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    } else {
        (Get-Location).Path
    }
}

# Prefer py -3 (Windows launcher), fallback to python
$pyOk = $false
$pyCmd = $null

try {
    $v = & py -3 --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $v) {
        $pyCmd = "py -3"
        $pyOk = $true
    }
} catch {
    # ignore
}

if (-not $pyOk) {
    try {
        $v = & python --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v) {
            $pyCmd = "python"
            $pyOk = $true
        }
    } catch {
        # ignore
    }
}

if (-not $pyOk) {
    Write-Error "Python 3 not found. Please install Python 3 or ensure 'py -3' or 'python' is on PATH. Hook installation aborted."
    exit 1
}

$hookDir = Join-Path $repoRoot ".git\hooks"
$hookPath = Join-Path $hookDir "pre-commit"
$sourcePath = Join-Path $repoRoot "tooling\git-hooks\pre-commit"

if (-not (Test-Path $sourcePath)) {
    Write-Error "Source hook not found: $sourcePath"
    exit 1
}

if (-not (Test-Path $hookDir)) {
    New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
}

# Copy hook (git ignores executable bit on Windows; shell script runs via sh/Git Bash)
Copy-Item -Path $sourcePath -Destination $hookPath -Force
Write-Host "Pre-commit hook installed: $hookPath"
Write-Host "It runs: $pyCmd tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict"
Write-Host "Commit will be blocked if registry validation fails."
