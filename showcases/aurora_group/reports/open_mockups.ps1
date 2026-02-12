# Open COM-001 page mockups in default browser
# Run from repo root: .\showcases\aurora_group\reports\open_mockups.ps1
# Or double-click this file (if PowerShell execution policy allows).

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$overview = Join-Path $scriptDir "COM-001_overview_mockup.html"
$detail  = Join-Path $scriptDir "COM-001_detail_mockup.html"

if (Test-Path $overview) { Start-Process $overview }
if (Test-Path $detail)   { Start-Process $detail }
