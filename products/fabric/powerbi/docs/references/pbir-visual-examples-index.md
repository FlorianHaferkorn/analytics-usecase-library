# Visual Examples Index

> Source: data-goblin/power-bi-agentic-development — pbir-format skill, `examples/visuals/`
>
> Standalone `visual.json` examples for common Power BI visual types.
> Each file is a complete, valid visual container that can be used as a template
> for `visual_builder.py` and PBIP report generation.

## Default Visuals (minimal, theme-driven)

| Visual Type ID | File | Notes |
|----------------|------|-------|
| `advancedSlicerVisual` | advancedSlicer.json | Button slicer |
| `areaChart` | areaChart.json | |
| `barChart` | barChart.json | Also covers clusteredBarChart |
| `card` | card.json | Legacy card |
| `cardVisual` | cardVisual.json | New card (preferred) |
| `columnChart` | columnChart.json | Clustered column |
| `lineStackedColumnComboChart` | comboChart.json | Combo chart — Y=columns, Y2=lines |
| `donutChart` | donutChart.json | |
| `gauge` | gauge.json | |
| `image` | image.json | Static image |
| `kpi` | kpi.json | Built-in KPI visual |
| `lineChart` | lineChart.json | |
| `pivotTable` | pivotTable.json | Matrix |
| `scatterChart` | scatterChart.json | |
| `slicer` | slicer-dropdown.json | Dropdown mode |
| `slicer` | slicer-list.json | List mode |
| `stackedAreaChart` | stackedAreaChart.json | |
| `tableEx` | tableEx.json | Flat table |
| `textbox` | textbox.json | |
| `waterfallChart` | waterfallChart.json | |

## Formatted Visuals (conditional formatting, filters, advanced patterns)

| Visual Type ID | File | Formatting Feature |
|----------------|------|--------------------|
| `actionButton` | actionButton.json | Theme color nav button |
| `advancedSlicerVisual` | advancedSlicer-buttons.json | Custom selection colors |
| `areaChart` | areaChart-multiple.json | Multi-series + line styles |
| `barChart` | barChart-bullet.json | Bullet chart pattern |
| `barChart` | barChart-divergent.json | Positive/negative divergent |
| `barChart` | barChart-lollipop.json | Lollipop pattern |
| `barChart` | barChart-progress.json | Progress bar pattern |
| `card` | card-with-filter.json | Gradient fill + visual filter |
| `cardVisual` | cardVisual.json | SVG image + visual filter |
| `clusteredBarChart` | clusteredBarChart-variance.json | Variance analysis |
| `columnChart` | columnChart.json | Custom data point colors |
| `lineStackedColumnComboChart` | comboChart.json | Styled combo |
| `lineStackedColumnComboChart` | comboChart-flash.json | Flash report: actuals vs targets |
| `donutChart` | donutChart.json | Gradient fill rule |
| `gauge` | gauge.json | Gradient fill + themed target |
| `image` | image-svg-measure.json | SVG-producing DAX measure |
| `kpi` | kpi-flash.json | Flash report KPI |
| `lineChart` | lineChart.json | Line styles + markers |
| `lineChart` | lineChart-thresholds.json | Reference lines (y-axis) |
| `lineChart` | lineChart-visual-calcs.json | Visual calculations |
| `pivotTable` | pivotTable-bullet-kpi.json | SVG bullet KPI in matrix |
| `pivotTable` | pivotTable-flash.json | Gradient CF + column widths |
| `scatterChart` | scatterChart.json | Conditional formatting |
| `scatterChart` | scatterChart-flash.json | Gradient fill |
| `shape` | shape.json | Decorative shape |
| `slicer` | slicer-flash.json | Dropdown + theme colors |
| `stackedAreaChart` | stackedAreaChart.json | Multi-series line styles |
| `tableEx` | tableEx-gradient.json | Gradient CF + column widths |
| `waterfallChart` | waterfallChart.json | Custom sentiment colors |
| `waterfallChart` | waterfallChart-flash.json | Flash report waterfall |

## Usage in `visual_builder.py`

When generating a visual container, reference these examples to understand:

1. The `visual.type` string (e.g. `"lineChart"`, `"pivotTable"`, `"cardVisual"`)
2. The minimum required `queryState` fields for each visual role
3. Correct `objects` structure for formatting overrides
4. How `filterConfig` is embedded at the visual level

Original files are in the data-goblin repository:
`https://github.com/data-goblin/power-bi-agentic-development/tree/main/plugins/pbip/skills/pbir-format/examples/visuals/`

## Role Mapping Reference

| Visual | Role name for Axis/Category | Role for Values | Role for Legend |
|--------|----------------------------|-----------------|-----------------|
| `barChart` / `columnChart` | `Category` | `Y` | `Series` |
| `lineChart` | `Category` | `Y` | `Series` |
| `lineStackedColumnComboChart` | `Category` | `Y` (cols) + `Y2` (lines) | `Series` |
| `scatterChart` | `X` + `Y` | `Size` | `Category` |
| `pivotTable` | `Rows` + `Columns` | `Values` | — |
| `tableEx` | `Values` (columns) | — | — |
| `kpi` | `TrendAxis` | `Indicator` | `Goal` |
| `cardVisual` | — | `Values` (measures) | — |
| `gauge` | — | `Y` | `Min` + `Max` + `TargetValue` |
| `waterfallChart` | `Category` | `Y` | `Breakdown` |
