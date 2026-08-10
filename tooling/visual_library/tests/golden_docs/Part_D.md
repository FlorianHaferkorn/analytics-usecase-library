## Part D — the visual idiom catalog

> **Generated** from `core/templates/page_templates/visual_library/` — do not hand-edit; run `tooling/visual_library/render_docs.py`. The library is the single source of truth; the runnable code per tool lives in `<idiom>.yaml` and is byte-for-byte frozen in `golden/`.

**Encoding rule (governed).** Magnitude → length/position (rank 1–3), never the colour of a number (rank 9–10); direction → colour **and** sign; size is the only highlight (`cookbook.md`).

### D.0 Which visual, when — the chooser

| Purpose | Question | Best idiom | Zone | Candidates |
|---|---|---|---|---|
| **time_comparison** | How is X developing over time — and against plan? | `line` | analysis | `line` · `area_stacked` · `small_multiples` · `indexed_line` · `slope` |
| **deviation_from_target** | Are we above/below plan or target — by how much? | `deviation_bar` | pulse / analysis | `deviation_bar` · `bullet` · `deviation_bar@ibcs` |
| **compare_categories** | Which categories lead or lag — where should attention focus? | `bar_ranking` | analysis | `bar_ranking` · `lollipop` · `bar_absolute` |
| **contribution_to_change** | What moved the number from A to B — which drivers? | `waterfall_pvm` | analysis | `waterfall_pvm` · `waterfall_buildup` · `waterfall_variance` · `waterfall_pvm@ibcs` |
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

### D.1 Validation status — what is proven, and what stays gated

> Evidence per idiom × tool, each proven by an ACTUAL headless render: **Deneb** rasterized across 5 data scenarios (`typical`, `negatives`, `single_category`, `many_categories`, `extremes`) and **SVG-DAX** rasterized (its emitted SVG) via vl-convert; **Recharts** React-rendered via the Node harness `acceptance/render_recharts.mjs`. Only **Power BI native** stays `structural · gated` — PBIR is a visual config with no headless renderer, so its proof is a Desktop load (`acceptance/CHECKLIST.md`). Regenerate with `render_acceptance.py matrix`.

| Idiom | Power BI · native | Power BI · SVG-DAX | Deneb / Vega-Lite | Web · Recharts |
|---|---|---|---|---|
| `deviation_bar` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `line` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `bar_ranking` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `waterfall_pvm` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `area_stacked` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `indexed_line` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `matrix_evidence` | structural · gated | rendered ✓ | — | — |
| `scatter` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `donut` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `bullet` | — | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `slope` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `stacked_100` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `lollipop` | — | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `histogram` | — | — | rendered ✓ 5/5 | rendered ✓ |
| `boxplot` | — | — | rendered ✓ 5/5 | — |
| `small_multiples` | — | — | rendered ✓ 5/5 | — |
| `sankey` | — | — | — | rendered ✓ |
| `decomposition_tree` | structural · gated | — | — | — |
| `bar_absolute` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `waterfall_buildup` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `waterfall_variance` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |

**Legend.** `rendered ✓` = actually rendered headlessly (Deneb shows the scenario count) · `structural · gated` = deterministic + structurally valid, live render needs its host (Desktop) · `—` = tool n/a.

### Idioms

#### `deviation_bar` — Deviation bar
- **Purpose:** deviation_from_target, compare_categories · **zone:** pulse / analysis · **best form for:** `deviation_from_target`
- **Avoid:** color_of_number_for_magnitude, decorative_tint, gauge
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/deviation_bar.yaml` (+ `golden/deviation_bar.*`)

#### `line` — Trend line
- **Purpose:** time_comparison · **zone:** analysis · **best form for:** `time_comparison`
- **Avoid:** bars_for_time, autoscale_without_reference, dual_axis_no_reason, legend_when_direct_label_works
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/line.yaml` (+ `golden/line.*`)

#### `bar_ranking` — Bar ranking
- **Purpose:** compare_categories · **zone:** analysis · **best form for:** `compare_categories`
- **Avoid:** unsorted_bars, pie_for_comparison, broken_baseline_on_absolute_bar, color_to_separate_equal_categories
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/bar_ranking.yaml` (+ `golden/bar_ranking.*`)

#### `waterfall_pvm` — Waterfall bridge (PVM)
- **Purpose:** contribution_to_change · **zone:** analysis · **best form for:** `contribution_to_change`
- **Avoid:** bridge_without_connectors, color_beyond_semantic, too_many_steps, unlabelled_zoomed_axis
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a full multi-step bridge with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS waterfall UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
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
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
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

#### `lollipop` — Lollipop
- **Purpose:** compare_categories · **zone:** analysis
- **Avoid:** lollipop_for_many_dense_categories, hidden_zoomed_axis
- **Tools:** Power BI · native n/a (Power BI has no native lollipop base visual → SVG-DAX (a lollipop cell in a matrix) or Deneb) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/lollipop.yaml` (+ `golden/lollipop.*`)

