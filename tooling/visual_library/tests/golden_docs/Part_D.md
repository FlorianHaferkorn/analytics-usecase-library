## Part D — the visual idiom catalog

> **Generated** from `core/templates/page_templates/visual_library/` — do not hand-edit; run `tooling/visual_library/render_docs.py`. The library is the single source of truth; the runnable code per tool lives in `<idiom>.yaml` and is byte-for-byte frozen in `golden/`.

**Encoding rule (governed).** Magnitude → length/position (rank 1–3), never the colour of a number (rank 9–10); direction → colour **and** sign; size is the only highlight (`cookbook.md`).

### D.0 Which visual, when — the chooser

| Purpose | Question | Best idiom | Zone | Candidates |
|---|---|---|---|---|
| **time_comparison** | How is X developing over time — and against plan? | `line` | analysis | `line` · `column_time` · `area_stacked` · `small_multiples` · `indexed_line` · `slope` |
| **deviation_from_target** | Are we above/below plan or target — by how much? | `deviation_bar` | pulse / analysis | `deviation_bar` · `bullet` · `deviation_bar@ibcs` |
| **compare_categories** | Which categories lead or lag — where should attention focus? | `bar_ranking` | analysis | `bar_ranking` · `lollipop` · `bar_absolute` · `dumbbell` |
| **contribution_to_change** | What moved the number from A to B — which drivers? | `waterfall_pvm` | analysis | `waterfall_pvm` · `waterfall_buildup` · `waterfall_variance` · `waterfall_pvm@ibcs` |
| **part_to_whole** | What is the share of the whole (<= 4 parts)? | `donut` | analysis | `donut` · `stacked_100` · `bar_stacked` |
| **correlation** | How do two continuous variables relate? | `scatter` | analysis | `scatter` |
| **flow_between_stages** | How does quantity flow between stages — where does it leak? | `sankey` | detail | `sankey` |
| **driver_breakdown** | Which dimension drives the number? (interactive) | `decomposition_tree` | detail | `decomposition_tree` |
| **distribution** | What is the spread / median / outliers of a variable? | `histogram` | analysis | `histogram` · `boxplot` |
| **evidence_detail** | Which rows are worst — and what is the next action? | `matrix_evidence` | detail | `matrix_evidence` · `matrix_sparkline` · `matrix_bullet` · `matrix_delta_pill` · `column_time` · `dumbbell` · `bar_stacked` |
| **value_verdict** | What is the headline value and its verdict? | `kpi_card_spark` | pulse | `kpi_card_spark` · `kpi_card_bullet` · `kpi_card_sparkbar` |

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
| `small_multiples` | structural · gated | — | rendered ✓ 5/5 | — |
| `sankey` | — | — | — | rendered ✓ |
| `decomposition_tree` | structural · gated | — | — | — |
| `bar_absolute` | structural · gated | rendered ✓ | rendered ✓ 5/5 | rendered ✓ |
| `waterfall_buildup` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `waterfall_variance` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `kpi_card_spark` | structural · gated | rendered ✓ | — | — |
| `kpi_card_bullet` | — | rendered ✓ | — | — |
| `kpi_card_sparkbar` | — | rendered ✓ | — | — |
| `matrix_sparkline` | structural · gated | rendered ✓ | — | — |
| `matrix_bullet` | — | rendered ✓ | — | — |
| `matrix_delta_pill` | — | rendered ✓ | — | — |
| `column_time` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |
| `dumbbell` | — | rendered ✓ | rendered ✓ 5/5 | — |
| `bar_stacked` | structural · gated | — | rendered ✓ 5/5 | rendered ✓ |

**Legend.** `rendered ✓` = actually rendered headlessly (Deneb shows the scenario count) · `structural · gated` = deterministic + structurally valid, live render needs its host (Desktop) · `—` = tool n/a.

### Idioms

#### `deviation_bar` — Deviation bar
- **Purpose:** deviation_from_target, compare_categories · **zone:** pulse / analysis · **best form for:** `deviation_from_target` · **min size:** 3×2 grid (292×96px @1280, 438×144px @1920)
- **Avoid:** color_of_number_for_magnitude, decorative_tint, gauge
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/deviation_bar.yaml` (+ `golden/deviation_bar.*`)

#### `line` — Trend line
- **Purpose:** time_comparison · **zone:** analysis · **best form for:** `time_comparison` · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** bars_for_time, autoscale_without_reference, dual_axis_no_reason, legend_when_direct_label_works
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/line.yaml` (+ `golden/line.*`)

