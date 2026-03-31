# pbir-theme.md — PBIR Report Themes

> **Source**: `data-goblin/power-bi-agentic-development` pbir-format/references/theme.md
> **Purpose**: Theme architecture, inheritance system, and modification guidance for PBIR reports.

---

## Theme Architecture

A PBIR report uses two theme layers:

```
StaticResources/
  SharedResources/
    BaseThemes/
      CY24SU10.json    ← base theme (Power BI built-in)
  RegisteredResources/
    <ThemeName>.json   ← custom theme (your overrides)
```

The custom theme inherits from the base theme and overrides specific properties. **Modify the custom theme file, not the base theme.** The base theme is managed by Microsoft and changes with Power BI updates.

---

## Theme File Structure

```json
{
  "name": "Aurora Monochromatic Light",
  "dataColors": ["#1A56DB", "#1C64F2", "#3F83F8", "#76A9FA", "#BAD0FD", "#E1EAFE"],
  "background": "#FFFFFF",
  "foreground": "#111827",
  "tableAccent": "#1A56DB",
  "visualStyles": {
    "*": {
      "*": {
        "general": [{ "responsive": { "value": true } }],
        "background": [{ "show": { "value": false } }],
        "border": [{ "show": { "value": false } }]
      }
    }
  },
  "textClasses": {
    "label": { "fontFace": "Segoe UI", "fontSize": 9, "color": "#6B7280" },
    "callout": { "fontFace": "Segoe UI Semibold", "fontSize": 45, "color": "#111827" },
    "title": { "fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#111827" },
    "header": { "fontFace": "Segoe UI", "fontSize": 12, "color": "#111827" },
    "largeTitle": { "fontFace": "Segoe UI Semibold", "fontSize": 14, "color": "#111827" }
  }
}
```

---

## Three-Level Inheritance System

Visual formatting follows a strict cascade — more specific settings override less specific ones:

```
Theme (lowest specificity)
  ↓
Visual Type defaults
  ↓
Per-visual instance settings (highest specificity)
```

**Best practice**: Set defaults at the theme level. Override per visual type only when necessary. Set per-instance overrides only for exceptional cases.

### Wildcard Selectors in visualStyles

`visualStyles` uses three levels of specificity:

```json
{
  "visualStyles": {
    "*": {           ← applies to all visual types
      "*": {         ← applies to all instances of that type
        "property": [{ "value": "..." }]
      }
    },
    "card": {        ← applies to card visual type only
      "*": {         ← applies to all card instances
        "property": [{ "value": "..." }]
      }
    }
  }
}
```

Example — disable borders on all visuals, but enable them on tables:

```json
{
  "visualStyles": {
    "*": {
      "*": {
        "border": [{ "show": { "value": false } }]
      }
    },
    "tableEx": {
      "*": {
        "border": [{ "show": { "value": true } }]
      }
    }
  }
}
```

---

## Color System

### dataColors

The `dataColors` array defines the series palette (used for bar charts, line charts, pie charts, etc.):

```json
{
  "dataColors": [
    "#1A56DB",  ← color 1 (primary)
    "#1C64F2",  ← color 2
    "#3F83F8",  ← color 3
    "#76A9FA",  ← color 4
    "#BAD0FD",  ← color 5
    "#E1EAFE"   ← color 6
  ]
}
```

### Semantic Colors

These named colors are used by conditional formatting (see `pbir-conditional-formatting.md`):

```json
{
  "good": "#16A34A",
  "neutral": "#D97706",
  "bad": "#DC2626",
  "maximum": "#1A56DB",
  "center": "#E5E7EB",
  "minimum": "#EF4444",
  "null": "#9CA3AF"
}
```

### Background and Foreground

```json
{
  "background": "#FFFFFF",    ← page background
  "foreground": "#111827",    ← default text / foreground
  "tableAccent": "#1A56DB"    ← table header accent
}
```

---

## Common Visual Style Properties

### Card / KPI Card

```json
"card": {
  "*": {
    "labels": [{ "color": { "value": "#6B7280" }, "fontSize": { "value": 10 } }],
    "calloutValue": [{ "color": { "value": "#111827" }, "fontSize": { "value": 28 } }],
    "categoryLabel": [{ "color": { "value": "#6B7280" }, "fontSize": { "value": 10 } }],
    "background": [{ "show": { "value": false } }]
  }
}
```

### Table / Matrix

```json
"tableEx": {
  "*": {
    "columnHeaders": [{
      "fontColor": { "value": "#FFFFFF" },
      "backColor": { "value": "#1A56DB" },
      "fontSize": { "value": 11 }
    }],
    "values": [{
      "fontColor": { "value": "#111827" },
      "backColor": { "value": "#FFFFFF" },
      "altBackColor": { "value": "#F9FAFB" }
    }],
    "total": [{
      "fontColor": { "value": "#111827" },
      "backColor": { "value": "#E5E7EB" }
    }]
  }
}
```

### Slicer

```json
"slicer": {
  "*": {
    "data": [{ "fontColor": { "value": "#111827" }, "fontSize": { "value": 10 } }],
    "selection": [{ "selectAllCheckboxEnabled": { "value": true } }],
    "header": [{ "show": { "value": false } }]
  }
}
```

### Line / Bar Chart

```json
"lineChart": {
  "*": {
    "categoryAxis": [{ "show": { "value": true }, "gridlineShow": { "value": false } }],
    "valueAxis": [{ "show": { "value": true }, "gridlineShow": { "value": true }, "gridlineColor": { "value": "#E5E7EB" } }],
    "legend": [{ "show": { "value": false } }]
  }
}
```

---

## Text Classes

`textClasses` defines reusable font presets referenced across visual styles:

| Class | Typical Use | Default Size |
|---|---|---|
| `label` | Axis labels, data labels | 9pt |
| `callout` | KPI card values | 45pt |
| `title` | Visual titles | 12pt |
| `header` | Column headers | 12pt |
| `largeTitle` | Page titles | 14pt |

```json
{
  "textClasses": {
    "label": { "fontFace": "Segoe UI", "fontSize": 9, "color": "#6B7280" },
    "callout": { "fontFace": "Segoe UI Semibold", "fontSize": 45, "color": "#111827" },
    "title": { "fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#111827" }
  }
}
```

---

## Applying a Theme via Fabric CLI

```bash
# After updating theme.json locally, redeploy the report
fab import "Workspace.Workspace/Report.Report" \
  -i ./dist/Report.Report \
  -f

# Or update just the theme file via API
# (requires full report definition update — no partial file updates in Fabric API)
```

---

## Theme vs. Per-Visual Formatting

| Scenario | Use Theme | Use Per-Visual |
|---|---|---|
| Consistent brand colors across all visuals | Yes | No |
| Default font across all cards | Yes | No |
| One chart with a custom accent color | No | Yes |
| Page-level background | Yes (background property) | No |
| Individual visual background | No | Yes (objects.background) |

**Rule**: If more than one visual needs a formatting rule, put it in the theme. If it's truly one-off, set it in the visual's `objects`.
