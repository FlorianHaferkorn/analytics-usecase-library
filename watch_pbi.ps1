# watch_pbi.ps1 — Bridge für Power BI Desktop → Cursor
# Liest PBIDesktop.log und schreibt Fehler in .cursor/pbi_errors.log (rohe Meldungen).
# Fehler + Lösungen leben in internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md; der Agent
# soll dort nach dem Fix eine neue Zeile (Symptom | Cause | Fix) ergänzen, falls neu.
# Von Repo-Root aus starten: .\watch_pbi.ps1

$ErrorActionPreference = "Stop"
$logPath = "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\Traces\PBIDesktop.log"
$bridgeFile = Join-Path $PSScriptRoot ".cursor\pbi_errors.log"
$cursorDir = Join-Path $PSScriptRoot ".cursor"

if (!(Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
}

if (!(Test-Path $logPath)) {
    Write-Host "Power BI Log nicht gefunden: $logPath" -ForegroundColor Yellow
    Write-Host "Power BI Desktop einmal starten und eine .pbip-Datei öffnen, dann erneut versuchen." -ForegroundColor Yellow
    exit 1
}

Write-Host "Watcher läuft. Cursor beobachtet PBI-Fehler in: $bridgeFile" -ForegroundColor Green
Write-Host "Beenden mit Strg+C." -ForegroundColor Gray

Get-Content -Path $logPath -Wait -Tail 0 | ForEach-Object {
    if ($_ -match "Error" -or $_ -match "Exception" -or $_ -match "DataSource\.Error") {
        $errorEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $_"
        $errorEntry | Out-File -FilePath $bridgeFile -Append -Encoding utf8
        Write-Host "Fehler an Cursor übertragen." -ForegroundColor Red
    }
}
