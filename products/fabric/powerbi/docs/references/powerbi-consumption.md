# powerbi-consumption.md — Power BI Semantic Model Discovery & Impact Analysis

> **Purpose**: Guidance for reading and exploring **already-deployed** semantic models via DAX Information Functions. Use this when you need to audit structure, trace KPI lineage, run impact analysis, or answer "what is in this model?" without touching TMDL files.
>
> **Companion docs**: `fabric-api-core.md` (auth, REST), `fabric-powerbi-authoring.md` (create/update), `execute_dax.py` (CLI runner).

---

## Must / Prefer / Avoid

### MUST DO

- Use `INFO.VIEW.*` functions before `INFO.*` — `INFO.VIEW.*` respects object-level permissions; `INFO.*` requires admin or elevated workspace roles
- Estimate query scope before running deep discovery — large models with thousands of measures/columns can return MB-scale result sets
- Use `SELECTCOLUMNS` + `FILTER` to narrow result sets — never return full rowsets for discovery in production models
- Use `execute_dax.py --format ascii` for quick ad-hoc queries, `--format json` when piping to downstream scripts

### PREFER

- `INFO.VIEW.*` over `INFO.*` everywhere (see permission table below)
- Scope-estimation queries (count rows first) before full column/measure discovery
- `INFO.DEPENDENCIES()` for DAX lineage tracing — more reliable than parsing DAX strings
- REST API endpoints for security/role membership (RLS members are not exposed via DAX)
- `fab api` over direct `az rest` for executeQueries — simpler auth wiring

### AVOID

- Running `EVALUATE INFO.VIEW.MEASURES()` without `FILTER` on models with >500 measures
- Using `INFO.*` (non-VIEW variants) without confirming admin access — will return 403 silently in some tenants
- Parsing DAX expression strings to infer dependencies — use `INFO.DEPENDENCIES()` instead
- Hardcoding workspace/dataset IDs — resolve dynamically via REST

---

## Recommended Discovery Sequence

For a complete structural audit of an unknown model, execute in this order to minimise query cost:

```
Step 1 — Scope estimation (always run first)
Step 2 — INFO.VIEW.TABLES()
Step 3 — INFO.VIEW.COLUMNS() + INFO.VIEW.MEASURES()
Step 4 — INFO.VIEW.RELATIONSHIPS()
Step 5 — INFO.DEPENDENCIES()  (DAX lineage only when needed)
Step 6 — REST API            (roles, permissions — not available via DAX)
```

---

## Scope Estimation Queries

Always start here. If the counts are large, narrow with `FILTER` before pulling details.

```dax
-- Model overview: table count, measure count, column count
EVALUATE
ROW(
    "Tables",       COUNTROWS( INFO.VIEW.TABLES() ),
    "Measures",     COUNTROWS( INFO.VIEW.MEASURES() ),
    "Columns",      COUNTROWS( INFO.VIEW.COLUMNS() ),
    "Relationships",COUNTROWS( INFO.VIEW.RELATIONSHIPS() )
)
```

```dax
-- Measures per table (to decide which tables to drill into)
EVALUATE
SUMMARIZECOLUMNS(
    INFO.VIEW.MEASURES()[Table],
    "Measure Count", COUNTROWS( INFO.VIEW.MEASURES() )
)
ORDER BY [Measure Count] DESC
```

---

## Core INFO.VIEW.* Functions

### Tables

```dax
-- All tables (name, type, hidden status)
EVALUATE
SELECTCOLUMNS(
    INFO.VIEW.TABLES(),
    "Name",         [Name],
    "Type",         [TableType],
    "Hidden",       [IsHidden],
    "Row Count",    [RowsCount]
)
ORDER BY [Name]
```

### Columns

```dax
-- All columns for a specific table
EVALUATE
SELECTCOLUMNS(
    FILTER(
        INFO.VIEW.COLUMNS(),
        [TableName] = "FactSales"
    ),
    "Column",       [ExplicitName],
    "DataType",     [ExplicitDataType],
    "Hidden",       [IsHidden],
    "SummarizeBy",  [SummarizeBy]
)
```

```dax
-- Find columns without summarizeBy: none (potential model quality issue)
EVALUATE
FILTER(
    SELECTCOLUMNS(
        INFO.VIEW.COLUMNS(),
        "Table",        [TableName],
        "Column",       [ExplicitName],
        "SummarizeBy",  [SummarizeBy]
    ),
    [SummarizeBy] <> "None" && [SummarizeBy] <> ""
)
```

### Measures

```dax
-- All measures: name, table, expression, format string
EVALUATE
SELECTCOLUMNS(
    INFO.VIEW.MEASURES(),
    "Table",        [Table],
    "Measure",      [Name],
    "Expression",   [Expression],
    "Format",       [FormatString],
    "Hidden",       [IsHidden]
)
ORDER BY [Table], [Measure]
```

```dax
-- Find measures without a format string (model quality check)
EVALUATE
FILTER(
    SELECTCOLUMNS(
        INFO.VIEW.MEASURES(),
        "Table",    [Table],
        "Measure",  [Name],
        "Format",   [FormatString]
    ),
    ISBLANK( [Format] )
)
```

### Relationships

