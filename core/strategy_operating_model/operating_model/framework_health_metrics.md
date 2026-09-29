# Framework Health Metrics

## Purpose

This document defines the measurable health indicators for the Analytics Use
Case Framework. These metrics answer: **"Is the framework production-ready?"**
and **"Where is quality declining or improving?"**

Framework health is not a one-time gate — it is a continuous quality signal.
Health metrics are tracked across releases and reviewed at each major version.

**Production-ready threshold:** All five core metrics must score ≥80%.

---

## Metric Overview

| # | Metric | Description | Target | Owner |
|---|--------|-------------|--------|-------|
| H1 | Golden Thread Coverage % | Strategic KPIs fully traceable from strategy to action | ≥90% | Framework Owner |
| H2 | Semantic Model Stability % | Measures with governance.status = active (not draft) | ≥80% | Domain Leads |
| H3 | Data Contract Coverage % | UseCase required_facts present in domain data contracts | ≥90% | Data Engineering |
| H4 | Action Code Completeness % | Action Codes with complete execution_bridge + impact_valuation | ≥80% | Domain Leads |
| H5 | Factsheet Quality Score | Average section completeness across core Business Factsheets | ≥80% | Business Owners |
| H6 | Prioritization & Readiness Coverage % | Use cases with both a prioritization and a readiness block | ≥80% | Framework Owner |
| H7 | Report Binding Integrity % | Generated report visual bindings that resolve to a defined TMDL measure | 100% | Data Engineering |
| H8 | AI-Readiness / Linguistic Coverage % | Governed synonyms in the linguistic schema (Copilot) + AI-surface hygiene (0 visible keys, 0 weak descriptions) | 100% | Data Engineering |

---

## H1 — Golden Thread Coverage %

**Definition:** The percentage of KPIs declared as "strategic" in
`core/strategy_operating_model/company/` that have unbroken traceability
across all five layers of the Golden Thread.

**Five layers of the Golden Thread (all must be present for a KPI to count):**

1. KPI exists in `core/kpi_catalog/KPI_Catalog.md`
2. KPI is referenced in at least one `UseCase_Bracket.yaml` (`required_kpi_ids`)
3. KPI has a corresponding measure in a `Measure_Dictionary_*.md` with `aggregation_method`
4. Measure's source table exists in a `core/data_contracts/domains/*.yaml`
5. At least one Action Code linked to the use case has the KPI in its `kpi_trigger_ids`

**Calculation:**

```
H1 = (KPIs with all 5 layers present) / (Total strategic KPIs) × 100
```

**How to check:**

Run `tooling/validation/check_action_codes_vs_kpi.ps1` and
`tooling/validation/check_factsheet_vs_kpi.ps1` and
`tooling/validation/check_data_contract_kpi_coverage.ps1` in sequence.
The union of passing KPIs across all three checks approximates H1.

**Target:** ≥90%

**Current status:** Tracked in `tooling/validation/results/latest_results.json`

---

## H2 — Semantic Model Stability %

**Definition:** The percentage of measure entries in all Measure Dictionary
files (`core/semantic_models/domains/*/Measure_Dictionary_*.md`) that have
`governance.status: active` (as opposed to `draft` or `review`).

**Calculation:**

```
H2 = (Measures with status: active) / (Total measures in all Dictionaries) × 100
```

**How to check:**

Run `tooling/validation/check_semantic_model_status.ps1` with `-FailOnError`.
Count of `draft` entries is surfaced as a warning.

**Why it matters:** Draft measures are not guaranteed to have consistent
definitions or aggregation methods. When teams build reports on draft measures,
metric definitions diverge across implementations. Active status = reviewed,
`aggregation_method` present, `logical` expression documented.

**Target:** ≥80%

---

## H3 — Data Contract Coverage %

**Definition:** The percentage of fact tables declared in `required_facts`
sections of UseCase Bracket files that exist in at least one domain data
contract under `core/data_contracts/domains/`.

**Calculation:**

```
H3 = (required_facts entries with matching data contract fact table) /
     (Total required_facts entries across all core Brackets) × 100
```

**How to check:**

Run `tooling/validation/check_data_contract_kpi_coverage.ps1`.
Failures indicate fact tables referenced in Brackets but absent from contracts.

