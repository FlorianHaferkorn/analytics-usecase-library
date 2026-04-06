# Layer Sample: 30-Second — The Diagnostic Layer

> **Layer:** Zone 3 (rows 3–8 of the 12×12 grid, full width)
> **Purpose:** Explain why — drivers, trends, variance, ranking
> **Reading pattern:** Z-pattern — primary visual top-left, secondary top-right, tertiary bottom
> **Spec ref:** `Design_Spec_3_30_300.md §5.3`

---

## What the 30-Second Layer Answers

> *Why am I off track? What are the drivers?*

The reader has seen the KPI signal (3s layer) and now wants to understand the cause. Each visual slot answers one specific diagnostic question. No more than three slots on a standard overview page (SQLBI recommendation; BPA limit: 20 visuals, 3 slicers).

---

## Full 30-Second Zone Wireframe (Standard 3-slot layout)

```
Canvas: 1280×720  |  Grid rows 3–8  |  3 equal columns (4 LU each)

Col:   0─────────4    4─────────8    8─────────12
       │                                         │
  R3 ──┤                                         │
       │  Main_1       │  Main_2       │  Main_3  │
       │  TREND        │  VARIANCE     │  RANKING │
       │               │               │          │
       │  ╭─────────╮  │  ╭─────────╮  │ ╭──────╮ │
       │  │  /──╮   │  │  │ ■ 42.3  │  │ │DACH ████│
       │  │ /   ╰─╮ │  │  │ □ 38.1  │  │ │BNL  ███ │
       │  │╱      ╰─│  │  │ ─────── │  │ │NOR  ██  │
       │  │  ─target │  │  │ +Price  │  │ │CEE  ██  │
       │  ╰─────────╯  │  │ +2.1    │  │ │SE   █   │
       │               │  │ -Mix    │  │ ╰──────╯ │
       │               │  │ -1.4    │  │          │
       │               │  │ -Volume │  │          │
       │               │  │ -0.8    │  │          │
       │               │  ╰─────────╯  │          │
  R8 ──┤                                         │
       └─────────────────────────────────────────┘

Slot grid positions:
  Main_1  [col=0, row=3, col_span=4, row_span=6]
  Main_2  [col=4, row=3, col_span=4, row_span=6]
  Main_3  [col=8, row=3, col_span=4, row_span=6]
```

---

## Slot 1 — Trend (Main_1)

**Question:** How is the KPI developing over time?

**Default visual:** Line chart with reference line (target / prior year)

```
┌────────────────────────────────────────────┐
│ How is Net Sales trending vs prior year?   │  ← chart_title (md, question-oriented)
│                                            │
│   €M                                       │
│ 50 ┤  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  (Target)       │  ← reference line: semantic.neutral
│ 45 ┤            ╭──╮                        │
│ 40 ┤   ╭──╮  ╭──╯  ╰──╮                    │  ← actual: color.primary
│ 35 ┤  ╭╯  ╰──╯         ╰──╮                │
│ 30 ┤──╯                    ╰───            │
│    └────┬───┬───┬───┬───┬───┬────          │
│        Jan Feb Mar Apr May Jun             │  ← axis_label (xs)
│                                            │
│  ── Actual    ─ ─ Target    ── Prior Year  │  ← legend_label (xs)
└────────────────────────────────────────────┘

Signal: No signal color on the chart itself — signals are in Zone 1 KPI cards.
        Reference line uses semantic.neutral (grey).
        Actual series uses color.primary (brand color).
        Prior year uses color.secondary or neutral-400 (muted).
```

**Component spec:**

| Field | Required | Notes |
|---|---|---|
| Question title | Yes | "How is [KPI] trending vs [reference]?" |
| Actual series | Yes | `color.primary`; line or area |
| Reference line | Recommended | Target, Budget, or Prior Year; `semantic.neutral` |
| Prior year line | Optional | `color.secondary` or muted grey |
| X axis | Yes | Time periods; max 8 labels; auto-rotate if >6 |
| Y axis | Yes | Unit-labelled (€M, %, etc.); no gridline clutter |
| Legend | Yes | Short labels; `legend_label` (xs) |
| Data labels | No | Avoid — clutter; let axis convey scale |

**Allowed visual types:** Line chart (default), Area chart (T1 only)

---

## Slot 2 — Variance (Main_2)

**Question:** Where are we off plan, and what explains the gap?

**Default visual:** Waterfall chart (bridge: plan → actuals, with contributor bars)

