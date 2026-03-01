<#
.SYNOPSIS
  Daemon: überwacht .cursor/pbi_errors.log und wendet automatisch Fixes per LLM an (Azure OpenAI oder OpenAI).

.DESCRIPTION
  Läuft im Hintergrund. Bei neuem Eintrag in pbi_errors.log wird nach kurzer Verzögerung (Debounce)
  die konfigurierte LLM-API aufgerufen; die Antwort (file_edits + optional knowledge_base_row) wird
  angewendet und KNOWN_ERRORS_AND_FIXES.md bei Bedarf ergänzt.

  Voraussetzung: watch_pbi.ps1 schreibt weiterhin in .cursor/pbi_errors.log.

.PARAMETER RepoRoot
  Pfad zum Repo-Root (Standard: über dem Ordner tooling).

.PARAMETER DebounceSeconds
  Sekunden warten nach letzter Änderung an pbi_errors.log, bevor ein Fix versucht wird (Standard: 3).

.EXAMPLE
  .\tooling\pbi_auto_fix_daemon.ps1
  # Startet Daemon; Umgebungsvariablen siehe unten.

.NOTES
  Umgebungsvariablen (eine der beiden Varianten):
  - Azure OpenAI: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT (z. B. gpt-4o)
  - OpenAI:      OPENAI_API_KEY (Modell z. B. gpt-4o über AZURE_OPENAI_DEPLOYMENT oder OPENAI_MODEL)
#>

param(
  [string] $RepoRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
  [int]    $DebounceSeconds = 3
)

$ErrorActionPreference = "Stop"
$bridgeFile = Join-Path $RepoRoot ".cursor\pbi_errors.log"
$knowledgePath = Join-Path $RepoRoot "internal\project_mgmt\KNOWN_ERRORS_AND_FIXES.md"
$logPath = Join-Path $RepoRoot ".cursor\pbi_auto_fix.log"

function Write-DaemonLog {
  param([string] $Message, [string] $Level = "INFO")
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
  Write-Host $line
  try { $line | Out-File -FilePath $logPath -Append -Encoding utf8 } catch {}
}

# --- API-Konfiguration ---
$useAzure = $env:AZURE_OPENAI_API_KEY -and $env:AZURE_OPENAI_ENDPOINT -and $env:AZURE_OPENAI_DEPLOYMENT
$useOpenAI = $env:OPENAI_API_KEY
if (-not $useAzure -and -not $useOpenAI) {
  Write-DaemonLog "Weder Azure OpenAI noch OpenAI konfiguriert. Setze AZURE_OPENAI_* oder OPENAI_API_KEY." "ERROR"
  exit 1
}

$deployment = $env:AZURE_OPENAI_DEPLOYMENT ?? $env:OPENAI_MODEL ?? "gpt-4o"

# --- Hilfsfunktion: LLM aufrufen ---
function Invoke-LlmFix {
  param([string] $UserPrompt, [string] $SystemPrompt)
  $body = @{
    model   = $deployment
    messages = @(
      @{ role = "system"; content = $SystemPrompt },
      @{ role = "user";   content = $UserPrompt }
    )
    response_format = @{ type = "json_object" }
    temperature     = 0.1
  } | ConvertTo-Json -Depth 10

  if ($useAzure) {
    $uri = "$($env:AZURE_OPENAI_ENDPOINT.TrimEnd('/'))/openai/deployments/$deployment/chat/completions?api-version=2024-02-15-preview"
    $headers = @{ "api-key" = $env:AZURE_OPENAI_API_KEY; "Content-Type" = "application/json" }
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -Encoding utf8
    $response.choices[0].message.content
  } else {
    $uri = "https://api.openai.com/v1/chat/completions"
    $headers = @{ "Authorization" = "Bearer $env:OPENAI_API_KEY"; "Content-Type" = "application/json" }
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -Encoding utf8
    $response.choices[0].message.content
  }
}

# --- Hilfsfunktion: Knowledge-Base-Zeile einfügen ---
function Add-KnowledgeBaseRow {
  param([string] $KbPath, [string] $Section, [string] $Symptom, [string] $Cause, [string] $Fix)
  $content = Get-Content -Path $KbPath -Raw -Encoding utf8
  $marker = "## $Section"
  $idx = $content.IndexOf($marker)
  if ($idx -lt 0) {
    $marker = "## " + ($Section -replace "\s*/\s*.*", "")
    $idx = $content.IndexOf($marker)
  }
  if ($idx -lt 0) {
    Write-DaemonLog "Section '$Section' nicht gefunden; füge am Ende ein." "WARN"
    $newRow = "`n| $Symptom | $Cause | $Fix |`n"
    Add-Content -Path $KbPath -Value $newRow -Encoding utf8
    return
  }
  $afterSection = $content.Substring($idx)
  $endOfTable = $afterSection.IndexOf("`n---")
  if ($endOfTable -lt 0) { $endOfTable = $afterSection.IndexOf("`n## ") }
  if ($endOfTable -lt 0) { $endOfTable = $afterSection.Length }
  $insertPos = $idx + $endOfTable
  $newRow = "`n| $Symptom | $Cause | $Fix |"
  $content = $content.Insert($insertPos, $newRow)
  Set-Content -Path $KbPath -Value $content -NoNewline -Encoding utf8
}

