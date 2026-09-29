# Closes the agent workday: removes the marker file so agents do not start new work.
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
$markerPath = Join-Path $repoRoot "internal\project_mgmt\AGENT_WORKDAY_OPEN"
if (Test-Path $markerPath -PathType Leaf) {
    Remove-Item -Path $markerPath -Force
    Write-Host "Agent workday closed. Marker removed: $markerPath" -ForegroundColor Green
} else {
    Write-Host "Marker already absent; workday was already closed." -ForegroundColor Gray
}
