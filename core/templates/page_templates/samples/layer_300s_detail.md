# Layer Sample: 300-Second — The Action Matrix

> **Layer:** Zone 4 (full page — Detail page only)
> **Purpose:** Validate, drill, and act — evidence data + prescription
> **Reading pattern:** F-pattern — slicer pane anchors left, detail fills center, action panel anchors right
> **Template:** Any (with slicer/matrix); T4 additionally requires Action Panel
> **Spec ref:** `Design_Spec_3_30_300.md §5.4`

---

## What the 300-Second Layer Answers

> *What exactly happened? Which records explain the KPI? What should I do?*

The reader has confirmed from Zone 1–3 that there is a problem and understands the driver. Now they need to find the specific entities (customers, invoices, products, regions) to act on, and — for T4 — receive a concrete prescription.

---

## Full Action Matrix Wireframe (T4 — with Action Panel)

```
Canvas: 1280×720  |  Full page (12 × 12 grid)

Col:  0──2   2──────────────────────10   10──12
      │                                       │
 R0 ──┤  │  Smart_Narrative (8 LU)   │  │     │
      │  │  "Net Sales -€4.2M vs     │  │  A  │
      │  │   plan YTD, driven by     │  │  C  │
      │  │   DACH (-€3.1M)"          │  │  T  │
 R1 ──┤  S ──────────────────────── ──  │  I  │
      │  L                               │  O  │
      │  I  Detail_Matrix (8 LU × 11 LU) │  N  │
      │  C  ───────────────────────────  │     │
      │  E  Region │Sales│ Δ Plan │ Δ% │  │  P  │
      │  R  DACH   │18.2 │  -3.1  │-15%│  │  A  │
      │     Benelux│12.4 │  +0.4  │ +3%│  │  N  │
      │  P  Nordics│ 8.1 │  -0.2  │ -2%│  │  E  │
      │  A  CEE    │ 6.8 │  -1.3  │-16%│  │  L  │
      │  N  S.EU   │ 4.2 │  -1.1  │-21%│  │     │
      │  E  ...    │ ... │   ...  │ ..%│  │     │
      │             ──── [Export] [→] ──   │     │
 R11 ─┤  │                               │  │     │
      └──────────────────────────────────────────┘

Slot grid positions:
  Slicer_Pane    [col=0,  row=0,  col_span=2,  row_span=12]
  Smart_Narrative[col=2,  row=0,  col_span=8,  row_span=1]
  Detail_Matrix  [col=2,  row=1,  col_span=8,  row_span=11]
  ActionPanel    [col=10, row=1,  col_span=2,  row_span=11]
```

---

## Component 1: Slicer Pane (Left Sidebar)

**Purpose:** Context switch — filter Detail Matrix and Action Panel simultaneously

```
┌──────────────┐
│ FILTERS      │  ← heading_3 (lg) — "FILTERS" or "Context"
├──────────────┤
│ TIME PERIOD  │  ← table_header (sm, muted)
│ [Oct 2025 ▾] │  ← slicer control
│              │
│ REGION       │
│ [▢] All      │
│ [▣] DACH     │
│ [▢] Benelux  │
│ [▢] Nordics  │
│              │
│ SEGMENT      │
│ [B2C  ▾]     │
│              │
│ ─────────── │
│ Clear all    │  ← link, neutral-400
└──────────────┘
```

**Rules:**
- Max 3 slicers (BPA rule + `ux_design_system §5.1`)
- Time period slicer always first
- Active selections highlighted (bold label or checked state)
- "Clear all" always visible

---

## Component 2: Smart Narrative

**Purpose:** 1-sentence context summary — what does the current filter state mean?

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Net Sales of €38.1M is -€4.2M (-10%) vs Plan YTD,      │
│  primarily driven by DACH (-€3.1M) and adverse Mix.      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Typography:** `body` role (md), `neutral-700`, left-aligned, single paragraph
**Generation:** Auto-generated from active filter context + key KPI delta (Smart Narrative visual type in PBI), or authored text in `UseCase_Bracket.yaml`
**Max length:** 2 sentences, ~200 characters. Never wrap to more than 2 lines.

---

## Component 3: Detail Matrix

**Purpose:** Operative entity list — the records that explain the KPI gap

```
┌─────────────────────────────────────────────────────────────────────┐
│ Which regions and channels explain the revenue gap?  [Export ↓]     │  ← chart_title (md)
├────────────┬────────┬──────────┬──────┬───────────┬──────────────── ┤
│ Region     │ Sales  │ Δ Plan   │  Δ%  │ Margin%   │ Trend (12m)    │  ← table_header (sm)
├────────────┼────────┼──────────┼──────┼───────────┼──────────────── ┤
│ DACH       │ €18.2M │ -€3.1M   │ -15% │  17.2%    │ ╭──╮╮          │  ← table_cell (sm)
│            │        │ ████████ │[RED] │           │ ╯  ╰╯          │    data bar on Δ Plan
│ Benelux    │ €12.4M │  +€0.4M  │  +3% │  19.8%    │ ╭╮ ╭╮          │
│            │        │ ██       │[GRN] │           │ ╯╰─╯╰          │
│ Nordics    │  €8.1M │ -€0.2M   │  -2% │  21.1%    │ ──╮╭──         │
│            │        │ ██       │[AMB] │           │   ╰╯           │
│ CEE        │  €6.8M │ -€1.3M   │ -16% │  14.2%    │ ╮╭──╮╮         │
│            │        │ █████    │[RED] │           │ ╰╯  ╰╯         │
│ S. EU      │  €4.2M │ -€1.1M   │ -21% │  15.6%    │ ─╮╭╮           │
│            │        │ █████    │[RED] │           │  ╰╯╰           │
├────────────┴────────┴──────────┴──────┴───────────┴──────────────── ┤
│ Total      │ €49.7M │ -€5.3M           │  17.8%                     │  ← totals row
└─────────────────────────────────────────────────────────────────────┘
  Showing top 5 of 12 regions · Sorted by |Δ Plan| desc  [Show all]    ← caption (xs)
```