#### `bar_ranking` — Bar ranking
- **Purpose:** compare_categories · **zone:** analysis · **best form for:** `compare_categories` · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** unsorted_bars, pie_for_comparison, broken_baseline_on_absolute_bar, color_to_separate_equal_categories
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/bar_ranking.yaml` (+ `golden/bar_ranking.*`)

#### `waterfall_pvm` — Waterfall bridge (PVM)
- **Purpose:** contribution_to_change · **zone:** analysis · **best form for:** `contribution_to_change` · **min size:** 4×5 grid (395×264px @1280, 592×396px @1920)
- **Avoid:** bridge_without_connectors, color_beyond_semantic, too_many_steps, unlabelled_zoomed_axis
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a full multi-step bridge with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS waterfall UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/waterfall_pvm.yaml` (+ `golden/waterfall_pvm.*`)

#### `area_stacked` — Stacked area
- **Purpose:** time_comparison · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** stacked_bars_for_composition_over_time, too_many_series, inconsistent_series_colours
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (multi-series stacked area is not a single-cell micro-chart (a single-series area sparkline is — see `line`) → powerbi_native (stackedAreaChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/area_stacked.yaml` (+ `golden/area_stacked.*`)

#### `indexed_line` — Indexed line
- **Purpose:** time_comparison · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** mixing_indexed_and_absolute_axes, hidden_base_period, autoscale_without_base_line
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/indexed_line.yaml` (+ `golden/indexed_line.*`)

#### `matrix_evidence` — Evidence matrix
- **Purpose:** evidence_detail · **zone:** detail · **best form for:** `evidence_detail` · **min size:** 5×6 grid (497×320px @1280, 746×480px @1920)
- **Avoid:** unsorted_rows, long_bar_list_instead_of_table, too_many_columns
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (Vega-Lite is not a table tool → powerbi_native (tableEx) with an SVG-DAX data-bar column) · Web · Recharts n/a (Recharts has no table primitive → an HTML <table> with CSS data-bar cells (div width = normalised deviation))
- **Code:** `visual_library/matrix_evidence.yaml` (+ `golden/matrix_evidence.*`)

#### `scatter` — Scatter plot
- **Purpose:** correlation · **zone:** analysis · **best form for:** `correlation` · **min size:** 3×5 grid (292×264px @1280, 438×396px @1920)
- **Avoid:** line_for_correlation, overplotting_without_opacity, dual_axis_no_reason
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a two-axis scatter is a full chart, not a single-cell micro-chart → powerbi_native (scatterChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/scatter.yaml` (+ `golden/scatter.*`)

#### `donut` — Donut
- **Purpose:** part_to_whole · **zone:** analysis · **best form for:** `part_to_whole` · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** pie_or_donut_gt_4, many_thin_slivers, 3d_or_exploded
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (arc-path geometry in DAX is impractical → the DaxLib.SVG donut UDF (daxlib.org), or powerbi_native (donutChart) / Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/donut.yaml` (+ `golden/donut.*`)

#### `bullet` — Bullet graph
- **Purpose:** deviation_from_target · **zone:** pulse / analysis · **min size:** 3×2 grid (292×96px @1280, 438×144px @1920)
- **Avoid:** gauge_instead, colour_bands_instead_of_greys
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die lineare Form. Geprueft wurde ausdruecklich `gauge` (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026): es fuehrt dieselben Datenrollen (Y, MinValue, MaxValue, TargetValue) und ein `target`-Objekt, zeichnet sie aber radial. Die lineare Spur mit qualitativen Baendern IST das Idiom; ein Halbkreis mit denselben Zahlen ist eine andere Aussage → deneb_vegalite, or the xViz/Inforiver IBCS bullet custom visual) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` · `print_safe` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/bullet.yaml` (+ `golden/bullet.*`)

#### `slope` — Slope chart
- **Purpose:** time_comparison · **zone:** analysis · **min size:** 3×5 grid (292×264px @1280, 438×396px @1920)
- **Avoid:** many_periods_use_line, crossing_spaghetti_too_many_series
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/slope.yaml` (+ `golden/slope.*`)

#### `stacked_100` — 100% stacked bar
- **Purpose:** part_to_whole · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** too_many_series, stacked_absolute_when_share_is_the_point, inconsistent_series_colours
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (multi-series normalised stacking is not a single-cell micro-chart → powerbi_native (hundredPercentStackedColumnChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/stacked_100.yaml` (+ `golden/stacked_100.*`)

#### `lollipop` — Lollipop
- **Purpose:** compare_categories · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** lollipop_for_many_dense_categories, hidden_zoomed_axis
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die Form (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026). Stiel plus Kopf ist Balken plus Punktmarke auf derselben Achse; kein Kernvisual kombiniert beides in einer Serie → SVG-DAX (a lollipop cell in a matrix) or Deneb) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/lollipop.yaml` (+ `golden/lollipop.*`)

#### `histogram` — Histogram
- **Purpose:** distribution · **zone:** analysis · **best form for:** `distribution` · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** bars_with_gaps_imply_categories, too_few_or_too_many_bins
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die Form, und keine Klassenbildung im Visual (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026: `columnChart` hat kein Objekt mit 'bin' im Namen). Klassen entstehen in Power BI modellseitig als Gruppierung, nicht als Visual-Eigenschaft — das Idiom beschreibt aber die Darstellung, nicht die Vorbereitung → create a bin group on the field, then a columnChart of the count (or use Deneb)) · Power BI · SVG-DAX n/a (a full distribution is not a single-cell micro-chart → deneb_vegalite, or the DaxLib.SVG histogram helper) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/histogram.yaml` (+ `golden/histogram.*`)

#### `boxplot` — Box plot
- **Purpose:** distribution · **zone:** analysis · **min size:** 3×4 grid (292×208px @1280, 438×312px @1920)
- **Avoid:** boxplot_without_labelled_quartiles_in_a_brief, too_many_groups
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die Form (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026: 59 Typen durchgesehen, keiner mit Box-Plot-Rollen oder -Objekt; `textbox` ist der einzige Namenstreffer auf 'box' und ein Textfeld). Median, Quartile und Whisker sind vier Marken auf einer Achse — das drueckt kein Kernvisual aus → deneb_vegalite (boxplot mark), or a box-plot custom visual) · Power BI · SVG-DAX n/a (requires five quartile measures + an axis; not a simple substitution template → the DaxLib.SVG boxplot helper (daxlib.org) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts n/a (Recharts has no box-plot primitive → a custom SVG/D3 box-plot, or a charting lib with box-plot support (ECharts, Plotly))
- **Code:** `visual_library/boxplot.yaml` (+ `golden/boxplot.*`)

#### `small_multiples` — Small multiples
- **Purpose:** time_comparison · **zone:** analysis · **min size:** 5×6 grid (497×320px @1280, 746×480px @1920)
- **Avoid:** independent_y_scales_per_panel, too_many_panels
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a grid of panels is not a single-cell micro-chart → deneb_vegalite (facet) or the native Small multiples well) · Deneb / Vega-Lite ✓ · Web · Recharts n/a (no single small-multiples component → map the series to a CSS grid of <LineChart> with a shared YAxis domain)
- **Code:** `visual_library/small_multiples.yaml` (+ `golden/small_multiples.*`)

