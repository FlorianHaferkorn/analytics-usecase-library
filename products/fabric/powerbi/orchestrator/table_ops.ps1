# products/fabric/powerbi/orchestrator/table_ops.ps1

Param(
    [ValidateSet("Create","Update","Delete","Get","List","CreateFromContract","ExportFromContract","PatchDescriptionsFromContract","PatchPartitionSourceToBlank","PatchAddSummarizeByNone","WriteExpressionsTmdl","PatchPartitionSourceToGoldDataPath","WriteDirectLakeExpression","PatchPartitionSourceToDirectLake","WriteModelFiles")]
    [string]$Operation = "List",
    [string]$ConnectionName = "local_pbip",
    [hashtable]$TableDefinition,
    [string]$DataContractPath,
    [string]$TableName,
    [string]$OutJsonPath,
    [string]$UseCase,
    [string]$DefinitionPath,
    [ValidateSet("AuroraGoldLayer","Blank","GoldDataPath")]
    [string]$PartitionSourceStyle = "Blank",
    # Direct Lake parameters
    [ValidateSet("Import","DirectLake")]
    [string]$StorageMode = "Import",
    [string]$WorkspaceId,
    [string]$LakehouseId,
    [string]$ExpressionName = "DL_Lakehouse",
    [string]$SchemaName = "dbo",
    # WriteModelFiles parameters
    [string]$ModelName,         # Database/model name (e.g. "Commercial"); defaults to parent folder stem
    [string]$Culture = "de-DE"  # Default culture for model.tmdl
)

$ErrorActionPreference = "Stop"

