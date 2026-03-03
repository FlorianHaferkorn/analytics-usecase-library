# TMDL Best Practices & Syntax Reference

## Purpose

This document defines **TMDL (Tabular Model Definition Language)** formatting rules and best practices for Power BI semantic models within the ActionReady Framework.

TMDL is a YAML-like declarative syntax for defining semantic models in Power BI and Fabric. This document ensures consistency, validates against the Power BI MCP, and prevents common syntax errors.

## Scope

Included:
- TMDL syntax rules (indentation, properties, keywords)
- M-Expression formatting for partitions
- Measure properties and documentation patterns
- Column, table, and relationship formatting
- Validation workflow with Power BI MCP
- Common pitfalls and error patterns

Not included:
- Business logic or measure calculations (see `measure_system.md`)
- Data modeling principles (see `semantic_layer.md`)
- High-level Fabric/Power BI architecture (see `fabric/powerbi.md`)

---

## 1. Core TMDL Syntax Rules

### 1.1 Indentation (CRITICAL)

**RULE**: Use **TABS only** for indentation. Spaces are NOT allowed.

```tmdl
table dim_date
 lineageTag: ef5816f6-16fe-4dd5-9d71-20835fbf02b7    // 1 TAB

 column DateKey
  dataType: int64                                  // 2 TABS
  isHidden                                         // 2 TABS
```

**Common Error**:
```tmdl
table dim_date
  lineageTag: ef5816f6-16fe-4dd5-9d71-20835fbf02b7   // ❌ Tab+Space = PARSER ERROR
```

**Indentation Levels**:
- Table-level properties: **1 TAB**
- Column/measure properties: **2 TABS**
- Nested properties (annotations, alternateOf): **3 TABS**
- M-expression `let`/`in`: **3 TABS** (within partition)

### 1.2 Supported Properties

**Measures**:
- ✅ `formatString` - Currency/percent formatting
- ✅ `displayFolder` - Organizational folder
- ✅ `lineageTag` - GUID for tracking
- ✅ `isHidden` - Visibility flag
- ❌ `description` - NOT SUPPORTED (use `///` comments instead)

**Columns**:
- ✅ `dataType`, `sourceColumn`, `isHidden`, `isKey`
- ✅ `formatString`, `summarizeBy`, `sortByColumn`
- ✅ `lineageTag`, `annotations`
- ❌ `description` - NOT SUPPORTED

**Numeric columns (summarizeBy: none):** Set `summarizeBy: none` for **all** numeric columns (`int64`, `int32`, `double`, `decimal`) to prevent unintentional summarization in client tools. Create measures for columns that are supposed to be summarized (e.g. `Net Sales Amount` → measure `[Net Sales Amount] = SUM(fact_sales[Net Sales Amount])`). This applies to keys, IDs, and all fact columns—Power BI should aggregate via measures, not by default summarization of columns.

**Tables**:
- ✅ `lineageTag`, `annotations`, `isHidden`
- ❌ `description` - NOT SUPPORTED

### 1.3 Comments and Documentation

**TMDL Comments** (preferred):
```tmdl
/// Total invoiced revenue net of discounts and returns
measure 'Net Sales Amount' =
  SUM(fact_sales[Net Sales Amount])
 formatString: #,0.00
```

**DAX Comments** (within expression):
```tmdl
measure 'Net Sales Amount' =
  -- Sum all invoice line amounts
  SUM(fact_sales[Net Sales Amount])
 formatString: #,0.00
```

**NOT SUPPORTED**:
```tmdl
measure 'Net Sales Amount' =
  SUM(fact_sales[Net Sales Amount])
 formatString: #,0.00
 description: "Total revenue"    // ❌ PARSER ERROR
```

**Measure description block (standard format):**  
Use a three-line `///` block above each measure: **KPI ID** (or Supporting), **Description**, and **Purpose**. Source: `core/kpi_catalog/KPI_Catalog.md`. For supporting measures use `/// Supporting: <id> — <Display Name>` and supply Description and Purpose from the measure dictionary or a short formulation.

```tmdl
/// KPI: sales.net_sales.amount — Net Sales Amount
/// Description: Total invoiced revenue net of discounts and returns.
/// Purpose: Total invoiced revenue net of discounts and returns.
measure 'Net Sales Amount' = ...
```

### 1.4 Object names and property delimiters (Microsoft Learn)

