# Quick Start Script for Fabric Architecture Setup
# Interactive PowerShell script to guide users through initial setup

param(
    [string]$Environment = "dev",
    [switch]$SkipPrerequisites
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fabric Architecture Setup - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
if (-not $SkipPrerequisites) {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Python not found. Please install Python 3.9-3.12" -ForegroundColor Red
        exit 1
    }
    
    # Check Fabric CLI
    try {
        $fabricVersion = fab --version 2>&1
        Write-Host "  ✓ Fabric CLI found: $fabricVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Fabric CLI not found. Installing..." -ForegroundColor Yellow
        pip install ms-fabric-cli==1.7.0
    }
    
    # Check if requirements.txt exists
    $requirementsPath = Join-Path $PSScriptRoot "..\resources\requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Host "  ✓ Requirements file found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Requirements file not found: $requirementsPath" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
}

# Prompt for credentials
Write-Host "Enter service principal credentials:" -ForegroundColor Cyan
$tenantId = Read-Host "Tenant ID"
$clientId = Read-Host "Client ID"
$clientSecret = Read-Host "Client Secret" -AsSecureString
$clientSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($clientSecret)
)

# Optional: GitHub PAT
$useGitHub = Read-Host "Using GitHub? (y/n)"
$githubPat = ""
if ($useGitHub -eq "y" -or $useGitHub -eq "Y") {
    $githubPatSecure = Read-Host "GitHub PAT" -AsSecureString
    $githubPat = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($githubPatSecure)
    )
}

# Set environment variables
$env:TENANT_ID = $tenantId
$env:CLIENT_ID = $clientId
$env:CLIENT_SECRET = $clientSecretPlain
if ($githubPat) {
    $env:GITHUB_PAT = $githubPat
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "..\resources\requirements.txt"
pip install -r $requirementsPath

Write-Host ""
Write-Host "Running setup for environment: $Environment" -ForegroundColor Cyan
$setupScript = Join-Path $PSScriptRoot "fabric_setup.py"

python $setupScript `
    --environment $Environment `
    --action create `
    --tenant_id $tenantId `
    --client_id $clientId `
    --client_secret $clientSecretPlain `
    --github_pat $githubPat

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Setup completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Verify workspaces in Fabric portal"
    Write-Host "  2. Review Git connections"
    Write-Host "  3. Configure deployment pipelines (optional)"
    Write-Host "  4. Run release script to deploy items"
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Setup failed. Check errors above." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

# Clean up sensitive variables
Remove-Item Env:\CLIENT_SECRET -ErrorAction SilentlyContinue
Remove-Item Env:\GITHUB_PAT -ErrorAction SilentlyContinue
