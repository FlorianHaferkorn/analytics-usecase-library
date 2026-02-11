# tooling/powerbi_mcp/table_ops.ps1

Param(
    [ValidateSet("Create","Update","Delete","Get","List","CreateFromContract")]
    [string]$Operation = "List",
    [string]$ConnectionName = "local_pbip",
    [hashtable]$TableDefinition,
    [string]$DataContractPath,
    [string]$TableName
)

$ErrorActionPreference = "Stop"

# =========================================
# Helper: Load Connection
# =========================================
function Get-Connection {
    param([string]$Name)
    
    $connFile = "tooling/powerbi_mcp/connections.json"
    if (-not (Test-Path $connFile)) {
        throw "Connection file not found: $connFile. Run setup_connection.ps1 first."
    }
    
    $connections = Get-Content $connFile -Raw | ConvertFrom-Json
    if (-not $connections.$Name) {
        throw "Connection '$Name' not found in $connFile"
    }
    
    return $connections.$Name
}

# =========================================
# Helper: Convert Data Contract YAML -> TMDL Table Definition
# =========================================
function Convert-DataContractToTableDef {
    param([object]$Contract, [string]$TableName)
    
    # Find dimension or fact table by name
    $table = $null
    if ($Contract.dimension) {
        $table = $Contract.dimension | Where-Object { $_.name -eq $TableName } | Select-Object -First 1
    }
    if (-not $table -and $Contract.fact) {
        $table = $Contract.fact | Where-Object { $_.name -eq $TableName } | Select-Object -First 1
    }
    
    if (-not $table) {
        throw "Table '$TableName' not found in contract. Available: $($Contract.dimension.name -join ', '), $($Contract.fact.name -join ', ')"
    }
    
    # Map YAML types to Power BI Data Types
    $typeMap = @{
        "int" = "Int64"
        "text" = "String"
        "date" = "DateTime"
        "decimal" = "Decimal"
        "double" = "Double"
        "bool" = "Boolean"
        "datetime" = "DateTime"
    }
    
    $columns = @()
    foreach ($col in $table.columns) {
        $pbType = $typeMap[$col.type]
        if (-not $pbType) { $pbType = "String" }  # Fallback
        
        $columns += @{
            name = $col.name
            dataType = $pbType
            isHidden = ($col.role -eq "key")
            sourceColumn = $col.name
        }
    }
    
    return @{
        name = $table.name
        columns = $columns
        description = "Auto-generated from Data Contract"
    }
}

# =========================================
# Main Operations
# =========================================

$conn = Get-Connection -Name $ConnectionName

switch ($Operation) {
    "CreateFromContract" {
        if (-not $DataContractPath) {
            throw "-DataContractPath required for CreateFromContract operation"
        }
        if (-not $TableName) {
            throw "-TableName required for CreateFromContract operation"
        }
        
        Write-Host "Loading Data Contract: $DataContractPath" -ForegroundColor Gray
        
        # Load YAML (requires powershell-yaml module or manual parsing)
        if (Get-Module -ListAvailable -Name powershell-yaml) {
            Import-Module powershell-yaml
            $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
        } else {
            # Fallback: Simple YAML parsing
            Write-Host "  Warning: powershell-yaml not installed. Using basic parsing." -ForegroundColor Yellow
            $yamlContent = Get-Content $DataContractPath -Raw
            # For now, throw error - proper YAML parsing needed
            throw "powershell-yaml module required. Install: Install-Module -Name powershell-yaml"
        }
        
        $tableDef = Convert-DataContractToTableDef -Contract $contract -TableName $TableName
        
        Write-Host "Creating table: $($tableDef.name) ($($tableDef.columns.Count) columns)" -ForegroundColor Cyan
        
        # TODO: Call Power BI MCP table_operations
        # For now: Generate TMDL file manually
        $tmdlPath = "$($conn.definitionPath)\tables\$($tableDef.name).tmdl"
        
        $tab = "`t"
        $tmdlContent = "table $($tableDef.name)`r`n"
        $tmdlContent += "$tab lineageTag: $([guid]::NewGuid())`r`n`r`n"
        
        foreach ($col in $tableDef.columns) {
            $tmdlContent += "$tab column $($col.name)`r`n"
            $tmdlContent += "$tab$tab dataType: $($col.dataType)`r`n"
            $tmdlContent += "$tab$tab sourceColumn: $($col.sourceColumn)`r`n"
            if ($col.isHidden) {
                $tmdlContent += "$tab$tab isHidden`r`n"
            }
            $tmdlContent += "`r`n"
        }
        
        # Add partition (required for Power BI)
        $tmdlContent += "$tab partition $($tableDef.name) = m`r`n"
        $tmdlContent += "$tab$tab mode: import`r`n"
        $tmdlContent += "$tab$tab source =`r`n"
        $tmdlContent += "$tab$tab$tab let`r`n"
        $tmdlContent += "$tab$tab$tab$tab Source = AuroraGoldLayer{[Schema=`"dbo`",Item=`"$($tableDef.name)`"]}[Data]`r`n"
        $tmdlContent += "$tab$tab$tab in`r`n"
        $tmdlContent += "$tab$tab$tab$tab Source`r`n`r`n"
        
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($tmdlPath, $tmdlContent, $utf8)
        
        Write-Host "  Created: $tmdlPath" -ForegroundColor Green
    }
    
    "List" {
        $tablesDir = "$($conn.definitionPath)\tables"
        if (Test-Path $tablesDir) {
            $tables = Get-ChildItem $tablesDir -Filter "*.tmdl" | Select-Object -ExpandProperty BaseName
            Write-Host "Tables in model:" -ForegroundColor Cyan
            $tables | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
            return $tables
        } else {
            Write-Host "No tables directory found" -ForegroundColor Yellow
            return @()
        }
    }
    
    "Get" {
        if (-not $TableName) {
            throw "-TableName required for Get operation"
        }
        
        $tmdlPath = "$($conn.definitionPath)\tables\$TableName.tmdl"
        if (Test-Path $tmdlPath) {
            Get-Content $tmdlPath -Raw
        } else {
            throw "Table '$TableName' not found at $tmdlPath"
        }
    }
    
    default {
        Write-Host "Operation '$Operation' not yet implemented" -ForegroundColor Yellow
        Write-Host "Available: CreateFromContract, List, Get" -ForegroundColor Gray
    }
}
