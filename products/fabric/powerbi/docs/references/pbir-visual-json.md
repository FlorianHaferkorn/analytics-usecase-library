# pbir-visual-json.md — PBIR Visual Configuration

> **Source**: `data-goblin/power-bi-agentic-development` pbir-format/references/visual-json.md
> **Purpose**: Complete structure of `visual.json` files in PBIR format — position, expressions, data binding, objects, and advanced features.

---

## File Location

Each visual in a PBIR report has its own directory and `visual.json`:

```
ReportName.Report/
  definition/
    pages/
      <pageId>/
        visuals/
          <visualId>/
            visual.json    ← this file
```

---

## Top-Level Structure

```json
{
  "name": "<visualId>",
  "position": {
    "x": 16,
    "y": 80,
    "z": 0,
    "width": 400,
    "height": 240,
    "tabOrder": 1000
  },
  "visual": {
    "visualType": "lineChart",
    "query": { ... },
    "objects": { ... },
    "visualContainerObjects": { ... },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": { ... }
}
```

---

## Position Properties

All values are in pixels, measured from the top-left corner of the page canvas.

| Property | Description |
|---|---|
| `x` | Left edge distance from page left |
| `y` | Top edge distance from page top |
| `z` | Z-index (layer order; higher = on top) |
| `width` | Visual width in pixels |
| `height` | Visual height in pixels |
| `tabOrder` | Keyboard tab order (lower = earlier); increment by 1000 |

**Page canvas**: the ALUCA canvases in `core/templates/page_templates/tokens/layout_grid.yaml` (`canvas.design_base` 1280 × 720 for slot coordinates, `canvas.production` 1920 × 1080 for deployed reports; prose in `governance/Layout_Grid_System.md`), not the Power BI default. `tooling/validation/validate_report.ps1` (ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY) reads them from there. Use `products/fabric/powerbi/tooling/page_scaffold_generator/` for layout calculations.

---

## Visual Types (visualType)

Common values for `visual.visualType`:

| Value | Visual |
|---|---|
| `card` | Card (single value KPI) |
| `multiRowCard` | Multi-row card |
| `kpiVisual` | KPI visual |
| `lineChart` | Line chart |
| `barChart` | Clustered bar chart |
| `columnChart` | Clustered column chart |
| `waterfallChart` | Waterfall chart |
| `tableEx` | Table |
| `pivotTable` | Matrix |
| `slicer` | Slicer |
| `textbox` | Text box |
| `image` | Image |
| `shape` | Shape |
| `actionButton` | Button |
| `smartNarrativeVisual` | Smart narrative |
| `scatterChart` | Scatter chart |
| `ribbonChart` | Ribbon chart |
| `funnel` | Funnel chart |

---

## Query / Data Binding

The `query` object defines what data the visual requests from the semantic model.

### Projections

```json
{
  "query": {
    "queryState": {
      "Rows": {
        "projections": [
          {
            "field": {
              "Column": {
                "Expression": { "SourceRef": { "Entity": "Date" } },
                "Property": "Month"
              }
            },
            "queryRef": "Date.Month",
            "active": true
          }
        ]
      },
      "Values": {
        "projections": [
          {
            "field": {
              "Measure": {
                "Expression": { "SourceRef": { "Entity": "_Measures" } },
                "Property": "Total Revenue"
              }
            },
            "queryRef": "_Measures.Total Revenue"
          }
        ]
      }
    }
  }
}
```

### Query Role Names by Visual Type

| Visual Type | Available Roles |
|---|---|
| Line / Bar / Column chart | `Category`, `Series`, `Values`, `Tooltips` |
| Card | `Values` |
| KPI | `Indicator`, `TrendAxis`, `Goal` |
| Table | `Values` |
| Matrix | `Rows`, `Columns`, `Values`, `Tooltips` |
| Slicer | `Field` |
| Scatter | `XValue`, `YValue`, `Size`, `Details`, `Series` |

---

## Expression Types

### Column Reference

```json
{
  "Column": {
    "Expression": { "SourceRef": { "Entity": "TableName" } },
    "Property": "ColumnName"
  }
}
```

### Measure Reference

```json
{
  "Measure": {
    "Expression": { "SourceRef": { "Entity": "_Measures" } },
    "Property": "Measure Name"
  }
}
```

### Extension Measure Reference

```json
{
  "Measure": {
    "Expression": { "SourceRef": { "Schema": "extension", "Entity": "_Measures" } },
    "Property": "Extension Measure Name"
  }
}
```

### Hierarchy Level Reference

```json
{
  "HierarchyLevel": {
    "Expression": {
      "Hierarchy": {
        "Expression": { "SourceRef": { "Entity": "Date" } },
        "Hierarchy": "Date Hierarchy"
      }
    },
    "Level": "Month"
  }
}
```