**Why it matters:** Missing data contracts mean no quality rules, no lineage
documentation, and no Silver→Gold mapping governance for those tables. This
creates audit risk and implementation ambiguity.

**Target:** ≥90%

---

## H4 — Action Code Completeness %

**Definition:** The percentage of active Action Codes (in
`core/action_codes/*/`) that have all four completeness criteria met:

| Criterion | Field |
|-----------|-------|
| At least one L1 trigger defined | `l1_trigger` |
| Impact valuation present | `impact_valuation.magnitude` or `impact_valuation.formula` |
| Execution bridge defined | `execution_bridge.type` (not null, not "TBD") |
| At least one KPI trigger ID | `kpi_trigger_ids` (non-empty list) |

**Calculation:**

```
H4 = (Action Codes with all 4 criteria met) / (Total active Action Codes) × 100
```

**How to check:**

Run `tooling/validation/audit_action_codes_content.ps1` which audits fields
for completeness. Supplement with schema validation from `check_schema_validation.ps1`.

**Target:** ≥80%

---

## H5 — Factsheet Quality Score

**Definition:** The average completeness score across all core Business
Factsheets (`core/usecases/core/*/Business_Factsheet.md`), rated on a 5-point
scale per factsheet.

**Scoring rubric per factsheet (each section = 1 point):**

| Section | Earns 1 point when... |
|---------|----------------------|
| §1 Business Summary | No TBD markers; purpose and value stated |
| §2 Core Business Questions | ≥3 concrete, non-generic questions present |
| §5 3-30-300 Page Layout | KPI cards + ≥2 named visuals with X/Y axes |
| §8 Success Criteria | At least Impact + Adoption criteria defined |
| §10 Decision Scenarios | ≥2 scenarios with Situation + Action Code |

**Scale:**
- 5/5 = Fully complete
- 4/5 = Minor gap (one section thin)
- 3/5 = Partial (two sections thin or one missing)
- 2/5 = Draft-quality
- 1/5 = Boilerplate only

**Calculation:**

```
H5 = (Sum of individual factsheet scores) / (15 use cases × 5 points) × 100
```

**How to check:**

Run `tooling/validation/validate_factsheets.ps1`. Manual spot-check for §10
quality (automated check only validates presence, not depth).

**Target:** ≥80% (≥4.0 average score across 15 use cases)

---

## H8 — AI-Readiness / Linguistic Coverage %

**Definition:** The percentage of governed column synonyms (data-contract
`synonyms`) that are present in the committed model **linguistic schema**
(`cultures/<culture>.tmdl`). Power BI Copilot reads synonyms from the linguistic
schema, not from `///` description text — so a synonym that only reaches the `///`
block does not act as a synonym in-product. H8 is the gate that keeps the
**third projection** (see `core/semantic_models/AI_Description_Standard.md`) from
silently regressing: drop a governed synonym from the schema and H8 goes red even
though H2 (description text) stays green.

**Calculation:**

```
H8 = (governed synonyms present in cultures/*.tmdl) / (governed synonyms in contracts) × 100
```

A domain contributes only when its contract carries `synonyms`; today that is
Aurora **Commercial** (`Region`, `Channel`, `Net Sales Amount` → 7 governed
synonyms, 100% present). Other domains join as their contracts are curated.

**Consumer after the Q&A retirement (re-assessed 29.09.2026, plan W3.3).** Q&A ends in
February 2027 (banner on every Learn Q&A page). The gate is **kept**; its consumer is now
Copilot alone (`H8_CONSUMERS` in `tooling/health_scorecard.py`, returned in the H8
details). Evidence, Learn, read 29.09.2026:

- *Use Copilot with semantic models*: Copilot in DAX query view grounds on "Synonyms from
  the model linguistic schema"; "Power BI relies on the same linguistic modeling as the
  Q&A feature".
- *Ask data questions with Copilot*: "Add synonyms to data field names to clarify
  business-specific terms for Copilot".

Counter-signal, also Learn 29.09.2026: the *Prep data for AI* FAQ lists AI data schema,
verified answers, AI instructions and descriptions as the Copilot tooling and routes
"understand the term I'm using" to **AI instructions**, not synonyms. Copilot data
questions and *Prep data for AI* still require the model's Q&A setting to be on (it
drives value indexing). Re-check both points before February 2027; if Copilot stops
reading synonyms, the coverage half of H8 loses its consumer and has to be re-targeted.
The hygiene half is independent of Q&A.

