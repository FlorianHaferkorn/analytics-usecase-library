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

### Base theme: Fluent 2 for new reports, CY26SU10 in ALUCA

Since August 2026, **Fluent 2** is the base theme of every new report in Desktop and the
service; Classic 2026 and Classic 2018 remain selectable. Existing reports keep their base
theme until someone selects **Update theme** or **Reset to default**. Fluent 2 changes, among
others: titles and subtitles on, axis titles off, more padding with rounded corners, smooth
lines in line charts, grey wallpaper and background, 1920×1080 for new pages
([Visual defaults in Power BI reports](https://learn.microsoft.com/power-bi/create-reports/power-bi-reports-visual-defaults), checked 29.09.2026).

ALUCA generators pin the base theme that the pinned official CLI
(`@microsoft/powerbi-report-authoring-cli` 0.4.0) scaffolds new reports with: `CY26SU10`
(Meridian D-587, 30.09.2026). Name, `reportVersionAtImport` and the vendored file live in one
place, `tooling/report_quality/base_theme.py` + `tooling/schemas/pbir/base_themes/`; the
generators (`page_scaffold_generator/pbip_writer.py`, `adapters/pbip.py`,
`apply_report_theme.py`, `tooling/superversion/targets/pbir.py`) read them and ship
`BaseThemes/CY26SU10.json`. `tooling/tests/test_base_theme_drift.py` compares the copy against
a `scaffold` of the pinned CLI; `apply_report_theme --sync-base-theme [--check]` moves existing
reports. Generated reports therefore do not move to Fluent 2 on their own
(ANNAHME, ungeprueft: `CY26SU10` is Classic 2026, not Fluent 2 — D-587). A custom theme must still not rely on the base theme for
what it wants to control: whatever it leaves out changes when a report is created in
Desktop or its base theme is updated.

Measured on 29.09.2026 (script over the theme JSONs, one flag per property):

| Property Fluent 2 changes | Vendored themes (`themes/`, 32) | BrandSpec derivation (`core/brand/derivations/pbi_theme.py`) |
|---|---|---|
| Fonts: `textClasses` callout/title/header/label with face, size, colour | 32/32 | set since 29.09.2026 (before: none) |
| `title.show`, `subTitle.show` | 32/32 | not set |
| `padding`, `border.radius` | 32/32 | not set |
| Page `background` and `outspace` | 32/32 | not set |
| `categoryAxis`/`valueAxis` `showAxisTitle` | 0/32 | not set |
| `lineStyles.lineChartType` | 0/32 | not set |

The vendored themes come from Freelancing `products/pbi_theme` (read-only here, `themes/PIN.json`);
gaps in them are fixed there and re-mirrored.

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
