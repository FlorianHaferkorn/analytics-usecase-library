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
| H8 | AI-Readiness / Linguistic Coverage % | Governed column synonyms present in the model linguistic schema (Copilot/Q&A) | 100% | Data Engineering |

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
(`cultures/<culture>.tmdl`). Power BI Copilot/Q&A resolve natural language against
the linguistic schema, not against `///` description text — so a synonym that only
reaches the `///` block is invisible in-product. H8 is the gate that keeps the
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

**How to check:**

```bash
python3 tooling/health_scorecard.py                                            # H8 row
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