**AI-surface hygiene (folded in).** H8 is the composite AI-readiness gate: in
addition to linguistic coverage it must show **0 visible surrogate/FK keys** (C1 —
`*Key` join columns are hidden, not on the user/AI surface) and **0 name-restating
or low-information descriptions** (C2). Either defect turns H8 red even at 100%
synonym coverage. Both checks run standalone for CI:

```bash
python3 tooling/validation/check_ai_surface_hygiene.py --domain Commercial --strict
python3 tooling/validation/check_ai_surface_hygiene.py --domain Commercial --fix   # hide visible keys
```

**How to check:**

```bash
python3 tooling/health_scorecard.py                                            # H8 row (coverage + hygiene)
python3 -m products.fabric.powerbi.tooling.linguistic_schema --all --check     # CI gate (exit 1 on a gap)
```

Regenerate the schema after editing contract synonyms:
`python3 -m products.fabric.powerbi.tooling.linguistic_schema --all`.

**Target:** 100% (every governed synonym reaches the linguistic schema)

---

## Snapshot: Framework Health v2.1.0

Assessed on 2026-03-27 against the current framework state.

| Metric | Score | Status |
|--------|-------|--------|
| H1 Golden Thread Coverage | ~72% | below target — data contracts for ESG/Risk/Efficiency/Growth are new stubs |
| H2 Semantic Model Stability | ~85% | on target — Finance/Ops/SCM updated to active |
| H3 Data Contract Coverage | ~88% | near target — new domains added; fact tables need bracket alignment |
| H4 Action Code Completeness | ~78% | near target — majority complete; 14 ACs have stub execution_bridge |
| H5 Factsheet Quality Score | ~80% | on target — 6 of 15 factsheets fully enriched; 9 at 3/5 |

**Next priority to reach all metrics ≥80%:**
1. Align ESG/Risk/Efficiency/Growth brackets to new data contract tables (H1, H3)
2. Resolve remaining 14 Action Code execution_bridge stubs (H4)
3. Enrich remaining 9 factsheets with §10 Decision Scenarios (H5)

---

## Health Tracking Cadence

| Review | Trigger | Owner |
|--------|---------|-------|
| Release review | Every MINOR or MAJOR version | Framework Owner |
| Quarterly health check | Calendar Q1/Q2/Q3/Q4 | Domain Leads |
| CI gate | Every PR to main | Automated (Stage 1) |

Health metric results from CI runs are stored in
`internal/metrics/runs/*_stage1.json`. Aggregate health scoring is a manual
review step pending automated H1/H5 scoring tooling.

---

## Sources & Grounding

The health-metric design in this document — defining each metric against an explicit goal and
target, distinguishing predictive (leading) from confirmatory (lagging) signals, and tracking
delivery/stability health continuously rather than as a one-time gate — is grounded in the
established measurement and KPI literature:

- **Goal-driven metric definition** (deriving metrics top-down from goals via questions, so each
  metric is purposeful) — Goal-Question-Metric (GQM) approach, Basili, Caldiera & Rombach, *The
  Goal Question Metric Approach* (Encyclopedia of Software Engineering, 1994):
  <https://www.cs.umd.edu/users/mvz/handouts/gqm.pdf>
- **Leading vs. lagging indicators** (balancing predictive drivers against outcome measures) —
  Balanced Scorecard, Robert S. Kaplan & David P. Norton, Harvard Business Review, *The Balanced
  Scorecard — Measures That Drive Performance* (1992):
  <https://hbr.org/1992/01/the-balanced-scorecard-measures-that-drive-performance-2>
- **Software delivery & stability health metrics** (deployment frequency, lead time for changes,
  change failure rate, time to restore — velocity vs. stability) — DORA (DevOps Research and
  Assessment), software delivery performance metrics:
  <https://dora.dev/guides/dora-metrics/>

> These external frameworks inform *how* health metrics are designed (goal-anchored, balanced,
> continuous). The concrete H1–H8 metrics, targets, and checks are framework-specific and defined
> in the sections above.
