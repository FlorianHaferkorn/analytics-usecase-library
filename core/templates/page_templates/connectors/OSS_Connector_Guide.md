# OSS Connector Guide — 3-30-300 Framework

> **Scope:** This document is a **reference sketch** for implementing the 3-30-300 page template framework using open-source BI tools.
>
> **Status:** Reference / Architectural Guide — not production-validated. Tool-specific connectors require full compliance verification per `Connector_Spec.md §5`.
>
> **Covers:** Apache Superset, Grafana, Metabase
>
> **Abstract spec:** `../layout_330300_design_spec.md` · `../Connector_Spec.md` · `../Abstract_Visual_Types.md`

---

## 1. Architecture Overview

The OSS connector implements the same abstract contract as any other connector. The translation layer adapts slot positions, color tokens, and visual types to the native constructs of each tool.

```
Abstract Page Spec
  ├── Slot IDs + Grid (12×12 LU)
  ├── Color Semantic Roles
  ├── Abstract Visual Types
  └── Interaction Patterns
        │
        ▼
  OSS Connector Translation Layer
        │
        ├── Apache Superset → Dashboard JSON + Native Filters
        ├── Grafana → Dashboard JSON + Variables
        └── Metabase → Dashboard definition + Question
```

---

## 2. Slot → Panel Mapping

### 2.1 Common Mapping (all OSS tools)

| Slot ID | Visual Purpose | OSS Panel Type |
|---|---|---|
| `KPI_Cards` | Status + delta | `big_number_total` (Superset) / `stat` (Grafana) / `metric` (Metabase) |
| `Slicer_Date` | Temporal filter | Native filter / Time range variable |
| `Slicer_Cat_1/2` | Categorical filter | Native filter / Dashboard variable |
| `Main_1` (Trend) | Time series | Line chart panel |
| `Main_2` (Variance) | Deviation | Bar chart (horizontal, delta) or waterfall plugin |
| `Main_3` (Ranking) | Entity comparison | Bar chart (horizontal, sorted) |
| `Slicer_Pane` | Context switch (detail) | Left-side filter panel (tool-native) |
| `Smart_Narrative` | Summary text | Markdown / text panel |
| `Detail_Matrix` | Entity-grain table | Table with conditional formatting |
| `ActionPanel` | Recommendation block | Markdown panel (structured) |

---

## 3. Grid Translation

The 12×12 LU grid translates to OSS tool layout systems as follows.

### Design Canvas Reference

- Design base: 1280×720 (from `layout_330300_design_spec.md §3.1`)
- Grid parameters: 32px outer margin, 16px gutter, 12×12 LU

### Computed LU Sizes (1280×720)

```
content_width  = 1280 - 2×32 = 1216px
content_height = 720  - 2×32 = 656px
lu_width  = (1216 - 11×16) / 12 = (1216 - 176) / 12 = 86.7px
lu_height = (656  - 11×16) / 12 = (656  - 176) / 12 = 40.0px
```

### Superset Grid Translation

Superset uses a **12-column fluid grid** internally (inherited from Bootstrap). This maps directly to the 12-column LU system.

| LU Parameter | Superset |
|---|---|
| Column span | `width` property in layout JSON (1–12) |
| Row span | `height` (in row units, ≈120px per unit at default) |
| Column start | Position in row order |
| Gutters | Handled by Superset's layout engine |

**Standard slot positions (Superset columns, "Pulse" layout):**

| Slot | Superset width | Superset row height | Notes |
|---|---|---|---|
| `KPI_Cards` (5 cards) | 2–3 per card | 2 | Cards in a row, each 2–3 columns |
| `Slicer_Date` | 12 | 1 | Full-width filter bar |
| `Main_1` | 4 | 6 | 1/3 of content width |
| `Main_2` | 4 | 6 | 1/3 of content width |
| `Main_3` | 4 | 6 | 1/3 of content width |

### Grafana Grid Translation

Grafana uses a **24-column grid** with panels sized in (width, height) units where 1 unit ≈ 30px at 1920px.

| LU Parameter | Grafana |
|---|---|
| Column span (12 LU) | Multiply by 2 (24-col grid) |
| Row height | 1 Grafana unit ≈ 30px |
| LU to Grafana columns | `grafana_w = lu_col_span × 2` |
| LU to Grafana height | `grafana_h = lu_row_span × 1.3` (approximate) |

**Standard slot positions (Grafana, "Pulse" layout):**