- **Object names**: Enclose in single quotes (`'`) if the name contains: dot (`.`), equals (`=`), colon (`:`), single quote, or space. Escape a single quote inside a name with two single quotes.
- **Property values**: Use colon (`:`) for non-expression properties; use equals (`=`) for expression properties (measure expression, partition source, etc.). Text values: optional leading/trailing double quotes; required if value has leading/trailing whitespace; inside double quotes escape `"` with `""`.
- **Boolean shortcut**: You can set a boolean property by writing only the property name (e.g. `isHidden`); `true` is implied.

### 1.5 TMDL folder structure and PBIP (Microsoft Learn)

TMDL uses a **folder structure**, not a single file. Default layout:

- **Subfolders** (one level): `cultures/`, `perspectives/`, `roles/`, `tables/` — each contains `.tmdl` files per object.
- **Root files**: `database.tmdl`, `model.tmdl`, `relationships.tmdl`, `expressions.tmdl`, `dataSources.tmdl`, `functions.tmdl`.
- **Tables**: One file per table (e.g. `Sales.tmdl`, `Product.tmdl`). All table metadata (columns, measures, partitions, hierarchies) lives in that table’s file. Measures can be defined in the table file or in a **partial declaration** (e.g. a shared `_Measures.tmdl` file that declares measures for multiple tables).
- **PBIP semantic model folder**: When using TMDL format, the dataset is stored under `definition/` (replacing `model.bim`). Required: `definition.pbism` (version 4.0+ for TMDL). Exclude from source control: `.pbi/localSettings.json`, `.pbi/cache.abf`. Optional: `Copilot/` (Prep for AI schema, verified answers, instructions), `DAXQueries/`, `TMDLScripts/`.

**Source**: [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), [Power BI Desktop project semantic model folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).

---

## 2. M-Expression Formatting (Partitions)

### 2.1 Standard Pattern

**Preferred**: `let...in` block with `type table` definition

```tmdl
partition dim_date = m
 mode: import
 source =
   let
    Source = Folder.Files("C:\\path\\to\\data\\dim_date"),
    FilteredFiles = Table.SelectRows(Source, each Text.EndsWith([Name], ".parquet")),
    FirstFile = FilteredFiles{0}[Content],
    ParquetData = Parquet.Document(FirstFile)
   in
    ParquetData
```

**Alternative** (for empty tables):
```tmdl
partition _Measures = m
 mode: import
 source =
   let
    Source = #table(type table [], {})
   in
    Source
```

### 2.2 Indentation within M-Expressions

- `partition <name> = m`: **1 TAB**
- `mode:`, `source =`: **2 TABS**
- `let`: **3 TABS**
- M-expression statements (`Source = ...`): **3 TABS + 4 spaces** (M-language convention)
- `in`: **3 TABS**
- Return expression: **3 TABS + 4 spaces**

### 2.3 Common M-Expression Errors

❌ **Inline without `let...in`** (causes Composite Model error):
```tmdl
source = #table({"col1", "col2"}, {})    // ❌ ENTITY-BASED QUERY ERROR
```

❌ **Incorrect `type table` syntax** (causes M-Engine error):
```tmdl
Source = #table(type table [Col1 = int64], {})    // ❌ Expected comma
```

✅ **Correct `type table` syntax**:
```tmdl
Source = #table(
 type table [
  Col1 = Int64.Type,
  Col2 = Text.Type
 ],
 {}
)
```

---

## 3. Measure Definitions

### 3.1 Mandatory Properties

```tmdl
/// <Business purpose in one line>
measure '<Measure Name>' =
  <DAX Expression>
 formatString: <format>
 displayFolder: "<Folder Path>"
```

### 3.2 FormatString Patterns

| Data Type | Format String | Example Output |
|-----------|---------------|----------------|
| Currency | `#,0.00` | 1,234.56 |
| Currency (with symbol) | `€ #,0.00` | € 1,234.56 |
| Percentage | `0.0%` | 12.5% |
| Integer | `#,0` | 1,235 |
| Decimal (1 digit) | `#,0.0` | 1,234.6 |

### 3.3 DisplayFolder Hierarchy

```tmdl
displayFolder: "COM-001 Sales Performance"
displayFolder: "COM-001 Sales Performance\\PVM Analysis"
displayFolder: "10_Tech"
```

**Convention**: Use `\\` for subfolders (Windows path syntax).

### 3.4 Full Example

```tmdl
/// Quantifies the pure price impact in the PVM bridge: (Actual Price - Plan Price) x Actual Quantity
measure 'Price Effect Amount' =
  VAR ActualPrice = DIVIDE([Net Sales Amount], SUM(fact_sales[Quantity]))
  VAR PlanPrice = DIVIDE([Plan Sales Amount], SUM(fact_sales[Plan Quantity]))
  VAR ActualQty = SUM(fact_sales[Quantity])
  RETURN
   (ActualPrice - PlanPrice) * ActualQty
 formatString: #,0.00
 displayFolder: "COM-001 Sales Performance\\PVM Analysis"
 lineageTag: a1b2c3d4-1234-5678-9abc-def012345678
```

