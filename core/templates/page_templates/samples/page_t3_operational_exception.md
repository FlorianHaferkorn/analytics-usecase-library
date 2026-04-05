# Full Page Sample: T3 — Operational Monitoring (Exception Dashboard)

> **Page type:** Overview | **Layer:** 3-second + 30-second
> **Template:** T3 Operational Monitoring — Exception-first layout
> **Reading pattern:** F-pattern (exception list anchors the left column)
> **Use case example:** LOG-001 Order Backlog & SLA Compliance
> **Spec ref:** `layout_330300_design_spec.md §6.1` · `page_types/T3_Operational_Monitoring.md`

---

## The Big Idea

> "14 orders are currently breaching the 48-hour SLA threshold — 3 are critical (>72 hours) and require escalation to shift lead before next refresh."

This page is a **control panel**, not a performance summary. The reader acts — they do not analyze.

---

## What This Page Answers

| Layer | Question | Element |
|---|---|---|
| 3s | "Is execution under control right now?" | Exception count KPIs (traffic light) |
| 30s | "Which exceptions need attention now?" | Exception list (sorted by severity) |
| 30s | "Is the situation improving or worsening?" | Short-term trend |
| 30s | "Where is the concentration?" | Owner / team ranking |

---

## Complete Page Wireframe

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row
Navigation: Overview (F-pattern reading)
Decision question: "Where is execution currently outside operational thresholds?"

╔═══════════════════════════════════════════════════════════════════════╗
║ DECISION QUESTION BANNER                                [heading_3]  ║
║ "Where is execution currently outside operational thresholds?"       ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 1 — 3 SECONDS  [row 0–1, col 0–12]                               ║
║                                                                       ║
║ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  ║
║ │ OPEN         │ │ CRITICAL     │ │ SLA          │ │ AVG DELAY    │  ║
║ │ EXCEPTIONS   │ │ (>72h)       │ │ COMPLIANCE   │ │              │  ║
║ │              │ │              │ │              │ │              │  ║
║ │     14       │ │      3       │ │    91.2%     │ │   +6.4h      │  ║
║ │              │ │              │ │              │ │              │  ║
║ │  ▲ +4 [RED]  │ │  ▲ +2 [RED] │ │  ▼ -2.1pp   │ │  ▲ +1.2h     │  ║
║ │  vs prior    │ │  vs prior    │ │  [RED]       │ │  [RED]       │  ║
║ │  refresh     │ │  refresh     │ │  vs 95% SLA  │ │  vs 4h avg   │  ║
║ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 2 — FILTER  [row 2, col 0–12]                                    ║
║                                                                       ║
║ ┌────────────────────────┐  ┌──────────────────────┐                  ║
║ │ Date: [Today (Live) ▾] │  │ Team: [All Teams  ▾] │                  ║
║ └────────────────────────┘  └──────────────────────┘                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 3 — 30 SECONDS  [row 3–11, col 0–12]                             ║
║                                                                       ║
║ ┌──────────────────────────────────────────┐  ┌──────────────────────┐║
║ │ Which orders are currently breaching     │  │ How has exception    │║
║ │ the 48-hour SLA threshold?               │  │ count trended (30d)? │║
║ │                                          │  │                      │║
║ │ ● Order #   ● Severity ● Delay ● Team   │  │  n                   │║
║ │ ──────────────────────────────────────── │  │ 20                   │║
║ │ ORD-8821  ■ CRITICAL  +74h  Shift-A     │  │    ╮                 │║
║ │ ORD-9043  ■ CRITICAL  +68h  Shift-B     │  │ 15 │                 │║
║ │ ORD-7714  ■ CRITICAL  +51h  Shift-A     │  │    ╰─╮   ╭──         │║
║ │ ORD-8890  ⚠ WARNING   +44h  Shift-C     │  │ 10   ╰───╯           │║
║ │ ORD-9102  ⚠ WARNING   +41h  Shift-B     │  │                      │║
║ │ ORD-7823  ⚠ WARNING   +38h  Shift-A     │  │  5                   │║
║ │ ORD-8654  ⚠ WARNING   +35h  Shift-C     │  │  ────────────────    │║
║ │ ORD-9201  ⚠ WARNING   +31h  Shift-B     │  │  01 08 15 22 29 Apr  │║
║ │ ORD-8341  ℹ INFO      +12h  Shift-A     │  │                      │║
║ │ ORD-8902  ℹ INFO      +11h  Shift-C     │  │ [col=8, 4×8]         │║
║ │ ORD-7990  ℹ INFO       +9h  Shift-B     │  └──────────────────────┘║
║ │ ──────────────────────────────────────── │  ┌──────────────────────┐║
║ │ Showing 11 of 14 · Sorted by delay desc  │  │ Which team has most  │║
║ │ [Show all 14]                [Export ↓]  │  │ open exceptions?     │║
║ │                                          │  │                      │║
║ │ [col=0, row=3, col_span=8, row_span=9]   │  │ Shift-A  ■■■■■■  6   │║
║ └──────────────────────────────────────────┘  │ Shift-B  ■■■■    4   │║
║                                               │ Shift-C  ■■■     3   │║
║                                               │ Shift-D  ■       1   │║
║                                               │                      │║
║                                               │ [col=8, 4×4]         │║
║                                               └──────────────────────┘║
╚═══════════════════════════════════════════════════════════════════════╝