| Slot | Grafana x | Grafana w | Grafana y | Grafana h |
|---|---|---|---|---|
| `KPI_Cards` (5 cards) | 0, 5, 10, 15, 19 | 5, 5, 5, 4, 5 | 0 | 3 |
| `Slicer_Date` | 0 | 24 | 3 | 1 |
| `Main_1` | 0 | 8 | 4 | 8 |
| `Main_2` | 8 | 8 | 4 | 8 |
| `Main_3` | 16 | 8 | 4 | 8 |

### Metabase Grid Translation

Metabase uses a **24-column × fixed-row** grid. Mapping is analogous to Grafana.

---

## 4. Color Semantic Role Mapping

### 4.1 Apache Superset

Superset uses CSS-based theming. Map abstract roles to theme variables:

```json
{
  "semantic.positive": "var(--color-success)",
  "semantic.negative": "var(--color-error)",
  "semantic.warning": "var(--color-warning)",
  "semantic.neutral":  "var(--color-secondary)",
  "brand.primary":     "var(--color-primary)",
  "brand.data_colors": ["var(--color-info)", ...]
}
```

For conditional formatting on tables (Detail Matrix):
- `semantic.negative` delta rows: background `#FFE6E6`, text `#1F1F1F`
- `semantic.warning` delta rows: background `#FFF9E6`, text `#1F1F1F`
- `semantic.positive` delta rows: background `#E6F5E6`, text `#1F1F1F`

### 4.2 Grafana

Grafana uses threshold-based color rules. Map abstract roles to threshold configs:

```yaml
# In panel field config (fieldConfig.defaults.thresholds):
thresholds:
  mode: absolute
  steps:
    - color: "red"        # semantic.negative
      value: null
    - color: "orange"     # semantic.warning
      value: <warning_threshold>
    - color: "green"      # semantic.positive
      value: <positive_threshold>
```

For stat panels (KPI cards): use `color.mode: "thresholds"`.
For bar charts: use `color.mode: "fixed"` with `brand.primary` for single series; `color.mode: "palette-classic"` for categorical series.

### 4.3 Metabase

Metabase uses column-level formatting for conditional colors:

```json
{
  "column_settings": {
    "delta_column": {
      "color_getter": "threshold",
      "positive_color": "#1F6B2B",
      "negative_color": "#B00020",
      "zero_color": "#757575"
    }
  }
}
```

---

## 5. Visual Type Implementation

### 5.1 KPI Card with Delta (kpi_card)

**Superset:** Use `big_number_total` chart type. Configure:
- Metric: primary KPI measure
- Subheader: formatted delta string (use calculated column or metric)
- Color threshold: on metric or on delta field

**Grafana:** Use `stat` panel. Configure:
- `reducers: ["lastNotNull"]`
- `fieldConfig.defaults.color.mode: "thresholds"`
- Thresholds aligned to semantic roles
- Text mode: `"value_and_name"`

**Metabase:** Use `metric` question with trend enabled:
- Comparison period: prior period or target value
- Trend arrows and color: auto-configured from comparison

### 5.2 Trend Line Chart (line_chart)

All tools: Line chart with:
- Primary series: current period (solid, 2px)
- Reference series (target/PY): dashed, 1px, lighter color
- Time dimension on x-axis
- Direct labels at line endpoints (where tool supports it)
- Annotate significant inflection points with text callout (Grafana: Annotations; Superset: Text annotation; Metabase: N/A — use Markdown panel below chart)

### 5.3 Horizontal Bar Chart — Ranking (bar_chart_horizontal)

All tools: Horizontal bar chart with:
- Entities on y-axis (categorical)
- Value on x-axis
- Sort: descending by value (most important first)
- Max 15 bars without pagination
- Color: `brand.primary` for all bars; `semantic.negative` or `semantic.positive` on delta bars

### 5.4 Variance / Waterfall (waterfall)

- **Superset:** No native waterfall. Use `echarts_timeseries_bar` with custom JavaScript transform, or install `superset-plugin-chart-waterfall`. Alternative: horizontal bar chart showing driver contributions as positive/negative bars (acceptable approximation for most use cases).
- **Grafana:** No native waterfall. Use bar chart with stacked + subtraction logic, or a community plugin. Documented approximation: grouped bar chart with base/delta encoding.
- **Metabase:** No native waterfall. Use table with conditional formatting as approximation.

