# Power BI MCP - Implementation Cheatsheet

## 🎯 MCP Operations Overview

### Available Power BI MCP Tools

```yaml
Semantic Model Operations:
  - mcp_powerbi-model_table_operations          # Tables erstellen/aktualisieren/löschen
  - mcp_powerbi-model_column_operations         # Columns verwalten
  - mcp_powerbi-model_measure_operations        # Measures aus TMDL importieren
  - mcp_powerbi-model_relationship_operations   # Relationships auto-config
  - mcp_powerbi-model_user_hierarchy_operations # Hierarchies (Year>Month, Plant>Line)
  - mcp_powerbi-model_perspective_operations    # Perspectives für Use Cases
  - mcp_powerbi-model_trace_operations          # Performance Tracing
  - batch_perspective_operations                # Batch Perspective Management

Multi-Operations:
  - multi_replace_string_in_file                # Batch TMDL edits
```

---

## 🔄 **Iteration Pattern: Quality Gates mit Auto-Correction**

### Pattern 1: Measure Validation Loop

```powershell
do {
    # Generate measures
    ./_internal/tools/generation/generate_tmdl_measures.ps1 -UseCase $UseCase
    
    # Validate
    $result = ./implementations/microsoft_fabric_powerbi/tools/test_tmdl.ps1 -TmdlFile $tmdlPath
    
    if ($LASTEXITCODE -eq 0) {
        break  # Success
    }
    
    # Parse errors
    $errors = $result | Select-String "WARN|FAIL"
    
    # Auto-fix known patterns
    foreach ($error in $errors) {
        if ($error -match "missing formatString") {
            # Inject default format from KPI Catalog
            Add-FormatStringToMeasure $measureName
        }
        if ($error -match "missing displayFolder") {
            # Inject default folder from domain
            Add-DisplayFolderToMeasure $measureName
        }
    }
    
    $iteration++
} while ($iteration -lt $maxIterations)
```

### Pattern 2: Relationship Auto-Config

```powershell
# Step 1: Detect from Technical Factsheet
$factsheet = Get-Content "framework\usecases\core\$UseCase\Technical_Factsheet.md" -Raw
$relSection = Extract-Section $factsheet "### 4.2 Relationships"

# Step 2: Parse relationship definitions
$relationships = Parse-RelationshipYAML $relSection

# Step 3: Create via MCP
foreach ($rel in $relationships) {
    mcp_powerbi-model_relationship_operations `
        -Operation "create" `
        -FromTable $rel.from `
        -FromColumn $rel.fromColumn `
        -ToTable $rel.to `
        -ToColumn $rel.toColumn `
        -Cardinality "ManyToOne" `
        -CrossFilteringBehavior "single"
}

# Step 4: Validate no ambiguity
$validation = mcp_powerbi-model_relationship_operations -Operation "validate"

