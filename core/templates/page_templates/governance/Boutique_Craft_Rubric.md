# Boutique-Craft Rubric — Authority & Reference (K1)

> **Authority:** Governs the machine-readable rubric
> [`tokens/boutique_craft_rubric.yaml`](../tokens/boutique_craft_rubric.yaml). This is
> the **K1 artifact** of the report-quality concept
> ([`docs/plans/KONZEPT_REPORT_QUALITAET.md`](../../../../docs/plans/KONZEPT_REPORT_QUALITAET.md)): it turns
> the Craft-Core (§5) into a **versioned, checkable "Boutique bar"** and pins it to a
> concrete reference report (COM-002).
>
> **Renderer-agnostic.** The rubric scores the report **intent/design-spec**, not a
> format. The same bar applies to Power BI, Web and PDF renders — each at its own
> fidelity limit (Concept §3).
>
> **Shared IP — this repo is the source (A-35, 09.10.2026).** The YAML here holds the rules
> both tools share (statement, severity, weight, concept scope, `gilt_fuer`, thresholds,
> dimensions and weights). Meridian mirrors it (`Freelancing: meridian/vendor/aluca/visual_library`)
> and generates its own file (`meridian/design/boutique-craft-rubric.yaml`) from the mirror plus
> a tool overlay (`check`, `machine_hint`, `source`). A common field changes here, never there.
>
> **Status:** v1.1 · 2026-10-09 (v1.0 2026-07-10). Enforcement (structural checks + LLM-judge)
> is **K6**: 20 rules scored by the live scorecard, coverage 54.6 % of the 100-point rubric
> (measured 09.10.2026 with `tooling/report_quality/boutique_scorecard.py` and the spec-heuristic
> judge; 73.4 % under v1.0 — same rules scored, the new dimensions have no ALUCA validator yet).

---

## 1. What this rubric is for

The existing quality gate proves a report is *valid* (slot-grid, bindings, schema).
This rubric adds the missing axis: is it *excellent*? It is the operational form of
the Concept's Zielbild (§2) — the bar a report must clear to read as boutique-grade
rather than competent-standard.

It is **not** a new theory. It compresses the repo's own authorities
(`Storytelling_Principles.md`, `Layout_Grid_System.md`, `Color_Semantics_Formatting.md`,
IBCS/ISO 24896) into 30 rules across 6 dimensions, each with an ID, severity, weight
and a check-mode (`structural` = machine-checkable, `judge` = semi-automatic LLM +
human). Every rule cites its source in the YAML. Version 1.1 adds two IBCS-scoped rules
(`concept: ibcs`) and two dimensions from the Meridian Frontend-Mindeststandard
(`transparency`, `dataviz_base`, 16 rules): 48 rules across 8 dimensions.

## 2. Scoring model

- Each rule scored **0.0 / 0.5 / 1.0** at evaluation.
- `dimension_score` = weighted mean of its rules; `total_score_pct` = Σ (dimension_score
  × dimension.weight). Weights sum to 100.
- **PASS iff** `total_score_pct ≥ 70` **AND** `knock_out` violations = 0.

Dimension weights (chart-craft and narrative carry the most — that is where "wow"
lives), since v1.1: color 12 · typography 10 · layout 12 · **chart_craft 22** · **narrative 16** ·
brand 6 · transparency 10 · dataviz_base 12 (v1.0: 15 · 12 · 15 · 28 · 20 · 10).

**Design concepts and frontends (v1.1).** `concept: ibcs` scopes a rule to the IBCS notation,
`not_concept: ibcs` to every other; an out-of-scope rule is not applicable and its weight is
renormalised. `gilt_fuer` records per frontend whether a rule is `nativ`, met by a named
`ersatz`, or `entfaellt`. `thresholds` names the limits a statement uses (BC-LAYOUT-04:
≤5 KPI tiles per page **and** ≤7 elements per zone — the two former readings of ALUCA and
Meridian, both kept).

**Knock-outs (any one → automatic fail, regardless of score):**

