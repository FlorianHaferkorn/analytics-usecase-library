# products/fabric_powerbi/orchestrator/AuroraDomainMapping.ps1
# Central mapping: Use-Case prefix <-> Domain name <-> model name and data contract.
# Aurora = tool-agnostic showcase (gold data, structure). Fabric output lives under products/fabric_powerbi/dist.
# Dot-source from orchestrate or other scripts: . "$PSScriptRoot\AuroraDomainMapping.ps1"

# Prefix (e.g. COM) -> Domain display name (e.g. Commercial)
$script:AuroraPrefixToDomain = @{
    COM = "Commercial"
    FIN = "Finance"
    OPS = "Operations"
    SCM = "SupplyChain"
    XD  = "Experience"
}

# Domain display name -> semantic model folder name (tool-agnostic; used for Fabric under dist)
$script:AuroraDomainToModelName = @{
    Commercial  = "Commercial.SemanticModel"
    Finance     = "Finance.SemanticModel"
    Operations  = "Operations.SemanticModel"
    SupplyChain = "SupplyChain.SemanticModel"
    Experience  = "Experience.SemanticModel"
}

# Fabric: single output root for semantic models and reports (tool-specific)
$script:FabricDistRoot = "products\fabric_powerbi\dist"

# Domain display name -> data contract path (relative to repo root) for table creation from gold
$script:AuroraDomainToDataContract = @{
    Commercial  = "core\data_contracts\domains\commercial_sales.yaml"
    Finance     = "core\data_contracts\domains\finance.yaml"
    Operations  = "core\data_contracts\domains\operations.yaml"
    SupplyChain = "core\data_contracts\domains\supply_chain.yaml"
    Experience  = "core\data_contracts\domains\experience.yaml"
}

# Required tables per domain (minimal set; must exist in data contract). Shared dims first.
$script:AuroraDomainRequiredTables = @{
    Commercial  = @("dim_date", "dim_org", "dim_product", "dim_customer", "fact_sales")
    Finance     = @("dim_date", "dim_org", "fact_cash_position", "fact_cash_flow", "fact_accounts_receivable", "fact_accounts_payable")
    Operations  = @("dim_date", "dim_org", "dim_asset", "dim_product", "fact_ops", "fact_quality")
    SupplyChain = @("dim_date", "dim_org", "dim_product", "fact_inventory", "fact_forecast", "fact_fulfillment")
    Experience  = @("dim_date", "dim_org", "dim_case_queue", "fact_support_cases")
}

function Get-DomainNameFromPrefix {
    param([string]$Prefix)
    if (-not $Prefix) { return $null }
    return $script:AuroraPrefixToDomain[$Prefix]
}

function Get-PrefixFromDomainName {
    param([string]$DomainName)
    if (-not $DomainName) { return $null }
    foreach ($p in $script:AuroraPrefixToDomain.Keys) {
        if ($script:AuroraPrefixToDomain[$p] -eq $DomainName) { return $p }
    }
    return $null
}

function Get-DomainPrefixFromUseCaseId {
    param([string]$UcId)
    if ($UcId -match '^([A-Z]{2,3})-') { return $Matches[1] }
    return $null
}

function Get-DomainNameFromUseCaseId {
    param([string]$UcId)
    $prefix = Get-DomainPrefixFromUseCaseId -UcId $UcId
    return Get-DomainNameFromPrefix -Prefix $prefix
}

# Returns relative path to domain semantic model folder in Fabric dist (single output location)
function Get-FabricDomainModelPath {
    param([string]$DomainName)
    if (-not $DomainName) { return $null }
    $modelName = $script:AuroraDomainToModelName[$DomainName]
    if (-not $modelName) { return $null }
    return "$($script:FabricDistRoot)\$modelName"
}

# Returns relative path to domain model's definition folder in Fabric dist
function Get-FabricDomainDefinitionPath {
    param([string]$DomainName)
    $modelPath = Get-FabricDomainModelPath -DomainName $DomainName
    if (-not $modelPath) { return $null }
    return "$modelPath\definition"
}

# Returns relative path to domain model's definition/tables folder in Fabric dist (for _Measures.tmdl)
function Get-FabricDomainTablesPath {
    param([string]$DomainName)
    $modelPath = Get-FabricDomainModelPath -DomainName $DomainName
    if (-not $modelPath) { return $null }
    return "$modelPath\definition\tables"
}

# Legacy: Aurora showcase path (tool-agnostic reference only; Fabric builds to dist)
function Get-AuroraDomainModelPath {
    param([string]$DomainName)
    if (-not $DomainName) { return $null }
    $modelName = $script:AuroraDomainToModelName[$DomainName]
    if (-not $modelName) { return $null }
    return "showcases\aurora_group\semantic_models\$modelName"
}

function Get-AuroraDomainTablesPath {
    param([string]$DomainName)
    $modelPath = Get-FabricDomainModelPath -DomainName $DomainName
    if (-not $modelPath) { return $null }
    return "$modelPath\definition\tables"
}

# Returns data contract path for domain (relative to repo root)
function Get-AuroraDomainDataContract {
    param([string]$DomainName)
    return $script:AuroraDomainToDataContract[$DomainName]
}

# Returns required table names for domain
function Get-AuroraDomainRequiredTables {
    param([string]$DomainName)
    $tables = $script:AuroraDomainRequiredTables[$DomainName]
    if ($tables) { return @($tables) }
    return @()
}

# Group use case IDs by domain. Returns hashtable: DomainName -> @(ucId1, ucId2, ...)
function Get-UseCaseIdsGroupedByDomain {
    param([string[]]$UseCaseIds)
    $byDomain = @{}
    foreach ($ucId in $UseCaseIds) {
        $domainName = Get-DomainNameFromUseCaseId -UcId $ucId
        if (-not $domainName) { continue }
        if (-not $byDomain[$domainName]) { $byDomain[$domainName] = @() }
        $byDomain[$domainName] += $ucId
    }
    return $byDomain
}

# Relative path from products/fabric_powerbi/dist/<UC>.Report to domain semantic model in same dist (for datasetReference)
function Get-DatasetReferenceRelativeFromReport {
    param([string]$DomainName)
    $modelName = $script:AuroraDomainToModelName[$DomainName]
    if (-not $modelName) { return $null }
    return "..\$($modelName -replace '/','\')"
}
