# Power BI / Fabric Connector

> **Connector version:** 2.0.1 (implements abstract spec v2.0)
> **Status:** Active — production connector for the Fabric/Power BI product track
> **Location:** `products/fabric/powerbi/`
> **Abstract spec:** `../Design_Spec_3_30_300.md` · `../Connector_Spec.md` · `../Abstract_Visual_Types.md`

---

## 1. Connector Overview

This document is the formal registration of the Power BI / Fabric connector against the `Connector_Spec.md` contract. It maps every abstract framework requirement to the corresponding Power BI implementation and documents all PBI-specific properties.

### Tooling

| Tool | Location | Purpose |
|---|---|---|
| Page scaffold generator | `products/fabric/powerbi/tooling/page_scaffold_generator/` | Generates PBIP page JSON from `UseCase_Bracket.yaml` |
| Grid calculator | `…/page_scaffold_generator/grid_calculator.py` | 12×12 LU → pixel coordinate conversion |
| Theme generator | `products/fabric/powerbi/tooling/theme_generator/` | Generates PBI theme JSON with semantic color roles |
| BPA linter | `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md` | Validates framework hard limits |
| Mockup design spec | `products/fabric/powerbi/tooling/page_scaffold_generator/MOCKUP_DESIGN_SPEC.md` | PBI-specific design authority |

---

## 2. Canvas and Scaling

### Canvas Configuration

| Mode | Canvas size | Usage |
|---|---|---|
| **Design base** | 1280×720 | All grid calculations performed at this size |
| **Production** | 1920×1080 | Scaffold output; FitToPage scales to display |
| **4K** | 2560×1440 | Optional; requires +4pt font compensation |

**PBI-specific issue:** Power BI fonts are defined in points and do **not** scale proportionally when FitToPage changes the display size. At 1920×1080 displayed on a 1366×768 screen (0.71× scale), a 9pt font becomes visually ~6pt — unreadable.

**Resolution applied by scaffold generator:**

| Design canvas | Production canvas | Font delta applied |
|---|---|---|
| 1280×720 | 1920×1080 | +2pt on all typography roles |
| 1280×720 | 2560×1440 | +4pt on all typography roles |

Font delta values are set in `products/fabric/powerbi/tooling/page_scaffold_generator/typography_config.json`.

### Grid → Pixel Conversion

The `GridCalculator` class (`grid_calculator.py`) implements the 12×12 LU formulae from `tokens/layout_grid.yaml` (prose: `governance/Layout_Grid_System.md §Grid Formulae`):

```python
# Default parameters (1920×1080 production canvas)
canvas_width  = 1920, canvas_height = 1080
outer_margin  = 32
gutter        = 16

# Computed LU sizes at 1920×1080
lu_width  = (1920 - 2×32 - 11×16) / 12 = 128.0px
lu_height = (1080 - 2×32 - 11×16) / 12 = 72.0px

# Slot (col=0, row=0, col_span=12, row_span=2) → KPI_Cards band
x=32, y=32, width=1856, height=160
```

Usage: `from grid_calculator import calculate_visual_rect`

---

## 3. Visual Type Mapping (Abstract → PBI)

| Abstract Type | PBI `visualType` | Notes |
|---|---|---|
| `kpi_card` | `cardVisual` | New Card visual (2023+); use `visualContainerObjects` for title |
| `kpi_card_hero` | `cardVisual` | Same as `kpi_card`; larger `height` via grid slot |
| `kpi_card_compact` | `cardVisual` | Same as `kpi_card`; `col_span=2` instead of default |
| `status_tile` | `cardVisual` | KPI Card with threshold-based background fill |
| `line_chart` | `lineChart` | |
| `area_chart` | `areaChart` | |
| `sparkline` | Inline in `cardVisual` | Configured via `sparkline` property in cardVisual JSON |
| `bar_chart_horizontal` | `barChart` | `orientation: "horizontal"` in `objects` |
| `bar_chart_column` | `columnChart` | |
| `stacked_bar_100pct` | `stackedBarChart` | `percentageStackedLayout: true` |
| `waterfall` | `waterfallVisual` | Native; no plugin required |
| `scatter_plot` | `scatterChart` | |
| `decomposition_tree` | `decompositionTree` | |
| `funnel_chart` | `funnelChart` | |
| `recommendation_table` | `tableEx` | With conditional formatting on priority column |
| `action_card` | `textbox` | Structured markdown text visual |
| `action_teaser` | `textbox` | Short inline text callout |
| `table_with_databars` | `tableEx` | Data bars via `columnFormatting.dataBarFormatting` |
| `matrix` | `pivotTable` | |
| `text_narrative` | `textbox` | Smart Narrative or static text |
| `slicer_dropdown` | `slicer` | `style: "Dropdown"` in slicer objects |
| `slicer_range` | `slicer` | `style: "BetweenSlider"` for date range |
| `slicer_list` | `slicer` | `style: "VerticalList"` |
| `slicer_toggle` | `slicer` | `style: "TileList"` (button-style) |

