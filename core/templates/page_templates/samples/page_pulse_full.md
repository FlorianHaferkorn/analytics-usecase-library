# Full Page Sample: The Pulse (Overview — 3s + 30s)

> **Page type:** Overview  |  **Layers:** 3-second + 30-second
> **Template:** T2 Tactical Variance (standard; other templates follow same structure)
> **Reading pattern:** Z-pattern
> **Use case example:** COM-001 Sales Performance
> **Spec ref:** `layout_330300_design_spec.md §6.1`

---

## What This Page Answers

1. *Am I on track?* (3s — KPI band)
2. *Why am I off track?* (30s — trend, variance, ranking)

This page does NOT show detail records (that is the Action Matrix / Detail page).

---

## Complete Page Wireframe

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row
Navigation target: Overview page  |  Drillthrough source for Detail page

╔═══════════════════════════════════════════════════════════════════════════════╗
║ [Decision question banner]                                                    ║
║ "Are we on track for our Commercial targets this month?"          ← heading_3 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ZONE 1 — 3 SECONDS  [row 0–1, col 0–12]                                       ║
║                                                                               ║
║ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ║
║ │ NET SALES   │ │ GM MARGIN % │ │ UNITS SOLD  │ │ CUSTOMERS   │ │ AVG ORDER│ ║
║ │             │ │             │ │             │ │             │ │          │ ║
║ │  €42.3M     │ │   18.4%     │ │   1.24M     │ │   98.7K     │ │   €428   │ ║
║ │  ▲ +8.2%    │ │  ▼ -1.1pp   │ │  ▲ +3.4%    │ │  ▲ +5.0%    │ │  ─ ±0%  │ ║
║ │  [GREEN]    │ │  [RED]      │ │  [GREEN]    │ │  [GREEN]    │ │  [GREY]  │ ║
║ │  vs Plan    │ │  vs Plan    │ │  vs PY      │ │  vs PY      │ │  vs PY   │ ║
║ │  ▬▬▬▬▬▬▬▬ │ │  ▬▬▬▬▬▬▬▬ │ │  ▬▬▬▬▬▬▬▬ │ │  ▬▬▬▬▬▬▬▬ │ │          │ ║
║ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ZONE 2 — SLICER BAR  [row 2, col 0–12]                                        ║
║                                                                               ║
║ ┌─────────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐  ║
║ │ Time: [Oct 2025 MTD  ▾] │ │ Region: [All   ▾] │ │ Channel: [All      ▾] │  ║
║ └─────────────────────────┘ └───────────────────┘ └────────────────────────┘  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ ZONE 3 — 30 SECONDS  [row 3–10, col 0–12]                                     ║
║                                                                               ║
║ ┌───────────────────────────┐ ┌───────────────────────────┐ ┌──────────────┐ ║
║ │ How is Net Sales trending │ │ Where does the revenue    │ │ Which regions│ ║
║ │ vs prior year?            │ │ gap come from?            │ │ drive revenue│ ║
║ │                           │ │                           │ │              │ ║
║ │   €M                      │ │  €M                       │ │ DACH  ████  │ ║
║ │ 50 ─ ─ ─ ─ ─ ─(Target)   │ │ 45 ████ ← Plan            │ │ BNL   ███   │ ║
║ │ 45    ╭──╮                │ │    ████                   │ │ NOR   ██    │ ║
║ │ 40  ╭──╯  ╰──╮            │ │ 40      ╭─╮ +Price        │ │ CEE   ██    │ ║
║ │ 35 ╭╯         ╰──╮        │ │         ╰─╯               │ │ SE    █     │ ║
║ │ 30╯              ╰──      │ │ 38           ╭─╮ -Mix      │ │             │ ║
║ │  ──────────────────       │ │              ╰─╯           │ │ ▲+5% ▲+8%  │ ║
║ │  Jan Feb Mar Apr Jun      │ │ 36                ╭─╮ -Vol  │ │ ▼-3% ▼-7%  │ ║
║ │                           │ │                   ╰─╯       │ │ ─±0%       │ ║
║ │  ── Actual  ─ ─ Target    │ │ 34    Plan +Px -Mix -V Act  │ │             │ ║
║ │  ── PY                    │ │ Summary: -€4.2M gap         │ │             │ ║
║ └───────────────────────────┘ └───────────────────────────┘ └──────────────┘ ║
║                                                                               ║
║   [col=0, row=3, 4×8]           [col=4, row=3, 4×8]       [col=8, row=3, 4×8]║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ NAVIGATION  [row 11, col 0–12]                                                ║
║                                                                               ║
║ [← Back]              [Drill through to Detail →]  [Export page ↓]           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Grid slot summary:
  Decision banner    [col=0,  row=0,  col_span=12, row_span=1]  — optional
  KPI_Cards          [col=0,  row=0,  col_span=12, row_span=2]  — Zone 1
  Slicer bar         [col=0,  row=2,  col_span=12, row_span=1]  — Zone 2
  Main_1 (Trend)     [col=0,  row=3,  col_span=4,  row_span=8]  — Zone 3
  Main_2 (Variance)  [col=4,  row=3,  col_span=4,  row_span=8]  — Zone 3
  Main_3 (Ranking)   [col=8,  row=3,  col_span=4,  row_span=8]  — Zone 3
  Navigation strip   [col=0,  row=11, col_span=12, row_span=1]  — optional
