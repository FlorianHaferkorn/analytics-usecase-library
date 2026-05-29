# Fix Broken Field References in PBIR Reports

> Source: data-goblin/power-bi-agentic-development — pbir-format skill reference

Workflow for diagnosing and repairing reports with broken field references caused by semantic model changes (renamed tables, renamed columns/measures, moved measures between tables, or removed fields).

## Symptoms

- Visual error icons (X) with "Something's wrong with one or more fields"
- "Fields that need to be fixed" dialog showing `Missing_References`
- Filter pane showing warning icons on filters
- Visuals rendering with blank/zero data despite valid filters
- `pbir validate --fields` reporting missing fields (when model is accessible)

## Diagnosis: Categorise Each Broken Reference

| Category | Example | Fix strategy |
|----------|---------|--------------|
| **Table renamed** | `1. Measures: Actuals` -> `Actuals` | Replace Entity everywhere |
| **Field renamed** | `Gross Sales MTD` -> `Turnover MTD` | Replace Property + queryRef + metadata |
| **Field moved** | `Invoices.Revenue` -> `Actuals.Revenue` | Replace Entity only (Property unchanged) |
| **Field removed** | `Gross Sales YTD` no longer exists | Find substitute or remove from visuals |

## Step 1: Use `pbir fields replace` for Structured References

```bash
pbir fields replace "Report.Report" \
  --from "OldTable.OldField" --to "NewTable.NewField" --skip-validation
```

Handles `Entity`, `Property`, and `queryRef` in query projections and sort definitions.

## Step 2: Bulk-Replace Remaining References

`pbir fields replace` does not catch all locations. Also replace:

- `queryRef` strings: `"OldTable.FieldName"` -> `"NewTable.FieldName"`
- `metadata` selectors: `"metadata": "OldTable.FieldName"` in `objects`
- filter `Entity` references: `"Entity": "OldTable"` in `From` arrays
- FillRule/Conditional expressions: deeply nested `SourceRef.Entity`

```python
import os, json

replacements = {
    '"OldTableName"': '"NewTableName"',
    'OldTable.FieldName': 'NewTable.FieldName',
}

for root, dirs, files in os.walk('Report.Report/definition'):
    for f in files:
        if not f.endswith('.json'):
            continue
        path = os.path.join(root, f)
        with open(path) as fh:
            content = fh.read()
        original = content
        for old, new in sorted(replacements.items(), key=lambda x: -len(x[0])):
            content = content.replace(old, new)
        if content != original:
            json.loads(content)  # validate JSON before writing
            with open(path, 'w') as fh:
                fh.write(content)
```

## Step 3: Handle Slicer Filter Values Carefully

**Critical distinction**: filter **field references** vs filter **literal values**.

- `"Entity": "TableName"` and `"Property": "FieldName"` are field references — replace them
- `"Value": "'Gross Sales MTD vs. Budget'"` is a **data value** — do NOT replace unless the model data actually changed

Slicer default selections contain literal values from model data. Renaming a measure does NOT change slicer data values.

## Step 4: Validate and Deploy

```bash
# Validate structure
pbir validate "Report.Report" --allow-download-schemas

# Deploy to Fabric
fab import "Workspace.Workspace/Report.Report" -i "Report.Report" -f
```

## Common Pitfalls

### queryRef mismatch causes blank visuals

Visuals may pass schema validation but render with no data if `queryRef` strings reference old table names. Power BI uses `queryRef` internally to match data to visual slots. Always update `queryRef` when renaming tables.

### Combo chart roles

`lineStackedColumnComboChart` and `lineClusteredColumnComboChart` use `Y` (column bars) and `Y2` (lines), NOT `ColumnY`/`LineY`.

### Report-level filters vs slicer-controlled filters

Avoid duplicating filter logic. If a slicer controls a field (e.g. Calendar Month), do not also add a report-level filter on the same field — they will conflict and may narrow results unexpectedly.