---

## 4. Table Definitions

### 4.1 Structure

```tmdl
table <table_name>
 lineageTag: <GUID>

 column <column_name>
  dataType: <type>
  sourceColumn: <source>
  [optional properties]

 partition <partition_name> = m
  mode: import
  source = <M-expression>
```

### 4.2 Column Names with Spaces

Use single quotes `'` for column names containing spaces:

```tmdl
column 'Net Sales Amount'
 dataType: string
 sourceColumn: Net Sales Amount
```

In M-expressions, use `#"Column Name"`:
```m
#"Net Sales Amount" = Text.Type
```

### 4.3 Hidden Columns

```tmdl
column DateKey
 dataType: int64
 sourceColumn: DateKey
 isHidden
```

---

## 5. Validation Workflow

### 5.1 Pre-Generation Validation

**Before creating TMDL files manually**:
1. Check existing MCP operations: `measure_operations Help`
2. Validate property names against MCP schema
3. Test indentation rules (Tabs vs Spaces)

### 5.2 Generation via MCP (RECOMMENDED)

**Use MCP tools instead of manual creation**:
```powershell
# Create measure via MCP
$measureDef = @{
    Name = "Net Sales Amount"
    TableName = "_Measures"
    Expression = "SUM(fact_sales[Net Sales Amount])"
    FormatString = "#,0.00"
    DisplayFolder = "COM-001 Sales Performance"
}

Invoke-MCPTool -Tool "measure_operations" -Operation "Create" -CreateDefinition $measureDef
```

### 5.3 Post-Generation Validation

**Export and verify**:
```powershell
# Export measure to TMDL
Invoke-MCPTool -Tool "measure_operations" -Operation "ExportTMDL" -MeasureName "Net Sales Amount"
```

**Check in Power BI Desktop**:
1. Open `.pbip` file
2. Verify no parser errors
3. Test measure calculations

### 5.4 PBIP load readiness

Before opening the semantic model in Power BI Desktop, run `check_tmdl_pbip_readiness.ps1` (via `run_fabric_checks.ps1`) to avoid load failures:

| Rule | Requirement |
|------|-------------|
| **Relationship IDs** | No duplicate relationship GUIDs or names across `relationships.tmdl` and `relationships/*.tmdl`. |
| **Measure names** | No duplicate `measure 'Name' =` in `_Measures.tmdl` (or across tables). |
| **RLS** | Security (RLS) relationships must use `securityFilteringBehavior: oneDirection`. |
| **Partition Source** | Use a Power Query parameter (e.g. `GoldDataPath & "/facts/..."`) in `Folder.Files(...)`; do not hardcode absolute or relative paths. |

Script: `products/fabric/powerbi/tooling/validation/check_tmdl_pbip_readiness.ps1`.

### 5.5 Error Handling

| Error Type | Message Pattern | Root Cause | Solution |
|------------|----------------|------------|----------|
| `UnknownKeyword` | `"description" is not supported` | Invalid property | Remove `description:`, use `///` comment |
| `Composite Model Error` | `entity-based query sources` | Inline M-expression | Wrap in `let...in` block |
| `M-Engine Syntax Error` | `Expected comma` | Incorrect `type table` | Use `Int64.Type` not `int64` |
| `TMDL Parser Error` | `"in" not recognized` | Mixed Tab+Space indent | Use pure TAB characters |

---

## 6. Semantic model and AI readiness (Prep for AI)

Power BI **Prep for AI** (and Fabric data agent / Copilot) uses semantic model metadata and configuration. TMDL does not support a `description` property; use **`///` comments** above tables, columns, and measures so that exported metadata and tooltips remain meaningful. Best practices from Microsoft Learn:

- **Descriptions**: Add `///` comments above each measure (and key tables/columns) with a short business purpose. This helps Copilot and data agent interpret the model.
- **AI data schema**: In Power BI (Desktop or service), configure **Prep for AI > Simplify data schema** to select only the tables, columns, and measures relevant for natural language queries. Reduces ambiguity and improves DAX generation.
- **Verified answers**: Define verified answers (trigger questions + visual) for frequent or ambiguous questions so the agent returns consistent results.
- **AI instructions**: In **Prep for AI > Add AI instructions**, add business terminology, default groupings (e.g. fiscal quarter), and metric preferences (e.g. “use Contribution Margin, not Gross Profit”). Keep instructions focused; semantic-model-specific instructions belong in Prep for AI, not in data agent–level instructions.
- **Naming**: Use clear, business-friendly names for tables, columns, and measures (e.g. “Total Revenue”, “Sales Region”). Avoid codes like `TR_AMT`, `DIM_GEO_01` unless synonyms/instructions clarify them.
- **Explicit measures**: Rely on explicit DAX measures for business metrics; avoid implicit measures for KPIs. Set correct default summarization on numeric columns.

