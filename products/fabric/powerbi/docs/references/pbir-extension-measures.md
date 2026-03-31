# pbir-extension-measures.md — Extension Measures (Report-Layer DAX)

> **Source**: `data-goblin/power-bi-agentic-development` pbir-format/references/measures.md
> **Purpose**: Report-layer DAX measures defined in `reportExtensions.json` that exist only at the report layer, not in the semantic model.

---

## What Are Extension Measures?

Extension measures are DAX calculations stored in `ReportName.Report/definition/reportExtensions.json`. They:
- Exist **only at the report layer** — not in the semantic model
- Attach to **existing** semantic model entities (cannot create new tables)
- Are ideal for formatting/color logic that doesn't need reuse across reports
- Are also called "thin report measures" or "report-level measures"

---

## When to Use vs. Alternatives

| Use Extension Measures | Use Model Measures | Use Visual Calculations |
|---|---|---|
| Report-specific formatting logic | Core business metrics | Single-visual calculations |
| Color coding and status indicators | Multi-report reuse | Temporary prototypes |
| Display labels and text formatting | Filtering or categorization | |
| Centralizing formatting DAX across many visuals | KPI definitions and lineage | |

**Cannot be used for:**
- Filters (must live in the model)
- Slicer categories (must live in the model)
- Calculated columns

---

## File Location

```
ReportName.Report/
  definition/
    reportExtensions.json   ← extension measures live here
```

> **Critical**: Delete this file entirely when it has no measures. An empty `reportExtensions.json` causes Power BI deserialization errors.

---

## File Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
  "name": "extension",
  "entities": [
    {
      "name": "ExistingModelTable",
      "measures": [
        {
          "name": "Measure Name",
          "dataType": "Text",
          "expression": "IF([Revenue] >= [Target], \"good\", \"bad\")",
          "displayFolder": "Formatting\\Colors",
          "description": "Status color for Revenue vs Target",
          "hidden": false,
          "references": {
            "measures": ["Revenue", "Target"]
          }
        }
      ]
    }
  ]
}
```

**Fields:**
- `name` (entity) — must match an **existing** table name in the semantic model
- `name` (measure) — unique measure name within the entity
- `dataType` — **must be `"Text"` for color formatting** properties
- `expression` — DAX expression (no `=` prefix, just the expression body)
- `displayFolder` — optional; use `\\` for sub-folders
- `hidden` — hide helper measures from the Fields pane
- `references.measures` — document model measure dependencies

---

## Color Formatting Pattern

The most common use case is returning theme color tokens instead of hardcoded hex values:

```json
{
  "name": "Revenue Status Color",
  "dataType": "Text",
  "expression": "IF([Total Revenue] >= [Revenue Target], \"good\", IF([Total Revenue] >= [Revenue Target] * 0.9, \"neutral\", \"bad\"))",
  "displayFolder": "Formatting\\Colors"
}
```

**Theme token values** (preferred over hex — respects theme changes):
- `"good"` — green / positive
- `"neutral"` — yellow / warning
- `"bad"` — red / negative
- `"foreground"` — default text color
- `"background"` — default background

---

## Referencing Extension Measures in Visuals

Visual `visual.json` files reference extension measures using `"Schema": "extension"` in the `SourceRef`:

```json
{
  "type": "Extension",
  "Expression": {
    "Measure": {
      "Expression": {
        "SourceRef": {
          "Schema": "extension",
          "Entity": "ExistingModelTable"
        }
      },
      "Property": "Revenue Status Color"
    }
  }
}
```

> Without `"Schema": "extension"`, the visual cannot find the measure.

---

## Organising Extension Measures

- Host in measure-only tables (e.g. `_Measures`, `_Formatting`) when possible
- Use display folders: `"displayFolder": "Formatting\\Colors"`
- Mark helper measures as `"hidden": true`
- Document purpose in `"description"` field
- Track model dependencies in `"references.measures"`

---

## Promotion Path

Once an extension measure is stable and needed in other reports, move it to the semantic model:

1. Copy the DAX expression to a new measure in the `_Measures` table (`.tmdl`)
2. Add `formatString`, `displayFolder`, `lineageTag`, and `/// Purpose:` doc comment
3. Update the visual reference: remove `"Schema": "extension"` from `SourceRef`
4. Delete the entry from `reportExtensions.json` (delete file if now empty)
5. Run `run_fabric_checks.ps1` to validate

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| Deserialization error on report open | Empty `reportExtensions.json` | Delete the file entirely |
| Measure not found in visual | Missing `"Schema": "extension"` in SourceRef | Add `"Schema": "extension"` to the entity's SourceRef |
| Cannot create new table | Extension measures must attach to existing entities | Use an existing model table as the entity |
| Color not applying | `dataType` is not `"Text"` | Change `dataType` to `"Text"` |
