# Full Page Sample: The Action Matrix (Detail — 300s)

> **Page type:** Detail  |  **Layer:** 300-second
> **Templates:** All (T1–T4); Action Panel only for T4
> **Reading pattern:** F-pattern
> **Use case example:** COM-001 Sales Performance (T2), T4 variant shown separately
> **Spec ref:** `layout_330300_design_spec.md §6.2`

---

## What This Page Answers

> *What exactly happened? Which entities explain the gap? What should I do next (T4)?*

---

## Variant A — T1/T2/T3 (No Action Panel)

```
Canvas: 1280×720 (design base)  |  Grid: 12 col × 12 row
Navigation: Detail (drillthrough target + direct access)

╔═══════════════════════════════════════════════════════════════════════════════╗
║ [Decision question banner]                                                    ║
║ "Which regions explain the revenue gap?"                          ← heading_3 ║
╠══╦════════════════════════════════════════════════════════════════════════════╣
║  ║ Smart_Narrative                                                [row 0]     ║
║S ║                                                                            ║
║L ║  Net Sales of €38.1M is -€4.2M (-10%) vs Plan YTD,                       ║
║I ║  primarily driven by DACH (-€3.1M) and adverse Mix effect.   ← body (md) ║
║C ╠════════════════════════════════════════════════════════════════╣            ║
║E ║ Detail_Matrix                         [rows 1–11]             [Export ↓]  ║
║R ║                                                                            ║
║  ║ Which regions explain the revenue gap?                        ← chart_title║
║P ╠══════════╦═════════╦══════════════════╦══════╦════════════╦══════════════╣ ║
║A ║ Region   ║ Sales   ║ Δ Plan           ║  Δ%  ║ Margin %  ║ 12m Trend   ║ ║
║N ╠══════════╬═════════╬══════════════════╬══════╬════════════╬══════════════╣ ║
║E ║ DACH     ║ €18.2M  ║ -€3.1M ████████ ║ -15% ║  17.2%    ║  ╮╭──       ║ ║
║  ║          ║         ║         [RED]    ║[RED] ║           ║  ╰╯         ║ ║
║  ╠══════════╬═════════╬══════════════════╬══════╬════════════╬══════════════╣ ║
║  ║ Benelux  ║ €12.4M  ║  +€0.4M ██      ║  +3% ║  19.8%    ║  ╭╮╭╮       ║ ║
║  ║          ║         ║          [GRN]   ║[GRN] ║           ║  ╯╰─╯       ║ ║
║  ╠══════════╬═════════╬══════════════════╬══════╬════════════╬══════════════╣ ║
║  ║ Nordics  ║  €8.1M  ║ -€0.2M ██       ║  -2% ║  21.1%    ║  ──╮╭──     ║ ║
║  ║          ║         ║         [AMB]    ║[AMB] ║           ║    ╰╯       ║ ║
║  ╠══════════╬═════════╬══════════════════╬══════╬════════════╬══════════════╣ ║
║  ║ CEE      ║  €6.8M  ║ -€1.3M █████    ║ -16% ║  14.2%    ║  ╮╭──╮      ║ ║
║  ║          ║         ║         [RED]    ║[RED] ║           ║  ╰╯  ╰      ║ ║
║  ╠══════════╬═════════╬══════════════════╬══════╬════════════╬══════════════╣ ║
║  ║ S. EU    ║  €4.2M  ║ -€1.1M █████    ║ -21% ║  15.6%    ║  ─╮╭╮       ║ ║
║  ║          ║         ║         [RED]    ║[RED] ║           ║   ╰╯╰       ║ ║
║  ╠══════════╩═════════╩══════════════════╩══════╩════════════╩══════════════╣ ║
║  ║ Total    ║ €49.7M  ║ -€5.3M           ║      ║  17.8%                  ║ ║
║  ╚══════════╩═════════╩══════════════════════════╩═════════════════════════╝ ║
║   Showing top 5 of 12 regions · Sorted by |Δ Plan| desc · [Show all]         ║
╚══╩════════════════════════════════════════════════════════════════════════════╝

Grid positions:
  Slicer_Pane    [col=0,  row=0, col_span=2, row_span=12]
  Smart_Narrative[col=2,  row=0, col_span=10, row_span=1]
  Detail_Matrix  [col=2,  row=1, col_span=10, row_span=11]
```

