# Loads .env from repo root into process environment. Safe to dot-source; no error if .env missing.
# Use: . "$PSScriptRoot\Load-ProjectEnv.ps1"
# .env format: one KEY=value per line (no spaces around =). Comment lines with #.
# Ensures GITHUB_TOKEN and optional PROJECT_* are set so you don't have to type them each time.

$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$repoRoot = $scriptDir
while ($repoRoot -and -not (Test-Path (Join-Path $repoRoot ".git") -PathType Container)) {
    $parent = Split-Path -Parent $repoRoot
    if ($parent -eq $repoRoot) { break }
    $repoRoot = $parent
}
$envPath = Join-Path $repoRoot ".env"
if (Test-Path $envPath -PathType Leaf) {
    Get-Content $envPath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -and $line -notmatch '^\s*#') {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
                $key = $Matches[1]
                $val = $Matches[2].Trim()
                if ($val -match '^["''](.+)["'']\s*$') { $val = $Matches[1] }
                Set-Item -Path "Env:$key" -Value $val -Force
            }
        }
    }
}