# --- Einmaliger Fix-Versuch ---
function Invoke-OneFix {
  if (-not (Test-Path $bridgeFile)) { return }
  $tail = Get-Content -Path $bridgeFile -Tail 30 -Encoding utf8 -ErrorAction SilentlyContinue
  if (-not $tail) { return }
  $errorBlock = $tail -join "`n"
  if (-not (Test-Path $knowledgePath)) {
    Write-DaemonLog "KNOWN_ERRORS_AND_FIXES.md nicht gefunden." "WARN"
    return
  }
  $knowledgeContent = Get-Content -Path $knowledgePath -Raw -Encoding utf8

  $systemPrompt = @"
Du bist ein Power-BI-PBIP-Experte. Du bekommst einen Fehlerauszug aus der Power-Bi-Desktop-Log und die Wissensdatenbank (KNOWN_ERRORS_AND_FIXES).
Antworte NUR mit einem einzelnen JSON-Objekt, sonst nichts.

Format:
{
  "file_edits": [
    { "path": "relativer Pfad ab Repo-Root (z.B. products/fabric/powerbi/dist/.../definition/model.tmdl)", "search": "exakter zu suchender Text (Newlines als \\n)", "replace": "Ersatztext" }
  ],
  "knowledge_base_row": { "section": "TMDL / PBIP oder DAX / measures oder datasetReference usw.", "symptom": "...", "cause": "...", "fix": "..." }
}

Regeln:
- path nur unter products/fabric/powerbi/dist oder internal/project_mgmt; Forward-Slashes.
- search/replace exakt (escaping in JSON); nur die nötigste Änderung.
- Wenn du keinen sicheren Fix kennst: "file_edits": [], "knowledge_base_row": null.
- section muss exakt zu einer Überschrift in der Wissensdatenbank passen (z.B. "TMDL / PBIP").
"@

  $userPrompt = @"
Fehlerauszug (letzte Zeilen aus pbi_errors.log):
---
$errorBlock
---

Auszug Wissensdatenbank (Known errors and fixes):
---
$($knowledgeContent.Substring(0, [Math]::Min(12000, $knowledgeContent.Length)))
---

Antworte nur mit dem JSON-Objekt.
"@

  try {
    $jsonText = Invoke-LlmFix -UserPrompt $userPrompt -SystemPrompt $systemPrompt
    $jsonText = ($jsonText -replace '(?s)^\s*```(?:json)?\s*', '' -replace '\s*```\s*$', '').Trim()
    $json = $jsonText | ConvertFrom-Json
  } catch {
    Write-DaemonLog "LLM-Aufruf oder JSON-Parse fehlgeschlagen: $_" "ERROR"
    return
  }

  $editCount = 0
  foreach ($ed in $json.file_edits) {
    $fullPath = Join-Path $RepoRoot ($ed.path -replace "/", [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path $fullPath)) {
      Write-DaemonLog "Datei nicht gefunden: $fullPath" "WARN"
      continue
    }
    $search = $ed.search -replace "\\n", "`n"
    $replace = $ed.replace -replace "\\n", "`n"
    $content = Get-Content -Path $fullPath -Raw -Encoding utf8
    if (-not $content.Contains($search)) {
      Write-DaemonLog "Search-Text in Datei nicht gefunden: $($ed.path)" "WARN"
      continue
    }
    $newContent = $content.Replace($search, $replace)
    Set-Content -Path $fullPath -Value $newContent -NoNewline -Encoding utf8
    $editCount++
    Write-DaemonLog "Geändert: $($ed.path)"
  }

  if ($json.knowledge_base_row -and $json.knowledge_base_row.section) {
    Add-KnowledgeBaseRow -KbPath $knowledgePath `
      -Section $json.knowledge_base_row.section `
      -Symptom $json.knowledge_base_row.symptom `
      -Cause $json.knowledge_base_row.cause `
      -Fix $json.knowledge_base_row.fix
    Write-DaemonLog "Wissensdatenbank ergänzt: $($json.knowledge_base_row.symptom)"
  }

  if ($editCount -gt 0) {
    Write-DaemonLog "Auto-Fix abgeschlossen: $editCount Datei(en) geändert."
  } else {
    Write-DaemonLog "Keine Dateiänderungen vorgenommen (LLM gab keine oder ungültige file_edits)."
  }
}

# --- Watcher ---
if (-not (Test-Path $bridgeFile)) {
  $cursorDir = Join-Path $RepoRoot ".cursor"
  if (-not (Test-Path $cursorDir)) { New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null }
  Write-DaemonLog "Bridge-Datei noch nicht vorhanden. Starte watch_pbi.ps1 in einem anderen Terminal. Warte auf .cursor\pbi_errors.log ..."
}

$global:lastPbiErrorLogEvent = [datetime]::MinValue
$fsw = New-Object System.IO.FileSystemWatcher
$fsw.Path = Join-Path $RepoRoot ".cursor"
$fsw.Filter = "pbi_errors.log"
$fsw.EnableRaisingEvents = $true

$onChange = {
  $global:lastPbiErrorLogEvent = Get-Date
}

Register-ObjectEvent -InputObject $fsw -EventName Changed -Action $onChange | Out-Null
Register-ObjectEvent -InputObject $fsw -EventName Created -Action $onChange | Out-Null

Write-DaemonLog "Daemon gestartet (RepoRoot=$RepoRoot, Debounce=${DebounceSeconds}s). Beenden mit Strg+C."
try {
  while ($true) {
    Start-Sleep -Seconds 1
    if ($global:lastPbiErrorLogEvent -eq [datetime]::MinValue) { continue }
    $elapsed = (Get-Date) - $global:lastPbiErrorLogEvent
    if ($elapsed.TotalSeconds -lt $DebounceSeconds) { continue }
    $global:lastPbiErrorLogEvent = [datetime]::MinValue
    Invoke-OneFix
  }
} finally {
  $fsw.EnableRaisingEvents = $false
  Get-EventSubscriber | Where-Object { $_.SourceObject -eq $fsw } | Unregister-Event -Force -ErrorAction SilentlyContinue
  Write-DaemonLog "Daemon beendet."
}