# =========================================
# Helper: Load Connection
# =========================================
function Get-Connection {
    param([string]$Name)
    
    $connFile = Join-Path $PSScriptRoot "connections.json"
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
# Helper: PBI dataType -> Power Query M type name (for #table type table [...])
# =========================================
function Get-MTypeFromPbiDataType {
    param([string]$PbiDataType)
    $m = @{
        "Int64" = "Int64.Type"
        "DateTime" = "DateTime.Type"
        "String" = "Text.Type"
        "Decimal" = "Number.Type"
        "Double" = "Double.Type"
        "Boolean" = "Logical.Type"
    }
    if ($m[$PbiDataType]) { return $m[$PbiDataType] }
    return "Text.Type"
}

# =========================================
# Helper: M identifier for type table - use #"Name" if name has space/special chars
# =========================================
function Get-MQuotedColumnRef {
    param([string]$ColumnName)
    $name = $ColumnName.Trim()
    if ($name -match '^[a-zA-Z_][a-zA-Z0-9_]*$') { return $name }
    return '#"' + $name.Replace('"', '""') + '"'
}

# =========================================
# Helper: Build Direct Lake entity partition block (TMDL)
# Returns the full partition block lines (without table-level indentation).
# =========================================
function Get-DirectLakePartitionBlock {
    param(
        [string]$TableName,
        [string]$EntityName,       # Delta table name in Lakehouse (defaults to TableName)
        [string]$SchemaName = "dbo",
        [string]$ExpressionName = "DL_Lakehouse"
    )
    if (-not $EntityName) { $EntityName = $TableName }
    $tab = "`t"
    $lines = @()
    $lines += "${tab}partition $TableName = entity"
    $lines += "${tab}${tab}mode: directLake"
    $lines += "${tab}${tab}source"
    $lines += "${tab}${tab}${tab}entityName: $EntityName"
    $lines += "${tab}${tab}${tab}schemaName: $SchemaName"
    $lines += "${tab}${tab}${tab}expressionSource: $ExpressionName"
    return $lines
}

# =========================================
# Helper: Build Direct Lake named expression M query
# =========================================
function Get-DirectLakeExpressionContent {
    param(
        [string]$WorkspaceId,
        [string]$LakehouseId,
        [string]$ExpressionName = "DL_Lakehouse"
    )
    $url = "https://onelake.dfs.fabric.microsoft.com/$WorkspaceId/$LakehouseId"
    $lineageTag = [guid]::NewGuid()
    $tab = "`t"
    $content  = "expression $ExpressionName =`r`n"
    $content += "${tab}let`r`n"
    $content += "${tab}${tab}Source = AzureStorage.DataLake(`"$url`", [HierarchicalNavigation = true, Timeout = Duration.From(null)])`r`n"
    $content += "${tab}in`r`n"
    $content += "${tab}${tab}Source`r`n"
    $content += "${tab}lineageTag: $lineageTag`r`n"
    $content += "${tab}annotation PBI_NavigationStepName = $ExpressionName`r`n"
    $content += "${tab}annotation PBI_ResultType = Table`r`n"
    return $content
}

# =========================================
# Helper: Build partition source M expression (AuroraGoldLayer, Blank #table, or GoldDataPath)
# =========================================
function Get-PartitionSourceExpression {
    param([string]$Style, [string]$TableName, [array]$Columns)
    if ($Style -eq "Blank") {
        $parts = @()
        foreach ($col in $Columns) {
            $mType = Get-MTypeFromPbiDataType -PbiDataType $col.dataType
            if (-not $mType) { $mType = "Text.Type" }
            $mRef = Get-MQuotedColumnRef -ColumnName $col.name
            $parts += "$mRef = $mType"
        }
        $typeTable = "type table [" + ($parts -join ", ") + "]"
        return "#table($typeTable, {})"
    }
    if ($Style -eq "GoldDataPath") {
        $subDir = if ($TableName -match '^dim_') { "dimensions" } else { "facts" }
        return "let`r`n`t`tSource = Folder.Files(GoldDataPath & `"`/$subDir/$TableName`"),`r`n`t`tFilteredFiles = Table.SelectRows(Source, each Text.EndsWith([Name], `".parquet`")),`r`n`t`tFirstFile = FilteredFiles{0}[Content],`r`n`t`tParquetData = Parquet.Document(FirstFile)`r`n`t`tin`r`n`t`tParquetData"
    }
    return "AuroraGoldLayer{[Schema=`"dbo`",Item=`"$TableName`"]}[Data]"
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
        "number" = "Double"
        "bool" = "Boolean"
        "boolean" = "Boolean"
        "datetime" = "DateTime"
        "currency" = "Decimal"
    }
    
    $columns = @()
    foreach ($col in $table.columns) {
        $pbType = $typeMap[$col.type]
        if (-not $pbType) { $pbType = "String" }  # Fallback
        $colDesc = $null
        if ($col.description) { $colDesc = $col.description }
        elseif ($col.purpose) { $colDesc = $col.purpose }
        $columns += @{
            name = $col.name
            dataType = $pbType
            isHidden = ($col.role -eq "key")
            sourceColumn = $col.name
            description = $colDesc
        }
    }
    $tableDesc = $table.description
    if (-not $tableDesc -and $table.purpose) { $tableDesc = $table.purpose }
    if (-not $tableDesc) { $tableDesc = "Auto-generated from Data Contract" }
    
    return @{
        name = $table.name
        columns = $columns
        description = $tableDesc
    }
}

# =========================================
# Main Operations
# =========================================

$conn = $null
try { $conn = Get-Connection -Name $ConnectionName } catch { $conn = $null }

