# Abstract Visual Type Vocabulary

> **Authority:** This document defines the tool-agnostic vocabulary for all visual types used in the 3-30-300 framework. Connectors translate these abstract types to tool-native components.
>
> **Used by:** `Connector_Spec.md` · `governance/Visual_Whitelist.md` · `tokens/visual_slot_mapping.yaml`

---

## 1. Purpose

Visual types in this framework use abstract identifiers that are independent of any BI tool. This allows:

- The abstract spec to describe layouts without coupling to Power BI, Superset, or any specific tool
- Connectors to map one abstract type to possibly different tool-native components
- New connectors to be added without changing the abstract spec

---

## 2. Abstract Type Registry

### KPI & Status

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `kpi_card` | Single KPI with value, delta, reference, optional sparkline | `KPI_Cards` | T1, T2, T3, T4 |
| `kpi_card_hero` | Large-format KPI card for single dominant metric | `KPI_Cards` | T1 |
| `kpi_card_compact` | Small-format KPI card for 6-card rows | `KPI_Cards` | T3 |
| `status_tile` | Traffic-light tile: entity × status | `KPI_Cards`, `Exceptions` | T3 |

---

### Time Series

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `line_chart` | Continuous time series, 1–4 series | `Main_1` (Trend) | T1, T2, T3 |
| `area_chart` | Time series with filled area, single series | `Main_1` (Trend) | T1 (sparingly) |
| `sparkline` | Compact inline trend, no axes | `KPI_Cards` (within card) | All |

---

### Comparison & Ranking

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `bar_chart_horizontal` | Ranked entities sorted by value | `Main_3` (Ranking) | T1, T2, T3 |
| `bar_chart_column` | Time-based or categorical comparison | `Main_3` (Ranking) | T3 only |
| `stacked_bar_100pct` | Part-to-whole composition across categories | `Main_3` (Mix), `Main_2` | T1, T2 |

---

### Variance & Diagnostics

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `waterfall` | Variance bridge — baseline → drivers → actual | `Main_2` (Variance) | T2 |
| `scatter_plot` | Two-variable correlation; impact-effort matrix | `Main_2`, `Root Cause` | T3, T4 |
| `decomposition_tree` | Hierarchical driver breakdown | `Focus_Area`, `Root Cause` | T3 |
| `funnel_chart` | Sequential conversion / drop-off analysis | `Funnel` slot | T2 only |

---

### Prescriptive & Action

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `recommendation_table` | Ranked list of actions with impact and priority | `Prescriptive` | T4 |
| `action_card` | Structured action block: title, owner, steps, impact | `ActionPanel` | T4 |
| `action_teaser` | Compact single-line action signal (no full panel) | Summary callout area | T1, T2, T3 (optional) |

---

### Detail & Validation

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `table_with_databars` | Entity-grain table with inline delta bars | `Detail_Matrix` | All (300s only) |
| `matrix` | Cross-tabular entity × metric table | `Detail_Matrix` | All (300s only) |

Rules:
- Detail visual types are allowed **only on 300-second (Detail) pages**
- They must not be the primary insight driver

---

### Narrative & Text

| Abstract Type | Semantic Purpose | Allowed Slots | Allowed Templates |
|---|---|---|---|
| `text_narrative` | Summary sentence(s) of current filter context | `Smart_Narrative` | All (Detail pages) |
| `text_callout` | Single highlighted insight or annotation | Annotation overlay | All |

---

### Interaction Controls

| Abstract Type | Semantic Purpose | Allowed Slots | Notes |
|---|---|---|---|
| `slicer_dropdown` | Single-select or multi-select dropdown | `Slicer_Date`, `Slicer_Cat_1/2` | Max 3 per page |
| `slicer_range` | Date range picker | `Slicer_Date` | Preferred for date |
| `slicer_list` | Scrollable list (sidebar slicers) | `Slicer_Pane` | Detail pages |
| `slicer_toggle` | Binary switch (mode switch) | Optional 4th slicer | Scenario, currency |

---

## 3. Disallowed Abstract Types

The following abstract types are explicitly **not part of this framework** and must not be introduced by connectors:

| Abstract Type | Reason |
|---|---|
| `pie_chart` / `donut_chart` | Part-to-whole comparison without spatial position is perceptually inaccurate; use `stacked_bar_100pct` |
| `gauge` / `speedometer` | Wastes 80% of visual space on chrome; use `kpi_card` with delta |
| `radar_chart` / `spider_chart` | No clear decision axis; perception of area is unreliable |
| `treemap` | Area encoding is less accurate than position; exceptions require governance approval |
| `3d_chart` | Introduces perspective distortion; adds no data value |
| `animated_chart` | Distracting in analytical contexts; use only for live operational monitoring |
| `map_choropleth` | Use only with governance approval when geography is the primary analytical dimension |

---

## 4. Connector Mapping Table

Connectors map abstract types to tool-native components. This table shows the reference mapping for known connectors.

| Abstract Type | Power BI / Fabric | Apache Superset | Grafana | Metabase |
|---|---|---|---|---|
| `kpi_card` | `cardVisual` (new card) | `big_number_total` | `stat` | `metric` |
| `kpi_card_hero` | `cardVisual` (large) | `big_number_total` | `stat` (large) | `metric` |
| `line_chart` | `lineChart` | `echarts_timeseries_line` | `timeseries` | `line` |
| `area_chart` | `areaChart` | `echarts_area` | `timeseries` (fill) | `area` |
| `sparkline` | cardVisual sparkline | Inline text widget | — | — |
| `bar_chart_horizontal` | `barChart` (horizontal) | `bar_chart` (horizontal) | `barchart` (h) | `row` |
| `bar_chart_column` | `columnChart` | `bar_chart` | `barchart` | `bar` |
| `stacked_bar_100pct` | `stackedBarChart` (100%) | `echarts_bar` (stack pct) | `barchart` (stacked) | `bar` (stacked) |
| `waterfall` | `waterfallVisual` | `echarts_waterfall` (plugin) | — (plugin) | — |
| `scatter_plot` | `scatterChart` | `scatter` | `scatterplot` | `scatter` |
| `decomposition_tree` | `decompositionTree` | `Treemap` (limited) | — | — |
| `funnel_chart` | `funnelChart` | `funnel` | `bargauge` (approx) | `funnel` (plugin) |
| `recommendation_table` | `tableEx` (formatted) | `table` | `table` | `table` |
| `action_card` | Text visual (structured) | `markdown` panel | `text` panel | `text` |
| `table_with_databars` | `tableEx` (data bars) | `table` (color fmt) | `table` | `table` |
| `matrix` | `pivotTable` | `pivot_table` | `table` | `pivot_table` |
| `text_narrative` | Smart Narrative / `textbox` | `markdown` panel | `text` panel | `text` |
| `slicer_dropdown` | `slicer` (dropdown) | Filter | Variable | Filter |
| `slicer_range` | `slicer` (between) | Time range filter | Time picker | Date filter |
| `slicer_list` | `slicer` (list) | Filter | Variable | Filter |
| `slicer_toggle` | `slicer` (tile/button) | Filter (button) | Variable (enum) | Filter |

> **Note:** `—` means no native equivalent; a plugin or custom implementation is required. If no native or plugin equivalent exists, the slot must be implemented with the closest available alternative and documented in the connector spec.

---

## 5. Visual Selection Decision Guide

When choosing an abstract visual type for a slot, apply in this order:

1. **What analytical relationship does this slot answer?**
   - Time development → `line_chart`
   - Deviation from reference → `waterfall` (structured) or `bar_chart_horizontal` (entity ranking)
   - Part-to-whole → `stacked_bar_100pct`
   - Two-variable correlation → `scatter_plot`
   - Entity detail → `table_with_databars`

2. **Is a simpler type sufficient?**
   - Never use `scatter_plot` when `bar_chart_horizontal` answers the question
   - Never use `decomposition_tree` when a `waterfall` explains the drivers
   - The simplest type that answers the question is the correct type (Few's principle)

3. **Does the audience match the visual complexity?**
   - T1 (executive): `kpi_card`, `line_chart`, `bar_chart_horizontal` only
   - T4 (decision owner): `scatter_plot` for impact-effort is acceptable
   - T3 (operational): focus on `status_tile` and `bar_chart_horizontal` for fast scanning
