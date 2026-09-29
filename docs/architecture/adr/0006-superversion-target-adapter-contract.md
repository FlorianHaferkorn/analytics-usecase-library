# ADR 0006 — Superversion Target (Stack) Adapter Contract

- **Status:** Accepted
- **Date:** 2026-06-23
- **Scope:** How the Superversion layer emits stack-specific artifacts (Power BI/TMDL, PBIR, OSI, …) FROM the canonical model — the *target* side of the adapter pattern, complementing the *source* side (`from_aluca`, I-1). Defines the contract only; concrete adapters are separate tasks.
- **Supersedes:** —
- **Related:** [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../plans/UMSETZUNGSPLAN_SUPERVERSION.md) (I-3.1 ratified here; I-3.2/I-3.3 implement adapters), [`../../../tooling/superversion/targets/base.py`](../../../tooling/superversion/targets/base.py), [`../../../PRODUCT_PLAN.md`](../../plans/PRODUCT_PLAN.md) (§2 F1/F2/F4)

---

## Context

I-1 docked ALUCA's meaning/visual layer onto the canonical model (`from_aluca`,
*source* side). Delivery (PRODUCT_PLAN Q15) needs the *target* side: emit validated,
deterministic stack artifacts **from** that canonical model.

Meridian already solved this generically (its ADR-0036, `core/pbi_engine/target/
registry.py`): one contract — `emit(canonical) -> {relative_path: content}` — plus a
registry and a generic `render(stack_id, canonical, dest)` dispatch. A new stack is a
module with `emit()` + one `register(...)` call; the core never changes. Meridian ships
9 live targets (pbir, pbip, osi, rill, evidence, cube, databricks, snowflake, duckdb) on
exactly this contract.

ALUCA must not fork that engine (ADR-0005). But it needs the contract *present in ALUCA*
so the Superversion's own target work (TMDL emit I-3.2, PBIR-via-official-skill I-3.3) has
a stable seam, standalone-runnable, and 1:1 portable when ALUCA docks onto Meridian.

## Decision

**Adopt Meridian's target-adapter contract verbatim as ALUCA's own
`tooling/superversion/targets/base.py`: a `TargetAdapter` (id, label, fmt, `emit`,
data_platform, visualization, status), a `REGISTRY`, and a generic
`render(stack_id, canonical, dest)`. This ADR ratifies the *contract only* — no concrete
adapters are registered yet.**

Five rules:

1. **One contract: `emit(canonical) -> {relative_path: content}`.** Pure, deterministic
   (Invariant I2), no I/O — a map from the canonical model to text files. `render()` does
   the writing and validates the shape (`{str: str}`), failing loudly on a breach.

2. **Registry + generic dispatch.** `register()`/`get()`/`available()`/`render()`. A new
   stack = an `emit()` module + one `register(...)` entry — no change to the contract or
   the dispatch (ableitbar, as in Meridian).

3. **Field names + `emit` signature are identical to Meridian's `TargetAdapter`** (ADR-0036),
   so the seam is 1:1 portable: docking onto Meridian swaps this module for the originals
   without touching adapters (ADR-0005 "dock, don't rebuild").

4. **CanonicalModel only through the seam.** `targets.base` imports `CanonicalModel` from
   `canonical_contract`, never `core.pbi_engine` directly (ADR-0005 rule 4). Targets consume
   the canonical model; they never read ALUCA brackets or Meridian sources.

5. **Contract first, adapters later, official-first.** The registry ships **empty**.
   Concrete adapters are separate tasks and must clear the premium floors: TMDL/semantic
   emit (I-3.2) under the TMDL hard-rules; PBIR report via the **official** MS skill +
   `check_pbir` 0 errors (I-3.3, Invariant I3) — never a bespoke renderer. Dialect/DAX is a
   *target-side* concern here (Invariant I1: the source stays dialect-neutral).

## What this ratifies vs. defers

- **Ratified now:** the contract (`emit` signature), the registry + `render` dispatch, field
  parity with Meridian, the seam-only import rule, and "contract ships empty".
- **Deferred:** every concrete adapter — TMDL (I-3.2), PBIR via official skill (I-3.3),
  the Golden-Thread gate (I-3.4), the E2E smoke (I-3.5); further stacks (OSI/Tableau, I-7).

## Consequences

**Positive**
- A new stack costs one `emit()` module — the agnostic-core promise is structural, not
  aspirational; ALUCA and Meridian share the same target contract.
- `render()`'s shape check turns a contract breach into a loud failure, not silent garbage.
- Determinism (F2) and standalone (F4) are inherited: `emit` is pure and the contract
  imports only the seam.

**Negative / cost**
- Two definitions of the same contract (here + Meridian) must stay aligned; field parity is
  the portability guarantee and must be kept (a breach is "angleichen", per I-3.1 DoD).
  **Accepted boundary (unlike the model seam):** this target-contract parity is *not*
  mechanically guarded today. The model seam has `test_contract_parity_with_meridian`
  (ADR-0005 rule 3) because Meridian's `model`+`parsers` are vendored; Meridian's
  `target/registry.py` is deliberately **not** vendored here (it pulls 9 heavy adapters —
  see Alternatives), so there is nothing to assert against. Until ALUCA vendors/adopts the
  target registry (I-7 / the Meridian dock), parity is maintained by review, and a mechanical
  parity guard symmetric to ADR-0005 rule 3 is added **at that point**. This mirrors
  ADR-0005's precedent of naming an unguarded interval explicitly rather than implying a
  guarantee the code does not yet provide.
- An empty registry is intentionally inert until I-3.2/I-3.3 — the value lands with the
  first official-validated adapter, not with this ADR.

**Neutral**
- `status` defaults to `geplant`: ALUCA marks adapters `live` only once they pass their
  official validator (F1), unlike Meridian where 9 are already live.

## Alternatives considered

- **Import Meridian's `target.registry` directly (vendored).** Rejected for now: the target
  registry pulls all 9 concrete adapters (heavy deps: pbir/osi/snowflake/…); ALUCA needs
  only the *contract* at I-3.1. Vendoring the contract surface (this ADR) keeps the import
  graph minimal; ALUCA may re-export Meridian's registry later (like the model seam) when it
  adopts those targets.
- **Bespoke render path per stack (no registry).** Rejected: that is exactly the pattern
  Meridian's ADR-0036 replaced; it recreates per-stack drift and blocks the agnostic claim.
- **Define a richer contract than Meridian (extra fields/hooks).** Rejected: diverging from
  Meridian breaks 1:1 portability for no present need; extend only when a concrete adapter
  demands it, and align both sides then.

## References

- Internal: [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md),
  [`../../../tooling/superversion/targets/base.py`](../../../tooling/superversion/targets/base.py),
  [`../../../tooling/superversion/_INDEX.md`](../../../tooling/superversion/_INDEX.md),
  [`../../../PRODUCT_PLAN.md`](../../plans/PRODUCT_PLAN.md) (§2 F1/F2/F4)
- External (Meridian, by reference): Meridian ADR-0036 (canonical core + source/target
  adapter pattern), `core/pbi_engine/target/registry.py` (the `emit`/registry contract).
