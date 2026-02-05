# Test Script - Validate and Simulate Without Fabric Capacity
# Runs validation and dry-run simulations to verify configuration

param(
    [string]$Environment = "dev",
    [switch]$AllEnvironments,
    [switch]$Simulate
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fabric Automation - Test Without Fabric" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found. Please install Python 3.9-3.12" -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "..\resources\requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "  ✓ Requirements file found" -ForegroundColor Green
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    pip install -q -r $requirementsPath 2>&1 | Out-Null
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Requirements file not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Run validation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Validate Configuration Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$validateScript = Join-Path $PSScriptRoot "validate_config.py"
$validateArgs = if ($AllEnvironments) { "--all" } else { "--environment $Environment" }
if ($Simulate) { $validateArgs += " --simulate" }

python $validateScript $validateArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Validation failed. Fix errors before proceeding." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Dry-Run Simulation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$setupScript = Join-Path $PSScriptRoot "fabric_setup.py"

if ($AllEnvironments) {
    $envs = @("dev", "tst", "prd")
    foreach ($env in $envs) {
        Write-Host ""
        Write-Host "Simulating $env environment..." -ForegroundColor Yellow
        python $setupScript --environment $env --dry-run
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Simulation failed for $env" -ForegroundColor Red
        }
    }
} else {
    python $setupScript --environment $Environment --dry-run
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Simulation failed." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ All Tests Passed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration is valid and ready to use." -ForegroundColor Green
Write-Host "When you have Fabric capacity, run:" -ForegroundColor Yellow
Write-Host "  python $setupScript --environment $Environment" -ForegroundColor White
