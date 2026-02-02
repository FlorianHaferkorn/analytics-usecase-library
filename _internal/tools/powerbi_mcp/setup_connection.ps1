# _internal/tools/powerbi_mcp/setup_connection.ps1

Param(
    [string]$WorkspaceRoot = "showcases/aurora_group/semantic_models",
    [string]$ModelName = "CoreActionReady",
    [string]$ConnectionName = "local_pbip"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Power BI MCP Connection Setup ===" -ForegroundColor Cyan

# 1. Stelle sicher dass PBIP-Struktur existiert
$modelPath = Join-Path $WorkspaceRoot "$ModelName.SemanticModel"

if (-not (Test-Path $modelPath)) {
    Write-Host "Creating PBIP structure..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "$modelPath\definition\tables" -Force | Out-Null
    New-Item -ItemType Directory -Path "$modelPath\definition\relationships" -Force | Out-Null
    
    # model.tmdl erstellen
    $modelContent = "model Model`r`n  culture: de-DE`r`n  defaultPowerBIDataSourceVersion: PowerBI_V3`r`n`r`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("$modelPath\definition\model.tmdl", $modelContent, $utf8)
    
    # .platform erstellen
    $guid = [guid]::NewGuid().ToString()
    $platformContent = "{`r`n  `"`$schema`": `"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json`",`r`n  `"metadata`": {`r`n    `"type`": `"SemanticModel`",`r`n    `"displayName`": `"$ModelName`"`r`n  },`r`n  `"config`": {`r`n    `"version`": `"2.0`",`r`n    `"logicalId`": `"$guid`"`r`n  }`r`n}"
    [System.IO.File]::WriteAllText("$modelPath\.platform", $platformContent, $utf8)
    
    Write-Host "  Created: $modelPath\definition\model.tmdl" -ForegroundColor Green
    Write-Host "  Created: $modelPath\.platform" -ForegroundColor Green
} else {
    Write-Host "  PBIP structure already exists" -ForegroundColor Gray
}

Write-Host "`n[OK] PBIP structure ready: $modelPath" -ForegroundColor Green

# 2. Connection Details ausgeben
Write-Host "`nPower BI MCP Connection Details:" -ForegroundColor Cyan
Write-Host "  Connection Name: $ConnectionName" -ForegroundColor Gray
Write-Host "  Model Path:      $modelPath" -ForegroundColor Gray
Write-Host "  Definition Path: $modelPath\definition" -ForegroundColor Gray

# 3. Connection-Datei erstellen
$connFile = "_internal/tools/powerbi_mcp/connections.json"
New-Item -ItemType Directory -Path (Split-Path $connFile -Parent) -Force -ErrorAction SilentlyContinue | Out-Null

$conn = @{
    $ConnectionName = @{
        modelPath = $modelPath
        definitionPath = "$modelPath\definition"
        lastUsed = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
}
$connJson = $conn | ConvertTo-Json -Depth 5
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($connFile, $connJson, $utf8)

Write-Host "`n[OK] Connection saved: $connFile" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: ./_internal/tools/powerbi_mcp/orchestrate_full_model.ps1 -UseCase 'COM-001'" -ForegroundColor Gray
