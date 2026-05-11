<#
.SYNOPSIS
  Checks that the local environment is ready to work in this repository.
.DESCRIPTION
  Verifies Python, Node/npm, and the Node deps for schema validation.
  Prints actionable fix instructions for every missing prerequisite.
  Does not install anything — it only checks and guides.

  Run from the repository root:
    .\tooling\check_local_setup.ps1
#>

$ErrorActionPreference = "SilentlyContinue"

$ok    = 0
$warn  = 0
$fail  = 0

function Write-OK   { param($msg) Write-Host "  OK    $msg" -ForegroundColor Green;  $script:ok++ }
function Write-WARN { param($msg) Write-Host "  WARN  $msg" -ForegroundColor Yellow; $script:warn++ }
function Write-FAIL { param($msg) Write-Host "  FAIL  $msg" -ForegroundColor Red;    $script:fail++ }
function Write-Fix  { param($msg) Write-Host "        FIX: $msg" -ForegroundColor DarkYellow }

Write-Host ""
Write-Host "Analytics Framework — local setup check" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

# ---------- Python ----------
Write-Host "Python"
$pyCmd = $null
foreach ($c in @("py", "python3", "python")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $pyCmd = $c; break }
}
if (-not $pyCmd) {
    Write-FAIL "Python 3.11+ not found on PATH"
    Write-Fix  "Install from https://www.python.org/downloads/ (add to PATH)"
} else {
    $pyVer = & $pyCmd --version 2>&1
    if ($pyVer -match "3\.(1[1-9]|[2-9]\d)") {
        Write-OK   "Python found: $pyVer"
    } else {
        Write-WARN "Python found but version may be below 3.11: $pyVer"
        Write-Fix  "Upgrade to Python 3.11+ for full compatibility"
    }
}

# requirements.txt
$reqFile = Join-Path $PSScriptRoot "..\requirements.txt"
if (Test-Path $reqFile) {
    if ($pyCmd) {
        $pipList = & $pyCmd -m pip list 2>&1 | Out-String
        $missing = @()
        foreach ($line in (Get-Content $reqFile)) {
            $pkg = ($line -split "[=><!]")[0].Trim()
            if ($pkg -and -not ($pkg.StartsWith("#")) -and ($pipList -notmatch [regex]::Escape($pkg))) {
                $missing += $pkg
            }
        }
        if ($missing.Count -eq 0) {
            Write-OK "Python packages installed (requirements.txt)"
        } else {
            Write-WARN "Some Python packages missing: $($missing -join ', ')"
            Write-Fix  "pip install -r requirements.txt"
        }
    }
} else {
    Write-WARN "requirements.txt not found at repo root"
}

Write-Host ""

# ---------- Node / npm ----------
Write-Host "Node.js (for JSON-schema validation)"
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-FAIL "Node.js not found on PATH"
    Write-Fix  "Install from https://nodejs.org/ (LTS, v18+)"
} else {
    $nodeVer = & node --version 2>&1
    Write-OK   "Node found: $nodeVer"
}

if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-FAIL "npm not found"
    Write-Fix  "npm ships with Node.js — reinstall Node"
} else {
    # Check if node_modules installed for schema validation
    $nmPath = Join-Path $PSScriptRoot "validation\node_modules"
    if (Test-Path $nmPath) {
        Write-OK "Schema validation deps installed (tooling/validation/node_modules)"
    } else {
        Write-FAIL "Schema validation deps missing"
        Write-Fix  "cd tooling\validation; npm ci; cd ..\.."
    }
}

Write-Host ""

# ---------- PowerShell version ----------
Write-Host "PowerShell"
$psVer = $PSVersionTable.PSVersion
if ($psVer.Major -ge 7) {
    Write-OK "PowerShell $($psVer.ToString()) (good)"
} else {
    Write-WARN "PowerShell $($psVer.ToString()) — PowerShell 7+ is recommended"
    Write-Fix  "Install from https://aka.ms/powershell or: winget install Microsoft.PowerShell"
}

Write-Host ""

# ---------- Stage 1 dry run ----------
Write-Host "Stage 1 gate"
$stage1 = Join-Path $PSScriptRoot "run_stage1_checks.ps1"
if (Test-Path $stage1) {
    Write-OK "run_stage1_checks.ps1 found"
    Write-Host "        To run: .\tooling\run_stage1_checks.ps1" -ForegroundColor DarkGray
} else {
    Write-FAIL "run_stage1_checks.ps1 not found — check you are running from the repo root"
}

Write-Host ""

# ---------- Summary ----------
Write-Host "========================================"
if ($fail -gt 0) {
    Write-Host "Result: $fail issue(s) to fix before you can run Stage 1." -ForegroundColor Red
    Write-Host ""
    Write-Host "After fixing, re-run this script to confirm everything is ready."
} elseif ($warn -gt 0) {
    Write-Host "Result: Setup mostly OK ($warn warning(s)). You can likely run Stage 1." -ForegroundColor Yellow
} else {
    Write-Host "Result: All checks passed. You are ready to work in this repo." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Read ONBOARDING.md for the one-hour walkthrough"
    Write-Host "  2. Run: .\tooling\run_stage1_checks.ps1"
    Write-Host "  3. Run: python tooling/health_scorecard.py"
}
Write-Host ""
Write-Host "Stuck? See internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md"
Write-Host ""