| ID | Rule |
|---|---|
| BC-COLOR-02 | Colour used decoratively / to distinguish equal-rank categories |
| BC-CHART-01 | Mixed scale on one axis |
| BC-CHART-10 | Evidence table unsorted / no Top-N |
| BC-NARR-01 | Title carries the conclusion instead of describing it; key-message slot empty (rule reversed 08.10.2026, A-34 / IBCS UN 2.1/2.2 — before: title is a label, not a conclusion) |
| BC-BRAND-01 | Renderer default theme (no composed custom theme) |
| BC-DV-01 | Dual axis — two value scales on one plot (v1.1) |
| BC-DV-02 | Categorical palette not run through the palette validator (v1.1) |

## 3. Relationship to the existing gates

This rubric **extends**, does not replace:
- **Validity gate** (Stage-1, bindings, `report_quality.cli`) stays the floor — a report
  must be valid *before* it is scored for craft.
- **Scorecard gate** (Umsetzungsplan C3/R3.3) gains this craft axis in **K6**.
- Uniformity (slot-grid) remains normative — craft comes *on top*, never instead.

## 4. Reference exemplar — COM-002 scored against the bar (2026-07-10)

COM-002 (`core/usecases/core/COM-002_Margin_Price_Performance`) is the pilot and the
structurally strongest report in the set. Scoring it makes the bar concrete **and**
exposes the exact remaining gaps — which feed K2/K3/K4. Scored from the governed
`UseCase_Bracket.yaml` + PBIR state described in the Umsetzungsplan ledger (R1.1–R1.6);
`judge`-mode rules are marked *provisional* pending a real render (K7).

| Dimension | Score | Basis |
|---|---|---|
| color | ~0.8 | Semantic colours governed (`color_semantics.yaml`); one-accent discipline unverified (provisional) |
| typography | ~0.9 | `typography.yaml`: one family, **tabular numerals**, hero≥2× — strong |
| layout | ~0.9 | Slot-grid enforced, edges aligned, Zone-0 Big-Idea header present (R1.1) |
| chart_craft | ~0.7 | **Pass:** mixed-scale resolved (R1.4, BC-CHART-01), IBCS PVM waterfall vs_plan (Main_2, BC-CHART-02), curated worst-first Top-20 evidence (R1.3, BC-CHART-10). **Gap:** direct-labelling, reference lines, one-highlight unproven |
| narrative | **fail** | Governed `big_idea` + grounded Smart-Narrative (R1.2) are strong, **but** page/visual titles are **labels** ("Commercial Summary & Insights"), not conclusions → **BC-NARR-01 knock-out** |
| brand | ~0.7 | Custom theme registered, but recognisable cross-report identity not yet composed (BC-BRAND-01 borderline; see R3.1 theme conflict) |

**Verdict: COM-002 does not clear the Boutique bar today — it trips the BC-NARR-01
knock-out.** This is the honest, useful result: our *best* report is structurally
excellent yet still reads as standard because its titles describe instead of conclude,
and the craft finish (direct labels, reference lines, in-card sparklines/reference-
labels, deviation cell colour, a composed brand theme) is not yet emitted.

### 4.1 Gap → Cut mapping (what closes each)

| Gap on COM-002 | Rule(s) | Closed by |
|---|---|---|
| Titles are labels, not conclusions | BC-NARR-01 | **K2** — title-as-statement becomes a governed intent field (message → rendered title) |
| No in-card delta/sparkline, no deviation cell colour | BC-NARR-04, BC-CHART-02 | **K3** — Maximize Power BI (reference-labels, sparklines, DAX colour measure) |
| Direct labelling, reference lines, one-highlight | BC-CHART-03/05/07 | **K3** — native craft pass, schema-verified |
| Number lacks benchmark context | BC-NARR-04 | **K4** — Content-Grounding benchmark layer |
| No composed recognisable theme | BC-BRAND-01/02 | **K3** — brand theme across all 17 reports |

## 5. Change control

`rubric_version` bumps on any rule add/remove/severity change. The reference scorecard
(§4) is re-run whenever COM-002 is regenerated (K7 close-loop) and when the rubric
version changes. Weights and the 70 % threshold are **provisional** and confirmed in K6
after the first real render-based judge pass.
