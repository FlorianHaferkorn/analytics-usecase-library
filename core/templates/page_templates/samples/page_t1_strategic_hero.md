# Full Page Sample: T1 — Strategic Overview (Hero Layout)

> **Page type:** Overview | **Layer:** 3-second + 30-second
> **Template:** T1 Strategic Overview — Hero Layout (1 dominant KPI, 2 context charts)
> **Reading pattern:** Z-pattern
> **Use case example:** FIN-001 Group Financial Performance
> **Spec ref:** `layout_330300_design_spec.md §6.1` · `page_types/T1_Strategic_Overview.md`

---

## The Big Idea

> "Group EBITDA margin is below the 15% strategic threshold for the third consecutive quarter — cost efficiency programme acceleration is required."

This sentence is the narrative anchor. Every element on the page supports, contextualizes, or validates it.

---

## What This Page Answers

| Layer | Question | Element |
|---|---|---|
| 3s | "Are we on track strategically?" | Hero KPI band |
| 30s | "What is the strategic trajectory?" | Trend chart |
| 30s | "How is the portfolio positioned?" | Portfolio comparison |
| — | 300s is explicitly out of scope for T1 | — |

---

## Complete Page Wireframe

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row
Navigation: Overview (Z-pattern reading)
Decision question: "Are we meeting our strategic targets this quarter?"

╔═══════════════════════════════════════════════════════════════════════╗
║ DECISION QUESTION BANNER                                [heading_3]  ║
║ "Are we meeting our strategic targets this quarter?"                 ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 1 — 3 SECONDS  [row 0–2, col 0–12]                               ║
║                                                                       ║
║ ┌──────────────────────────┐  ┌────────────────┐  ┌────────────────┐ ║
║ │                          │  │                │  │                │ ║
║ │  EBITDA MARGIN           │  │  REVENUE       │  │  NET INCOME    │ ║
║ │                          │  │                │  │                │ ║
║ │         13.8%            │  │    €218.4M     │  │    €24.1M      │ ║
║ │                          │  │                │  │                │ ║
║ │    ▼ -1.2pp  [RED]       │  │  ▲ +4.8% [GRN] │  │ ▼ -8.3% [RED] │ ║
║ │    vs 15% target         │  │  vs PY         │  │  vs PY         │ ║
║ │                          │  │                │  │                │ ║
║ │  ╭──────────────────╮    │  │ ▬▬▬▬▬▬▬▬▬▬▬▬  │  │ ▬▬▬▬▬▬▬▬▬▬▬▬  │ ║
║ │  │  ▬▬▬╮╭▬▬╮╰▬▬▬▬ │    │  │                │  │                │ ║
║ │  ╰──────────────────╯    │  │                │  │                │ ║
║ │   [HERO — 4 LU wide]     │  │ [2 LU wide]    │  │ [2 LU wide]    │ ║
║ └──────────────────────────┘  └────────────────┘  └────────────────┘ ║
║                                                                       ║
║   NOTE: Hero card occupies col 0–4 (4 LU). KPI 2+3 at col 5–8.      ║
║   Right 4 LU (col 8–12) reserved for strategic signal callout.       ║
║                                                                       ║
║   ┌────────────────────────────┐                                      ║
║   │ ⚠ STRATEGIC SIGNAL         │  col 8–12, row 0–2                   ║
║   │                            │                                      ║
║   │ "EBITDA margin below 15%   │                                      ║
║   │  threshold for Q3 — cost   │                                      ║
║   │  review recommended."      │                                      ║
║   └────────────────────────────┘                                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 2 — FILTER  [row 3, col 0–12]                                    ║
║                                                                       ║
║ ┌──────────────────────────┐   ┌───────────────────────────┐          ║
║ │ Period: [Q3 2025 YTD ▾]  │   │ Business Unit: [All    ▾] │          ║
║ └──────────────────────────┘   └───────────────────────────┘          ║
╠═══════════════════════════════════════════════════════════════════════╣
║ ZONE 3 — 30 SECONDS  [row 4–11, col 0–12]                             ║
║                                                                       ║
║ ┌───────────────────────────────────────┐  ┌───────────────────────┐  ║
║ │                                       │  │                       │  ║
║ │ How has EBITDA margin developed       │  │ Which business units  │  ║
║ │ vs the 15% target over 3 years?       │  │ are on and off track? │  ║
║ │                                       │  │                       │  ║
║ │  %                                    │  │ BU Alpha   ▓▓▓▓▓▓  16.2%│ ║
║ │ 18 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │  │ BU Beta    ▓▓▓▓    14.1%│ ║
║ │ 16         ╭──╮                       │  │ BU Gamma   ▓▓▓     12.8%│ ║
║ │ 15 - - - - ┼ -╯╮- - - - - [Target]  │  │ BU Delta   ▓▓      11.4%│ ║
║ │ 14        ╭╯    ╰──╮                  │  │ BU Epsilon ▓        9.2%│ ║
║ │ 13       ╭╯         ╰──╮              │  │                       │  ║
║ │ 12      ╭╯              ╰──           │  │           ─ 15% target│  ║
║ │  ────────────────────────────         │  │                       │  ║
║ │  Q1'23 Q2'23 Q3'23 Q4'23 Q1'24...    │  │ [col=7, row=4, 5×8]   │  ║
║ │                                       │  │                       │  ║
║ │  ── Actual    - - 15% Target          │  │ RED  = below 15%      │  ║
║ │  [col=0, row=4, col_span=7, row_span=8]│  │ GRN  = above 15%     │  ║
║ └───────────────────────────────────────┘  └───────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════╝

