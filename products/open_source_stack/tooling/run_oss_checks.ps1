Param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath($Root)

$pythonLauncher = $null
$pythonPrefixArgs = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
  $pythonLauncher = "py"
  $pythonPrefixArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $pythonLauncher = "python"
} else {
  throw "Python launcher not found. Install 'py' or 'python' to run OSS checks."
}

function Invoke-Python {
  param(
    [string[]]$Arguments
  )

  & $pythonLauncher @pythonPrefixArgs @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Python command failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
  }
}

Write-Host "Running OSS stack checks..." -ForegroundColor Cyan

Write-Host "[1/4] Validating OSS artifacts..." -ForegroundColor Cyan
Invoke-Python @("$repoRoot/products/open_source_stack/tooling/validate_oss.py", "--root", "$repoRoot")

Write-Host "[2/4] Running OSS tooling tests..." -ForegroundColor Cyan
Push-Location "$repoRoot/products/open_source_stack/tooling"
try {
  Invoke-Python @("-m", "pytest", "tests/", "-v")
} finally {
  Pop-Location
}

Write-Host "[3/4] Running page generator tests..." -ForegroundColor Cyan
Push-Location "$repoRoot/products/open_source_stack/tooling/page_generator"
try {
  Invoke-Python @("-m", "pytest", "tests/", "-v")
} finally {
  Pop-Location
}

Write-Host "[4/4] Running metric generator tests..." -ForegroundColor Cyan
Push-Location "$repoRoot/products/open_source_stack/tooling"
try {
  Invoke-Python @("-m", "pytest", "metric_generator/tests/", "-v")
} finally {
  Pop-Location
}

Write-Host "" 
Write-Host "All OSS checks passed." -ForegroundColor Green