Grid slot summary:
  Decision banner      [col=0, row=0,  col_span=12, row_span=1]
  KPI_Cards (4 cards)  [col=0, row=0,  col_span=12, row_span=2]  Zone 1
  Slicer_Date          [col=0, row=2,  col_span=6,  row_span=1]  Zone 2
  Slicer_Team          [col=6, row=2,  col_span=6,  row_span=1]  Zone 2
  Main_1 (Exceptions)  [col=0, row=3,  col_span=8,  row_span=9]  Zone 3
  Main_2 (Trend)       [col=8, row=3,  col_span=4,  row_span=4]  Zone 3
  Main_3 (Ranking)     [col=8, row=7,  col_span=4,  row_span=5]  Zone 3
```

---

## Narrative Annotation

```
F-Pattern reading flow:

→ Step 1 (top scan): KPI band — "14 exceptions, 3 critical, SLA at 91.2%"
                     IMMEDIATE: Is anything on fire? Yes: 3 critical orders.

↓ Step 2 (left column): Exception list — sorted CRITICAL → WARNING → INFO
                          PRIORITIZATION: Who needs attention first?
                          Eye stops at RED rows automatically (pre-attentive color).
                          ORD-8821 → +74 hours → Shift-A → call Shift-A lead NOW.

→ Step 3 (right, top): Trend — "exceptions spiked 3 weeks ago, slightly recovering"
                        PATTERN: Is this a one-time spike or ongoing deterioration?

→ Step 4 (right, bottom): Ranking — "Shift-A has 6 of 14 exceptions"
                            CONCENTRATION: Where should attention focus?
```

The F-pattern is intentional: the exception list dominates the left 8 columns because that is where 80% of the user's viewing time lands. Trend and ranking provide context but do not compete for primary attention.

---

## Exception List Design — Column Order

```
■ Severity  |  Order #  |  Delay  |  Team   |  Age (days)  |  Status
```

Column order rationale (F-pattern + importance):
1. **Severity icon** (leftmost) — pre-attentive signal; eye stops at red before reading
2. **Order #** — entity identifier, anchors the row
3. **Delay** — the key metric: how far outside threshold?
4. **Team** — who is responsible?
5. **Age** — secondary context; how long has this been open?

Conditional formatting:
- Critical row background: light red (#FFE6E6)
- Warning row background: light amber (#FFF9E6)
- Info row: white (no highlight — informational only)

---

## Big Idea Verification

After viewing this page for 15 seconds, an operational manager should be able to:

1. State the number of critical exceptions
2. Identify the most delayed order and which team owns it
3. Know whether the situation is improving or worsening

If any of these three cannot be answered within 15 seconds, the design has failed.

---

## KPI Card Design for T3

T3 exception-count KPIs differ from outcome KPIs:

```
[OPEN EXCEPTIONS]     ← label: what category of exception
[14]                  ← hero value: count (not revenue, not %)
[▲ +4 since last]    ← delta: change since last refresh (not vs target)
[vs prior refresh]    ← reference: temporal comparison, operational cadence
```

For T3, the delta reference is **operational** (vs prior refresh, vs yesterday) not **strategic** (vs plan, vs PY). The signal direction must be configured correctly:
- For exception counts: `status_logic: "lower_is_better"` → more exceptions = red
- For SLA compliance: `status_logic: "higher_is_better"` → lower compliance = red

---

## UseCase_Bracket.yaml Reference

```yaml
ux_layout_rules:
  report_structure: "2-Page-Lead"
  page_1_summary:
    template_type: "T3"
    grid_template: "pulse"
    decision_question: "Where is execution currently outside operational thresholds?"
    component_3s:
      kpi_cards:
        - kpi_id: ops.sla.exception_count
          status_logic: "lower_is_better"
          comparison: "vs_prior_refresh"
        - kpi_id: ops.sla.critical_count
          status_logic: "lower_is_better"
          comparison: "vs_prior_refresh"
        - kpi_id: ops.sla.compliance_pct
          status_logic: "higher_is_better"
          comparison: "vs_target"
          target_value: 0.95
        - kpi_id: ops.sla.avg_delay_hours
          status_logic: "lower_is_better"
          comparison: "vs_prior_period_avg"
    component_30s:
      - slot: "Main_1"
        visual_type: table_with_databars
        exception_filter: "threshold_breached == true"
        sort_by: "delay_hours DESC"
        columns: [severity, order_id, delay_hours, team, age_days]
      - slot: "Main_2"
        visual_type: line_chart
        kpi_id: ops.sla.exception_count
        time_window: "rolling_30d"
      - slot: "Main_3"
        visual_type: bar_chart_horizontal
        kpi_id: ops.sla.exception_count
        segment_by: team
        sort_by: "value DESC"
```

---

## Content Quality Checklist (T3)

- [x] Zone 1 KPIs are exception counts and compliance rates — not revenue or margin
- [x] Exception list is the primary (largest) visual — col 0–8 of 12
- [x] Exception list sorted Critical first, then Warning, then Info
- [x] Each exception row has entity, severity, magnitude, and owner
- [x] Visual titles are question-form and operationally specific
- [x] Trend uses short window (30 days) — not 12-month strategic view
- [x] No variance bridge (that is T2 content)
- [x] No action steps or prescriptive content (that is T4 content)
- [x] Max 2 slicers (date + team)
- [x] F-pattern anchored by exception list on the left
