# Opens the agent workday: creates the marker file so agents may accept new work.
# Run from repo root or from any subdirectory. See internal/project_mgmt/AGENT_WORKDAY.md.

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$repoRoot = $scriptDir
while ($repoRoot -and -not (Test-Path (Join-Path $repoRoot ".git") -PathType Container)) {
    $parent = Split-Path -Parent $repoRoot
    if ($parent -eq $repoRoot) { break }
    $repoRoot = $parent
}
if (-not (Test-Path (Join-Path $repoRoot ".git") -PathType Container)) {
    Write-Error "Repo root (containing .git) not found. Run from repository root or tooling/project_mgmt."
}
$markerDir = Join-Path $repoRoot "internal\project_mgmt"
$markerPath = Join-Path $markerDir "AGENT_WORKDAY_OPEN"
if (-not (Test-Path $markerDir -PathType Container)) {
    New-Item -ItemType Directory -Path $markerDir -Force | Out-Null
}
$timestamp = Get-Date -Format "o"
Set-Content -Path $markerPath -Value "Workday opened at $timestamp" -Encoding UTF8 -NoNewline
Write-Host "Agent workday opened. Marker: $markerPath" -ForegroundColor Green