```dax
-- All relationships with cardinality and active status
EVALUATE
SELECTCOLUMNS(
    INFO.VIEW.RELATIONSHIPS(),
    "From Table",       [FromTableName],
    "From Column",      [FromColumnName],
    "To Table",         [ToTableName],
    "To Column",        [ToColumnName],
    "Cardinality",      [CrossFilteringBehavior],
    "Active",           [IsActive]
)
```

---

## DAX Dependency Tracing (INFO.DEPENDENCIES)

`INFO.DEPENDENCIES()` returns the full dependency graph: which measures/calculated columns reference which other objects. Use for KPI lineage and impact analysis before renaming or deleting.

```dax
-- Direct dependencies of a specific measure
EVALUATE
FILTER(
    SELECTCOLUMNS(
        INFO.DEPENDENCIES(),
        "Object",           [ObjectName],
        "ObjectType",       [ObjectType],
        "References Table", [ReferencedTableName],
        "References Object",[ReferencedObjectName],
        "Ref Type",         [ReferencedObjectType]
    ),
    [Object] = "Revenue YTD"
)
```

```dax
-- Impact analysis: find all measures that use a given column
EVALUATE
FILTER(
    SELECTCOLUMNS(
        INFO.DEPENDENCIES(),
        "Measure",          [ObjectName],
        "References Table", [ReferencedTableName],
        "References Column",[ReferencedObjectName]
    ),
    [References Table] = "FactSales"
    && [References Column] = "Amount"
)
```

---

## Additional INFO Functions

| Function | Permission | Use for |
|---|---|---|
| `INFO.VIEW.TABLES()` | Read (VIEW) | Table inventory |
| `INFO.VIEW.COLUMNS()` | Read (VIEW) | Column audit |
| `INFO.VIEW.MEASURES()` | Read (VIEW) | Measure inventory |
| `INFO.VIEW.RELATIONSHIPS()` | Read (VIEW) | Schema map |
| `INFO.PARTITIONS()` | Admin preferred | Partition mode, Direct Lake status |
| `INFO.DEPENDENCIES()` | Read | DAX lineage graph |
| `INFO.ROLES()` | Admin | RLS role definitions |
| `INFO.ROLEMEMBERSHIPS()` | Admin | RLS user assignments — prefer REST API |
| `INFO.CALCULATIONGROUPS()` | Read | Calculation group items |
| `INFO.CALCULATIONITEMS()` | Read | Calculation item expressions |

> **Permission note**: `INFO.VIEW.*` requires only workspace Viewer or Contributor. `INFO.*` (non-VIEW) functions may require Admin or Build permission depending on tenant configuration. If `INFO.ROLES()` returns empty unexpectedly, use the REST endpoint `GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/Default.GetBoundRoleAssignments` instead.

---

## Narrowing Pattern

When discovery returns too many rows, apply this narrowing sequence:

```dax
-- 1. Count first
EVALUATE ROW( "Count", COUNTROWS( INFO.VIEW.MEASURES() ) )

-- 2. Filter by table
EVALUATE FILTER( INFO.VIEW.MEASURES(), [Table] = "KPI_Measures" )

-- 3. Filter by name pattern (use SEARCH for contains)
EVALUATE
FILTER(
    INFO.VIEW.MEASURES(),
    NOT ISERROR( SEARCH( "YTD", [Name], 1 ) )
)
```

---

## Usage with execute_dax.py

`products/fabric/powerbi/tooling/scripts/execute_dax.py` is the preferred CLI runner for these queries:

```bash
# Quick scope estimation (ASCII table output)
py -3 products/fabric/powerbi/tooling/scripts/execute_dax.py \
  --workspace "MyWorkspace" --model "Commercial" \
  --format ascii \
  "EVALUATE ROW(\"Tables\", COUNTROWS(INFO.VIEW.TABLES()), \"Measures\", COUNTROWS(INFO.VIEW.MEASURES()))"

# Export all measures to CSV for offline analysis
py -3 products/fabric/powerbi/tooling/scripts/execute_dax.py \
  --workspace "MyWorkspace" --model "Commercial" \
  --format csv \
  "EVALUATE SELECTCOLUMNS(INFO.VIEW.MEASURES(), \"Table\", [Table], \"Measure\", [Name], \"Expression\", [Expression])" \
  > measures_export.csv

# Pipe JSON to jq for filtering
py -3 products/fabric/powerbi/tooling/scripts/execute_dax.py \
  --workspace "MyWorkspace" --model "Commercial" \
  --format json \
  "EVALUATE INFO.VIEW.RELATIONSHIPS()" | jq '.[] | select(.IsActive == false)'
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ExecuteQuery not available` | MCP Server not connected or model offline | Check `fab auth status`; verify model is deployed and accessible |
| `INFO.* Permission Error` | Tenant restricts non-VIEW variants to admins | Switch to `INFO.VIEW.*` equivalents |
| `INFO.ROLEMEMBERSHIPS()` returns empty | RLS members stored outside model metadata | Use REST: `GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/Default.GetBoundRoleAssignments` |
| `DEPENDENCIES()` returns 0 rows for a measure | Measure has no external references (constant or parameter) | Expected — no action needed |
| Large result set / timeout | Model has thousands of objects | Apply `SELECTCOLUMNS` + `FILTER`; run scope estimation first |
| `fab api` returns 401 | Wrong audience or expired token | Run `fab auth login`; check `fab auth status` |
