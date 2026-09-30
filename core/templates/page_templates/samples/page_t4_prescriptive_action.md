# Full Page Sample: T4 — Prescriptive Recommendation (Full Action Layout)

> **Page type:** Detail | **Layer:** 3-second + 30-second + 300-second (combined)
> **Template:** T4 Prescriptive Recommendation — Full action panel
> **Reading pattern:** F-pattern (left = slicer + data; right = action)
> **Use case example:** COM-002 Promotional Effectiveness & Margin Recovery
> **Spec ref:** `Design_Spec_3_30_300.md §6.2` · `page_types/T4_Prescriptive_Recommendation.md`

---

## The Big Idea

> "GM% in DACH has been below the 18% threshold for 3 consecutive months due to excessive promotional depth. Recommended: cap promotional discounts at 15% — expected recovery of +0.8pp GM% by end of October, owned by Commercial Manager DACH."

The Big Idea is a **commitment**, not an observation. The action, the owner, and the expected impact are all present before the reader looks at a single chart.

---

## What This Page Answers

| Layer | Question | Element |
|---|---|---|
| 3s | "What is the recommended action?" | Action Panel header + KPI trigger context |
| 30s | "Why this action and why now?" | Trigger trend + affected entities |
| 300s | "Which accounts / entities validate this?" | Detail Matrix |
| — | "What exactly should I do?" | Action Panel steps |

---

## Complete Page Wireframe

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row
Navigation: Detail page (drillthrough target + direct access)
Decision question: "What should we do to recover GM% in DACH?"

╔══╦══════════════════════════════════════════════════╦═══════════════╗
║  ║ DECISION QUESTION                                ║               ║
║  ║ "What should we do to recover GM% in DACH?"     ║               ║
║  ╠══════════════════════════════════════════════════╣               ║
║  ║ Smart_Narrative                      [row 1]    ║ ● RECOMMENDED ║
║  ║                                                  ║   ACTION      ║
║S ║  "GM% in DACH is at 16.9%, -1.1pp below the    ║               ║
║L ║   18% threshold for the 3rd consecutive month.  ║ Cap promo     ║
║I ║   Primary driver: promotional depth at 22%      ║ depth in DACH ║
║C ║   vs 15% target. Action triggered."             ║ to ≤15%       ║
║E ╠══════════════════════════════════════════════════╣               ║
║R ║ Impact-Evidence Visuals         [rows 2–6]      ║ ─────────     ║
║  ║                                                  ║ WHY           ║
║P ║ ┌─────────────────────┐  ┌──────────────────┐   ║               ║
║A ║ │ How has GM% trended │  │ Which accounts   │   ║ GM% at 16.9%, ║
║N ║ │ vs 18% threshold in │  │ drive the promo  │   ║ below 18% for ║
║E ║ │ DACH (6 months)?    │  │ depth issue most? │   ║ 3 months.     ║
║  ║ │                     │  │                  │   ║ Depth: 22%    ║
║  ║ │ %                   │  │ Acct A ■■■■  24% │   ║ vs 15% target.║
║  ║ │ 20─────────         │  │ Acct B ■■■   22% │   ║               ║
║  ║ │ 18─ - - ─[Target]   │  │ Acct C ■■■   21% │   ║ ─────────     ║
║  ║ │ 17    ╭──╮           │  │ Acct D ■■    19% │   ║ OWNER         ║
║  ║ │ 16   ╭╯   ╰──╮       │  │ Acct E ■■    18% │   ║ Comm Mgr DACH ║
║  ║ │ 15  ╭╯         ╰──   │  │                  │   ║               ║
║  ║ │ ────────────────      │  │ [col=5, row=2,   │   ║ DUE           ║
║  ║ │ Oct Nov Dec Jan Feb   │  │  col_span=4,     │   ║ End October   ║
║  ║ │                       │  │  row_span=5]     │   ║               ║
║  ║ │ [col=1, row=2, 4×5]   │  └──────────────────┘   ║ ─────────     ║
║  ║ └─────────────────────┘                           ║ IMPACT        ║
║  ╠══════════════════════════════════════════════════╣ +0.8pp GM%    ║
║  ║ Detail Matrix                    [rows 7–11]     ║ +€1.2M margin ║
║  ║                                                  ║               ║
║  ║ Which DACH accounts explain the GM% shortfall?   ║ ─────────     ║
║  ╠═══════════╦══════════╦══════════╦═══════╦════════╣ STEPS         ║
║  ║ Account   ║ GM%      ║ Δ Target ║ Promo ║ Action ║               ║
║  ╠═══════════╬══════════╬══════════╬═══════╬════════╣ 1. Cap at 15% ║
║  ║ Acct A    ║ 14.2%    ║ -3.8pp██ ║  24%  ║ → Cap  ║               ║
║  ║ Acct B    ║ 15.1%    ║ -2.9pp██ ║  22%  ║ → Cap  ║ 2. Renegotiate║
║  ║ Acct C    ║ 16.8%    ║ -1.2pp█  ║  21%  ║ → Cap  ║    rebates    ║
║  ║ Acct D    ║ 17.4%    ║ -0.6pp   ║  19%  ║ →Monitor║              ║
║  ║ Acct E    ║ 18.3%    ║ +0.3pp   ║  18%  ║ ✓ OK   ║ 3. Alert CM   ║
║  ╚═══════════╩══════════╩══════════╩═══════╩════════╣               ║
║  ║ 5 of 23 DACH accounts · Sorted by |Δ Target|    ║ PRIORITY      ║
║  ║ [Show all]                          [Export ↓]  ║ HIGH          ║
╚══╩══════════════════════════════════════════════════╩═══════════════╝

