# Evidence-to-Model Uplift — Scope & Delivery Plan

> Status: **proposed** · Author: framework-architect-agent · Date: 2026-06-12
> Source of work: the `mapping_readiness` **deferred** backlog recorded in the 16 Domain
> Evidence Packs (DEPs) under `core/usecases/core/*/Domain_Evidence_Pack.yaml`.
> Authority to start: Framework Architect approval (DEP promotion gate, see §5).

---

## 1. Purpose

The 10 newly-authored DEPs (plus the original 6) resolved every **content** and **mapping**
gap directly into the factsheets, and correctly **rejected** 4 false positives. They also
recorded **27 deferred gaps** — **17 `model_gaps` + the bracket gaps blocked by them** — that
cannot be closed without changing the data/model layer.

This document scopes that backlog to a standard where each affected use case is **real,
end-to-end valid** (realistic data, working report) and **perfect on both axes**: business
content *and* technical implementation.

It is deliberately a **plan**, not an implementation. Nothing here mutates Core until the
governing DEPs are promoted to `approved` (§5).

---

## 2. Governing principle — the DEPs already designed the target model

Each DEP's `canonical_domain_model` (driver tree, diagnostic KPIs with IDs/units/benchmarks)
and `required_data_model` (required facts/dimensions/measures/grain) **already specify the
end state**. The uplift is therefore *materialization of an existing, evidence-grounded
design* down a fixed lockstep chain — not new invention. Every change below traces to a
specific DEP field and a specific recorded gap (see the §12 traceability appendix).

---

## 3. The lockstep change-set (what "one new diagnostic KPI" actually touches)

Adding a single evidence-backed diagnostic is **not** a one-file edit. The registry builder
and Stage-1/Fabric checks enforce a closed chain. For each new diagnostic KPI or fact column:

| # | Layer | File(s) | Enforced by |
|---|-------|---------|-------------|
| 1 | **Data contract** | `core/data_contracts/domains/<domain>.yaml` (fact/dim/column) | `check_validate_data_contracts.ps1`, `data_contract.schema.json` |
| 2 | **Synthetic data contract** | `core/data_contracts/sources/synthetic/synthetic_data_contract.yaml` | generator + FK integrity |
| 3 | **KPI catalog** | `core/kpi_catalog/KPI_Catalog.md` / `extended_playbook.md` (`technical.lineage` → step 1 columns; `depends_on_measures`) | `registry_builder.py` (`ref_integrity.missing_kpi`, closure), `check_factsheet_vs_kpi.ps1` |
| 4 | **Measure dictionary** | `core/semantic_models/domains/<Domain>/Measure_Dictionary_<Domain>.md` (`kpi_id_ref`, logical DAX, `dependencies.columns`) | `check_kpi_vs_measure_dictionary.ps1` |
| 5 | ~~**Fabric overlay**~~ | **entfallen 05.08.2026** — DAX aus `technical.calculation`, Format aus `business.unit_format`, Name aus `technical.measure_name`, Ordner aus `use_case_ref` | `build_ir.py` |
| 6 | **Bracket wiring** | `core/usecases/core/<UC>/UseCase_Bracket.yaml` (`supporting_kpi_ids`, `evidence_columns`, `evidence_grain`) | `registry_builder.py` (closure, `evidence_grain.governance_gap`) |
| 7 | **Synthetic generator logic** | `core/data_contracts/sources/synthetic/generate_gold_layer_contract_v2.py` (populate column with realistic, internally-consistent values) | row-level QA / driver-consistency |
| 8 | **Semantic model (generated)** | `products/fabric/powerbi/dist/<Domain>.SemanticModel/**` via orchestrator | `check_catalog_tmdl_drift.py`, `check_measures_vs_kpi.ps1`, TMDL hooks |
| 9 | **Report (generated)** | `products/fabric/powerbi/dist/<UC>_*.Report/**` via page scaffold generator | `validate_bindings.py`, `check_report_quality.ps1`, PBIR hooks |