```

---

## Page Configuration

| Property | Value |
|---|---|
| Page type | Overview (3s + 30s) |
| Grid | 12×12 LU |
| Canvas (design) | 1280×720 |
| Canvas (production) | 1920×1080 |
| Display option | FitToPage |
| Drillthrough | Source — links to Detail page |
| Navigation | Always visible |

---

## Z-Pattern Reading Flow

The eye follows the Z-pattern across this page:

```
Step 1 (top-left → top-right):   KPI cards — scan all signals left to right
Step 2 (diagonal, brief):        Slicer context — what period/filter is active?
Step 3 (left main visual):       Trend chart — how are we moving?
Step 4 (right secondary visual): Variance/Ranking — where/why is the gap?
```

The most important KPI card is placed at top-left (first in natural reading order).
The primary diagnostic visual (trend or variance) is placed at Main_1 (leftmost of Zone 3).

---

## Template Variations

| Template | KPI band | Main_1 | Main_2 | Main_3 |
|---|---|---|---|---|
| **T1 Strategic** | Hero card (1–2 large cards) | Trend (area chart, bold) | — | — |
| **T2 Tactical** | 3–5 cards | Trend (line chart) | Variance (waterfall) | Ranking (bar) |
| **T3 Operational** | 4–6 cards (incl. alert KPIs) | Exceptions table | Trend | Ranking |
| **T4 Prescriptive** | 3–5 cards | Prescriptive table | Trend | Ranking |

---

## PBIP Configuration Snippet

```yaml
# UseCase_Bracket.yaml → page_1_summary

ux_layout_rules:
  report_structure: "2-Page-Lead"
  page_1_summary:
    template_type: "T2"
    grid_template: "pulse"             # core/templates/page_templates/grid_templates/pulse.json
    component_3s:
      kpi_id: sales.net_sales.amount
      visual_type: kpi_card
      sparkline_field: "NetSales_Monthly"
      comparison: "vs_plan"
      status_logic: "higher_is_better"
    component_30s:
      - slot: "Main_1"
        visual_type: trend_line
        kpi_id: sales.net_sales.amount
      - slot: "Main_2"
        visual_type: waterfall
        kpi_ids: [sales.net_sales.delta_abs.plan]
      - slot: "Main_3"
        visual_type: bar_chart
        kpi_id: sales.net_sales.amount
        segment_by: region
```