> **Note:** If a native waterfall is not available in the target tool, use a **ranked contribution bar chart** as the approved fallback:
> - Each entity/driver as one horizontal bar
> - Positive contributions: green bars to the right of a zero axis
> - Negative contributions: red bars to the left
> - Total deviation shown as a reference line
> This retains the analytical value of the variance bridge without requiring a plugin.

### 5.5 Table with Data Bars (table_with_databars)

**Superset:** Use `table` chart type with conditional formatting:
- Delta columns: color scale based on `semantic.negative`/`semantic.positive`
- Progress bars: enable `show_cell_bars: true` on delta columns

**Grafana:** Use `table` panel with:
- Column override: `custom.displayMode: "color-background"` on delta column
- Threshold mapping for delta values

**Metabase:** Use `table` question:
- Column settings: enable conditional formatting on delta columns
- Progress bar: not natively supported — use color background as approximation

### 5.6 Smart Narrative / Action Panel (text_narrative, action_card)

All tools: Use **Markdown panel** / **Text panel**:

```markdown
## Summary

Net Sales of **€38.1M** is **-€4.2M (-10%)** vs Plan YTD,
primarily driven by DACH (-€3.1M) and adverse Mix effect.

---
*Filter context: Q3 2025 · Region: DACH · Channel: All*
```

For Action Panel (T4):

```markdown
## ● Recommended Action

**Cap promotional discounts in DACH to ≤15%**

**WHY:** GM% at 16.9%, -1.1pp below 18% threshold for 3 consecutive months.
Promotional depth at 22% vs 15% target is the primary driver.

**STEPS:**
1. Cap discount at 15% in all DACH accounts immediately
2. Renegotiate volume rebates with Top-3 DACH buyers
3. Alert Category Manager to shift product mix

| Owner | Comm Mgr DACH |
|---|---|
| Due | End October |
| Impact | +0.8pp GM% / +€1.2M |
| Priority | HIGH |
```

---

## 6. Interaction Patterns

### 6.1 Drillthrough (Overview → Detail)

| Tool | Implementation |
|---|---|
| Superset | Dashboard-to-dashboard navigation via `link_to_filtering_field` or URL redirect with filter parameters |
| Grafana | Panel data link: `url: /d/<detail_dashboard_id>?var-filter=${__value.raw}` |
| Metabase | Dashboard → Dashboard click behavior (requires Metabase Pro/Enterprise for parameterized dashboard linking) |

### 6.2 Slicer Cascade (All slicers filter all visuals)

| Tool | Implementation |
|---|---|
| Superset | Native filter: `cross_filters_enabled: true`; all charts subscribe to dashboard-level filters |
| Grafana | Template variables applied to all panel queries: `$time_range`, `$region`, `$segment` |
| Metabase | Dashboard filters linked to all questions on the dashboard |

### 6.3 Back Navigation

| Tool | Implementation |
|---|---|
| Superset | Markdown panel with hyperlink button to overview dashboard |
| Grafana | Dashboard row with link icon and URL to overview dashboard |
| Metabase | Markdown card with link to overview dashboard |

---

## 7. Compliance Gaps by Tool

Some abstract framework requirements have known gaps in OSS tools. Document them here for each connector implementation.

| Requirement | Superset | Grafana | Metabase |
|---|---|---|---|
| Native waterfall chart | Gap (plugin required) | Gap (plugin required) | Gap (approximation) |
| Sparkline in KPI card | Gap (separate panel) | Gap (sparkline stat panel available) | Partial (trend line available) |
| KPI card with reference + delta in one visual | Partial | Full (stat panel) | Partial |
| Drillthrough with full filter context | Partial (URL params) | Full (data links) | Limited (Pro only) |
| Cross-page filter isolation | Partial | Full (variables scoped per dash) | Full |
| Action Panel structured layout | Gap (Markdown approximation) | Gap (Text panel) | Gap (Text card) |

**Handling gaps:** Where a gap exists, use the documented approximation. Record the gap in the connector compliance report. Do not omit the slot — implement the best available approximation and note the limitation.

---

## 8. Connector Registration

To formalize an OSS connector implementation:

1. Create `connectors/<tool>_Connector.md` with full implementation details
2. Run compliance checklist from `Connector_Spec.md §5` against the implementation
3. Document all gaps in the compliance report
4. Register in `Connector_Spec.md §6` (Known Connectors table)
5. Pin to the abstract spec version it implements
