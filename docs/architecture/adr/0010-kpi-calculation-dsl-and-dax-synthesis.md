# ADR 0010 — Governed KPI Calculation DSL + Deterministic DAX Synthesis

- **Status:** Accepted
- **Date:** 2026-07-03
- **Scope:** Closes Critical Befund A1 (`SUPERVERSION_ZIELBILD_REVIEW.md`) — the
  Superversion emit path produced structurally valid but semantically empty
  Semantic Models (every measure `= BLANK()`). Defines: (a) the governed,
  stack-neutral `technical.calculation` grammar in the KPI catalog schema, (b)
  where and how it is resolved (`from_aluca.py`) vs. materialized into a real
  dialect (`targets/tmdl.py` + `targets/dax_synth.py`), (c) the HITL policy for
  KPIs outside the grammar, (d) the parity-test methodology against the legacy
  generator's output, (e) the legacy generator's deprecation.
- **Supersedes:** —
- **Related:** [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md)
  (Invariant I1, corrected here), [`0006-superversion-target-adapter-contract.md`](0006-superversion-target-adapter-contract.md)
  (dialect materialization is a target-side concern), [`../../../SUPERVERSION_ZIELBILD_REVIEW.md`](../../../SUPERVERSION_ZIELBILD_REVIEW.md)
  (Befund A1/A2, Cut S-1), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md)
  (I-10.0), [`../../../tooling/superversion/eval/refcalc.py`](../../../tooling/superversion/eval/refcalc.py)
  (the pre-existing readable formula DSL this grammar is modeled on),
  [`../../../tooling/generator/schemas/kpi_definition.schema.json`](../../../tooling/generator/schemas/kpi_definition.schema.json)

---

## Context

The independent Fable-review (`SUPERVERSION_ZIELBILD_REVIEW.md`, 2026-07-02) found that
the governed KPI catalog carried *meaning + lineage* but no *formula*: `from_aluca.py`
always set `Measure.expressions = {}`, and the TMDL target (`targets/tmdl.py`, I-3.2)
always emitted a `BLANK()` placeholder when no dialect was present — for **all 16 use
cases**, with every premium-floor gate (F1–F6) passing regardless. Invariant I1
("neutral core") had been over-tightened: the doctrine's intent was *neutral formula*,
not *no formula*. The legacy PowerShell generator
(`tooling/generator/generate_tmdl_measures.ps1`) already proved deterministic DAX
synthesis was possible — its output lives, frozen, in `products/fabric/powerbi/dist/**/
_Measures.tmdl` — but that synthesis was never ported to the Python Superversion path,
creating a second, diverging emit path (Befund A2, "second doppelsilo").

## Decision

### 1. Grammar: structured YAML, not free text

`eval/refcalc.py` already defines a minimal formula DSL (`sum(col)`,
`sum(a)/sum(b)`) as the value-certification oracle. Rather than parsing that exact
string grammar for governed catalog authoring, `technical.calculation` uses the
**same primitive vocabulary encoded as structured, schema-validated YAML** (an `op`
discriminator + typed args) — see `tooling/generator/schemas/kpi_definition.schema.json`
`$defs/calculation`. This is a deliberate widening of the original "textual DSL"
framing from the task brief: a structured shape gets JSON-Schema validation for
free (wrong op / missing arg is a schema error, not a runtime parse failure) and
is strictly more robust for a *governed, catalog-authored* field, at no cost to
the "based on refcalc's DSL" intent — the op vocabulary (`sum`/`ratio`/`delta`) is
identical, just not string-serialized at the authoring layer.

Seven ops, chosen to cover every calculation pattern actually observed in the 5
MVP use cases' legacy DAX (`products/fabric/powerbi/dist/**/_Measures.tmdl`):

| op | Shape | DAX pattern |
|---|---|---|
| `sum` | one column, from this KPI's own `technical.lineage` | `SUM ( table[col] )` |
| `ratio` | `numerator / denominator` (+ optional `scale`) | `DIVIDE ( x, y ) [* n]` |
| `delta` | `minuend - subtrahend` | `[A] - [B]` |
| `delta_pct` | `(minuend - subtrahend) / ABS(subtrahend)` | variance-vs-baseline % |
| `rate` | share of rows where a flag column is TRUE | `DIVIDE ( CALCULATE ( COUNTROWS (...), flag=TRUE() ), COUNTROWS (...) )` |
| `count` | row count of a bare-table lineage entry | `COUNTROWS ( table )` |
| `hitl` | explicit "not in this grammar" marker + a `reason` string | — (documented `BLANK()`) |

