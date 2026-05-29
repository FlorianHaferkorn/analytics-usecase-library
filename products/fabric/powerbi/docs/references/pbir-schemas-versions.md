# Power BI PBIR Schemas — Versions Reference

> Source: data-goblin/power-bi-agentic-development — pbir-format skill reference

**Schemas update frequently** — Microsoft updates PBIR schemas roughly monthly. Always match the `$schema` URL in existing report files. Do not upgrade schema versions unless intentional.

Source repository: `https://github.com/microsoft/json-schemas`

## Schema URL Patterns

**Most PBIR files** (inside `definition/`):

```
https://developer.microsoft.com/json-schemas/fabric/item/report/definition/{type}/{version}/schema.json
```

**Root-level files** (`definition.pbir`, `localSettings.json`):

```
https://developer.microsoft.com/json-schemas/fabric/item/report/{type}/{version}/schema.json
```

**Other:**

- Platform: `.../fabric/gitIntegration/platformProperties/2.0.0/schema.json`
- PBIP project: `.../fabric/pbip/pbipProperties/1.0.0/schema.json`
- Semantic model: `.../fabric/item/semanticModel/{type}/{version}/schema.json`

## Current Schema Versions (early 2026)

Use the schema version from your existing project files as the source of truth. These are reference versions as of early 2026:

| Schema Type | Example Version | File |
|-------------|---------|------|
| `visualContainer` | 2.7.0 | visual.json |
| `report` | 3.2.0 | report.json |
| `page` | 2.1.0 | page.json |
| `bookmark` | 2.1.0 | [id].bookmark.json |
| `semanticQuery` | 1.4.0 | embedded in visual.json query |
| `formattingObjectDefinitions` | 1.5.0 | embedded in visual.json objects |
| `reportExtension` | 1.0.0 | reportExtensions.json |
| `versionMetadata` | 1.0.0 | version.json |
| `pagesMetadata` | 1.0.0 | pages.json |
| `filterConfiguration` | 1.3.0 | embedded in report.json / visual.json |
| `visualConfiguration` | 2.3.0 | embedded in visual.json |
| `definitionProperties` | 2.0.0 | definition.pbir |

> To discover latest versions: `py -3 products/fabric/powerbi/tooling/discover_schema_latest.py`

## Schema Exploration

```bash
# List all schema versions for a type
gh api repos/microsoft/json-schemas/contents/fabric/item/report/definition/visualContainer

# Find all expression types in a schema
curl -s https://developer.microsoft.com/json-schemas/fabric/item/report/definition/semanticQuery/1.4.0/schema.json \
  | python3 -c "import sys,json; s=json.load(sys.stdin); print('\n'.join(s['definitions']['QueryExpressionContainer']['properties'].keys()))"
```

## Key Expression Types

Common `expr` wrapper types (the semanticQuery schema defines 48+ types):

| Type | Usage |
|------|-------|
| `Literal` | Fixed values with type suffixes (D=decimal, L=integer, inner single quotes for strings) |
| `ThemeDataColor` | Theme color references (ColorId + Percent) |
| `Measure` | DAX measure references |
| `Column` | Table column references |
| `Aggregation` | Aggregated expressions (Function codes 0–8) |
| `HierarchyLevel` | Hierarchy level references |
| `FillRule` | Gradient color scales (linearGradient2, linearGradient3) |
| `Conditional` | IF-THEN-ELSE branching via Cases array |
| `Comparison` | Comparisons (ComparisonKind: 0=Equal, 1=GT, 2=GTE, 3=LTE, 4=LT) |
| `Arithmetic` | Math operations |
| `And` / `Or` / `Not` | Logical operations |
| `SparklineData` | Inline sparklines in tables |

## dataViewWildcard.matchingOption

| Value | Name | Description |
|-------|------|-------------|
| 0 | Default | Match identities and totals |
| 1 | Instances | Match instances with identities only (per-point formatting) |
| 2 | Totals | Match totals only |

## Selector Types

| Selector | Purpose | Example |
|----------|---------|---------|
| (none) | Applies to all | No `selector` key |
| `metadata` | Specific column/measure | `"selector": {"metadata": "Orders.Order Lines"}` |
| `id` | Named instance | `"selector": {"id": "default"}` |
| `dataViewWildcard` | Pattern matching | `"selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}` |
| `scopeId` | Specific data point value | `"selector": {"data": [{"scopeId": {"Comparison": {...}}}]}` |