Grid slot summary:
  Decision banner      [col=1, row=0,  col_span=9,  row_span=1]
  Slicer_Pane          [col=0, row=0,  col_span=1,  row_span=12]
  Smart_Narrative      [col=1, row=1,  col_span=9,  row_span=1]
  Main_1 (Trend)       [col=1, row=2,  col_span=4,  row_span=5]
  Main_2 (Ranking)     [col=5, row=2,  col_span=5,  row_span=5]
  Detail_Matrix        [col=1, row=7,  col_span=9,  row_span=5]
  ActionPanel          [col=10, row=0, col_span=2,  row_span=12]
```

---

## Narrative Annotation

```
F-Pattern + Right-Anchor reading flow:

→ Step 1 (top scan, left to right): Decision question + Smart Narrative
  "What do I do? — [READS] — DACH GM% at 16.9%, below threshold for 3 months."
  CONTEXT SET. The reader knows the situation before seeing the charts.

→ Step 2 (right anchor — Action Panel): "Cap promo depth in DACH to ≤15%"
  RECOMMENDATION VISIBLE. The answer is on screen before diving into evidence.
  The reader can decide immediately; charts provide confidence, not the decision.

↓ Step 3 (left column scan):
  Trend chart: "When? Declining for 3 months — trend is accelerating."
  Ranking: "Who? Top 5 accounts — Acct A most severe at 24% promo depth."

↓ Step 4 (detail matrix): "Which accounts need intervention?"
  ActionCode column guides per-account response: "Cap" / "Monitor" / "OK"
  Sorted worst first — the reader knows where to act without reading all rows.

→ Step 5 (right, Action Panel body): Steps, owner, due, impact
  COMMITMENT. The reader decides and knows exactly what happens next.
