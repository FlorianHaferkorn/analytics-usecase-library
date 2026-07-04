# ADR 0012 — Governed KPI Calculation DSL → Databricks SQL Synthesis

- **Status:** Accepted
- **Date:** 2026-07-04
- **Scope:** Closes the "Deferred" item in [ADR-0010](0010-kpi-calculation-dsl-and-dax-synthesis.md)
  ("DSL→SQL (or any other dialect) transpilation... only `dax_synth.py` exists
  today"). Proves the governed `technical.calculation` DSL (ADR-0010, extended
  by ADR-0011) is genuinely stack-agnostic by adding a second synthesizer,
  `targets/sql_synth.py`, and wiring it into the two SQL-flavored targets
  (`targets/databricks.py`, `targets/osi.py`) that previously fell back to
  emitting a bare measure name as a fake "expression" — the same Befund-A1-class
  gap ADR-0010 closed for DAX, now closed for these two targets.
- **Supersedes:** —
- **Related:** [`0010-kpi-calculation-dsl-and-dax-synthesis.md`](0010-kpi-calculation-dsl-and-dax-synthesis.md),
  [`0011-kpi-calculation-dsl-grammar-extension.md`](0011-kpi-calculation-dsl-grammar-extension.md),
  [`../../../tooling/superversion/targets/sql_synth.py`](../../../tooling/superversion/targets/sql_synth.py),
  [`../../../tooling/superversion/targets/dax_synth.py`](../../../tooling/superversion/targets/dax_synth.py)

---

## Context

`targets/osi.py` (I-7.1) and `targets/databricks.py` (I-7.2) predate the I-10.0
calculation DSL. Both always emitted `m.expression or m.name` as a measure's
"expression" — and since `from_aluca.py` has kept `Measure.expression == ""`
for every measure since I-10.0 (dialect-neutral core; the real formula lives in
`expressions['dsl']`), that fallback was **always** taken: every OSI metric and
every Databricks Metric View measure carried its own bare NAME as a fake
"SQL"/"MDX" expression, for every KPI across all 16 use cases — the exact same
class of defect Review Befund A1 found and ADR-0010 fixed for `targets/tmdl.py`,
just unnoticed on these two secondary targets because neither has an official
online validator that checks expression *correctness* (only structural JSON/
YAML shape).

## Decision

### 1. `targets/sql_synth.py` — a second pure synthesizer, not a rewrite of `dax_synth.py`