**Source**: [Semantic model best practices for data agent](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices), [Prepare your data for AI in Power BI](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-prepare-data-ai).

---

## 7. Best Practices Summary

### 6.1 DO

✅ Use **Power BI MCP** for TMDL generation (avoid manual creation)
✅ Use **TABS only** for indentation (never spaces)
✅ Use `let...in` blocks for all M-expressions
✅ Add `///` comments above measures for documentation
✅ Test `.pbip` opening in Power BI Desktop before committing
✅ Use `ExportTMDL` operation to validate syntax
✅ Follow `fabric/powerbi.md` for high-level structure
✅ Use `displayFolder` for measure organization
✅ Use `formatString` for all numeric measures

### 7.2 DON'T

❌ Mix Tabs and Spaces in indentation
❌ Use `description:` property (not supported)
❌ Create inline M-expressions without `let...in`
❌ Manually edit TMDL files without MCP validation
❌ Use incorrect `type table` syntax
❌ Forget to test in Power BI Desktop after changes
❌ Create calculated columns for business logic (use measures)
❌ Hard-code display names in measure names (use `formatString`)

---

## 8. Integration with Framework

### 8.1 Relationship to Other Documents

- **fabric/powerbi.md**: High-level Fabric/Power BI architecture
- **semantic_layer.md**: Conceptual modeling principles
- **measure_system.md**: Business logic and KPI definitions
- **tmdl_best_practices.md** (THIS): Low-level TMDL syntax rules

### 8.2 Workflow

1. **Design**: Use Case → KPI Catalog → measure_system.md
2. **Model**: Data Contracts → semantic_layer.md → fabric/powerbi.md
3. **Implement**: MCP Operations → **tmdl_best_practices.md** → Power BI Desktop
4. **Validate**: Export TMDL → Test `.pbip` → Commit

### 7.3 MCP Tools Reference

| Operation | Tool | Use Case |
|-----------|------|----------|
| Create Measure | `measure_operations` | Generate new measures |
| Export TMDL | `measure_operations`, `table_operations` | Validate syntax |
| Import TMDL Folder | `database_operations` | Load existing model |
| Export to Folder | `database_operations` | Serialize entire model |
| Deploy to Fabric | `database_operations` | Publish to workspace |

---

## 9. Common Pitfalls

### 9.1 Parser Errors

**Symptom**: `UnknownKeyword` error in Power BI Desktop
**Cause**: Using unsupported properties (`description:`)
**Fix**: Replace with `///` comments

**Symptom**: `TMDL parser error: "in" not recognized`
**Cause**: Mixed Tab+Space indentation
**Fix**: Convert all indents to pure TAB characters

### 9.2 M-Expression Errors

**Symptom**: `Composite Model error: entity-based query sources`
**Cause**: Inline M-expression without `let...in`
**Fix**: Wrap in `let...in` block with `type table`

**Symptom**: `M-Engine syntax error: Expected comma`
**Cause**: Incorrect `type table` syntax (`int64` instead of `Int64.Type`)
**Fix**: Use correct M type names

### 9.3 Data Loading Errors

**Symptom**: Table shows "Error" in Power BI
**Cause**: Parquet file path incorrect or file not found
**Fix**: Verify `Folder.Files()` path, check file extension filter

### 9.4 PBIP load failures (self-correcting checklist)

To prevent recurrence of past load errors, ensure:

- **Duplicate relationship IDs**: Each relationship must have a unique GUID or name; merge or rename duplicates.
- **Duplicate measure names**: Only one definition per measure name in `_Measures.tmdl`; remove or merge duplicates.
- **RLS direction**: For RLS (e.g. `security_*`), set `securityFilteringBehavior: oneDirection` (not `bothDirections`).
- **Hardcoded paths**: Use a parameter (e.g. `GoldDataPath`) in partition `Source`; define the parameter in `expressions.tmdl`.

Run `run_fabric_checks.ps1` (includes `check_tmdl_pbip_readiness.ps1`) before committing TMDL changes.

---

## 10. Model View Layout (diagramLayout.json)