#### `sankey` — Sankey
- **Purpose:** flow_between_stages · **zone:** detail · **best form for:** `flow_between_stages` · **min size:** 5×6 grid (497×320px @1280, 746×480px @1920)
- **Avoid:** sankey_for_precise_comparison, spaghetti_too_many_crossings
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die Form (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026). `funnel`, `treemap` und `ribbonChart` zeigen Anteile bzw. Rangwechsel, aber keine Fluesse zwischen benannten Knoten mit erhaltener Breite → the Microsoft/PowerViz Sankey custom visual (AppSource)) · Power BI · SVG-DAX n/a (curved multi-node flows are impractical as a cell SVG measure → the Sankey custom visual, or Deneb (full Vega)) · Deneb / Vega-Lite n/a (Vega-Lite has no sankey mark → a full Vega spec in Deneb (sankey via linkpath transform), or the native custom visual) · Web · Recharts ✓
- **Code:** `visual_library/sankey.yaml` (+ `golden/sankey.*`)

#### `decomposition_tree` — Decomposition tree
- **Purpose:** driver_breakdown · **zone:** detail · **best form for:** `driver_breakdown` · **min size:** 6×7 grid (600×376px @1280, 900×564px @1920)
- **Avoid:** used_as_a_static_exhibit, too_many_explain_by_dims
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (an interactive AI drill tree is not a cell micro-chart → powerbi_native (decompositionTreeVisual)) · Deneb / Vega-Lite n/a (an interactive drill tree is not a declarative Vega idiom → powerbi_native (decompositionTreeVisual)) · Web · Recharts n/a (Recharts has no decomposition-tree component → a custom D3 tree with sorted bars per level)
- **Code:** `visual_library/decomposition_tree.yaml` (+ `golden/decomposition_tree.*`)

