Param(
  [string]$Root = ".",
  [switch]$FailOnError
)

$ErrorActionPreference = "Stop"

if ($Root -and (Test-Path $Root)) {
  $rootPath = (Resolve-Path -Path $Root).Path
} else {
  $rootPath = (Get-Location).Path
}

$cli = Join-Path $rootPath "tooling\validation\node_modules\.bin\markdownlint-cli2.cmd"
if (-not (Test-Path $cli)) {
  Write-Host "markdownlint-cli2 not found. Run: npm ci --prefix tooling/validation" -ForegroundColor Red
  exit 1
}

Write-Host "Markdownlint (MD010 no-hard-tabs | MD041 first-line-h1 | MD047 trailing-newline)" -ForegroundColor Cyan

Push-Location $rootPath
try {
  # Auto-fix first (handles MD047 trailing newline, MD010 hard tabs automatically)
  & $cli --fix 2>&1 | Out-Null

  # Re-check — remaining violations (e.g. missing H1) must be fixed manually
  $output = & $cli 2>&1
  $exitCode = $LASTEXITCODE
} finally {
  Pop-Location
}

if ($exitCode -ne 0) {
  $output | ForEach-Object { Write-Host $_ }
  Write-Host ""
  Write-Host "FAIL: markdownlint violations found (see above)." -ForegroundColor Red
  Write-Host "  MD041: add a # Heading as the first line of the file." -ForegroundColor Yellow
  Write-Host "  MD010: replace hard tabs with spaces." -ForegroundColor Yellow
  Write-Host "  MD047: add a trailing newline at end of file." -ForegroundColor Yellow
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: markdownlint clean." -ForegroundColor Green