### 10.1 Spaghetti Principle

The **spaghetti principle** ensures all tables in the model view are readable and logically arranged:

- **Top-left anchor:** `_Measures` table at position (x=0, y=0)
- **Top row (horizontal):** All fact tables arranged in a single horizontal row at y=0, starting at x=280 (immediately to the right of `_Measures`), with 250px spacing between tables (x=280, 530, 780, 1030, 1280, ...)
- **Left column (vertical):** All dimension tables stacked vertically at x=0, starting at y=120 (below `_Measures`), with 120px spacing between tables (y=120, 240, 360, 480, 600, ...)
- **Security tables:** Include `security_user_org` and other security/RLS tables in the left column alongside dimensions

### 10.2 Rationale

This layout provides:
- **Readability:** Facts are visible horizontally at the top; dimensions are accessible vertically on the left
- **Consistency:** Every semantic model follows the same pattern, making navigation predictable
- **Scalability:** New facts extend the horizontal row; new dimensions extend the vertical column

### 10.3 Implementation

The `diagramLayout.json` file in each semantic model's root (e.g. `Commercial.SemanticModel/diagramLayout.json`) defines node positions. When creating or updating semantic models:

1. Place `_Measures` at (0, 0)
2. Arrange all fact tables horizontally at y=0 with x increasing by 250px
3. Arrange all dimension tables vertically at x=0 with y increasing by 120px (starting at y=120)
4. Include security tables with dimensions in the left column

**Reproducible implementation:** The orchestrator generates both **relationships** and **diagramLayout.json** so that every build is best-practice compliant and reproducible.

- **Relationships:** Step 3.3 in `orchestrate_full_model.ps1` creates relationships **per domain** from `UseCase_Bracket.yaml` and the domain data contract (`overrides.data_contract_ref`). If no relationships are produced (e.g. missing contract ref), **AutoDetect** runs and writes TMDL from table naming conventions (`*Key` → `dim_*`). Script: `products/fabric/powerbi/orchestrator/relationship_ops.ps1` (operations `CreateFromBracket`, `AutoDetect` with `-DefinitionPath` to persist TMDL). Relationships are written to `definition/relationships/*.tmdl`.
- **Model View (diagramLayout.json):** Step 3.6 runs `write_diagram_layout.ps1` per domain. It reads `definition/tables/*.tmdl`, then writes `diagramLayout.json` in the semantic model root following the spaghetti principle. Script: `products/fabric/powerbi/orchestrator/write_diagram_layout.ps1`. **Single source of truth:** Run `orchestrate_full_model.ps1 -UseCase <id>` or `-Domain <name>`; do not hand-edit diagram layout or relationships if you want reproducible builds.

**Example structure** (actual file uses `diagrams[0].nodes`):
```json
{
  "diagrams": [{ "nodes": [
    {"nodeIndex": "_Measures", "location": {"x": 0, "y": 0}},
    {"nodeIndex": "fact_sales", "location": {"x": 280, "y": 0}},
    {"nodeIndex": "dim_date", "location": {"x": 0, "y": 120}},
    {"nodeIndex": "dim_org", "location": {"x": 0, "y": 240}}
  ]}]
}
```

**Validation:** The spaghetti layout is automatically enforced by `check_diagram_layout.ps1`, which runs as part of `run_fabric_checks.ps1`. The script validates:
- `_Measures` is at (0, 0)
- All fact tables are at y=0 with x≥280
- All dimension tables are at x=0 with y≥120
- Spacing is approximately 250px (facts) and 120px (dims)

Violations are reported as errors; spacing deviations are warnings.

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-03 | Initial release based on COM-001 PBIP implementation |

---

## 12. References

- **Power BI MCP**: `mcp_powerbi-model_*` tools
- **TMDL Documentation**: [Microsoft Learn - TMDL](https://learn.microsoft.com/analysis-services/tmdl/)
- **Fabric Implementation**: `products/fabric/powerbi/docs/fabric/powerbi.md`
- **Semantic Layer**: `core/strategy_operating_model/operating_model/semantic_layer.md`
- **Measure System**: `core/strategy_operating_model/operating_model/measure_system.md`
- **Fabric checks (measures vs KPI, TMDL vs dictionary, DAX)**: `products/fabric/powerbi/tooling/run_fabric_checks.ps1`
- **DAX best-practice rules**: `tooling/linters/powerbi/bpa-rules-dax.json` (see `tooling/linters/powerbi/README.md`)
- **Microsoft Learn**: [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), [PBIP semantic model folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [Semantic model best practices for data agent](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices), [Star schema and Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