if ($validation.hasAmbiguity) {
    # Auto-fix: Set one to inactive
    mcp_powerbi-model_relationship_operations `
        -Operation "update" `
        -RelationshipId $validation.ambiguous[0] `
        -IsActive $false
}
```

### Pattern 3: DAX Dependency Resolution

```powershell
# Step 1: Extract all measures
$measures = mcp_powerbi-model_measure_operations -Operation "list"

# Step 2: Build dependency graph
$graph = @{}
foreach ($measure in $measures) {
    $deps = Extract-DAXReferences $measure.expression
    $graph[$measure.name] = $deps
}

# Step 3: Detect cycles
$cycles = Find-Cycles $graph

if ($cycles.Count -gt 0) {
    Write-Host "Circular dependencies detected:" -ForegroundColor Red
    $cycles | ForEach-Object { Write-Host "  $_" }
    
    # Suggest fixes
    foreach ($cycle in $cycles) {
        $suggestion = Suggest-DAXRefactor $cycle
        Write-Host "  Suggestion: $suggestion" -ForegroundColor Yellow
    }
}
```

---

## 🎨 **Report Template Mapping**

### Template Structure → PBIR Conversion

```yaml
# Input: framework/templates/page_templates/overview_drivers_details.md

Template Sections:
  ## Page 1: Overview (3 seconds)
    -> PBIR Page with name="Overview", display order=1
    
  - KPI Cards: Net Sales, Gross Margin %, Price Realization %
    -> 3x Card Visuals, measure binding from KPI Catalog
    
  - Trend Chart: Net Sales (Last 12M)
    -> Line Chart, X=dim_date[Month], Y=[Net Sales Amount], Filter=DATESINPERIOD
    
  - Sparklines: GM% vs Plan
    -> Sparkline Custom Visual, Y=[Gross Margin %], Comparison=[Gross Margin % vs Plan]

# Output: COM-001.Report/definition/report.json

{
  "pages": [
    {
      "name": "Overview",
      "displayName": "Overview",
      "width": 1280,
      "height": 720,
      "visualContainers": [
        {
          "config": "{ type: 'card', x: 0, y: 0, width: 300, height: 150 }",
          "query": {
            "Commands": [{ "SemanticQueryDataShapeCommand": { "Query": { "Select": [{ "Measure": { "Expression": { "SourceRef": { "Source": "_Measures" } }, "Property": "Net Sales Amount" } }] } } }]
          }
        }
      ]
    }
  ]
}
```

### Visual Type Mapping

| Template Keyword | Power BI Visual | Config |
|------------------|-----------------|--------|
| KPI Card | Card | Basic value display |
| Trend Chart | Line Chart | X=Date, Y=Measure, Legend optional |
| Waterfall | Waterfall | Category=breakdown dim, Y=delta measure |
| Heatmap | Matrix + Conditional Formatting | Rows=dim1, Cols=dim2, Values=measure |
| Sparkline | Sparkline Custom Visual | Inline trend |
| Gauge | Gauge | Min/Max from threshold, Value=measure |
| Table | Table | Columns from factsheet |

---

## 🧩 **Integration Points**

### 1. KPI Catalog → Measures

```powershell
# From: framework/kpi_catalog/KPI_Catalog.md
- kpi_id: sales.net_sales.amount
  dax_name: "Net Sales Amount"
  dax_expression: "SUM(fact_sales[Net Sales Amount])"
  formatString: "#,0.00"
  displayFolder: "01_Sales"

# To: implementations/microsoft_fabric_powerbi/dist/COM-001/COM-001.SemanticModel/definition/tables/_Measures.tmdl
measure 'Net Sales Amount' =
    SUM(fact_sales[Net Sales Amount])
    formatString: "#,0.00"
    displayFolder: "01_Sales"
```

### 2. Data Contract → Tables

```yaml
# From: framework/data_contracts/sources/synthetic/synthetic_data_contract.yaml
tables:
  - name: dim_date
    type: dimension
    columns:
      - name: DateKey
        type: int
        role: key
      - name: Date
        type: date
      - name: Month
        type: string

# To: MCP Table Operation
mcp_powerbi-model_table_operations -Operation "create" -TableDefinition {
  name: "dim_date"
  columns: [
    { name: "DateKey", dataType: "int64", isHidden: true },
    { name: "Date", dataType: "date" },
    { name: "Month", dataType: "string" }
  ]
}
```

### 3. Technical Factsheet → Relationships

```yaml
# From: framework/usecases/core/COM-001_Sales_Performance/Technical_Factsheet.md
### 4.2 Relationships (Mandatory)
- dim_date (1) -> fact_sales on DateKey
- dim_org (1) -> fact_sales on OrgKey

# To: MCP Relationship Operation
mcp_powerbi-model_relationship_operations -Operation "create" -RelationshipDefinition {
  fromTable: "fact_sales"
  fromColumn: "DateKey"
  toTable: "dim_date"
  toColumn: "DateKey"
  cardinality: "ManyToOne"
  crossFilteringBehavior: "single"
}
```

### 4. Page Template → Report Pages

```markdown
# From: framework/templates/page_templates/overview_drivers_details.md
## Page 1: Overview (3 seconds)
- KPI Cards: Net Sales, Gross Margin %

# To: Report Generator
Generate-ReportPage -PageName "Overview" -Visuals @(
  @{ type="card"; measure="Net Sales Amount"; position=@{x=0;y=0} },
  @{ type="card"; measure="Gross Margin %"; position=@{x=320;y=0} }
)
```

---

## 🔍 **Quality Checks per Phase**

### Phase 1: Measure Generation

```powershell
Checks:
  ✓ TMDL Syntax Valid (./implementations/microsoft_fabric_powerbi/tools/test_tmdl.ps1)
  ✓ All Measures Have formatString
  ✓ All Measures Have displayFolder
  ✓ All Measures Have /// Description
  ✓ No := Operator Usage
  ✓ UTF-8 without BOM

Auto-Fixes:
  - Missing formatString → Infer from KPI Catalog dataType
  - Missing displayFolder → Use domain default (e.g., "01_Sales")
  - Missing description → Copy from KPI Catalog purpose
```

### Phase 2: Semantic Model Build

```powershell
Checks:
  ✓ All Tables Exist
  ✓ All Columns Mapped
  ✓ Relationships Created
  ✓ No Ambiguous Paths
  ✓ Hierarchies Defined
  ✓ Sort-By Columns Set

Auto-Fixes:
  - Ambiguous paths → Set one relationship inactive
  - Missing sort-by → Create from naming convention (*Number, *SortOrder)
```

### Phase 3: BPA & Advanced Validation

```powershell
Checks:
  ✓ No Floating Point DataTypes
  ✓ IsAvailableInMdx=false on Hidden Columns
  ✓ No Bi-Directional on High-Cardinality
  ✓ DAX Fully Qualified Column References
  ✓ No Circular Dependencies
  ✓ Format Strings Consistent

Auto-Fixes:
  - Float → Decimal conversion
  - IsAvailableInMdx → Set false
  - Bi-directional → Change to single
```

### Phase 4: Report Generation

```powershell
Checks:
  ✓ All Visuals Have Data Bindings
  ✓ Filters Applied from factsheet.filters_default
  ✓ Page Navigation Configured
  ✓ Bookmarks for 3-30-300 Pattern

Auto-Fixes:
  - Missing visual → Use default card
  - Missing filter → Apply "Last 12M"
```

---

## 🚦 **Status Indicators**

```powershell
# During orchestration, show status per phase:

[✓] Phase 1: Data Foundation          - 100% Complete (2.3s)
[✓] Phase 2: Measure Generation        - 100% Complete (5.1s)
[→] Phase 3: Semantic Model Build      - 60% Complete (Tables: 7/12)
[⏸] Phase 4: Validation                - Waiting...
[⏸] Phase 5: Report Generation         - Waiting...

# Iteration tracking:
Iteration 1: 3 errors found → 3 auto-fixed
Iteration 2: 1 error found → Manual intervention required
```

---

## 📦 **File Structure After Orchestration**

```
showcases/aurora_group/
  data/
    gold/
      dimensions/
        dim_date/
        dim_org/
        dim_product/
        ...
      facts/
        fact_sales/
        fact_sales_budget/
        ...
  semantic_models/
    CoreActionReady.SemanticModel/
      .platform
      definition/
        model.tmdl
        tables/
          dim_date.tmdl
          dim_org.tmdl
          fact_sales.tmdl
          _Measures.tmdl          ← Generated from KPI Catalog
        relationships/
          relationships.tmdl      ← Auto-generated from factsheet
  reports/
    COM-001.Report/
      .platform
      definition/
        report.json              ← Generated from page template
        pages/
          Overview.json
          Drivers.json
          Details.json
  logs/
    orchestration_COM-001_20260202_143022.log
    validation_results.json
    auto_fixes.json
```

---

## 🎓 **Learning Loop**

```yaml
After each orchestration run:
  1. Log all errors encountered
  2. Log all auto-fixes applied
  3. Track success rate per Use Case
  4. Identify patterns → Improve auto-fix rules
  5. Update Error Pattern Dictionary

Feedback to Framework:
  - Missing KPIs in Catalog → Add to backlog
  - Ambiguous factsheet → Improve template
  - Common DAX errors → Add to linter rules
  - Visual type gaps → Extend template engine
```

---

## 🔗 **Next Steps**

1. **Implement Phase 1:** Setup Connection & Data Validation
2. **Implement Phase 2:** Orchestrator Core Logic
3. **Implement Phase 3:** MCP Wrappers (Table, Relationship, Measure Ops)
4. **Implement Phase 4:** Self-Healing Error Handlers
5. **Implement Phase 5:** Report Template Engine
6. **Test:** Run orchestration for COM-001, COM-002, OPS-001
7. **Iterate:** Improve auto-fix rules based on logs
8. **Scale:** Apply to all 15 Use Cases

**Estimated Timeline:**
- Phase 1-2: 2 days
- Phase 3: 3 days
- Phase 4: 2 days
- Phase 5: 3 days
- Testing & Iteration: 3 days
- **Total: ~2 weeks** to production-ready automation

---

**Status:** Design Complete, Ready for Implementation  
**Dependencies:** Power BI MCP Server, Aurora Data, KPI Catalog, Page Templates  
**Owner:** Analytics Automation Team  
**Priority:** High (enables self-service model generation)