### PBIR Visual JSON Structure

Visual files live at:
```
ReportName.Report/definition/pages/<pageId>/visuals/<visualId>/visual.json
```

Minimum required structure:
```json
{
  "name": "<visualId>",
  "position": { "x": 32, "y": 32, "z": 0, "width": 1856, "height": 160, "tabOrder": 0 },
  "visual": {
    "visualType": "cardVisual",
    "query": { "queryState": { "Values": { "projections": [...] } } },
    "objects": {},
    "visualContainerObjects": {}
  }
}
```

Reference: `products/fabric/powerbi/docs/references/pbir-visual-json.md`

---

## 4. Color Semantic Role Mapping (Abstract → PBI Theme)

PBI theme JSON property paths for each abstract semantic role:

| Abstract Role | PBI Theme Property | Default Value |
|---|---|---|
| `semantic.positive` | `good` | `#1F6B2B` (WCAG AA green) |
| `semantic.negative` | `bad` | `#B00020` (WCAG AA red) |
| `semantic.warning` | `neutral` | `#E65100` (WCAG AA amber) |
| `semantic.neutral` | `foregroundNeutralSecondary` | `#757575` |
| `brand.primary` | `dataColors[0]` | Brand color 1 |
| `brand.secondary` | `dataColors[1]` | Brand color 2 |
| `brand.data_colors[0–7]` | `dataColors[0–7]` | Palette array |

**Target line / reference:** Use `dataColors[8]` or theme `hyperlink` color. Style: dashed, 1.5px.

### Theme JSON Structure

Generated by `theme_generator/`. Key semantic sections:

```json
{
  "name": "AnalyticsUseCase",
  "dataColors": ["#0066CC", "#E65100", ...],
  "good": "#1F6B2B",
  "bad": "#B00020",
  "neutral": "#E65100",
  "maximum": "#1F6B2B",
  "minimum": "#B00020",
  "null": "#757575",
  "background": "#FFFFFF",
  "tableAccent": "#E0E0E0",
  "foreground": "#1F1F1F",
  "textClasses": { ... }
}
```

Full spec: `core/brand/tool_derivations/powerbi_mapping.md`

---

## 5. Interaction Patterns (Abstract → PBI)

### Drillthrough

```json
// Detail page configuration in page.json:
{
  "type": "Drillthrough",
  "visibility": "AlwaysVisible",
  "displayName": "Detail",
  "pageBinding": { "type": "DefaultPageBinding" }
}
```

Filter context passes automatically from source visual to drillthrough target. The `pageBinding` configuration in PBIP handles this without custom JSON — set via `page.json` `type` field.

### Slicer Cascade

All slicers on a page cascade to all visuals by default in Power BI. Explicit sync control via Slicer Sync panel in PBI Desktop. For visuals that must **not** respond to slicer (e.g., a fixed reference KPI), set:

```json
// In visual.json:
"filters": [],
"drillFilterOtherVisuals": false
```

### Cross-filter

Controlled per visual via `drillFilterOtherVisuals`. KPI cards and date slicers must have this set to `false` to avoid unintended cross-filtering.

### Tooltip Pages

Report-page tooltips provide hover detail-on-demand without leaving the page:

```json
// In target visual.json objects:
"tooltips": {
  "type": { "type": "boolean" },
  "properties": { "type": { "expr": { "Literal": { "Value": "'ToolTipReport'" } } } }
}
```

Reference: `products/fabric/powerbi/docs/references/pbir-visual-json.md`

---

## 6. BPA Hard Limits (PBI Linter Enforcement)

The abstract Framework Hard Limits (`Connector_Spec.md §3.4`) are enforced in PBI by the BPA linter defined in `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md`.

| Abstract Limit | BPA Rule ID | Enforcement |
|---|---|---|
| ≤20 visible visuals per page | `PAGE_VISUAL_COUNT` | Error — blocks publish |
| ≤6 data fields per visual | `VISUAL_FIELD_COUNT` | Warning |
| ≤3 slicers per page | `SLICER_COUNT` | Warning |
| No vertical scroll | `PAGE_FIT_MODE` | Error if `displayOption ≠ FitToPage` |
| 0 hard-coded colors | `HARDCODED_COLOR` | Warning |
| 0 pie/donut charts | `DISALLOWED_VISUAL` | Error |