Mirrors `dax_synth.py`'s contract exactly (`synthesize_sql(resolved: dict) ->
str`, pure function, `SynthesisError` on malformed/unsupported input) but
targets Databricks SQL (the dialect a Metric View's `measures[].expr` and
Databricks-workspace SQL both speak):

| DSL op | DAX (`dax_synth`) | SQL (`sql_synth`) |
|---|---|---|
| `ratio` | `DIVIDE ( a, b )` | `TRY_DIVIDE ( a, b )` — a real Databricks SQL builtin, null-safe like `DIVIDE` |
| sibling-measure ref | `[Measure Name]` | `MEASURE ( name )` — Databricks Metric Views' own official sibling-measure-reference builtin (verified against `docs.databricks.com/.../metric-views/data-modeling/composability`) |
| column ref | `SUM ( table[col] )` | `SUM ( col )` — bare (a Metric View is single-source; no `table[...]` qualification needed) |
| `rate`/`distinctcount`/`count_threshold` filters | `= TRUE()` / `CALCULATE(...)` | `CASE WHEN ... THEN ... END` — the portable ANSI-SQL idiom for a filtered aggregate (Metric View measures have no separate per-measure `filter` key — confirmed against the vendored `databricks_metricview.schema.json`, which only allows `name`/`expr`/`comment`) |

11 of the 16 ops translate to a flat SQL aggregate expression this way. **4 do
not, and `sql_synth` says so explicitly** (`SynthesisError`, never a guessed
expression): `sumx_over_key`, `avgx_over_key`, `pvm_volume_effect`,
`pvm_price_effect`. DAX's `SUMX ( VALUES ( key ), CALCULATE ( value ) )`
pattern is fundamentally "aggregate per key, then aggregate across keys" — in
SQL that needs a `GROUP BY key` subquery composed with an outer reducer, which
a single Metric View `expr` string (or a single OSI `Expression.dialects[].
expression` string) cannot express. Faking it as a flat `SUM(value)`/`AVG(value)`
would only be correct when the value is already at the exact same grain as the
key (true for both of today's two real callers, `crm.lifetime_revenue.amount`
and `crm.clv.amount` — but that's an assumption about data grain the DSL
resolution layer has no way to verify generically). Guessing wrong here means a
silently incorrect number in a governed KPI — worse than an honest gap. Per
this repo's own "Ehrlichkeit v3" doctrine (already the explicit rationale for
`osi.py`'s MDX-not-SQL labelling and `databricks.py`'s `beta` status): **HITL,
not guessed.**

### 2. Wiring: same resolve/synthesize precedence as `targets/tmdl.py`

- **`targets/databricks.py`**: `_sql_for(measure)` tries a real `expressions['sql']`
  override first (parity with `dax_synth`'s `expressions['dax']` precedence),
  then `sql_synth.synthesize_sql(json.loads(expressions['dsl']))`, else a
  deterministic `NULL` placeholder (SQL's own "no value" literal — the
  Metric-View analogue of DAX's `BLANK()`) with the HITL reason surfaced via
  the measure's `comment` field (the schema already allows `comment`; no
  schema change needed). `hitl_gaps(canonical)` added, mirroring
  `targets/tmdl.py::hitl_gaps`.
- **`targets/osi.py`**: `_dialects_for(measure)` always tries `dax_synth` first
  (MDX dialect — all 16 ops resolve, matching `targets/tmdl.py`'s coverage
  exactly) and *additionally* tries `sql_synth` (a **DATABRICKS** dialect entry
  — OSI 0.2's `Dialect` enum has a dedicated `DATABRICKS` value, distinct from
  generic `ANSI_SQL`; `MEASURE(...)`/`TRY_DIVIDE(...)` are Databricks-specific
  builtins, so labelling them `DATABRICKS` rather than `ANSI_SQL` is the honest
  choice, not `ANSI_SQL` overreach). A metric can therefore carry 1 or 2
  dialect entries depending on whether its op has a flat SQL shape. Only when
  **neither** resolves does OSI fall back to the metric-name placeholder + a
  `HITL:`-prefixed `description` (OSI's `Metric.expression` is schema-required,
  so there is no BLANK()-style empty value to fall back to — the reason has to
  travel via `description` instead). `hitl_gaps(canonical)` added here too,
  narrower than `databricks.py`'s (a gap here means neither MDX nor DATABRICKS
  resolved, not just DATABRICKS).

### 3. Result

49 of the 53 authored `technical.calculation` KPIs synthesize real Databricks
SQL (the same 4 ops as above are the only gaps); all 5 MVP use cases' OSI
metrics carry an MDX dialect for every resolvable KPI and a DATABRICKS dialect
for 49 of them. Both targets' existing official/docs-derived schema validation
(`test_osi_target.py::test_osi_validates_against_official_schema`,
`test_databricks_target.py::test_metricview_validates_against_docs_schema`)
continue to pass unchanged — this is a content fix, not a structural one.

## What this ratifies vs. defers

**Ratified:** `sql_synth.py`'s 11-op coverage and Databricks-SQL dialect
choices (`TRY_DIVIDE`, `MEASURE()`, `CASE WHEN` filters); the explicit 4-op
HITL scope-out for per-key aggregation; the OSI multi-dialect wiring.

**Deferred (explicitly out of scope):**
- A GROUP BY-subquery or windowed-aggregate composition strategy for
  `sumx_over_key`/`avgx_over_key`/`pvm_volume_effect`/`pvm_price_effect` — would
  require either Metric View "joins"/composability features or a
  `targets/databricks.py` emission shape beyond one flat `expr` per measure;
  materially larger than this task.
- Any dialect beyond Databricks SQL (Snowflake, generic ANSI SQL, Tableau,
  MAQL — all present in OSI's `Dialect` enum) — `sql_synth.py` is explicitly
  Databricks-flavored (`TRY_DIVIDE`, `MEASURE()` are not portable SQL); a
  generic-ANSI-SQL synthesizer would need its own null-safe-division and
  sibling-reference strategy (e.g. CTEs) and is a separate follow-up.
- Making `targets/databricks.py`'s status `live` (still `beta` — the
  authoritative validator is a live Databricks workspace, unchanged from I-7.2;
  this task only fixed expression *content*, not the validation-gate story).