### Literal Value

```json
{ "Literal": { "Value": "42" } }
{ "Literal": { "Value": "'Text value'" } }
{ "Literal": { "Value": "true" } }
```

---

## Objects vs visualContainerObjects

This is a critical distinction:

| Key | Applies To | Examples |
|---|---|---|
| `objects` | **Visual content** — the chart, table, card content | Axis formatting, data colors, data labels, legend, series formatting |
| `visualContainerObjects` | **Visual container** — the wrapper box | Title, background, border, shadow, tooltip header |

```json
{
  "visual": {
    "objects": {
      "categoryAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } }, "selector": null }],
      "legend": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } }, "selector": null }]
    },
    "visualContainerObjects": {
      "title": [{
        "properties": {
          "show": { "expr": { "Literal": { "Value": "true" } } },
          "text": { "expr": { "Literal": { "Value": "'Revenue Trend'" } } },
          "fontSize": { "expr": { "Literal": { "Value": "12" } } }
        },
        "selector": null
      }],
      "background": [{
        "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } },
        "selector": null
      }]
    }
  }
}
```

---

## Common Object Configurations

### Disable Axis and Legend (Clean Chart)

```json
"objects": {
  "categoryAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } }, "selector": null }],
  "valueAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } }, "selector": null }],
  "legend": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } }, "selector": null }]
}
```

### Data Labels

```json
"objects": {
  "labels": [{
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#374151'" } } } } },
      "fontSize": { "expr": { "Literal": { "Value": "10" } } }
    },
    "selector": null
  }]
}
```

### Visual Title

```json
"visualContainerObjects": {
  "title": [{
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "text": { "expr": { "Literal": { "Value": "'My Visual Title'" } } },
      "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#111827'" } } } } },
      "fontSize": { "expr": { "Literal": { "Value": "12" } } },
      "fontFamily": { "expr": { "Literal": { "Value": "'Segoe UI Semibold'" } } }
    },
    "selector": null
  }]
}
```

### Slicer Style

```json
"objects": {
  "data": [{
    "properties": {
      "mode": { "expr": { "Literal": { "Value": "'Dropdown'" } } }
    },
    "selector": null
  }]
}
```

---

## Analytics Lines (Reference Lines)

Add constant or dynamic reference lines to charts:

```json
"objects": {
  "referenceLineLayer": [
    {
      "id": "referenceLine_1",
      "properties": {
        "show": { "expr": { "Literal": { "Value": "true" } } },
        "type": { "expr": { "Literal": { "Value": "'custom'" } } },
        "value": {
          "expr": {
            "Measure": {
              "Expression": { "SourceRef": { "Entity": "_Measures" } },
              "Property": "Target Revenue"
            }
          }
        },
        "lineColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#DC2626'" } } } } },
        "transparency": { "expr": { "Literal": { "Value": "0" } } },
        "style": { "expr": { "Literal": { "Value": "'dashed'" } } },
        "position": { "expr": { "Literal": { "Value": "'back'" } } },
        "label": {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "text": { "expr": { "Literal": { "Value": "'Target'" } } }
          }
        }
      },
      "selector": null
    }
  ]
}
```

---

## Small Multiples

Enable small multiples by adding a `SmallMultiples` query projection:

```json
{
  "SmallMultiples": {
    "projections": [
      {
        "field": {
          "Column": {
            "Expression": { "SourceRef": { "Entity": "Product" } },
            "Property": "Category"
          }
        },
        "queryRef": "Product.Category"
      }
    ]
  }
}
```

---

## filterConfig

Visual-level filters restrict the data returned for that visual without affecting other visuals on the page:

```json
{
  "filterConfig": {
    "filters": [
      {
        "name": "<filterId>",
        "field": {
          "Column": {
            "Expression": { "SourceRef": { "Entity": "Date" } },
            "Property": "Year"
          }
        },
        "filter": {
          "Version": 2,
          "From": [{ "Name": "d", "Entity": "Date", "Type": 0 }],
          "Where": [{
            "Condition": {
              "In": {
                "Expressions": [{ "Column": { "Expression": { "SourceRef": { "Source": "d" } }, "Property": "Year" } }],
                "Values": [[{ "Literal": { "Value": "2025" } }]]
              }
            }
          }]
        },
        "type": "TopN",
        "isHiddenInViewMode": true
      }
    ]
  }
}
```

---

## drillFilterOtherVisuals

Controls whether this visual participates in cross-filtering:

```json
{
  "visual": {
    "drillFilterOtherVisuals": true
  }
}
```

Set to `false` for KPI cards, text boxes, and date slicers that should not filter other visuals when clicked.
