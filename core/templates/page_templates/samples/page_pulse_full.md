# Full Page Sample: The Pulse (Overview — 3s + 30s)

> **Page type:** Overview  |  **Layers:** 3-second + 30-second
> **Template:** T2 Tactical Variance (standard; other templates follow same structure)
> **Reading pattern:** Z-pattern
> **Use case example:** COM-001 Sales Performance
> **Spec ref:** `Design_Spec_3_30_300.md §6.1`

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

## Narrative Annotation

```
Z-Pattern reading path — annotated:

→ Step 1 (top-left → top-right): KPI band
  ACT 1 — ESTABLISH. "Here is where we stand."
  NET SALES ▲ +8.2% → GREEN. First signal: we are above target on revenue.
  GM MARGIN ▼ -1.1pp → RED. Second signal: margin is under pressure.
  Eye reads left to right in ~1 second. Two conflicting signals = tension.

↘ Step 2 (diagonal): Slicer bar
  CONTEXT SET. "Oct 2025 MTD, All Regions, All Channels."
  Confirms the scope is current month. No re-reading needed after the Z-diagonal.

→ Step 3 (left main visual — Main_1):
  ACT 2 — TREND. "This is the journey."
  Revenue grew steadily, then dipped in Aug, recovered. Current momentum: positive.
  Annotated inflection point: "Aug: summer slowdown — recovered in Sep."
  Question answered: "Are we trending in the right direction?" → Yes, but margin tells a different story.

→ Step 4 (center — Main_2):
  ACT 2 — VARIANCE. "This is what caused the gap."
  Waterfall: Plan 45 → -2.1 Price → +3.2 Volume → -5.3 Mix → Actual 38.
  The Big Idea materializes: "Mix is the dominant negative driver."
  Reader now knows what is happening and why — in 30 seconds.

→ Step 5 (right — Main_3):
  ACT 2 — RANKING. "These are the actors."
  DACH drives the largest shortfall. BNL and NOR are green.
  Ranked by |Δ Plan| descending. Eye stops at the longest red bar → DACH.
  Reader knows where to intervene.
```

**The Z-path tells the complete story:** "Revenue is up but margin is under pressure (3s) → Mix decline in DACH is the driver, trend is recovering (30s) → action required: DACH mix review."

---

## Big Idea Verification

After 30 seconds on this page, the reader should be able to state:

> *"Net Sales is +8.2% vs Plan but GM% is -1.1pp below plan. The revenue gap from Plan is driven by adverse mix effects (-€5.3M), concentrated in DACH. Trend is recovering after an August dip."*

If this statement cannot be constructed from the page, the design has failed.

---

## Content Quality Checklist (Pulse — T2)

- [x] Decision question banner visible above KPI band
- [x] All KPI cards show delta vs reference (not value only)
- [x] Primary KPI (Net Sales) is leftmost and largest
- [x] Visual titles are question-form ("How is Net Sales trending vs prior year?")
- [x] Waterfall bars labeled with absolute + percentage contribution
- [x] Ranking sorted by |Δ Plan| descending (worst first)
- [x] Max 3 slicers (Time, Region, Channel)
- [x] No tables, no action panel (Overview page = signal + explanation only)
- [x] IBCS abbreviations used (PY, Plan, MTD, AC)
- [x] Inflection point on trend chart annotated

---

## Bracket YAML Reference (updated to abstract visual types)

```yaml
# UseCase_Bracket.yaml → page_1_summary

ux_layout_rules:
  report_structure: "2-Page-Lead"
  page_1_summary:
    title: "Commercial Overview"
    page_type: "T2_Tactical_Variance"
    template_id: "pulse"
    decision_question: "Are we on track for our Commercial targets this month?"
    big_idea: "Net Sales is +8.2% vs Plan but GM% is -1.1pp — adverse Mix in DACH requires attention."
    component_3s:
      kpi_id: KPI-COM-005
      visual_type: kpi_card
      sparkline_field: "NetSales_Monthly"
      comparison: "vs_plan"
      status_logic: "higher_is_better"
    component_30s:
      - slot_id: "Main_1"
        visual_type: line_chart
        kpi_id: KPI-COM-005
      - slot_id: "Main_2"
        visual_type: waterfall
        kpi_ids: [sales.net_sales.delta_abs.plan]
      - slot_id: "Main_3"
        visual_type: bar_chart_horizontal
        kpi_id: KPI-COM-005
        segment_by: region
```
