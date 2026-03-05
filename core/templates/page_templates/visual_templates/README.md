# Visual Templates (Baukasten)

Reusable visual building blocks. Each template defines a **visual_template_id**, **visual_type** (Power BI visual type), optional **action_logic** (e.g. `standard_variance` for conditional formatting), and **slot_compatibility** (which page slots can use this visual).

Page templates define slots; configuration (e.g. UseCase_Bracket) assigns a visual template and measure/KPI to each slot. The renderer builds the visual from the template and grid position.

**Tool-agnostic vs. Fabric:** UseCase_Bracket uses abstract `visual_type` values (e.g. `trend_line`, `bar_chart`, `kpi_card`). This folder holds the **Fabric/Power BI realisation** (PBI visualType: lineChart, cardVisual, etc.). The mapping from abstract to PBI is in `products/fabric/powerbi/tooling/page_scaffold_generator` (config_loader, visual_builder).

## Templates

| File | visual_template_id | visual_type | Use |
|------|--------------------|-------------|-----|
| kpi_card_with_delta.json | KPI_Card_WithDelta | cardVisual | KPI card with delta and status indicator. |
| slicer_top_bar.json | Slicer_TopBar | slicer | Top filter bar (horizontal). |
| slicer_left_pane.json | Slicer_LeftPane | slicer | Left vertical slicer pane. |
| smart_narrative.json | Smart_Narrative | textbox | Smart Narrative / summary sentence. |
| matrix_with_data_bars.json | Matrix_WithDataBars | tableEx | Matrix/table with data bars for delta columns. |
| trend_line.json | Trend_Line | lineChart | Trend / time series chart. |

## action_logic

- `standard_variance`: Engine applies conditional formatting (good/neutral/bad, data bars) to delta measures; colors from theme (e.g. Brand Blue Dark).
