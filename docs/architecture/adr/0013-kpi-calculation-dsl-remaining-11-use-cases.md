# ADR 0013 — KPI Calculation DSL: Remaining 11 Use Cases (Full-Catalog Closure)

- **Status:** Accepted
- **Date:** 2026-07-04
- **Scope:** Closes the "Deferred" item in [ADR-0011](0011-kpi-calculation-dsl-grammar-extension.md)
  ("The other 11 use cases entirely untouched by I-10.0"). Extends the governed
  `technical.calculation` DSL from the 5 MVP use cases (COM-001/002/003,
  FIN-002, SCM-002) to all remaining 11 — COM-004, OPS-001/002/003, FIN-001,
  SCM-001/003, XD-001/002/003/004 — so the full 16-use-case catalog resolves
  through the same real DSL→DAX pipeline. Extends the grammar with 4 more
  ops/filter-shapes; does **not** touch the resolve/synthesize split, the
  HITL policy, or the parity methodology established by ADR-0010/0011.
- **Supersedes:** —
- **Related:** [`0010-kpi-calculation-dsl-and-dax-synthesis.md`](0010-kpi-calculation-dsl-and-dax-synthesis.md),
  [`0011-kpi-calculation-dsl-grammar-extension.md`](0011-kpi-calculation-dsl-grammar-extension.md),
  [`0012-kpi-calculation-dsl-sql-synthesis.md`](0012-kpi-calculation-dsl-sql-synthesis.md),
  [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md) (I-10.0),
  [`../../../tooling/generator/schemas/kpi_definition.schema.json`](../../../tooling/generator/schemas/kpi_definition.schema.json),
  [`../../../tooling/superversion/targets/dax_synth.py`](../../../tooling/superversion/targets/dax_synth.py)

---

## Context

ADR-0010/0011 closed every `hitl` gap referenced by the 5 MVP use cases, but
explicitly flagged "the other 11 use cases" as out of scope. Those 11 span
four domains, each with its own legacy semantic model and `_Measures.tmdl`:
Commercial (COM-004), Operations (OPS-001/002/003), Finance (FIN-001),
SupplyChain (SCM-001/003), and Experience (XD-001/002/003/004). Closing them
required reading four more `_Measures.tmdl` files end to end and, per the
established discipline, extending the grammar only where a real observed
legacy pattern demanded it — never speculatively.

## Decision

### 1. Four grammar additions, evidence-based

| Addition | Shape | DAX pattern | First real caller |
|---|---|---|---|
| `add` | n-ary sum of terms | `a + b + ...` | `ops.oee.pct`-family; `wc.ccc.days` (`DSO + DIO`, then `delta` for `- DPO`); `res.occupancy.pct` ((Talk+Wrap)/(Talk+Wrap+Idle)) |
| `abs` | wraps one term | `ABS ( value )` | `plan.forecast.accuracy.pct` (`1 - ABS(DIVIDE(...))`) |
| `avg_filtered` | filtered row average | `CALCULATE ( AVERAGEX ( t, t[col] ), filters )` | `enterprise.action_effectiveness_delta.amount` |
| `count_filtered` `not_blank` filter | filter variant (existing op) | `NOT ISBLANK ( t[col] )` instead of an equality check | `enterprise.actions_executed.count` |

`literal` (a bare numeric `calc_ref`, added for the mid-batch proxy-factor
KPIs) and `avg`/`sumx_product`/`count_filtered` (added for the Operations
batch) predate this ADR's scope on paper but were introduced in the same
sequence of commits — see the per-domain PR history for their own
justification; this ADR covers `add`, `abs`, `avg_filtered`, and the
`not_blank` filter.

### 2. Domain-by-domain closure, each a separate reviewed increment

Following the exact per-domain, QA+SA-reviewed rhythm established in
ADR-0011:

- **COM-004 + Operations (OPS-001/002/003):** OEE %/Availability/Performance/
  Quality composites, MTBF/MTTR (referencing `ops.failure.count` rather than
  re-deriving `COUNTROWS`), Planned Output Units (`sumx_product`), PM
  Compliance % (`count_filtered` with string-equality filters). Left `hitl`:
  `ops.changeover.minutes`, `ops.speed_loss.pct` (new-territory, no legacy
  DAX, genuinely under-specified), `ops.safety.incident.count` (legacy DAX is
  itself a documented `BLANK()` placeholder — matches legacy, not a gap).