**Steps 1–7 are hand-authored Core/data work. Steps 8–9 are produced by the orchestrator**
(`orchestrate_full_model.ps1`) and the page scaffold generator — they are *generated*, never
hand-edited in `dist/`.

### 3a. Lean authoring path (the chain is grown — only 4 steps are true SSOT)

The 9-step chain has accreted redundancy. Of the steps, only **4 are genuine source-of-truth
files an author touches**; the rest are generated outputs or restatements kept in sync by
validators:

| Step | Verdict |
|---|---|
| 1 domain contract · 3 KPI catalog · 6 bracket · 7 generator logic | **Essential — author these** |
| 8 TMDL · 9 report | **Generated — not authoring work** |
| 2 synthetic contract | **Redundant restatement of #1** (even diverges on column naming) |
| 4 measure dictionary | **Redundant restatement of #3** — sole purpose is sync via `check_kpi_vs_measure_dictionary.ps1` |
| 5 Fabric overlay | **Optional** — author only when Fabric DAX/format genuinely diverges |

**Working rule for this uplift:** author #1, #3, #6, #7; touch #2/#4/#5 only the minimum needed
to pass the sync-validators (overlay only when divergent). This makes the real per-workstream
surface **≈4 files**, not 9.

**Separate tech-debt (not in this uplift):** collapse the dual contract (#1+#2 → one SSOT) and
**auto-generate the measure dictionary (#4) from the KPI catalog (#3)**. That refactor touches
the generator + every existing domain, so it ships as its own streamlining PR, not inside a
content workstream.

---

## 4. Environment reality (confirmed in-session)

| Capability | Status | Consequence |
|---|---|---|
| `pwsh` 7.4.6 | ✅ available | Orchestrator + Stage-1 + Fabric checks **run locally** → the full pipeline (TMDL + reports) is deliverable and validatable here, not just Core. |
| Python registry builder | ✅ runs on Linux | Referential integrity / closure validatable without pwsh. |
| `pandas` / `pyarrow` | ❌ not installed | The gold-data generator writes Delta/Parquet — needs `pip install pandas pyarrow` (network-policy dependent) before "real-life" row data can be produced. |
| GitHub Actions CI | ⚠️ environmental runner-limit | Cannot be relied on for green; **validate locally** before each push. |

---

## 5. Governance gates (must be honoured)

1. **DEP promotion is the real prerequisite.** Per `domain-evidence-pack-spec.md:272-273`:
   *"A DEP with status `draft` or `reviewed` may not be used to justify a schema change.
   Only an `approved` DEP may justify Core content updates."* All 10 new DEPs are `draft`.
   → **Phase 0** promotes them (Reviewer → Framework Architect sign-off).
2. **These are `model_gaps`, not `schema_gaps`.** Per `gap-classification.md:93-104`, adding
   facts/dimensions/columns/measures to a contract or TMDL is a `model_gap` the author may
   implement **without** a Schema Gap Report — *"unless a data-contract amendment requires it"*,
   and it *"follows the data-contract governance process"* (cross-domain duplicate audit,
   allowlisted shared tables). No change to any `*.schema.json` is anticipated; if one becomes
   necessary it escalates to an **SGR + Framework Architect** approval (`gap-classification.md:70`).
3. **Core-first** (`framework-architect.md:13`): every new KPI/measure is defined in `core/`
   before it appears in any product artifact.
4. **Validation gate per change**: Stage 1 (`run_stage1_checks.ps1`) + Fabric checks
   (`run_fabric_checks.ps1`) + `pytest` must pass locally before push.

---

## 6. Definition of Done (the quality bar)

A workstream is **done** only when all three hold:

- **Content-perfect**: every new KPI/measure traces to the DEP (`technical.lineage`,
  benchmark target, interpretation); the DEP's `mapping_readiness` gap flips `deferred → resolved`
  with a resolution note; the factsheet reflects the now-available diagnostic.
- **Technical-perfect**: Stage 1 + Fabric + pytest green locally; TMDL style + PBIR hooks pass;
  registry closure satisfied; no orphan KPIs/measures; golden COM-001 fixture unaffected.
- **Real-life valid**: the synthetic generator produces realistic, **internally-consistent**
  rows (driver relationships hold — e.g. MTBF rises as failures fall; OTIF = On-Time × In-Full;
  abandonment survives the SLA-on-handled blind spot) and the generated report renders the new
  diagnostics with non-empty, plausible values.

---

## 7. Workstreams (by domain)

Each workstream is a cohesive PR: contract + synthetic + catalog + measure-dict + overlay +
bracket + generator logic + DEP update, then regenerate TMDL/report and validate.

### WS-1 · Operations — OPS-002 Asset Performance  · size **M**
- **Contract** (`operations.yaml`): promote `fact_ops_failures.Cause Code` (free text) to a
  governed **`dim_cause_code`** (ISO 14224 failure-mode taxonomy) + `CauseCodeKey`; add
  **repair-time split** `Active Repair Hours` + `Logistic/Wait Hours` (EN 13306) decomposing
  `Repair Duration Hours`.
- **New KPIs** (already designed in the DEP): `ops.failure.count.by_mode`, MTTR active-vs-wait
  decomposition, repeat-failure %, PM-adequacy (reuse `ops.pm_compliance.pct`).
- **Bracket**: add failure-mode Pareto + MTTR-decomposition `evidence_columns`; add diagnostics
  to `supporting_kpi_ids` (now resolvable).
- **Synthetic**: cause-code distribution per asset class; wait-time correlated with
  `Parts Stockout Flag`.

### WS-2 · Operations — OPS-003 Quality & Yield  · size **L**
- **Contract**: add **`dim_defect_type`** + `DefectTypeKey` on a defect-grain quality fact
  (defect Pareto); add a **process-step grain** to quality facts (per-step FPY + Rolled
  Throughput Yield); add **PAF category** column to `fact_quality_costs`
  (prevention / appraisal / internal / external) for the internal-vs-external COPQ split.
- **New KPIs**: `quality.rty.pct`, per-step FPY, defect Pareto by type, COPQ internal/external.
- **Bracket**: separate COPQ (EUR) onto its own visual (resolves the EUR+% mixed-axis defer);
  add defect-Pareto + RTY evidence.
- **Risk**: the process-step grain change is the heaviest item — it re-grains `fact_quality`;
  verify no regression to OPS-001/existing OEE measures.

### WS-3 · Finance — FIN-002 Cost Performance  · size **L**
- **Contract** (`finance.yaml`): add **`Labor Cost Amount`** (+ standard hours/rate) to
  `fact_labor` (or reconcile with existing `efficiency.fact_cost_per_unit` per the
  duplicate-audit allowlist); add a **standard-cost reference** (`fact_standard_cost` or
  columns: Standard Price, Standard Quantity, Standard Labor Rate, Fixed Overhead Rate,
  Normal Volume).
- **New KPIs**: unit cost; material price/usage variance; labour rate/efficiency variance;
  fixed-overhead absorption variance.
- **Bracket**: unit-cost variance **waterfall** (plan → price/usage → rate/efficiency →
  absorption → actual); add variance diagnostics to `supporting_kpi_ids`.
- **Risk**: standard-costing is a small sub-model; the waterfall is a new visual pattern.

### WS-4 · Supply Chain — SCM-002 OTIF + SCM-003 Forecast  · size **M**
- **SCM-002** (`supply_chain.yaml`): add **appointment/MABD-compliance** signal to
  `fact_fulfillment` (or derive from `fact_logistics` lane timing) + carrier on-time by lane.
  New KPIs: appointment compliance %, carrier on-time %.
- **SCM-003**: add a **forecast lag** dimension (derive lag from `Forecast Version` vs actual
  month) + a stored **naive-benchmark** forecast series for Forecast Value Added. New KPIs:
  MAPE-by-horizon, bias %, FVA %, forecastability (CoV). Bracket: ABC/XYZ + CoV/FVA evidence.

### WS-5 · Experience — XD-001 Service + XD-002 Resource  · size **L**
- **XD-001** (`experience.yaml`): add offered/abandoned contact events + **answer timestamp
  (ASA)** + **reopen flag** + case open/close timestamps to `fact_support_cases` (or a new
  contact-grain `fact_contacts`). New KPIs: `svc.abandon.pct`, `svc.asa.seconds`,
  `svc.reopen.pct`, `svc.backlog.aging.days`. Bracket: aging/reopen evidence + diagnostics.
- **XD-002**: add **scheduled on-task minutes** + **planned-shrinkage baseline** to
  `fact_workforce_management`; add a **forecast-vs-actual** (volume/AHT) fact. New KPIs:
  `res.schedule_adherence.pct`, `res.shrinkage.unplanned.pct`, `res.idle.pct`,
  `res.forecast_accuracy.pct`. Bracket: occupancy-ceiling band overlay (generator) + diagnostics.

### WS-6 · Executive risk mart — XD-003 + XD-004  · size **L** (architectural)
- **XD-003** (`executive.yaml`): build the **risk mart** — `fact_kpi_snapshot`
  (cross-domain actual/plan/LY normalized), `fact_risk_weights` (materiality), `dim_domain`,
  `dim_kpi`. Measure: **Enterprise Value-at-Risk Index** (weighted sum) + per-domain
  contribution. Bracket: per-domain VaR-contribution evidence columns.
- **XD-004** (`governance.yaml`): add a **triggered-deviation ledger** (detected deviations +
  whether an action was routed) → Action Coverage % without survivorship bias; effectiveness-delta
  attribution via pre/post baseline windows joined to `fact_kpi_snapshot`. New KPIs:
  `enterprise.action_coverage.pct`, action latency, time-to-impact. Bracket: latency/coverage/
  time-to-impact evidence.
- **Dependency**: XD-004 attribution **depends on** XD-003's `fact_kpi_snapshot` → land XD-003 first.
- **Open architectural decision**: there is **no `Executive.SemanticModel`** today (5 models:
  Commercial, Finance, Operations, SupplyChain, Experience). Decide: host the risk mart in
  `Experience.SemanticModel` **or** stand up a new `Executive.SemanticModel`. *Recommendation:
  new `Executive.SemanticModel`* — keeps the cross-domain mart from polluting Experience and
  matches the XD domain boundary. This is the one item that may warrant a brief SGR-style note.

---

## 8. Cross-cutting phases

- **Phase 0 — Governance enablement (prereq). ✅ DONE 2026-06-12.** The 10 DEPs carrying the
  deferred backlog were promoted `draft → approved` (Framework Architect, repo owner) on the
  basis of the 16/16 SQ-E gate pass + mapping triage. No `*.schema.json` change is required (all
  deferred items are `model_gaps`). The WS-6 semantic-model decision (new `Executive.SemanticModel`)
  is recommended and revisited when WS-6 starts.
- **Phase 1 — Core + synthetic (per workstream).** Steps 1–7 of §3. Validatable with `pytest`
  + registry builder locally now.
- **Phase 2 — Generate (per workstream).** Run `orchestrate_full_model.ps1` (pwsh, available)
  to regenerate TMDL + reports; run `run_fabric_checks.ps1`. Steps 8–9.
- **Phase 3 — Real-life data validation.** `pip install pandas pyarrow`; run
  `generate_gold_layer_contract_v2.py`; point the model at the gold path (`-UseAuroraData`);
  confirm reports render the new diagnostics with realistic, driver-consistent values. Produce
  an Aurora Proof Dossier for the showcase use cases.

---

## 9. Sequencing, dependencies & PR slicing

```
Phase 0 (governance)  ──►  WS-1 OPS-002 ─┐
                            WS-2 OPS-003 ─┤
                            WS-3 FIN-002 ─┼─► (independent, parallelizable)
                            WS-4 SCM      ─┤
                            WS-5 XD-svc   ─┘
                            WS-6 XD-003 ──► WS-6 XD-004   (XD-004 after XD-003)
Each WS:  Phase 1 ─► Phase 2 ─► Phase 3 ─► DEP gap deferred→resolved ─► PR
```

- **One PR per workstream** (6 PRs), each independently green and reviewable.
- WS-1…WS-5 are mutually independent → can be built in any order / parallel.
- **WS-6 is the long pole** (architectural; internal XD-003 → XD-004 dependency).
- Recommended order by value/effort: **WS-4 → WS-1 → WS-5 → WS-3 → WS-2 → WS-6**
  (quickest credible wins first; heaviest/architectural last).

### Rough effort
| Workstream | Size | Drivers |
|---|---|---|
| WS-4 SCM | M | 2 contract signals + lag dim + 6 KPIs |
| WS-1 OPS-002 | M | cause-code dim + repair split + 4 KPIs |
| WS-5 XD-svc | L | contact-grain events + WFM forecast fact + 8 KPIs |
| WS-3 FIN-002 | L | standard-cost sub-model + 5 variance KPIs + waterfall |
| WS-2 OPS-003 | L | defect dim + **re-grain** + PAF split + 4 KPIs |
| WS-6 XD-exec | L | 4-table risk mart + deviation ledger + index measure + new semantic model |

---

## 10. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| DEPs still `draft` → cannot justify Core change | **Blocking** | Phase 0 promotion before any Core edit |
| Re-graining `fact_quality` (WS-2) regresses OPS-001 OEE | High | Add step grain additively; keep line-day rollup; regression-test OPS-001 |
| No `Executive.SemanticModel` (WS-6) | High | Decide host in Phase 0; recommend new model |
| `pandas`/`pyarrow` unavailable (no network) | Med | Phases 1–2 don't need it; gate Phase 3 on dep install |
| Cross-domain duplicate tables (shared `dim_*`) | Med | Follow data-contract duplicate-audit + allowlist (`core/data_contracts/README.md`) |
| Golden COM-001 fixture drift | Med | Workstreams don't touch COM-001; run scaffold golden test each PR |
| CI environmental red masks real failures | Med | Validate locally (pwsh present) before push; don't trust CI signal |
| Bracket closure errors when adding `supporting_kpi_ids` | Low | Add KPI catalog + measure-dict entries **before** wiring brackets (Core-first) |

---

## 11. What this unblocks

On completion, all 27 deferred gaps close, every core use case is backed by a real,
queryable model with realistic data and a rendering report, and the `mapping_readiness`
ledger across all 16 DEPs reads `resolved`/`rejected` only — i.e. the library reaches
**full evidence-to-model closure**.

---

## 12. Traceability appendix — deferred gap → workstream

| Use case | Deferred gap (DEP `mapping_readiness`) | Workstream |
|---|---|---|
| OPS-002 | `dim_cause_code`; repair active-vs-wait split; value-driver refinement | WS-1 |
| OPS-003 | `dim_defect_type`; process-step grain + RTY; COPQ PAF split; EUR+% axis | WS-2 |
| FIN-002 | `Labor Cost Amount`; standard-cost reference; variance diagnostics; waterfall | WS-3 |
| SCM-002 | appointment/MABD + carrier on-time | WS-4 |
| SCM-003 | forecast lag dim; naive-benchmark series; CoV/FVA evidence | WS-4 |
| XD-001 | offered/abandoned + ASA; reopen + aging; supporting/evidence wiring | WS-5 |
| XD-002 | scheduled on-task + planned shrinkage; forecast fact; occupancy band | WS-5 |
| XD-003 | `fact_kpi_snapshot` / `fact_risk_weights` / `dim_domain` / `dim_kpi`; VaR index measure; VaR evidence | WS-6 |
| XD-004 | triggered-deviation ledger; effectiveness-delta attribution; latency/coverage evidence | WS-6 |
| COM-004 | incremental/cannibalization measure validation (Commercial.SemanticModel) | (rider on WS — Commercial) |

> The two `Commercial.SemanticModel` measure-validation items (COM-004) are measure-only
> (no new facts) and can ride as a small rider PR against the Commercial model.