Run BPA validation: `.\tooling\run_stage1_checks.ps1` (from repo root)

---

## 7. Page Configuration

Every PBIP page requires a `page.json` file:

```json
{
  "name": "<pageId>",
  "displayName": "Overview",
  "displayOption": "FitToPage",
  "width": 1920,
  "height": 1080,
  "visibility": "HiddenInViewMode",
  "type": "Normal"
}
```

Detail pages:
```json
{
  "displayName": "Detail",
  "displayOption": "FitToPage",
  "type": "Drillthrough",
  "visibility": "AlwaysVisible"
}
```

---

## 8. Accessibility in PBI

| Abstract Requirement | PBI Implementation |
|---|---|
| Alt text / title on every visual | Set `title.text` in `visualContainerObjects`; used as accessibility label |
| Focus order | `tabOrder` field in `position` object; set per grid slot order |
| WCAG AA contrast | Theme generator validates contrast ratios; use `good`/`bad`/`neutral` theme roles |
| Colorblind safety | Delta signals always use icon (▲▼⚠─) via conditional formatting measure + color |

Tab order follows: `KPI_Cards` → `Main_1` → `Main_2` → `Main_3` → `Slicer_Date/Cat` → `ActionPanel` (if present)

---

## 9. Compliance Report (Power BI Connector v2.0.1)

Run date: per CI execution — see `tooling/validation/` output.

### Slot Coverage
- [x] All mandatory slots implemented
- [x] Optional slots handled per `UseCase_Bracket.yaml` activation
- [x] Slot positions within 5% of LU grid (grid_calculator.py)

### Visual Types
- [x] All required abstract types mapped (§3 above)
- [x] No disallowed visual types (BPA rule `DISALLOWED_VISUAL`)

### Color Semantics
- [x] All 4 semantic roles in theme JSON (`good`/`bad`/`neutral`/`foregroundNeutralSecondary`)
- [x] No hard-coded colors (BPA rule `HARDCODED_COLOR`)
- [x] WCAG AA validated by theme generator
- [x] Colorblind safety: icon+color on all delta signals

### Framework Hard Limits
- [x] ≤20 visuals per page (BPA `PAGE_VISUAL_COUNT`)
- [x] ≤6 fields per visual (BPA `VISUAL_FIELD_COUNT`)
- [x] ≤3 slicers (BPA `SLICER_COUNT`)
- [x] No vertical scroll (`displayOption: FitToPage`)
- [x] Pie/donut = 0 (BPA `DISALLOWED_VISUAL`)

### Navigation
- [x] Drillthrough passes filter context (`type: "Drillthrough"` + `pageBinding`)
- [x] Direct Detail access (`visibility: "AlwaysVisible"`)
- [x] Back navigation via page navigation button or breadcrumb bookmark

### Accessibility
- [x] Every visual has `title.text` in `visualContainerObjects`
- [x] Tab order set via `position.tabOrder`
- [x] WCAG AA verified by theme generator

### Known PBI-Specific Limitations

| Limitation | Workaround |
|---|---|
| Fonts don't scale with FitToPage | Font delta compensation applied by scaffold generator (+2pt at 1920×1080) |
| Smart Narrative AI not always available | Static `textbox` with authored text as fallback |
| Decomposition Tree limited in PBIR export | Scaffold flags this with a warning; manual configuration required post-import |
| Drillthrough loses slicer context (PBI limitation) | Use `pageBinding` + visual-level filter pass via custom measure |

---

## 10. References

| Document | Location |
|---|---|
| PBIR visual JSON structure | `products/fabric/powerbi/docs/references/pbir-visual-json.md` |
| PBIR conditional formatting | `products/fabric/powerbi/docs/references/pbir-conditional-formatting.md` |
| Theme JSON | `products/fabric/powerbi/docs/references/pbir-theme.md` |
| Extension measures | `products/fabric/powerbi/docs/references/pbir-extension-measures.md` |
| Mockup design spec | `products/fabric/powerbi/tooling/page_scaffold_generator/MOCKUP_DESIGN_SPEC.md` |
| BPA rules | `tooling/linters/powerbi/REPORT_BEST_PRACTICES.md` |
| Grid calculator | `products/fabric/powerbi/tooling/page_scaffold_generator/grid_calculator.py` |
| Brand/theme mapping | `core/brand/tool_derivations/powerbi_mapping.md` |
| Abstract spec | `core/templates/page_templates/Design_Spec_3_30_300.md` |
| Connector contract | `core/templates/page_templates/Connector_Spec.md` |
