# products/fabric/powerbi/orchestrator/table_ops.ps1

Param(
    [ValidateSet("Create","Update","Delete","Get","List","CreateFromContract","ExportFromContract","PatchDescriptionsFromContract","PatchPartitionSourceToBlank","PatchAddSummarizeByNone","WriteExpressionsTmdl","PatchPartitionSourceToGoldDataPath")]
    [string]$Operation = "List",
    [string]$ConnectionName = "local_pbip",
    [hashtable]$TableDefinition,
    [string]$DataContractPath,
    [string]$TableName,
    [string]$OutJsonPath,
    [string]$UseCase,
    [string]$DefinitionPath,
    [ValidateSet("AuroraGoldLayer","Blank","GoldDataPath")]
    [string]$PartitionSourceStyle = "Blank"
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
        
        # Add partition (required for Power BI). Source: AuroraGoldLayer (Fabric), Blank (local), or GoldDataPath (Aurora gold).
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
            # Fix M "Ungültiger Bezeichner": single-quoted column names in #table must be #"Name"
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
            for ($i = 0; $i -lt $lines.Count; $i++) {
                $line = $lines[$i]
                if ($line -match '^\tcolumn\s+') { $inColumn = $true; $needSummarize = $true; $addedSummarize = $false }
                elseif ($line -match '^\tpartition\s') { $inColumn = $false }
                elseif ($inColumn -and $line -match '^\t\tsummarizeBy') { $needSummarize = $false }
                # Skip duplicate summarizeBy lines (TMDL allows only one per column)
                if ($line -match '^\t\tsummarizeBy:\s*none' -and $out.Count -gt 0 -and $out[-1] -match '^\t\tsummarizeBy:\s*none') { continue }
                $out += $line
                # Add summarizeBy only if missing (next line in file is not already summarizeBy)
                if ($inColumn -and $needSummarize -and -not $addedSummarize -and $line -match '^\t\tsourceColumn:') {
                    $nextIsSummarize = ($i + 1 -lt $lines.Count) -and ($lines[$i + 1] -match '^\t\tsummarizeBy')
                    if (-not $nextIsSummarize) { $out += "`t`tsummarizeBy: none" }
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
