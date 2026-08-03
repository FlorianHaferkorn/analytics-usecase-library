## Part D — the visual idiom catalog

> **Generated** from `core/templates/page_templates/visual_library/` — do not hand-edit; run `tooling/visual_library/render_docs.py`. The library is the single source of truth; the runnable code per tool lives in `<idiom>.yaml` and is byte-for-byte frozen in `golden/`.

**Encoding rule (governed).** Magnitude → length/position (rank 1–3), never the colour of a number (rank 9–10); direction → colour **and** sign; size is the only highlight (`cookbook.md`).

### D.0 Which visual, when — the chooser

| Purpose | Question | Best idiom | Zone | Candidates |
|---|---|---|---|---|
| **time_comparison** | How is X developing over time — and against plan? | `line` | analysis | `line` · `area_stacked` · `small_multiples` · `indexed_line` · `slope` |
| **deviation_from_target** | Are we above/below plan or target — by how much? | `deviation_bar` | pulse / analysis | `deviation_bar` · `bullet` · `ibcs_overlapped` |
| **compare_categories** | Which categories lead or lag — where should attention focus? | `bar_ranking` | analysis | `bar_ranking` · `lollipop` · `bar_absolute` |
| **contribution_to_change** | What moved the number from A to B — which drivers? | `waterfall_pvm` | analysis | `waterfall_pvm` · `waterfall_buildup` · `waterfall_variance` · `waterfall_ibcs` |
| **part_to_whole** | What is the share of the whole (<= 4 parts)? | `donut` | analysis | `donut` · `stacked_100` |
| **correlation** | How do two continuous variables relate? | `scatter` | analysis | `scatter` |
| **flow_between_stages** | How does quantity flow between stages — where does it leak? | `sankey` | detail | `sankey` |
| **driver_breakdown** | Which dimension drives the number? (interactive) | `decomposition_tree` | detail | `decomposition_tree` |
| **distribution** | What is the spread / median / outliers of a variable? | `histogram` | analysis | `histogram` · `boxplot` |
| **evidence_detail** | Which rows are worst — and what is the next action? | `matrix_evidence` | detail | `matrix_evidence` |
| **value_verdict** | What is the headline value and its verdict? | `kpi_card` | pulse | `kpi_card` |

**Deny (never emit):** `pie_gt_4` · `three_d` · `gauge` · `radar` · `dual_axis_no_reason` · `color_as_decoration` · `powerbi_smart_narrative`.

**Situational / out:** `sankey` and `decomposition_tree` are situational [`Visual_Whitelist.md`](../../../../../core/templates/page_templates/governance/Visual_Whitelist.md) extensions (flow-structure only / Detail drill, one measure); `powerbi_smart_narrative` is out for Power BI (templated / unreliable) and kept other-tools only.

**Placement (unified with §A.8 layout).** 3s Pulse → `kpi_card` (deviation / bullet / hero); 30s Analysis → `line` → `waterfall_pvm` → `bar_ranking` → `area_stacked` / `scatter`; 300s Detail → `matrix_evidence` · `decomposition_tree` · `sankey`. Rule: question → idiom → zone → composition.

### Idioms

#### `deviation_bar` — Deviation bar
- **Purpose:** deviation_from_target, compare_categories · **zone:** pulse / analysis · **best form for:** `deviation_from_target`
- **Avoid:** color_of_number_for_magnitude, decorative_tint, gauge
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/deviation_bar.yaml` (+ `golden/deviation_bar.*`)

#### `line` — Trend line
- **Purpose:** time_comparison · **zone:** analysis · **best form for:** `time_comparison`
- **Avoid:** bars_for_time, autoscale_without_reference, dual_axis_no_reason, legend_when_direct_label_works
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/line.yaml` (+ `golden/line.*`)

#### `bar_ranking` — Bar ranking
- **Purpose:** compare_categories · **zone:** analysis · **best form for:** `compare_categories`
- **Avoid:** unsorted_bars, pie_for_comparison, broken_baseline_on_absolute_bar, color_to_separate_equal_categories
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/bar_ranking.yaml` (+ `golden/bar_ranking.*`)

#### `waterfall_pvm` — Waterfall bridge (PVM)
- **Purpose:** contribution_to_change · **zone:** analysis · **best form for:** `contribution_to_change`
- **Avoid:** bridge_without_connectors, color_beyond_semantic, too_many_steps, unlabelled_zoomed_axis
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a full multi-step bridge with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS waterfall UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/waterfall_pvm.yaml` (+ `golden/waterfall_pvm.*`)

#### `area_stacked` — Stacked area
- **Purpose:** time_comparison · **zone:** analysis
- **Avoid:** stacked_bars_for_composition_over_time, too_many_series, inconsistent_series_colours
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (multi-series stacked area is not a single-cell micro-chart (a single-series area sparkline is — see `line`) → powerbi_native (stackedAreaChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/area_stacked.yaml` (+ `golden/area_stacked.*`)

#### `indexed_line` — Indexed line
- **Purpose:** time_comparison · **zone:** analysis
- **Avoid:** mixing_indexed_and_absolute_axes, hidden_base_period, autoscale_without_base_line
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/indexed_line.yaml` (+ `golden/indexed_line.*`)

#### `matrix_evidence` — Evidence matrix
- **Purpose:** evidence_detail · **zone:** detail · **best form for:** `evidence_detail`
- **Avoid:** unsorted_rows, long_bar_list_instead_of_table, too_many_columns
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (Vega-Lite is not a table tool → powerbi_native (tableEx) with an SVG-DAX data-bar column) · Web · Recharts n/a (Recharts has no table primitive → an HTML <table> with CSS data-bar cells (div width = normalised deviation))
- **Code:** `visual_library/matrix_evidence.yaml` (+ `golden/matrix_evidence.*`)

#### `scatter` — Scatter plot
- **Purpose:** correlation · **zone:** analysis · **best form for:** `correlation`
- **Avoid:** line_for_correlation, overplotting_without_opacity, dual_axis_no_reason
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a two-axis scatter is a full chart, not a single-cell micro-chart → powerbi_native (scatterChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/scatter.yaml` (+ `golden/scatter.*`)

#### `donut` — Donut
- **Purpose:** part_to_whole · **zone:** analysis · **best form for:** `part_to_whole`
- **Avoid:** pie_or_donut_gt_4, many_thin_slivers, 3d_or_exploded
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (arc-path geometry in DAX is impractical → the DaxLib.SVG donut UDF (daxlib.org), or powerbi_native (donutChart) / Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/donut.yaml` (+ `golden/donut.*`)

#### `bullet` — Bullet graph
- **Purpose:** deviation_from_target · **zone:** pulse / analysis
- **Avoid:** gauge_instead, colour_bands_instead_of_greys
- **Tools:** Power BI · native n/a (Power BI has no native bullet base visual → deneb_vegalite, or the xViz/Inforiver IBCS bullet custom visual) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/bullet.yaml` (+ `golden/bullet.*`)

#### `slope` — Slope chart
- **Purpose:** time_comparison · **zone:** analysis
- **Avoid:** many_periods_use_line, crossing_spaghetti_too_many_series
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/slope.yaml` (+ `golden/slope.*`)

#### `stacked_100` — 100% stacked bar
- **Purpose:** part_to_whole · **zone:** analysis
- **Avoid:** too_many_series, stacked_absolute_when_share_is_the_point, inconsistent_series_colours
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (multi-series normalised stacking is not a single-cell micro-chart → powerbi_native (hundredPercentStackedColumnChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/stacked_100.yaml` (+ `golden/stacked_100.*`)