switch ($Operation) {
    "ExportFromContract" {
        if (-not $DataContractPath -or -not (Test-Path $DataContractPath)) {
            throw "-DataContractPath required and must exist for ExportFromContract"
        }
        $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
        $tables = @()
        foreach ($t in @($contract.dimension)) {
            if (-not $t.name) { continue }
            $tables += Convert-DataContractToTableDef -Contract $contract -TableName $t.name
        }
        foreach ($t in @($contract.fact)) {
            if (-not $t.name) { continue }
            $tables += Convert-DataContractToTableDef -Contract $contract -TableName $t.name
        }
        $payload = @{ tables = $tables; source = $DataContractPath; useCase = $UseCase; timestamp = (Get-Date -Format "o") }
        $jsonPath = $OutJsonPath
        if (-not $jsonPath -and $UseCase) {
            $outDir = Join-Path $PSScriptRoot "out"
            if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
            $jsonPath = Join-Path $outDir "table_ops_$UseCase.json"
        }
        if ($jsonPath) {
            $payload | ConvertTo-Json -Depth 6 | Set-Content -Path $jsonPath -Encoding utf8
            Write-Host "  Wrote: $jsonPath ($($tables.Count) tables)" -ForegroundColor Green
        }
        return $tables
    }
    "CreateFromContract" {
        if (-not $conn) { throw "Connection required for CreateFromContract. Run setup_connection.ps1 first." }
        if (-not $DataContractPath) {
            throw "-DataContractPath required for CreateFromContract operation"
        }
        if (-not $TableName) {
            throw "-TableName required for CreateFromContract operation"
        }
        
        Write-Host "Loading Data Contract: $DataContractPath" -ForegroundColor Gray
        $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
        
        $tableDef = Convert-DataContractToTableDef -Contract $contract -TableName $TableName
        
        Write-Host "Creating table: $($tableDef.name) ($($tableDef.columns.Count) columns)" -ForegroundColor Cyan
        
        $repoRoot = (Get-Location).Path
        $defPath = if ($DefinitionPath) {
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else {
            if (-not $conn) { throw "Connection or -DefinitionPath required for CreateFromContract." }
            Join-Path $repoRoot $conn.definitionPath
        }
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) { New-Item -ItemType Directory -Path $tablesDir -Force | Out-Null }
        $tmdlPath = Join-Path $tablesDir "$($tableDef.name).tmdl"
        
        $tab = "`t"
        $tmdlContent = ""
        if ($tableDef.description) {
            foreach ($line in ($tableDef.description -split "\r?\n")) {
                $tmdlContent += "/// " + $line.Trim() + "`r`n"
            }
        }
        $tmdlContent += "table $($tableDef.name)`r`n"
        $tmdlContent += "$tab lineageTag: $([guid]::NewGuid())`r`n`r`n"
        
        foreach ($col in $tableDef.columns) {
            if ($col.description) {
                foreach ($line in ($col.description -split "\r?\n")) {
                    $tmdlContent += "$tab/// " + $line.Trim() + "`r`n"
                }
            }
            $colDecl = if ($col.name -match ' ') { "column '$($col.name)'" } else { "column $($col.name)" }
            $tmdlContent += "$tab $colDecl`r`n"
            $tmdlContent += "$tab$tab dataType: $($col.dataType)`r`n"
            $tmdlContent += "$tab$tab sourceColumn: $($col.sourceColumn)`r`n"
            $tmdlContent += "$tab$tab summarizeBy: none`r`n"
            if ($col.isHidden) {
                $tmdlContent += "$tab$tab isHidden`r`n"
            }
            $tmdlContent += "`r`n"
        }
        
        # Add partition - Import (M) or DirectLake (entity partition)
        if ($StorageMode -eq "DirectLake") {
            if (-not $LakehouseId -or -not $WorkspaceId) {
                # Try to read from data contract settings
                $contractSettings = $contract.settings
                if ($contractSettings) {
                    if (-not $LakehouseId -and $contractSettings.lakehouse_id) { $LakehouseId = $contractSettings.lakehouse_id }
                    if (-not $WorkspaceId -and $contractSettings.workspace_id)  { $WorkspaceId  = $contractSettings.workspace_id  }
                }
                if (-not $LakehouseId -or -not $WorkspaceId) {
                    throw "StorageMode=DirectLake requires -WorkspaceId and -LakehouseId (or settings.workspace_id / settings.lakehouse_id in the data contract)."
                }
            }
            $dlLines = Get-DirectLakePartitionBlock -TableName $tableDef.name -SchemaName $SchemaName -ExpressionName $ExpressionName
            foreach ($line in $dlLines) { $tmdlContent += $line + "`r`n" }
            $tmdlContent += "`r`n"
        } else {
            $sourceExpr = Get-PartitionSourceExpression -Style $PartitionSourceStyle -TableName $tableDef.name -Columns $tableDef.columns
            $tmdlContent += "$tab partition $($tableDef.name) = m`r`n"
            $tmdlContent += "$tab$tab mode: import`r`n"
            $tmdlContent += "$tab$tab source =`r`n"
            if ($PartitionSourceStyle -eq "GoldDataPath") {
                foreach ($line in ($sourceExpr -split "\r?\n")) {
                    $tmdlContent += "$tab$tab$tab" + $line + "`r`n"
                }
            } else {
                $tmdlContent += "$tab$tab$tab let`r`n"
                $tmdlContent += "$tab$tab$tab$tab Source = $sourceExpr`r`n"
                $tmdlContent += "$tab$tab$tab in`r`n"
                $tmdlContent += "$tab$tab$tab$tab Source`r`n"
            }
            $tmdlContent += "`r`n"
        }
        
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($tmdlPath, $tmdlContent, $utf8)
        
        Write-Host "  Created: $tmdlPath" -ForegroundColor Green
        if ($OutJsonPath) {
            @{ table = $tableDef; source = $DataContractPath } | ConvertTo-Json -Depth 6 | Set-Content -Path $OutJsonPath -Encoding utf8
            Write-Host "  Wrote: $OutJsonPath" -ForegroundColor Gray
        }
    }
    
    "PatchDescriptionsFromContract" {
        if (-not $DataContractPath -or -not (Test-Path $DataContractPath)) {
            throw "-DataContractPath required and must exist for PatchDescriptionsFromContract"
        }
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else {
            if (-not $conn) { throw "Connection or -DefinitionPath required for PatchDescriptionsFromContract." }
            Join-Path (Get-Location).Path $conn.definitionPath
        }
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) {
            Write-Host "  No tables directory: $tablesDir" -ForegroundColor Yellow
            return
        }
        Write-Host "Patching table descriptions from contract: $DataContractPath" -ForegroundColor Gray
        $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
        $tableNames = @()
        if ($contract.dimension) { $tableNames += @($contract.dimension | ForEach-Object { $_.name }) }
        if ($contract.fact) { $tableNames += @($contract.fact | ForEach-Object { $_.name }) }
        $patched = 0
        foreach ($tname in $tableNames) {
            if (-not $tname) { continue }
            $tmdlPath = Join-Path $tablesDir "$tname.tmdl"
            if (-not (Test-Path $tmdlPath)) { continue }
            try {
                $tableDef = Convert-DataContractToTableDef -Contract $contract -TableName $tname
                $content = [System.IO.File]::ReadAllText($tmdlPath)
                $lines = $content -split "\r?\n"
                $bodyStartIndex = 0
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    if ($lines[$i] -match '^\s*table\s+') { $bodyStartIndex = $i; break }
                }
                $descLines = @()
                foreach ($line in ($tableDef.description -split "\r?\n")) {
                    $trimmed = $line.Trim()
                    if ($trimmed) { $descLines += "/// " + $trimmed }
                }
                $body = $lines[$bodyStartIndex..($lines.Count - 1)] -join "`r`n"
                $newContent = if ($descLines.Count -gt 0) {
                    ($descLines -join "`r`n") + "`r`n" + $body
                } else {
                    $body
                }
                $utf8 = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($tmdlPath, $newContent, $utf8)
                $patched++
                Write-Host "  Patched: $tname" -ForegroundColor Green
            } catch {
                Write-Host "  WARNING: Could not patch $tname : $_" -ForegroundColor Yellow
            }
        }
        Write-Host "  Patched $patched table(s)" -ForegroundColor Green
    }
    
    "PatchPartitionSourceToBlank" {
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else {
            if (-not $conn) { throw "Connection or -DefinitionPath required for PatchPartitionSourceToBlank." }
            Join-Path (Get-Location).Path $conn.definitionPath
        }
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) {
            Write-Host "  No tables directory: $tablesDir" -ForegroundColor Yellow
            return
        }
        Write-Host "Patching partition sources to Blank (local open): $tablesDir" -ForegroundColor Gray
        $patched = 0
        Get-ChildItem $tablesDir -Filter "*.tmdl" | ForEach-Object {
            $tmdlPath = $_.FullName
            $baseName = $_.BaseName
            if ($baseName -eq "_Measures" -or $baseName -eq "_ActionReady_Logic") { return }
            $content = [System.IO.File]::ReadAllText($tmdlPath)
            # Fix M "Ungueltiger Bezeichner": single-quoted column names in #table must be #"Name"
            if ($content -match "#table\s*\(\s*type\s+table" -and $content -match "'[^']+'\s*=\s*\w+\.Type") {
                $content = $content -replace "'([^']+)'\s*=\s*(\w+\.Type)", '#"$1" = $2'
                $utf8 = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($tmdlPath, $content, $utf8)
                $patched++
                Write-Host "  Fixed M identifiers: $baseName" -ForegroundColor Green
                return
            }
            if ($content -notmatch "AuroraGoldLayer") { return }
            # Parse column name + dataType from TMDL (column X or column 'Y' / dataType: Z)
            $cols = @()
            $lines = $content -split "\r?\n"
            for ($i = 0; $i -lt $lines.Count - 1; $i++) {
                if ($lines[$i] -match '^\tcolumn\s+(.+)$') {
                    $colName = $matches[1].Trim()
                    if ($colName.StartsWith("'") -and $colName.EndsWith("'") -and $colName.Length -gt 2) { $colName = $colName.Substring(1, $colName.Length - 2) }
                    elseif ($colName.StartsWith('"') -and $colName.EndsWith('"') -and $colName.Length -gt 2) { $colName = $colName.Substring(1, $colName.Length - 2) }
                    if ($lines[$i + 1] -match '^\t\tdataType:\s+(\w+)$') {
                        $cols += @{ name = $colName; dataType = $matches[1] }
                    }
                }
            }
            if ($cols.Count -eq 0) {
                Write-Host "  WARNING: No columns parsed from $baseName" -ForegroundColor Yellow
                return
            }
            $sourceExpr = Get-PartitionSourceExpression -Style "Blank" -TableName $baseName -Columns $cols
            $newContent = $content -replace 'Source\s*=\s*AuroraGoldLayer\{[^}]+\}\[Data\]', "Source = $sourceExpr"
            if ($newContent -eq $content) {
                Write-Host "  WARNING: No replacement in $baseName" -ForegroundColor Yellow
                return
            }
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($tmdlPath, $newContent, $utf8)
            $patched++
            Write-Host "  Patched: $baseName" -ForegroundColor Green
        }
        Write-Host "  Patched $patched table(s) to Blank partition source" -ForegroundColor Green
    }
    
    "PatchAddSummarizeByNone" {
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else {
            if (-not $conn) { throw "Connection or -DefinitionPath required for PatchAddSummarizeByNone." }
            Join-Path (Get-Location).Path $conn.definitionPath
        }
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) { Write-Host "  No tables directory" -ForegroundColor Yellow; return }
        $patched = 0
        Get-ChildItem $tablesDir -Filter "*.tmdl" | ForEach-Object {
            $baseName = $_.BaseName
            if ($baseName -eq "_Measures" -or $baseName -eq "_ActionReady_Logic") { return }
            $content = [System.IO.File]::ReadAllText($_.FullName)
            $lines = $content -split "\r?\n"
            $out = @()
            $inColumn = $false
            $needSummarize = $false
            $addedSummarize = $false
            $columnIndent = "`t`t"
            for ($i = 0; $i -lt $lines.Count; $i++) {
                $line = $lines[$i]
                if ($line -match '^\s+column\s+') { $inColumn = $true; $needSummarize = $true; $addedSummarize = $false }
                elseif ($line -match '^\s+partition\s') { $inColumn = $false }
                elseif ($inColumn -and $line -match '^\s+summarizeBy') { $needSummarize = $false }
                if ($line -match '^\s+summarizeBy:\s*none' -and $out.Count -gt 0 -and $out[-1] -match '^\s+summarizeBy:\s*none') { continue }
                $out += $line
                if ($inColumn -and $needSummarize -and -not $addedSummarize -and $line -match '^\s+sourceColumn:') {
                    $nextIsSummarize = ($i + 1 -lt $lines.Count) -and ($lines[$i + 1] -match '^\s+summarizeBy')
                    if (-not $nextIsSummarize) {
                        $out += "$columnIndent summarizeBy: none"
                    }
                    $addedSummarize = $true
                }
            }
            $newContent = $out -join "`r`n"
            if ($newContent -ne $content) {
                $utf8 = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($_.FullName, $newContent, $utf8)
                $patched++
                Write-Host "  Patched: $baseName" -ForegroundColor Green
            }
        }
        Write-Host "  Added summarizeBy: none to $patched table(s)" -ForegroundColor Green
    }
    
    "WriteExpressionsTmdl" {
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else { throw "DefinitionPath required for WriteExpressionsTmdl." }
        $repoRoot = (Get-Location).Path
        $goldRelative = "showcases\aurora_group\data\gold"
        $goldDefault = (Join-Path $repoRoot $goldRelative) -replace "\\", "/"
        $exprPath = Join-Path $defPath "expressions.tmdl"
        $content = @"
expression GoldDataPath = "$goldDefault" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
	lineageTag: $([guid]::NewGuid())
	annotation PBI_NavigationStepName = GoldDataPath
	annotation PBI_ResultType = Text
"@
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($exprPath, $content, $utf8)
        Write-Host "  Wrote: $exprPath" -ForegroundColor Green
    }
    
    "PatchPartitionSourceToGoldDataPath" {
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else { throw "DefinitionPath required for PatchPartitionSourceToGoldDataPath." }
        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) { Write-Host "  No tables directory" -ForegroundColor Yellow; return }
        $patched = 0
        Get-ChildItem $tablesDir -Filter "*.tmdl" | ForEach-Object {
            $baseName = $_.BaseName
            if ($baseName -eq "_Measures" -or $baseName -eq "_ActionReady_Logic") { return }
            $content = [System.IO.File]::ReadAllText($_.FullName)
            if ($content -match "GoldDataPath\s*&\s*`"`/") { return }
            $lines = $content -split "\r?\n"
            $newLines = @()
            $i = 0
            while ($i -lt $lines.Count) {
                $newLines += $lines[$i]
                if ($lines[$i] -match '^\tpartition\s+\w+\s*=\s*m\s*$') {
                    $i++
                    while ($i -lt $lines.Count -and $lines[$i] -match '^\t\t') {
                        if ($lines[$i] -match '^\t\tsource\s*=\s*$') {
                            $newLines += $lines[$i]
                            $i++
                            $goldBlock = Get-PartitionSourceExpression -Style "GoldDataPath" -TableName $baseName -Columns @()
                            foreach ($gline in ($goldBlock -split "\r?\n")) { $newLines += "`t`t`t" + $gline }
                            while ($i -lt $lines.Count -and $lines[$i] -match '^\t\t\t') { $i++ }
                        } else {
                            $newLines += $lines[$i]
                            $i++
                        }
                    }
                    continue
                }
                $i++
            }
            $newContent = $newLines -join "`r`n"
            if ($newContent -ne $content) {
                $utf8 = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($_.FullName, $newContent, $utf8)
                $patched++
                Write-Host "  Patched: $baseName" -ForegroundColor Green
            }
        }
        Write-Host "  Patched $patched table(s) to GoldDataPath" -ForegroundColor Green
    }
    
    "WriteDirectLakeExpression" {
        # Write expressions.tmdl containing the DL_Lakehouse named expression for Direct Lake models.
        # Resolves WorkspaceId / LakehouseId from parameters or data contract settings.
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else { throw "-DefinitionPath required for WriteDirectLakeExpression." }

        if ($DataContractPath -and (Test-Path $DataContractPath)) {
            $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
            $contractSettings = $contract.settings
            if ($contractSettings) {
                if (-not $LakehouseId -and $contractSettings.lakehouse_id) { $LakehouseId = $contractSettings.lakehouse_id }
                if (-not $WorkspaceId -and $contractSettings.workspace_id)  { $WorkspaceId  = $contractSettings.workspace_id  }
            }
        }
        if (-not $LakehouseId -or -not $WorkspaceId) {
            throw "-WorkspaceId and -LakehouseId are required (or settings.workspace_id / settings.lakehouse_id in the data contract)."
        }

        $exprContent = Get-DirectLakeExpressionContent -WorkspaceId $WorkspaceId -LakehouseId $LakehouseId -ExpressionName $ExpressionName
        $exprPath = Join-Path $defPath "expressions.tmdl"
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($exprPath, $exprContent, $utf8)
        Write-Host "  Wrote Direct Lake expression '$ExpressionName': $exprPath" -ForegroundColor Green
        Write-Host "  Workspace: $WorkspaceId" -ForegroundColor Gray
        Write-Host "  Lakehouse: $LakehouseId" -ForegroundColor Gray
    }

    "PatchPartitionSourceToDirectLake" {
        # Converts all Import-mode M partitions in a TMDL model to Direct Lake entity partitions.
        # Skips _Measures and _ActionReady_Logic tables (calculated tables).
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else { throw "-DefinitionPath required for PatchPartitionSourceToDirectLake." }

        if ($DataContractPath -and (Test-Path $DataContractPath)) {
            $contract = Get-Content $DataContractPath -Raw | ConvertFrom-Yaml
            $contractSettings = $contract.settings
            if ($contractSettings) {
                if (-not $LakehouseId -and $contractSettings.lakehouse_id) { $LakehouseId = $contractSettings.lakehouse_id }
                if (-not $WorkspaceId -and $contractSettings.workspace_id)  { $WorkspaceId  = $contractSettings.workspace_id  }
            }
        }
        if (-not $LakehouseId -or -not $WorkspaceId) {
            throw "-WorkspaceId and -LakehouseId are required for PatchPartitionSourceToDirectLake."
        }

        $tablesDir = Join-Path $defPath "tables"
        if (-not (Test-Path $tablesDir)) { Write-Host "  No tables directory" -ForegroundColor Yellow; return }

        # Also write/overwrite expressions.tmdl with the Direct Lake named expression
        $exprContent = Get-DirectLakeExpressionContent -WorkspaceId $WorkspaceId -LakehouseId $LakehouseId -ExpressionName $ExpressionName
        $exprPath = Join-Path $defPath "expressions.tmdl"
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($exprPath, $exprContent, $utf8)
        Write-Host "  Wrote Direct Lake expression: $exprPath" -ForegroundColor Green

        $patched = 0
        $skipped = 0
        Get-ChildItem $tablesDir -Filter "*.tmdl" | ForEach-Object {
            $baseName = $_.BaseName
            # Skip calculated tables - they do not have data partitions
            if ($baseName -eq "_Measures" -or $baseName -eq "_ActionReady_Logic") { $skipped++; return }

            $content = [System.IO.File]::ReadAllText($_.FullName)

            # Skip tables that already use Direct Lake
            if ($content -match 'partition\s+\S+\s*=\s*entity') {
                Write-Host "  Already DirectLake: $baseName" -ForegroundColor Gray
                $skipped++
                return
            }

            # Find the partition block and replace mode: import + source = <M expr> with entity partition
            $lines = $content -split "\r?\n"
            $newLines = @()
            $i = 0
            $replaced = $false
            while ($i -lt $lines.Count) {
                $line = $lines[$i]
                # Detect "partition <name> = m" line
                if ($line -match '^\tpartition\s+(\S+)\s*=\s*m\s*$') {
                    $partName = $matches[1]
                    # Emit Direct Lake partition block instead
                    $dlLines = Get-DirectLakePartitionBlock -TableName $partName -EntityName $baseName -SchemaName $SchemaName -ExpressionName $ExpressionName
                    foreach ($dlLine in $dlLines) { $newLines += $dlLine }
                    $replaced = $true
                    # Skip all original partition lines (mode, source block)
                    $i++
                    while ($i -lt $lines.Count -and ($lines[$i] -match '^\t\t' -or $lines[$i] -eq '')) {
                        # Keep blank lines after the partition block
                        if ($lines[$i] -eq '') { $newLines += ''; break }
                        $i++
                    }
                    continue
                }
                $newLines += $line
                $i++
            }

            if ($replaced) {
                $newContent = $newLines -join "`r`n"
                $utf8 = New-Object System.Text.UTF8Encoding $false
                [System.IO.File]::WriteAllText($_.FullName, $newContent, $utf8)
                $patched++
                Write-Host "  Patched to DirectLake: $baseName" -ForegroundColor Green
            } else {
                Write-Host "  WARNING: No import partition found in $baseName" -ForegroundColor Yellow
                $skipped++
            }
        }
        Write-Host "  Converted $patched table(s) to DirectLake ($skipped skipped)" -ForegroundColor Green
        Write-Host "" -ForegroundColor White
        Write-Host "  Next steps:" -ForegroundColor Cyan
        Write-Host "    1. Verify expressions.tmdl WorkspaceId + LakehouseId are correct" -ForegroundColor Gray
        Write-Host "    2. Ensure Delta tables exist in Lakehouse (same names as TMDL tables)" -ForegroundColor Gray
        Write-Host "    3. Import model to Fabric workspace via: fab import" -ForegroundColor Gray
        Write-Host "    4. Trigger full refresh to validate Direct Lake connectivity" -ForegroundColor Gray
    }

    "WriteModelFiles" {
        # Generate database.tmdl, model.tmdl, and definition.pbism from canonical templates.
        # Templates live in: core/strategy_operating_model/operating_model/reference/tmdl_base_templates/
        # This is the single source of truth for compatibilityLevel + format settings.
        $defPath = if ($DefinitionPath) {
            $repoRoot = (Get-Location).Path
            if ([System.IO.Path]::IsPathRooted($DefinitionPath)) { $DefinitionPath } else { Join-Path $repoRoot $DefinitionPath }
        } else { throw "-DefinitionPath required for WriteModelFiles." }

        $repoRoot = (Get-Location).Path
        $templatesDir = Join-Path $repoRoot "core\strategy_operating_model\operating_model\reference\tmdl_base_templates"
        if (-not (Test-Path $templatesDir)) {
            throw "Templates directory not found: $templatesDir. Run from repo root."
        }

        # Resolve model name: explicit param -> parent folder stem (remove .SemanticModel suffix) -> "Model"
        $resolvedModelName = $ModelName
        if (-not $resolvedModelName) {
            $parentFolder = Split-Path (Split-Path $defPath -Parent) -Leaf
            $resolvedModelName = $parentFolder -replace '\.SemanticModel$', ''
        }
        if (-not $resolvedModelName) { $resolvedModelName = "Model" }

        $utf8 = New-Object System.Text.UTF8Encoding $false

        # database.tmdl
        $dbTemplate = Get-Content (Join-Path $templatesDir "database.tmdl.template") -Raw
        $dbContent  = $dbTemplate -replace '\{\{MODEL_NAME\}\}', $resolvedModelName
        [System.IO.File]::WriteAllText((Join-Path $defPath "database.tmdl"), $dbContent, $utf8)
        Write-Host "  Wrote: database.tmdl  (model=$resolvedModelName, compatibilityLevel=1702)" -ForegroundColor Green

        # model.tmdl - only write if it does not exist (preserve existing ref table entries)
        $modelPath = Join-Path $defPath "model.tmdl"
        if (-not (Test-Path $modelPath)) {
            $mdlTemplate = Get-Content (Join-Path $templatesDir "model.tmdl.template") -Raw
            $mdlContent  = $mdlTemplate -replace '\{\{CULTURE\}\}', $Culture
            [System.IO.File]::WriteAllText($modelPath, $mdlContent, $utf8)
            Write-Host "  Wrote: model.tmdl  (culture=$Culture)" -ForegroundColor Green
        } else {
            Write-Host "  Skipped: model.tmdl (already exists - preserving ref table entries)" -ForegroundColor Gray
        }

        # definition.pbism - parent of definition/ folder
        $pbismPath = Join-Path (Split-Path $defPath -Parent) "definition.pbism"
        $pbismTemplate = Get-Content (Join-Path $templatesDir "definition.pbism.template") -Raw
        [System.IO.File]::WriteAllText($pbismPath, $pbismTemplate, $utf8)
        Write-Host "  Wrote: definition.pbism" -ForegroundColor Green
    }

    "List" {
        if (-not $conn) { throw "Connection required. Run setup_connection.ps1 first." }
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
        if (-not $conn) { throw "Connection required. Run setup_connection.ps1 first." }
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
        Write-Host "Available: CreateFromContract, ExportFromContract, PatchDescriptionsFromContract, List, Get" -ForegroundColor Gray
    }
}