---

## Variant B — T4 Prescriptive (With Action Panel)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║ "What should we do about the DACH margin gap?"                    ← heading_3 ║
╠══╦═══════════════════════════════════════════════════╦══════════════════════╣
║  ║ Smart_Narrative                                   ║ ACTION PANEL         ║
║S ║  Net Sales -€4.2M vs Plan in DACH. GM% 17.2%,    ║                      ║
║L ║  below 18% threshold — action triggered.          ║  ● RECOMMENDED       ║
║I ╠═══════════════════════════════════════════════════╣  ACTION              ║
║C ║ Detail_Matrix                        [rows 1–11]  ║                      ║
║E ║                                                   ║  Reduce promo        ║
║R ╠════════════╦═════════╦══════════════╦══════╦══════╣  depth in DACH       ║
║  ║ Region     ║ Sales   ║ Δ Plan       ║  Δ%  ║ GM%  ║  to protect GM%      ║
║P ╠════════════╬═════════╬══════════════╬══════╬══════╣  ──────────────      ║
║A ║ DACH       ║ €18.2M  ║ -3.1M ██████║ -15% ║17.2% ║  Owner               ║
║N ║            ║         ║        [RED] ║[RED] ║[RED] ║  Comm Mgr DACH       ║
║E ╠════════════╬═════════╬══════════════╬══════╬══════╣  ──────────────      ║
║  ║ Benelux    ║ €12.4M  ║  +0.4M ██   ║  +3% ║19.8% ║  Due                 ║
║  ║            ║         ║        [GRN] ║[GRN] ║      ║  End October         ║
║  ╠════════════╬═════════╬══════════════╬══════╬══════╣  ──────────────      ║
║  ║ Nordics    ║  €8.1M  ║ -0.2M ██    ║  -2% ║21.1% ║  Impact              ║
║  ║            ║         ║        [AMB] ║[AMB] ║[GRN] ║  +€1.2M GM           ║
║  ╠════════════╬═════════╬══════════════╬══════╬══════╣  +0.8pp margin       ║
║  ║ CEE        ║  €6.8M  ║ -1.3M ████  ║ -16% ║14.2% ║  ──────────────      ║
║  ║            ║         ║        [RED] ║[RED] ║[RED] ║  Steps               ║
║  ╠════════════╬═════════╬══════════════╬══════╬══════╣  1. Cap at 15%       ║
║  ║ S. EU      ║  €4.2M  ║ -1.1M ████  ║ -21% ║15.6% ║  2. Review calendar  ║
║  ╚════════════╩═════════╩══════════════╩══════╩══════╣  3. Alert buyer      ║
║   Top 5 of 12 · |Δ Plan| desc · [Show all]            ║                      ║
╚══╩═══════════════════════════════════════════════════╩══════════════════════╝

Grid positions:
  Slicer_Pane    [col=0,  row=0, col_span=2,  row_span=12]
  Smart_Narrative[col=2,  row=0, col_span=8,  row_span=1]
  Detail_Matrix  [col=2,  row=1, col_span=8,  row_span=11]
  ActionPanel    [col=10, row=0, col_span=2,  row_span=12]
```

---

## F-Pattern Reading Flow

The eye follows the F-pattern through this page:

```
Step 1 (top scan):   Smart Narrative — what is happening right now?
Step 2 (left scan):  Slicer pane — what context is active?
Step 3 (table rows): Detail Matrix — scan row by row down the left column
                     Eye stops at red cells, large data bars — the problem rows
Step 4 (right):      Action Panel (T4) — what should I do?
```

Column order in the Detail Matrix reinforces F-pattern: entity name (left, always visible) then values, then deltas (signal-critical), then secondary measures, then sparklines (rightmost, least critical).

---

## Interaction Notes

| Interaction | Behaviour |
|---|---|
| Arrive from drillthrough | Filter context from Overview page pre-applied; slicer shows active selection |
| Arrive directly | No filter; full entity list shown |
| Change slicer | Detail Matrix + Smart Narrative + Action Panel refresh |
| Click row in Matrix | Option to drill to next grain (if configured) |
| Click "Export ↓" | Downloads filtered view as CSV/Excel |
| Click "Show all" | Loads full entity list (paginated) |
| Click "[Mark Done]" (T4) | Phase 2 only — updates action status in model |

---

## Narrative Annotation

### Variant A — T1/T2/T3 (No Action Panel)

```
F-Pattern reading path — annotated (Variant A):