Grid slot summary:
  Decision banner      [col=0, row=0,  col_span=12, row_span=1]
  KPI_Cards Hero       [col=0, row=0,  col_span=4,  row_span=3]  Zone 1
  KPI_Card Revenue     [col=4, row=0,  col_span=2,  row_span=3]  Zone 1
  KPI_Card NetIncome   [col=6, row=0,  col_span=2,  row_span=3]  Zone 1
  Strategic Signal     [col=8, row=0,  col_span=4,  row_span=3]  Zone 1
  Slicer_Date          [col=0, row=3,  col_span=6,  row_span=1]  Zone 2
  Slicer_BU            [col=6, row=3,  col_span=6,  row_span=1]  Zone 2
  Main_1 (Trend)       [col=0, row=4,  col_span=7,  row_span=8]  Zone 3
  Main_2 (Portfolio)   [col=7, row=4,  col_span=5,  row_span=8]  Zone 3
```

---

## Narrative Annotation

```
Z-Pattern reading flow:

→ Step 1 (top-left): HERO KPI — "EBITDA margin 13.8% ▼ -1.2pp vs target"
                     FIRST CONTACT. Signal is immediate: RED. Below target.

→ Step 2 (top-right): Strategic Signal callout — "below threshold for Q3"
                       REINFORCES signal. Provides strategic framing.

↘ Step 3 (diagonal): Slicer bar — "Q3 2025 YTD, All BUs"
                      SETS CONTEXT. Confirms the scope is current.

→ Step 4 (left chart): Trend — "below target since Q2 2024, accelerating decline"
                        THE JOURNEY. When did it go wrong and is it getting worse?

→ Step 5 (right chart): Portfolio — "3 of 5 BUs below threshold"
                         THE SCOPE. Not isolated — systemic.
```

The Z-path tells a complete story: **"We have a problem (3s) → here for how long (30s) → here how widespread (30s)."**

---

## Big Idea Verification

After viewing this page for 30 seconds, an executive should be able to state:

> *"EBITDA margin is below the 15% strategic threshold. It has been declining for 5 quarters. 3 of 5 business units are affected. This requires strategic intervention."*

If this statement cannot be constructed from the page, the design has failed.

---

## T1 Hero Layout Variations

| Variation | When to use | Hero position |
|---|---|---|
| **Standard Hero (this sample)** | Single dominant outcome KPI + 2 context KPIs | col 0–4 (4 LU) |
| **Full-width Hero** | Board pack, single metric only | col 0–6 (6 LU), 1 KPI only |
| **Three Equal Cards** | 3 equally important strategic KPIs | col 0–4, 4–8, 8–12 each |

---

## UseCase_Bracket.yaml Reference

```yaml
ux_layout_rules:
  report_structure: "2-Page-Lead"
  page_1_summary:
    template_type: "T1"
    grid_template: "pulse"
    layout_variant: "hero"
    decision_question: "Are we meeting our strategic targets this quarter?"
    component_3s:
      hero_kpi:
        kpi_id: finance.ebitda.margin_pct
        visual_type: kpi_card_hero
        sparkline_field: "EBITDA_Margin_Quarterly"
        comparison: "vs_target"
        status_logic: "higher_is_better"
        target_value: 0.15
      supporting_kpis:
        - kpi_id: finance.revenue.amount
          comparison: "vs_py"
          status_logic: "higher_is_better"
        - kpi_id: finance.net_income.amount
          comparison: "vs_py"
          status_logic: "higher_is_better"
    strategic_signal:
      text_template: "{kpi_label} has been below threshold for {n} consecutive {periods}."
    component_30s:
      - slot: "Main_1"
        visual_type: line_chart
        kpi_id: finance.ebitda.margin_pct
        reference_line: "target"
      - slot: "Main_2"
        visual_type: bar_chart_horizontal
        kpi_id: finance.ebitda.margin_pct
        segment_by: business_unit
        reference_line: "target"
```

---

## Content Quality Checklist (T1)

- [x] Big Idea constructable in one sentence within 30 seconds
- [x] Hero KPI (strategic outcome) is the largest element and top-left
- [x] All KPI cards have a reference value (vs target or vs PY)
- [x] Visual titles are question-form
- [x] Max 2 slicers (period + business unit)
- [x] No operational data (no detail matrix, no exception list, no action steps)
- [x] Strategic callout uses directive language, not hedging
- [x] Z-pattern reading flows to the Big Idea