**Column anatomy:**

| Column | Required | Notes |
|---|---|---|
| Entity identifier | Yes | Region, customer, product, invoice — the grain |
| Primary KPI value | Yes | Absolute value with unit |
| Delta (absolute) | Yes | ±€ with data bar in same cell; signal-colored |
| Delta (%) | Yes | Signal-colored; direction icon (▲▼⚠─) |
| Secondary measure | Recommended | E.g., Margin %, Units, Conversion |
| Sparkline (mini trend) | Optional | 12-period mini trend; no labels |
| Action Code | Optional | T4 Phase 2; row-level recommended action |

**Data bar rule:** Delta columns use data bars (bar fills cell proportionally to magnitude). Positive bars: `semantic.positive`; negative bars: `semantic.negative`. Text value shown on top of bar.

**Sort:** Default descending by |Δ Plan| (worst gap first). User can re-sort by any column.

**Row limit:** Show top 10–50 rows by default. "Show all" or export for complete list. Never load all rows by default (performance + cognitive load).

---

## Component 4: Action Panel (T4 Only)

**Purpose:** Concrete prescription — what to do, who does it, when, and what impact is expected

```
┌──────────────────┐
│ ● RECOMMENDED    │  ← heading_3 (lg, semantic.positive or brand accent)
│   ACTION         │
├──────────────────┤
│ Reduce promo     │  ← body (md)
│ depth in DACH    │
│ to protect GM%   │
├──────────────────┤
│ Owner            │  ← table_header (sm, muted)
│ Commercial Mgr   │  ← body (md)
│ DACH             │
│                  │
│ Due              │
│ End of October   │
│                  │
│ Trigger          │
│ GM% < 17% AND    │
│ Δ Plan > -10%    │
├──────────────────┤
│ Expected Impact  │
│ +€1.2M GM        │  ← kpi_delta (md, semantic.positive)
│ +0.8pp margin    │
├──────────────────┤
│ Steps            │  ← table_header (sm, muted)
│ 1. Cap discount  │  ← body (md)
│    at 15%        │
│ 2. Review promo  │
│    calendar      │
│ 3. Alert buyer   │
│    DACH team     │
├──────────────────┤
│ [Mark Done]      │  ← action button (optional, Phase 2)
│ [Escalate]       │
└──────────────────┘
```

**Phase 1:** Content from `action_codes/*.yaml` at build time (static).
**Phase 2:** Content from semantic model `Action_Code` table (dynamic, row-level).

**Phase 1 YAML reference:**

```yaml
# core/action_codes/<code_id>.yaml
action_code: "AC-COM-001-DACH-PROMO"
trigger: "GM% < 17% AND Δ Plan > -10% for 2+ consecutive periods"
recommendation: "Reduce promotional depth in DACH to protect GM%"
owner_role: "Commercial Manager DACH"
due: "Within current month-end"
impact: "+€1.2M GM, +0.8pp margin"
steps:
  - "Cap promotional discounts at 15% max in DACH"
  - "Review and prioritise promotions by margin contribution"
  - "Alert DACH buying team to margin risk"
```

---

## T1/T2/T3 Detail Page (No Action Panel)

When the use case is not T4, the Action Panel is absent. The Detail Matrix expands to fill the full content area:

```
Col:  0──2   2──────────────────────12
      │                               │
 R0 ──┤  │  Smart_Narrative (10 LU)   │
      │  S ─────────────────────────  │
      │  L                            │
      │  I  Detail_Matrix (10 LU × 11)│
      │  C  ─────────────────────     │
      │  E  ... (same structure)      │
      │  R                            │
 R11 ─┤  │                            │
      └───────────────────────────────┘

Slot grid positions:
  Slicer_Pane    [col=0,  row=0,  col_span=2,  row_span=12]
  Smart_Narrative[col=2,  row=0,  col_span=10, row_span=1]
  Detail_Matrix  [col=2,  row=1,  col_span=10, row_span=11]
```

---

## Drillthrough Navigation

The Detail (300s) page is configured as a drillthrough target in PBI (`type: "Drillthrough"`, `visibility: "AlwaysVisible"`). This means:

1. It appears in the page navigation list as a normal page
2. It is also reachable via right-click → "Drill through" from Overview page visuals
3. Filter context (entity, time period) passes automatically on drillthrough
4. The reader sees the Detail Matrix pre-filtered to the entity they drilled from

Navigation marker shown in Smart Narrative: "Filtered to DACH · [Clear]"

---

## UseCase_Bracket.yaml Reference

300-second layer configured in `ux_layout_rules.page_2_execution.component_300s`:

```yaml
ux_layout_rules:
  page_2_execution:
    component_300s:
      evidence_grain: region             # Row level of the detail matrix
      evidence_columns:
        - region
        - sales.net_sales.amount
        - sales.net_sales.delta_abs.plan
        - sales.net_sales.delta_pct.plan
        - margin.gm.pct
      action_panel: true                 # T4 only
      payload_mode: full                 # Include all action code fields
```