A `ratio`/`delta`/`delta_pct` term (`calc_ref`) is either `{kpi: <id>}` (references
another governed KPI's own measure — Golden Thread, must exist in the catalog) or
`{column: <name>}` (a raw fact column, resolved against **this KPI's own**
`technical.lineage`, never an arbitrary table). This mixed grammar was necessary
because the legacy DAX itself mixes both styles per KPI (e.g. `COGS per Unit =
DIVIDE ( [Cost of Goods Sold Amount], SUM ( fact_sales[Quantity] ) )` — a
sibling-measure reference divided by a raw column).

`rate` was added beyond the brief's literal "sum/ratio/delta" list because it is
the ONLY way to express `supply.otif.pct` — SCM-002's **strategic KPI** — without
resorting to HITL; leaving the use case's own primary metric uncomputed would have
defeated I-10.0's purpose for that UC. `count` was added for the same reason
(`order.lines`/`shipments.count`, SCM-002 supporting KPIs, both a bare
`COUNTROWS(table)` in the legacy DAX). Both are deterministic, narrow, and
directly evidenced by real legacy DAX — not speculative grammar.

### 2. Where resolution happens vs. where DAX is materialized (Invariant I1, corrected)

- **`from_aluca.py` (source adapter, `_resolve_calculation`)** resolves the
  authored `calculation` (KPI-id refs → sibling `technical.measure_name`, column
  refs → this KPI's own `technical.lineage`) into a **fully self-contained,
  stack-neutral structure** — e.g. `{"op": "ratio", "numerator": {"kind":
  "measure", "name": "Gross Margin Amount"}, "denominator": {"kind": "measure",
  "name": "Net Sales Amount"}}` — carried as a JSON string in
  `Measure.expressions['dsl']`. This is *not* DAX; it names tables/columns/
  measures, never DAX syntax (`SUM`, `DIVIDE`, `CALCULATE`, …). A resolution
  failure (unknown KPI id, a column not in this KPI's own lineage) becomes an
  explicit `expressions['hitl_reason']` string — **never** silent `expressions={}`.
- **`targets/tmdl.py` + `targets/dax_synth.py` (stack adapter)** is the ONLY place
  that turns `expressions['dsl']` into real DAX (`dax_synth.synthesize_dax`, a
  pure function, one line of code per op). `from_aluca.py` never imports
  `dax_synth`.
- **Invariant I1 restated:** "neutral core" means the source adapter carries a
  neutral *formula* — it must never carry a `dax`/`sql` dialect key. It is
  explicitly allowed (now required, where derivable) to carry the neutral `dsl`
  key. `tests/test_from_aluca.py::test_neutral_core_no_dax_primacy_all_ucs` was
  updated to assert `set(m.expressions) <= {"dsl", "hitl_reason"}` (previously
  `m.expressions == {}`) — this is the doctrine correction the review demanded.

### 3. HITL policy: counted, never silent

13 KPIs referenced by the 5 MVP use cases fall outside the grammar (SUMX/AVERAGEX
iterators, DISTINCTCOUNT with multiple simultaneous filters, multi-term VAR
chains, or a documented pre-existing lineage/table mismatch — see
`tooling/superversion/tests/test_calculation_coverage.py::KNOWN_HITL_KPI_MEASURE_NAMES`
for the full list with reasons). Each carries `op: hitl` + a `reason` string in
its catalog YAML. `targets/tmdl.py::hitl_gaps(canonical)` enumerates every
placeholder measure (mirrors the existing `targets/pbir.py::hitl_gaps` pattern);
every `BLANK()` in the emitted TMDL has an adjacent `/// HITL: <reason>` comment —
`test_calculation_coverage.py::test_zero_silent_blank_across_all_16_use_cases`
enforces this mechanically across all 16 use cases, not just the 5 MVP ones.
FIN-002 and SCM-002 reference no HITL KPI at all — both are **fully computed**
(0 gaps).

### 4. Parity methodology: normalized column-set, not byte-equality

Cut S-1 explicitly allows "semantisch, nicht zwingend byte-gleich". The legacy
generator wraps most ratios in `VAR x = SUM(...) ... RETURN DIVIDE(x, y)`; the new
synthesizer emits the same ratio inline (`DIVIDE ( SUM(...), SUM(...) )`) — same
value, different DAX shape. `tests/test_dax_parity_legacy.py` normalizes both
sides to the **set of terminal `table[Column]` (and bare `COUNTROWS(table)`)
references they touch** (VAR-bindings inlined, one level of sibling
bracket-measure-reference resolved against the same legacy file) and asserts set
equality — 39 parity cases across the 5 MVP use cases, all green. Where a KPI has
no legacy counterpart at all (new territory, e.g. `margin.ebitda.pct`), parity is
reported as "nothing to diverge from", not a failure. Genuine divergences (none
found) would be listed in `KNOWN_DIVERGENCES` with a reason, never silently
reconciled (mirrors the Ledger's own "ehrlich, nicht glätten" discipline).

### 5. Legacy generator: warn-deprecated, not hard-removed

`generate_tmdl_measures.ps1` now emits a `Write-Warning` on every invocation
naming this ADR and the new emit path. It is **not** hard-blocked by default: it
is still wired into `.github/workflows/linux-generation.yml` and
`products/fabric/powerbi/tooling/adapter_build.ps1`, and migrating those callers
is materially larger than I-10.0's scope (governed formula + synthesis + parity).
A `-RejectDeprecatedLegacyGenerator` switch makes it refuse to run outright, for
use once callers have migrated. ⚠️ UNKLAR: migrating `linux-generation.yml` /
`adapter_build.ps1` off the legacy path, and eventually deleting it, is
explicitly out of this task's scope — flagged, not silently done.

## What this ratifies vs. defers

**Ratified:** the `calculation` grammar (7 ops) and its schema; the resolve
(source) / synthesize (target) split; the HITL-is-counted-not-silent policy; the
column-set parity methodology.

**Deferred (out of scope for I-10.0):**
- DSL→SQL (or any other dialect) transpilation — the grammar is dialect-agnostic
  by construction (a `dax_synth`-equivalent module for another target is a
  bounded follow-up), but only `dax_synth.py` exists today.
- The remaining ~13 HITL KPIs in the 5 MVP use cases, and the other 11 use cases
  entirely untouched by this task (their KPIs were never in scope) — all
  discoverable via `hitl_gaps()`, none silently dropped.
- Migrating `linux-generation.yml` / `adapter_build.ps1` off the legacy
  generator, and its eventual hard removal.
