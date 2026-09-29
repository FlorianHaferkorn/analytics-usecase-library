# ADR 0011 — KPI Calculation DSL Grammar Extension (13-KPI Closure)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Scope:** Closes the "Deferred" item in [ADR-0010](0010-kpi-calculation-dsl-and-dax-synthesis.md)
  ("The remaining ~13 HITL KPIs in the 5 MVP use cases"). Extends the governed
  `technical.calculation` grammar with 9 new ops + recursive `calc_ref` so all
  13 previously-`hitl` KPIs referenced by the 5 MVP use cases (COM-001/002/003,
  FIN-002, SCM-002) now resolve to real synthesized DAX. Does **not** touch the
  resolve/synthesize split, the HITL policy, or the parity methodology
  established by ADR-0010 — this is a grammar widening, not a redesign.
- **Supersedes:** —
- **Related:** [`0010-kpi-calculation-dsl-and-dax-synthesis.md`](0010-kpi-calculation-dsl-and-dax-synthesis.md)
  (the base grammar + architecture this extends), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../plans/UMSETZUNGSPLAN_SUPERVERSION.md)
  (I-10.0), [`../../../tooling/generator/schemas/kpi_definition.schema.json`](../../../tooling/generator/schemas/kpi_definition.schema.json),
  [`../../../tooling/superversion/targets/dax_synth.py`](../../../tooling/superversion/targets/dax_synth.py)

---

## Context

ADR-0010 closed Befund A1 for the KPIs expressible in a 7-op grammar
(`sum`/`ratio`/`delta`/`delta_pct`/`rate`/`count`/`hitl`), explicitly flagging
the remaining 13 KPIs (PVM price/volume/mix effects, margin-vs-plan,
promo incremental GM, and 6 COM-003 customer-analytics KPIs — CLV, lifetime
revenue, churned/active customers, retention, NPS, complaint count) as
deferred `hitl` gaps: their real legacy DAX uses `SUMX`/`AVERAGEX` iterators,
`DISTINCTCOUNT` with multiple simultaneous filters, multi-term `VAR` chains, and
nested sub-expressions the original 7-op grammar had no shape for.

Re-reading the exact legacy DAX for all 13 (`products/fabric/powerbi/dist/
Commercial.SemanticModel/definition/tables/_Measures.tmdl`) surfaced that
several were blocked not just by missing ops but by **wrong lineage** — three
KPIs' `technical.lineage` pointed at columns/tables the real DAX never
touches (documented per-KPI below), inherited from the same class of drift
ADR-0010 already found in `crm.complaint.count` (`fact_experience` vs. the
real `fact_complaints`).

## Decision

### 1. Nine new ops + recursive `calc_ref`

| op | Shape | DAX pattern | Used by |
|---|---|---|---|
| `mul` | n-ary product of terms | `a * b * ...` | Incremental GM, Revenue at Risk |
| `delta_chain` | minuend minus 1+ subtrahends, left to right | `a - b - c - ...` | Mix Effect Amount |
| `distinctcount` | `DISTINCTCOUNT` of a key column, optional CALCULATE-wrapped boolean-flag filters | `[CALCULATE (] DISTINCTCOUNT ( t[k] )[, t[f]=TRUE()... ] )` | Churned/Active Customers, Retention, Revenue at Risk |
| `count_threshold` | row count filtered by a numeric comparator | `CALCULATE ( COUNTROWS ( t ), t[c] >= n )` | NPS Promoters/Detractors |
| `round` | `ROUND ( value, digits )` wrapper | — | NPS index |
| `sumx_over_key` | per-key cumulative sum | `SUMX ( VALUES ( t[k] ), CALCULATE ( value ) )` | Customer Lifetime Revenue |
| `avgx_over_key` | per-key average | `AVERAGEX ( VALUES ( t[k] ), CALCULATE ( value ) )` | CLV |
| `pvm_volume_effect` | fixed-shape SUMX leaf, row-context columns (no aggregation wrapper) | `SUMX ( t, (qty-planqty) * DIVIDE(plansales,planqty) )` | Volume Effect Amount |
| `pvm_price_effect` | fixed-shape SUMX leaf, row-context columns | `SUMX ( t, (DIVIDE(netprice,qty)-DIVIDE(plansales,planqty)) * qty )` | Price Effect Amount |