#### `histogram` — Histogram
- **Purpose:** distribution · **zone:** analysis · **best form for:** `distribution`
- **Avoid:** bars_with_gaps_imply_categories, too_few_or_too_many_bins
- **Tools:** Power BI · native n/a (Power BI has no auto-bin mark → create a bin group on the field, then a columnChart of the count (or use Deneb)) · Power BI · SVG-DAX n/a (a full distribution is not a single-cell micro-chart → deneb_vegalite, or the DaxLib.SVG histogram helper) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/histogram.yaml` (+ `golden/histogram.*`)

#### `boxplot` — Box plot
- **Purpose:** distribution · **zone:** analysis
- **Avoid:** boxplot_without_labelled_quartiles_in_a_brief, too_many_groups
- **Tools:** Power BI · native n/a (Power BI has no native box-plot base visual → deneb_vegalite (boxplot mark), or a box-plot custom visual) · Power BI · SVG-DAX n/a (requires five quartile measures + an axis; not a simple substitution template → the DaxLib.SVG boxplot helper (daxlib.org) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts n/a (Recharts has no box-plot primitive → a custom SVG/D3 box-plot, or a charting lib with box-plot support (ECharts, Plotly))
- **Code:** `visual_library/boxplot.yaml` (+ `golden/boxplot.*`)

#### `small_multiples` — Small multiples
- **Purpose:** time_comparison · **zone:** analysis
- **Avoid:** independent_y_scales_per_panel, too_many_panels
- **Tools:** Power BI · native n/a (small multiples is a field-well option, not a distinct visual JSON idiom → a lineChart with the field placed in the Small multiples well (shared Y scale)) · Power BI · SVG-DAX n/a (a grid of panels is not a single-cell micro-chart → deneb_vegalite (facet) or the native Small multiples well) · Deneb / Vega-Lite ✓ · Web · Recharts n/a (no single small-multiples component → map the series to a CSS grid of <LineChart> with a shared YAxis domain)
- **Code:** `visual_library/small_multiples.yaml` (+ `golden/small_multiples.*`)

#### `sankey` — Sankey
- **Purpose:** flow_between_stages · **zone:** detail · **best form for:** `flow_between_stages`
- **Avoid:** sankey_for_precise_comparison, spaghetti_too_many_crossings
- **Tools:** Power BI · native n/a (Power BI has no native Sankey base visual → the Microsoft/PowerViz Sankey custom visual (AppSource)) · Power BI · SVG-DAX n/a (curved multi-node flows are impractical as a cell SVG measure → the Sankey custom visual, or Deneb (full Vega)) · Deneb / Vega-Lite n/a (Vega-Lite has no sankey mark → a full Vega spec in Deneb (sankey via linkpath transform), or the native custom visual) · Web · Recharts ✓
- **Code:** `visual_library/sankey.yaml` (+ `golden/sankey.*`)

#### `decomposition_tree` — Decomposition tree
- **Purpose:** driver_breakdown · **zone:** detail · **best form for:** `driver_breakdown`
- **Avoid:** used_as_a_static_exhibit, too_many_explain_by_dims
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (an interactive AI drill tree is not a cell micro-chart → powerbi_native (decompositionTreeVisual)) · Deneb / Vega-Lite n/a (an interactive drill tree is not a declarative Vega idiom → powerbi_native (decompositionTreeVisual)) · Web · Recharts n/a (Recharts has no decomposition-tree component → a custom D3 tree with sorted bars per level)
- **Code:** `visual_library/decomposition_tree.yaml` (+ `golden/decomposition_tree.*`)

#### `bar_absolute` — Bar (absolute magnitude)
- **Purpose:** compare_categories · **zone:** analysis
- **Avoid:** broken_baseline_on_absolute_bar, color_to_separate_equal_categories, pie_for_comparison, unsorted_bars
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/bar_absolute.yaml` (+ `golden/bar_absolute.*`)

#### `waterfall_buildup` — Waterfall (buildup to total)
- **Purpose:** contribution_to_change · **zone:** analysis
- **Avoid:** bridge_without_connectors, mixing_increase_and_decrease, too_many_steps, color_beyond_single_series
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a multi-step buildup with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS build-up UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/waterfall_buildup.yaml` (+ `golden/waterfall_buildup.*`)

#### `waterfall_variance` — Waterfall (variance bridge)
- **Purpose:** contribution_to_change · **zone:** analysis
- **Avoid:** bridge_without_connectors, color_beyond_semantic, too_many_steps, hiding_the_two_anchor_totals
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a two-anchor variance bridge with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS variance-bridge UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/waterfall_variance.yaml` (+ `golden/waterfall_variance.*`)
