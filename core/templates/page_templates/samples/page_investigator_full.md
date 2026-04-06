# Full Page Sample: The Investigator (Alternative Overview)

> **Page type:** Alternative Overview  |  **Layers:** 30-second (focus-driven)
> **Templates:** T2 Tactical, T3 Operational, T4 Prescriptive
> **Reading pattern:** F-pattern (focus visual dominates left column)
> **Use case:** When a single diagnostic question dominates the page (e.g., decomposition, root cause)
> **Spec ref:** `Design_Spec_3_30_300.md §6.3`
> **Grid template:** `core/templates/page_templates/grid_templates/investigator.json`

---

## When to Use the Investigator vs The Pulse

| | Pulse | Investigator |
|---|---|---|
| Primary content | Three equal diagnostic slots | One dominant focus visual |
| Reading pattern | Z-pattern (broad overview) | F-pattern (deep on one question) |
| KPI Band | Full width | Optional (added as top strip if needed) |
| Best for | T1 Strategic, T2 Tactical overview | T3 Operational drill, T4 root cause |
| Decision horizon | "What's happening everywhere?" | "Why is this specific thing happening?" |

---

## Full Page Wireframe (Without KPI Band — Focus Only)

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row

╔═══════════════════════════════════════════════════════════════════════════════╗
║ [Decision question banner]                                                    ║
║ "What explains the margin decline in DACH?"                       ← heading_3 ║
╠══╦═══════════════════════════════════════════╦══════════════════════════════╣
║  ║                                           ║                              ║
║S ║  Focus_Area  [col=2, row=0, 8×8]          ║  Support_1  [col=10, r=0, 2×4]║
║L ║                                           ║                              ║
║I ║  What drives the DACH margin gap?         ║  DACH trend (12m)            ║
║C ║                                           ║  ╭──╮╭───╮╮                 ║
║E ║  Revenue   +€2.1M ████████████████        ║  ╯  ╰╯   ╰╯                 ║
║R ║  Mix        -€3.4M  (decomp. driver)      ║                              ║
║  ║  Discount  -€1.8M                         ╠══════════════════════════════╣
║P ║  Returns   -€0.6M                         ║  Support_2  [col=10, r=4, 2×4]║
║A ║  Other     +€0.5M                         ║                              ║
║N ║                                           ║  Top products by gap         ║
║E ║  ─────────────────────────────────────    ║  Prod A ████ -€1.2M          ║
║  ║  Net GM gap:  -€3.2M  ▼ -18%  vs Plan    ║  Prod B ███  -€0.8M          ║
║  ║                                           ║  Prod C ██   -€0.6M          ║
║  ╠═══════════════════════════════════════════╩══════════════════════════════╣
║  ║  (Slicer Pane continues for full height)                                 ║
╚══╩═════════════════════════════════════════════════════════════════════════╝

Grid positions:
  Slicer_Pane [col=0,  row=0,  col_span=2, row_span=12]
  Focus_Area  [col=2,  row=0,  col_span=8, row_span=8]
  Support_1   [col=10, row=0,  col_span=2, row_span=4]
  Support_2   [col=10, row=4,  col_span=2, row_span=4]
```

---

## Full Page Wireframe (With KPI Band)

When the use case also needs headline KPIs on the Investigator page (optional):

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ ZONE 1 — KPI BAND  [row 0–1, col 0–12]  (optional, same as Pulse)            ║
║ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  ║
║ │ GM MARGIN % │ │ NET SALES   │ │ GM ABSOLUTE │ │  [Time Slicer]          │  ║
║ │  18.4% ▼    │ │  €42.3M ▲  │ │   €7.8M ▼   │ │  Oct 2025 MTD       ▾  │  ║
║ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────────┘  ║
╠══╦═══════════════════════════════════════════╦══════════════════════════════╣
║  ║  Focus_Area  [col=2, row=2, 8×8]          ║  Support_1  [col=10, r=2, 2×4]║
║  ║  Decomposition / Root Cause Visual        ║  Context visual 1            ║
║  ║  ...                                      ╠══════════════════════════════╣
║  ║                                           ║  Support_2  [col=10, r=6, 2×4]║
║  ║                                           ║  Context visual 2            ║
╚══╩═══════════════════════════════════════════╩══════════════════════════════╝

Grid positions (with KPI band):
  KPI_Cards   [col=0,  row=0,  col_span=12, row_span=2]
  Slicer_Pane [col=0,  row=2,  col_span=2,  row_span=10]
  Focus_Area  [col=2,  row=2,  col_span=8,  row_span=8]
  Support_1   [col=10, row=2,  col_span=2,  row_span=4]
  Support_2   [col=10, row=6,  col_span=2,  row_span=4]
```

---

## Focus Area — Visual Options

The Focus_Area slot supports the most analytical visual types. Selection depends on the question:

| Question type | Recommended visual | When |
|---|---|---|
| "What drives the gap?" | Waterfall decomposition / Bridge chart | Known driver dimensions |
| "Why is X happening?" | Scatter plot (driver vs outcome) | T3, T4; correlation analysis |
| "What is the breakdown?" | Horizontal bar (sorted) | Simple ranking with detail |
| "How does the structure change?" | Stacked bar over time | Mix shift analysis |
| "What are the exceptions?" | Highlighted table with conditional formatting | T3 operational monitoring |

---

## Support Panels — Purpose

Support panels give **context** to the Focus Area — they are not competing analyses.

| Panel | Purpose | Examples |
|---|---|---|
| Support_1 | Temporal context — how does Focus Area change over time? | Trend sparkline, mini line chart |
| Support_2 | Dimensional context — what else correlates or contrasts? | Top-N bar, comparison card |

Support panels are deliberately small (2 LU wide × 4 LU tall). They are context, not primary analysis. If a support visual needs more space, it belongs in a different slot or page.

---

## Page Configuration

| Property | Value |
|---|---|
| Page type | Alternative Overview |
| Grid template | `investigator.json` |
| Drillthrough | Source → Detail (Action Matrix) |
| Canvas (design) | 1280×720 |
| Canvas (production) | 1920×1080 |
| Reading pattern | F-pattern |
| With KPI band | Optional (add if headline status is needed) |

---

## UseCase_Bracket.yaml Reference

```yaml
ux_layout_rules:
  page_1_summary:
    template_type: "T3"
    grid_template: "investigator"
    component_3s: null                  # No KPI band (or add if needed)
    component_30s:
      - slot: "Focus_Area"
        visual_type: waterfall
        kpi_ids: [margin.gm.delta_abs.plan]
        decompose_by: [price, mix, volume]
      - slot: "Support_1"
        visual_type: trend_line
        kpi_id: margin.gm.pct
      - slot: "Support_2"
        visual_type: bar_chart
        kpi_id: margin.gm.delta_abs.plan
        segment_by: product
        top_n: 5
```