`calc_ref` (the term type used inside `ratio`/`delta`/`mul`/`delta_chain`/…)
gains a third shape: `{"calc": {...nested calculation...}}` — a fully
recursive nested formula, resolved via the same `_resolve_calc_node` that
resolves the top-level `technical.calculation`. This is how VAR-chain-shaped
legacy formulas (e.g. `margin.gm.vs_plan.pct`'s `PlanGM = SUM(...) - SUM(...)`
sub-expression, or NPS's triple-nested `ROUND(DIVIDE(delta(...), count(...))
* 100, 0)`) become expressible without a bespoke op per VAR shape: each VAR
becomes one nested `calc` node. Recursion is genuine (verified to 2+ levels
deep, not hardcoded to one level — `test_calc_resolution.py::
test_recursive_calc_ref_two_levels_deep`).

`pvm_volume_effect`/`pvm_price_effect` are the two exceptions to "compose from
existing ops": their legacy DAX iterates raw row-context columns inside
`SUMX` (`fact_sales[Quantity]`, not `SUM(fact_sales[Quantity])` — the `SUM`
wrapper the generic `column` term always renders would be semantically
different, relying on an implicit CALCULATE context-transition rather than
plain row-context access) — a fixed-shape op matching that exact legacy
pattern was more honest than stretching `mul`/`delta_chain` with a "raw
column, no aggregation" term-kind that only these two callers would ever use.

### 2. Lineage corrections discovered alongside (not a separate task)

Three KPIs' `technical.lineage` was factually wrong — pointing at a
table/column the real legacy DAX never reads — the same drift class ADR-0010
already found once (`crm.complaint.count`). Fixed at the source (not worked
around):

| KPI | Was | Now (matches real DAX) |
|---|---|---|
| `sales.pvm.price_effect.amount` | `fact_sales.Net Sales Amount` | `fact_sales.Net Price Amount` |
| `margin.gm.vs_plan.pct` | `fact_plan_sales.Plan Gross Margin Amount` (no such column) | `fact_sales.Plan Sales Amount` + `fact_sales.Plan COGS Amount` |
| `crm.churned_customers.count`, `crm.active_customers.count`, `crm.retention.pct`, `crm.revenue_at_risk.amount` | `dim_customer.CustomerKey` | `fact_customer_events.CustomerKey` |
| `crm.lifetime_revenue.amount` | `dim_customer.CustomerKey` | `fact_sales.CustomerKey` |
| `crm.clv.amount` | `fact_sales.CustomerKey` (wrong table) | `fact_customer_value.CustomerKey` + `fact_customer_value.CLV Amount` |
| `crm.complaint.count` | `fact_experience` (column-less, already flagged in ADR-0010) | `fact_complaints.Complaint Count` |

`crm.revenue_at_risk.amount`'s `business.purpose`/`definition`/
`depends_on_measures`/`qa_rules` also documented a completely different
formula (Net Sales × average OTIF/FPY failure rate) than its real DAX
(Net Sales × Churned/Active customer ratio) — corrected to match; this was a
content-drift bug (likely a copy-paste origin), not a formula decision.

### 3. Result

All 13 KPIs resolve through the real pipeline (`from_aluca._resolve_calculation`
+ `dax_synth.synthesize_dax`) with 0 remaining `op: hitl` entries referenced by
the 5 MVP use cases — `hitl_gaps()` returns `[]` for all five
(`test_calculation_coverage.py::test_all_5_core_use_cases_are_fully_computed`).
13 new parity cases were added to `test_dax_parity_legacy.py`
(`KPI_TO_LEGACY`), all green — several synthesize to DAX that is column-set
*and* byte-identical to the legacy generator's output (`crm.clv.amount`,
`sales.pvm.mix_effect.amount`).

## What this ratifies vs. defers

**Ratified:** the 9 new ops + their schema shapes; recursive `calc_ref`; the
lineage corrections above (evidenced against real legacy DAX, not guessed).

**Deferred (unchanged from ADR-0010, still out of scope):**
- DSL→SQL (or any other dialect) transpilation for `targets/osi.py` /
  `targets/databricks.py` — tracked as a separate, immediately-following task
  ("go for 2"), not part of this grammar-extension ADR.
- The other 11 use cases entirely untouched by I-10.0 (their KPIs were never
  in scope).
- Migrating `linux-generation.yml` / `adapter_build.ps1` off the legacy
  generator, and its eventual hard removal.