- **Finance (FIN-001) + SupplyChain (SCM-001/003):** Working Capital (DSO/
  DIO/DPO/CCC Days), Cash (Balance/OCF/vs-Plan %), Inventory (Turnover/DIO/
  Stockout %/Obsolete %), Forecast (Accuracy %/Bias %/Replan Count). Left
  `hitl`: `plan.forecast.mape.pct`/`plan.forecast.service_impact.pct`
  (per-key `AVERAGEX`/per-row conditional `SUMX` composites, beyond
  `sumx_over_key`/`avgx_over_key`), `scm.supplier_risk.score` (legacy `BLANK()`
  placeholder), `inv.excess_inventory.amount` (new-territory, under-specified).
  `plan.forecast.accuracy.pct` documents a narrow, real divergence in its own
  `governance.qa_rules`: legacy's explicit `IF(Actual=0,BLANK())` guard vs.
  the synthesized `1 - DIVIDE(...)`'s DAX blank-coercion (evaluates to `1` at
  zero-denominator, not `BLANK()`) — the column set matches exactly, this is
  a value-level edge case, not a lineage gap.
- **Experience (XD-001/002/003/004):** Service (SLA/FCR/Escalation % via
  `rate`; AHT Minutes via `ratio(SUM,count)`; Backlog/Tickets Closed via
  `count_filtered`; NPS Index mirroring `crm.nps.index`'s existing pattern),
  Workforce (Utilization/Overtime/Shrinkage % via `ratio`; Occupancy % via
  the new `add` op), Executive (`enterprise.value_at_risk.index` — the
  deepest composition in this ADR, see below), Governance (the
  `enterprise.action_*` family). Left `hitl`: `people.digital_adoption.pct`/
  `people.attrition_risk.pct` (legacy `BLANK()` placeholders).

### 3. `enterprise.value_at_risk.index` — faithful reproduction, not simplification

Legacy's VAR chain has a real redundancy: `RevenueAtRiskShare =
DIVIDE(NetSales × CombinedRiskFactor, NetSales)` is algebraically ≈
`CombinedRiskFactor` itself, then averaged again with two risk terms
derived from the same two underlying signals. The DSL composition
reproduces this round-trip exactly (via nested `ratio`/`add`/`mul`/`delta`/
`literal` — no new op needed) rather than collapsing it, because the
round-trip changes zero-Net-Sales-denominator `BLANK()` behavior:
`DIVIDE(0×C, 0)` is `BLANK()`, but a collapsed `CombinedRiskFactor` alone
would not be. Documented in the KPI's own `qa_rules`.

### 4. `ops.working_capital.ccc.days` — a deliberate, distinct proxy formula

This KPI id (aliased `fin.liquidity.cash_conversion_cycle_days`) is
**not** the same catalog entry as Finance's `wc.ccc.days`. Its real legacy
DAX (Experience.SemanticModel) computes DSO/DIO/DPO as fixed-ratio proxies
(12%/15%/8%) off `Net Sales`/`COGS Amount`, because the Experience-domain
reporting context has no real receivables/inventory/payables fact tables.
Both formulas are legitimate for their own reporting context; conflating
them into one KPI id would silently pick the wrong one for whichever
context loses. Documented in both KPIs' `qa_rules`.

### 5. `enterprise.action_outcome_rate.pct` — canonical-vs-superseded duplicate

Experience.SemanticModel carries two measures tagged with this same KPI id
comment: `'Action Outcome Rate % (XD)'` (`fact_action_outcome`, the actively
maintained table shared by 3 sibling KPIs in this ADR) and an older
`'Action Outcome Rate % (XD Log)'` (`fact_action_log`, no surviving sibling
measures). The former was chosen as canonical for internal consistency with
its sibling family; documented in `qa_rules`, not silently picked.

### 6. Lineage / business-doc corrections discovered alongside

Same drift class as ADR-0010/0011 (stale `depends_on_measures`, wrong
lineage columns) — fixed at the source wherever found: `ops.mtbf.hours`/
`ops.mttr.hours` (stale sibling lists), `wc.dio.days`/`inv.dio.days`/
`plan.forecast.accuracy.pct` (stale `depends_on_measures`),
`fin.liquidity.inventory.amount` (`Inventory Amount`→`Average Inventory
Amount`), `svc.tickets.closed.count` (`Case Closed Date`→`Open Case Flag`),
`res.utilization.pct`/`enterprise.value_at_risk.index` (stale sibling
lists rewritten to the real formula's actual dependencies), and several
`business.definition` corrections to honestly describe proxy factors
(`sales.promo.cannibalized_sales.amount`, `ops.planned_output.units`,
`ops.working_capital.ccc.days`) rather than leaving stale prose.

### 7. Test-methodology fix: `COUNTROWS ( FILTER ( table, ... ) )` normalization

`test_dax_parity_legacy.py`'s column-set normalizer recognized bare
`COUNTROWS ( table )` as touching `(table, "*")` but not legacy's equivalent
`COUNTROWS ( FILTER ( table, cond ) )` spelling — a purely textual-idiom gap
that would have read as a false column-set divergence for
`enterprise.actions_executed.count`. Widened the regex to recognize both
spellings identically (`_COUNTROWS_FILTER_TABLE_RE`); confined to the test's
own normalizer, does not touch `dax_synth.py`/`sql_synth.py`.

## Result

All 16 use cases now resolve through the real pipeline
(`from_aluca._resolve_calculation` + `dax_synth.synthesize_dax`). 9 unique
KPIs remain `op: hitl` across the full catalog, every one individually
justified and documented — 4 legacy-`BLANK()`-placeholder matches
(`scm.supplier_risk.score`, `ops.safety.incident.count`,
`people.digital_adoption.pct`, `people.attrition_risk.pct`), 2
grammar-limitation cases (`plan.forecast.mape.pct`,
`plan.forecast.service_impact.pct`), and 3 new-territory,
genuinely-under-specified cases (`inv.excess_inventory.amount`,
`ops.changeover.minutes`, `ops.speed_loss.pct`):

| Remaining `hitl` KPI | Reason class |
|---|---|
| `scm.supplier_risk.score` | Legacy DAX itself is a documented `BLANK()` placeholder |
| `ops.safety.incident.count` | Legacy DAX itself is a documented `BLANK()` placeholder |
| `people.digital_adoption.pct` | Legacy DAX itself is a documented `BLANK()` placeholder |
| `people.attrition_risk.pct` | Legacy DAX itself is a documented `BLANK()` placeholder |
| `plan.forecast.mape.pct` | Per-key `AVERAGEX` composite of two independent `CALCULATE(SUM(...))` lookups, beyond grammar |
| `plan.forecast.service_impact.pct` | Per-row conditional `SUMX` comparing a row-level column to a context-filtered aggregate, beyond grammar |
| `inv.excess_inventory.amount` | New-territory, no legacy counterpart, under-specified months-of-coverage threshold |
| `ops.changeover.minutes` | New-territory, no legacy counterpart, under-specified |
| `ops.speed_loss.pct` | New-territory, no legacy counterpart, under-specified |

**Evidence:** `python -m pytest tooling/superversion/ -q` → 566 passed, 1
skipped · `python -m pytest tooling/superversion/ tooling/tests/ products/
-q` → 1453 passed, 26 skipped (repo-wide green) · `hitl_gaps()` across all
16 use cases: 18 total gap references, 9 unique KPIs, every one
individually justified above (`0` silent `BLANK()`) · parity test
(`test_dax_parity_legacy.py`) extended with the full Operations/Finance/
SupplyChain/Experience `KPI_TO_LEGACY` set, all green ·
`python scripts/check_index.py --strict` exit 0 · **QA/SA double-review per
domain increment** (COM-004+Operations, Finance+SupplyChain, Experience —
3 separate Opus sub-agent review pairs), each **0 Critical / 0 Major**.

## What this ratifies vs. defers

**Ratified:** the `add`/`abs`/`avg_filtered` ops and the `not_blank` filter
shape (shared `$defs/calc_filters`); the domain-by-domain closure of all 16
use cases; the lineage/business-doc corrections above; the parity-test
normalizer widening.

**Deferred (unchanged from ADR-0010/0011, still out of scope):**
- The 9 remaining `hitl` KPIs listed above — each individually justified,
  not silently dropped, but genuinely requiring either upstream data
  (3 legacy-`BLANK()` cases + `ops.safety.incident.count`), a further
  grammar extension for per-key/per-row composite iterators (2 cases), or a
  business decision on an under-specified threshold (3 cases).
- Migrating `linux-generation.yml` / `adapter_build.ps1` off the legacy
  generator, and its eventual hard removal.
- Any SQL-target (`sql_synth.py`) equivalents for the new `add`/`abs`/
  `avg_filtered`/`not_blank` shapes beyond what was already wired in
  alongside each op (SQL support was added in lockstep with each DAX op in
  this batch, not deferred).
