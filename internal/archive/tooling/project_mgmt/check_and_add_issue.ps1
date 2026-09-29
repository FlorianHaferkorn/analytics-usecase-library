# Check if a GitHub issue with the given title (or pattern) exists; if not, create it.
# Usage: .\check_and_add_issue.ps1 -Title "[Epic] Strategy Pattern / AI urgency and automated reasoning"
#        .\check_and_add_issue.ps1 -Title "Strategy Pattern"
# Run from repo root. Uses .env (GITHUB_TOKEN) or gh auth token.

param(
    [Parameter(Mandatory = $true)]
    [string]$Title,
    [string]$Body = "",
    [string]$Milestone = "Phase 2",
    [string[]]$Labels = @("epic")
)

$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
Push-Location $repoRoot
try {
    . (Join-Path $scriptDir "load_project_env.ps1")
    $token = $env:GITHUB_TOKEN; if (-not $token) { $token = $env:GH_TOKEN }; if (-not $token) { try { $token = (gh auth token 2>$null) } catch {} }
    if (-not $token) { Write-Error "Set GITHUB_TOKEN in .env or run gh auth login." }
    $owner = "FlorianHaferkorn"; $name = "analytics-usecase-library"
    if ($env:GITHUB_REPOSITORY -match "^([^/]+)/(.+)$") { $owner = $Matches[1]; $name = $Matches[2] }
    $h = @{ "Authorization" = "Bearer $token"; "Accept" = "application/vnd.github+json"; "X-GitHub-Api-Version" = "2022-11-28" }
    $base = "https://api.github.com/repos/$owner/$name"
    $all = @(); $page = 1
    do {
        $r = Invoke-RestMethod -Method Get -Uri "$base/issues?state=all&per_page=100&page=$page" -Headers $h
        $all += $r; $page++; if ($r.Count -lt 100) { break }
    } while ($true)
    $match = $all | Where-Object { $_.title -eq $Title -or ($Title.Length -lt 50 -and $_.title -like "*$Title*") } | Select-Object -First 1
    if ($match) {
        Write-Host "Issue already exists: #$($match.number) - $($match.title)" -ForegroundColor Green
        exit 0
    }
    $ms = Invoke-RestMethod -Method Get -Uri "$base/milestones?state=all" -Headers $h
    $msId = ($ms | Where-Object { $_.title -eq $Milestone } | Select-Object -First 1).number
    $payload = @{ title = $Title; body = $Body; labels = $Labels }
    if ($msId) { $payload.milestone = $msId }
    $new = Invoke-RestMethod -Method Post -Uri "$base/issues" -Headers $h -Body ($payload | ConvertTo-Json) -ContentType "application/json"
    Write-Host "Created issue #$($new.number): $($new.title)" -ForegroundColor Cyan
    Write-Host "URL: $($new.html_url)" -ForegroundColor Gray
} finally {
    Pop-Location
}