→ Step 1 (top scan): Smart Narrative
  ACT 3 — RESOLUTION OPENING. "Here is what is happening in this context."
  "Net Sales of €38.1M is -€4.2M (-10%) vs Plan YTD, primarily driven by DACH (-€3.1M)."
  The Big Idea for this filter context. Quantified. Present tense. No hedging.
  Reader arrives knowing the answer before looking at the table.

↓ Step 2 (left column): Slicer Pane
  CONTEXT CONTROL. Time, Region, Segment.
  User sees their active filter (DACH) is already pre-set from the drillthrough.
  Slicer is sidebar — consistent with F-pattern: controls on the left, data on the right.

↓ Step 3 (table scan — left column first):
  ENTITY IDENTIFICATION. Region column anchors each row.
  Eye reads: DACH → Benelux → Nordics → CEE → S.EU
  The leftmost column is always the entity name — this is the F-pattern anchor.

→ Step 4 (horizontal scan per row):
  DELTA READING. Δ Plan column with data bars.
  Eye moves right: €18.2M → -€3.1M [RED ████████]
  Data bars make the relative magnitudes visible without reading numbers.
  Red rows attract eye via pre-attentive color — DACH and CEE stop the scan.

→ Step 5 (rightmost column): 12m Trend sparklines
  MOMENTUM. Brief inline trend per entity.
  DACH sparkline shows declining curve — confirms the Smart Narrative.
  Rightmost column = least critical; user reads only if they want context.
```

**The F-path tells the complete 300s story:** "DACH and CEE explain the gap (Smart Narrative) → worst entities first (sorted table) → DACH is declining not just behind (sparkline)."

### Variant B — T4 (With Action Panel)

```
F + Right-Anchor path — annotated (Variant B):

→ Same F-pattern as Variant A for left portion

→ Right anchor (Action Panel — always visible from page load):
  ACT 3 — RESOLUTION COMPLETE. "Here is what to do."
  Action Panel is RIGHT-side, full height — visible immediately on page load.
  The reader can decide BEFORE reading the table.
  This is the critical T4 design principle: recommendation leads, evidence follows.

  Panel reading order:
  1. "Reduce promo depth in DACH" — directive, 5 words, immediately actionable
  2. "Owner: CM DACH" — who
  3. "Due: EOM" — when
  4. "Impact: +€1.2M GM" — what we get
  5. Steps 1–3 — how
  Reader spends <10 seconds on the panel to reach a decision.
```

---

## Big Idea Verification

### Variant A (T2 Detail)
After arriving from drillthrough on DACH, the reader should state within 15 seconds:

> *"DACH is -€3.1M vs Plan. CEE is also significantly off. Mix and volume are the primary drivers. I know where to intervene."*

### Variant B (T4 Detail)
After arriving, the reader should state within 10 seconds:

> *"I need to reduce promo depth in DACH by end of month. Owner: CM DACH. Impact: +€1.2M. Here are the accounts to target."*

If either statement requires more than the stated time, the layout or content has failed.

---

## Content Quality Checklist (Action Matrix)

- [x] Smart Narrative is quantified, ≤2 sentences, present tense
- [x] Smart Narrative answers Big Idea for current filter context (not generic)
- [x] Detail Matrix sorted by |Δ Plan| descending (worst entities first)
- [x] Entity column is leftmost (F-pattern anchor)
- [x] Delta columns have data bars
- [x] Sparklines in rightmost column only (optional, decorative context)
- [x] Slicer pane on left sidebar (F-pattern: controls on left)
- [x] "Show all" and "Export" controls present but non-prominent
- [x] Action Panel (Variant B): all mandatory fields populated (title, owner, due, impact, steps)
- [x] Action Panel (Variant B): right-side anchor, full height, visible on load
- [x] Drillthrough filter context pre-applied (slicer shows active selection)

---

## Page Configuration

| Property | Value |
|---|---|
| Page type | Detail (300s) |
| Visibility | AlwaysVisible |
| Page nav type | Drillthrough |
| Filter context | Passed from drillthrough source |
| Display option | FitToPage |
| Canvas (design) | 1280×720 |
| Canvas (production) | 1920×1080 |