#### `bar_absolute` — Bar (absolute magnitude)
- **Purpose:** compare_categories · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** broken_baseline_on_absolute_bar, color_to_separate_equal_categories, pie_for_comparison, unsorted_bars
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/bar_absolute.yaml` (+ `golden/bar_absolute.*`)

#### `waterfall_buildup` — Waterfall (buildup to total)
- **Purpose:** contribution_to_change · **zone:** analysis · **min size:** 4×5 grid (395×264px @1280, 592×396px @1920)
- **Avoid:** bridge_without_connectors, mixing_increase_and_decrease, too_many_steps, color_beyond_single_series
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a multi-step buildup with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS build-up UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/waterfall_buildup.yaml` (+ `golden/waterfall_buildup.*`)

#### `waterfall_variance` — Waterfall (variance bridge)
- **Purpose:** contribution_to_change · **zone:** analysis · **min size:** 4×5 grid (395×264px @1280, 592×396px @1920)
- **Avoid:** bridge_without_connectors, color_beyond_semantic, too_many_steps, hiding_the_two_anchor_totals
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a two-anchor variance bridge with a running total is not a single-cell micro-chart → powerbi_native (waterfallChart) or the PowerofBI.IBCS variance-bridge UDF (daxlib.org)) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/waterfall_variance.yaml` (+ `golden/waterfall_variance.*`)

#### `kpi_card_spark` — KPI card · value + spark + delta
- **Purpose:** value_verdict · **zone:** pulse · **best form for:** `value_verdict` · **min size:** 3×3 grid (292×152px @1280, 438×228px @1920)
- **Avoid:** number_without_context, color_of_number_for_magnitude, decorative_sparkline_no_axis_meaning
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (a KPI card composite (headline value + trailing spark + delta chip) is a card LAYOUT, not one Vega-Lite view; Deneb draws the spark, the value/delta are card chrome → powerbi_svg_dax for the whole card; or `line` in Deneb for just the spark inside a card) · Web · Recharts n/a (a KPI card is HTML (the value + delta) with a chart inside — a React component, not a single Recharts chart → compose in React: value/delta as HTML + a small Recharts `line` sparkline)
- **Code:** `visual_library/kpi_card_spark.yaml` (+ `golden/kpi_card_spark.*`)

#### `kpi_card_bullet` — KPI card · value + bullet
- **Purpose:** value_verdict · **zone:** pulse · **min size:** 3×3 grid (292×152px @1280, 438×228px @1920)
- **Avoid:** gauge_instead, number_without_context, color_of_number_for_magnitude
- **Tools:** Power BI · native n/a (kein Kartentyp traegt einen Balken mit Zielmarke. Gemessen 07.09.2026 gegen @microsoft/powerbi-core-visual-schema (Pin 0.1.1): `cardVisual` fuehrt 33 Objekte, darunter `referenceLabel`/`referenceLabelValue`/`referenceLabelDetail` — der Zielwert erscheint dort als TEXT neben der Zahl. `kpi` fuehrt sechs Objekte (general, goals, indicator, lastDate, status, trendline); `goals` zeigt Ziel und Abstand ebenfalls als Zahl. Beide koennen den Zielwert, keiner die Erreichung als Laenge. Genau das ist aber `encoding.attainment: bullet_bar_vs_tick` und der einzige Unterschied dieser Karte zu kpi_card_spark — eine native Spur haette den Rang-2-Kanal weggelassen und waere die Schwesterkarte mit anderem Namen. Dasselbe Ergebnis wie beim Idiom `bullet` selbst, dort am `gauge` gemessen → powerbi_svg_dax (cardVisual callout.imageFX)) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (the value + delta chip are card chrome; Deneb draws the bullet only, not the headline layout → powerbi_svg_dax for the whole card; or `bullet` in Deneb for just the attainment track) · Web · Recharts n/a (a KPI card is HTML (value + delta) with a chart inside — a React component, not a single Recharts chart → compose in React: value/delta as HTML + a Recharts `bullet`)
- **Code:** `visual_library/kpi_card_bullet.yaml` (+ `golden/kpi_card_bullet.*`)

#### `kpi_card_sparkbar` — KPI card · value + column trend
- **Purpose:** value_verdict · **zone:** pulse · **min size:** 3×3 grid (292×152px @1280, 438×228px @1920)
- **Avoid:** number_without_context, color_of_number_for_magnitude, line_when_periods_are_discrete
- **Tools:** Power BI · native n/a (die native Trendspur ist eine Linie und laesst sich nicht in Saeulen umschalten. Gemessen 07.09.2026 gegen @microsoft/powerbi-core-visual-schema (Pin 0.1.1): `kpi.objects.trendline` fuehrt genau zwei Eigenschaften, `show` und `transparency` — keine Form, keine Marker, keine Wahl zwischen Linie und Saeule. `cardVisual` traegt ueberhaupt keine eingebettete Trendspur (33 Objekte, keines davon ein Diagramm). Eine native Spur zeichnete hier also die Linie, die `anti_patterns` dieses Idioms unter `line_when_periods_are_discrete` ausdruecklich verbietet: dann waere es kpi_card_spark. Die Saeulenform gibt es nativ nur als eigenstaendiges Visual — siehe Idiom `column_time`, dort `clusteredColumnChart` — nicht innerhalb einer Karte → powerbi_svg_dax (cardVisual callout.imageFX); die Saeulen allein nativ als `column_time`) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (the value + delta chip are card chrome; Deneb draws the column trend only, not the headline layout → powerbi_svg_dax for the whole card; or `column_time` in Deneb for just the trend) · Web · Recharts n/a (a KPI card is HTML (value + delta) with a chart inside — a React component, not a single Recharts chart → compose in React: value/delta as HTML + a small Recharts `column_time` bar trend)
- **Code:** `visual_library/kpi_card_sparkbar.yaml` (+ `golden/kpi_card_sparkbar.*`)

#### `matrix_sparkline` — Matrix column · sparkline
- **Purpose:** evidence_detail · **zone:** detail · **min size:** 5×4 grid (497×208px @1280, 746×312px @1920)
- **Avoid:** axis_labels_in_a_sparkline, line_when_periods_are_discrete
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (a per-row cell chart inside a table is not a Vega-Lite view → the whole trend as a standalone chart is `line` in Deneb; the cell column is SVG-DAX) · Web · Recharts n/a (Recharts has no table cell primitive → an HTML <table> with a small Recharts `line` per row)
- **Code:** `visual_library/matrix_sparkline.yaml` (+ `golden/matrix_sparkline.*`)

#### `matrix_bullet` — Matrix column · bullet
- **Purpose:** evidence_detail · **zone:** detail · **min size:** 5×4 grid (497×208px @1280, 746×312px @1920)
- **Avoid:** colour_bands_in_a_cell, gauge_instead
- **Tools:** Power BI · native n/a (eine Spalten-Measure in der Zelle (ImageUrl), kein eigenstaendiges Visual — die Wirtstabelle ist matrix_evidence (tableEx). Nativ geprueft (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026): `tableEx.columnFormatting` fuehrt `dataBars`, genau die Eigenschaft, die matrix_evidence schon benutzt — aber als proportionalen Balken ohne Referenzmarke. Der Zielstrich ist das, was `encoding.attainment: bullet_bar_vs_tick` ausmacht → matrix_evidence (tableEx) + this SVG-DAX column, image height ~20px) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (a per-row cell chart inside a table is not a Vega-Lite view → the standalone attainment chart is `bullet` in Deneb; the cell column is SVG-DAX) · Web · Recharts n/a (Recharts has no table cell primitive → an HTML <table> with a small Recharts `bullet` per row)
- **Code:** `visual_library/matrix_bullet.yaml` (+ `golden/matrix_bullet.*`)

#### `matrix_delta_pill` — Matrix column · delta pill
- **Purpose:** evidence_detail · **zone:** detail · **min size:** 5×4 grid (497×208px @1280, 746×312px @1920)
- **Avoid:** pill_without_the_number, tint_not_from_severity_tints, color_as_decoration
- **Tools:** Power BI · native n/a (eine Spalten-Measure in der Zelle (ImageUrl), kein eigenstaendiges Visual — die Wirtstabelle ist matrix_evidence (tableEx). Nativ geprueft (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026): `columnFormatting` fuehrt `fontColor` und `backColor`, also die Pillenfarbe, aber KEINE Icon-Eigenschaft — die neun Eigenschaften sind labelDisplayUnits, labelPrecision, fontColor, backColor, alignment, styleHeader, styleValues, styleTotal, dataBars. Der Richtungspfeil aus `encoding.direction` hat damit keinen nativen Traeger. KORREKTUR: die fruehere Begruendung nannte 'icon + font colour' als native Teilform; die Schriftfarbe stimmt, das Icon steht in diesem Katalogstand nicht → matrix_evidence (tableEx) + this SVG-DAX column; or native conditional font colour + KPI icon) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite n/a (a per-row cell pill inside a table is not a Vega-Lite view → SVG-DAX column; or a Deneb text mark with a conditional fill for a standalone board) · Web · Recharts n/a (Recharts is a charting library, not for text/pill table cells → an HTML <table> cell: a span with severity-tint background + the signed value)
- **Code:** `visual_library/matrix_delta_pill.yaml` (+ `golden/matrix_delta_pill.*`)

#### `column_time` — Column chart over time
- **Purpose:** time_comparison · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** line_for_few_discrete_periods, column_for_many_continuous_points
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (a full column-over-time chart is not a single-cell micro-chart → kpi_card_sparkbar for the in-card column trend; powerbi_native / Deneb for the full chart) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Notation profiles:** `house_default` · `ibcs` — the same idiom in another convention (see `_notation_profiles.yaml`)
- **Code:** `visual_library/column_time.yaml` (+ `golden/column_time.*`)

#### `dumbbell` — Dumbbell (before / after)
- **Purpose:** compare_categories · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** dumbbell_for_one_value, too_many_categories
- **Tools:** Power BI · native n/a (kein Visualtyp traegt die Form (Katalog @microsoft/powerbi-core-visual-schema 0.1.1, gemessen 07.09.2026). Zwei Punkte auf einer Zeile mit verbundener Strecke ist keine Rolle, die ein Kernvisual kennt; `scatterChart` setzt Punkte, verbindet sie aber nicht paarweise → SVG-DAX (a dumbbell cell in a matrix) or Deneb (layered rule + two points)) · Power BI · SVG-DAX ✓ · Deneb / Vega-Lite ✓ · Web · Recharts n/a (a dumbbell needs a custom connector shape between two series — not a stock Recharts primitive → SVG-DAX cell, Deneb, or a Recharts ScatterChart with a custom <Line> segment layer)
- **Code:** `visual_library/dumbbell.yaml` (+ `golden/dumbbell.*`)

#### `bar_stacked` — Stacked bar (absolute)
- **Purpose:** part_to_whole · **zone:** analysis · **min size:** 4×4 grid (395×208px @1280, 592×312px @1920)
- **Avoid:** too_many_series, stack_when_comparing_parts, normalize_when_totals_matter
- **Tools:** Power BI · native ✓ · Power BI · SVG-DAX n/a (multi-series absolute stacking is not a single-cell micro-chart → powerbi_native (stackedColumnChart) or Deneb) · Deneb / Vega-Lite ✓ · Web · Recharts ✓
- **Code:** `visual_library/bar_stacked.yaml` (+ `golden/bar_stacked.*`)