```
┌────────────────────────────────────────────┐
│ Where does the revenue gap come from?       │  ← chart_title (md)
│                                            │
│ €M                                         │
│ 45 ┤  ████  ← Plan                         │  ← neutral-200 (plan baseline)
│ 42 ┤  ████                                 │
│    │  ████  ╭───╮  ← +Price effect         │  ← semantic.positive
│ 40 ┤        ╰───╯                          │
│    │               ╭───╮  ← -Mix effect    │  ← semantic.negative
│ 38 ┤               ╰───╯                   │
│    │                     ╭───╮  ← -Volume  │  ← semantic.negative
│ 36 ┤                     ╰───╯             │
│    │                           ████  ← Act │  ← color.primary (actual total)
│    └────────────────────────────────────   │
│       Plan  Price   Mix   Volume  Actual   │
│                                            │
│  Plan €42.3M → Actual €38.1M = -€4.2M     │  ← caption (xs, summary line)
└────────────────────────────────────────────┘

Positive contributors: semantic.positive (green bars, go up)
Negative contributors: semantic.negative (red bars, go down)
Plan and Actual totals: neutral-200 / color.primary
```

**Component spec:**

| Field | Required | Notes |
|---|---|---|
| Question title | Yes | "Where does the [KPI] gap come from?" |
| Plan/budget bar | Yes | Baseline; neutral-200 |
| Contributor bars | Yes | +/− effect; semantic.positive / negative |
| Actual total bar | Yes | `color.primary` |
| Value labels on bars | Yes | Show €M value on each bar |
| Summary line | Recommended | "Plan €X → Actual €Y = ±€Z" as caption |

**Fallback visual (when no decomposition available):** Horizontal bar chart comparing actuals vs targets across entities (regions, products, channels).

---

## Slot 3 — Ranking (Main_3)

**Question:** Who drives what? Which entities perform best or worst?

**Default visual:** Horizontal bar chart (sorted descending by value)

```
┌────────────────────────────────────────────┐
│ Which regions drive revenue?                │  ← chart_title (md)
│                                            │
│  DACH      ████████████████  €18.2M  ▲+5%  │  ← color.primary + delta icon
│  Benelux   ████████████      €12.4M  ▲+8%  │
│  Nordics   ████████          € 8.1M  ▼-3%  │  ← semantic.negative on delta
│  CEE       ██████            € 6.8M  ▼-7%  │  ← semantic.negative on delta
│  S. EU     ████              € 4.2M  ─ ±0% │  ← semantic.neutral
│            │                               │
│            0    5    10   15   20  €M       │  ← axis_label (xs)
│                                            │
│  Top-5 regions by Net Sales  ·  vs Plan    │  ← caption (xs)
└────────────────────────────────────────────┘

Bar color: color.primary for all bars (ranking, not signal)
Delta values at row end: signal-colored (semantic.positive/negative)
Sort: descending by bar value (largest first)
Max items: 10 visible; "Show more" for full list (never load all by default)
```

**Component spec:**

| Field | Required | Notes |
|---|---|---|
| Question title | Yes | "Which [entities] drive [KPI]?" |
| Entity labels | Yes | Left-aligned; truncate at 20 chars with tooltip |
| Bar length | Yes | Proportional to value; `color.primary` |
| Value label | Yes | Absolute value at bar end (right-aligned) |
| Delta column | Recommended | Signal-colored ▲/▼ + % vs reference |
| Reference label | Yes | Caption: "vs Plan", "vs PY" |
| Sort order | Yes | Always sorted by primary value (descending) |
| Max items shown | Max 10 | More on demand; never overwhelm |

---

## Slot 4 — Mix (Optional, Main_4)

**Question:** How is the KPI distributed across categories?

**Visual:** 100% stacked bar chart

```
┌────────────────────────────────────────────┐
│ How is revenue distributed by channel?      │  ← chart_title (md)
│                                            │
│ 2025 │████████████████▓▓▓▓▓▓▒▒▒░░░│100%  │
│ 2024 │██████████████████▓▓▓▓▒▒░░░░│100%  │
│ 2023 │████████████████████▓▓▓░░░░░│100%  │
│                                            │
│  ██ Online  ▓▓ Stores  ▒▒ Wholesale  ░ B2B │  ← legend
└────────────────────────────────────────────┘

Color: use color.primary family (first segment) + derived palette (subsequent)
Never use pie/donut — always 100% stacked horizontal bar
```

---

## Adaptive Layout: Fewer Than 3 Slots

When a use case does not activate all 3 slots, remaining slots expand to fill width:

```
2 slots only (no Ranking):
  Main_1 [col=0, row=3, col_span=6, row_span=6]
  Main_2 [col=6, row=3, col_span=6, row_span=6]

1 slot only (dominant):
  Main_1 [col=0, row=3, col_span=12, row_span=6]
  (Hero layout — used in Investigator template)
```

---

## UseCase_Bracket.yaml Reference

30-second slots are configured in `ux_layout_rules.page_1_summary.component_30s`:

```yaml
ux_layout_rules:
  page_1_summary:
    component_30s:
      - kpi_id: sales.net_sales.amount
        visual_type: trend_line
        slot: "Main_1"
      - kpi_ids:
          - sales.net_sales.delta_pct.plan
          - sales.net_sales.delta_abs.plan
        visual_type: waterfall
        slot: "Main_2"
      - kpi_id: sales.net_sales.amount
        visual_type: bar_chart
        segment_by: region
        slot: "Main_3"
```