```

**Key T4 design insight:** The Action Panel must be **visible immediately** on page load — not reached after scrolling through evidence. The recommendation leads; evidence follows. This is the opposite of a presentation deck where you build to the punchline. In analytics, the punchline is first.

---

## Big Idea Verification

After 10 seconds on this page, a decision owner should be able to state:

1. What is the recommended action?
2. Who owns it?
3. When is it due?
4. What is the expected impact?

If any of the four cannot be answered without reading the charts, the Action Panel design has failed.

---

## Action Panel Copy Standards (T4)

The panel shown above uses these copy principles:

| Field | Principle | Applied |
|---|---|---|
| Title | Directive verb phrase, 3–5 words | "Cap promo depth in DACH to ≤15%" |
| WHY | Quantified trigger, 2 sentences max | "GM% at 16.9%, -1.1pp below 18% threshold for 3 months. Promo depth at 22% vs 15% target." |
| OWNER | Role, not name | "Comm Mgr DACH" |
| DUE | Specific date or cycle | "End October" |
| IMPACT | Quantified outcome | "+0.8pp GM% / +€1.2M margin" |
| STEPS | Ordered directives, max 3 | "1. Cap at 15% / 2. Renegotiate rebates / 3. Alert CM" |
| PRIORITY | One of: High / Medium / Low | "HIGH" |

---

## Detail Matrix Column Order (T4)

Column order for the T4 Detail Matrix follows F-pattern + decision relevance:

```
1. Entity name          — who (leftmost, always visible)
2. Current KPI value    — where we stand
3. Delta vs target      — how far out of bounds (+ data bar)
4. Root driver value    — what is causing it (promo depth %)
5. Action code          — what to do for this entity (optional Phase 2)
```

The `Action` column appears on T4 only, populated from Action Code YAML rules. It reduces operational complexity: the reader scans left-to-right and the last column tells them the answer per entity.

---

## UseCase_Bracket.yaml Reference

```yaml
ux_layout_rules:
  report_structure: "2-Page-Lead"
  page_1_summary:
    template_type: "T4"
    decision_question: "What should we do to recover GM% in DACH?"
    component_3s:
      kpi_cards:
        - kpi_id: KPI-COM-013
          filter: "region == 'DACH'"
          status_logic: "higher_is_better"
          comparison: "vs_target"
          target_value: 0.18
    component_30s:
      - slot: "Main_1"
        visual_type: line_chart
        kpi_id: KPI-COM-013
        filter: "region == 'DACH'"
        reference_line: "target"
        time_window: "rolling_6m"
      - slot: "Main_2"
        visual_type: bar_chart_horizontal
        kpi_id: margin.promo_depth_pct
        filter: "region == 'DACH'"
        segment_by: account
        sort_by: "value DESC"
        top_n: 10
    component_300s:
      detail_matrix:
        grain: account
        filter: "region == 'DACH'"
        columns:
          - field: account_name
          - field: KPI-COM-013
          - field: margin.gm.delta_target
            data_bars: true
          - field: margin.promo_depth_pct
          - field: action_code_label    # Phase 2 — from Action Code table
        sort_by: "margin.gm.delta_target ASC"
    action_panel:
      enabled: true
      action_code_ids: ["AC-COM-001"]
      trigger_condition: "KPI-COM-013 < 0.18 AND consecutive_periods >= 3"
```

---

## Content Quality Checklist (T4)

- [x] Big Idea constructable in one sentence including action, owner, impact, deadline
- [x] Action Panel visible immediately — top-right, full height
- [x] Action Panel has all mandatory fields: title, WHY, OWNER, DUE, IMPACT, STEPS, PRIORITY
- [x] Action title uses directive verb (not "consider..." or "review...")
- [x] IMPACT is quantified (not "improves performance")
- [x] Smart Narrative names the trigger condition and quantifies the deviation
- [x] Detail Matrix sorted by decision relevance (worst delta first)
- [x] Detail Matrix includes action direction per entity (Phase 2) or action code reference
- [x] Trend uses a window that shows the trigger pattern clearly (6m = 3 months below threshold)
- [x] No variance bridge (that is T2 content — why are we below? is handled in T2, not T4)
- [x] Decision question is specific to the action, not generic
