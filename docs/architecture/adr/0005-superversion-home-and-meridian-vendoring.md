# ADR 0005 — Superversion Home & Meridian-Core Vendoring

- **Status:** Accepted
- **Date:** 2026-06-22
- **Scope:** Where the Superversion layer (ALUCA's meaning/visual layer docked onto Meridian's canonical engine) lives, and how the Meridian canonical core is brought into ALUCA without copying it or making it a hard runtime dependency.
- **Supersedes:** —
- **Related:** [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md) (I-2.1, the task this ADR ratifies; I-2.2/I-2.4 implement it), [`../../../PRODUCT_PLAN.md`](../../../PRODUCT_PLAN.md) (§0 reconciliation, §2 premium floors F2/F4), [`../../../SYNERGY_ALUCA_MERIDIAN.md`](../../../SYNERGY_ALUCA_MERIDIAN.md), [`../../../tooling/superversion/_INDEX.md`](../../../tooling/superversion/_INDEX.md), [`0004-industry-variant-use-case-tier-taxonomy.md`](0004-industry-variant-use-case-tier-taxonomy.md)

---

## Context

The Superversion (`tooling/superversion/`) docks ALUCA's meaning/visual layer — use-case
brackets, KPI catalog, the 3-30-300 layout — onto Meridian's **canonical model** contract.
The Phase-0 spike and initiative I-1 (`from_aluca.py`, `canonical_contract.py`, golden
snapshots; ✅ at COM-001/002/003, FIN-002, SCM-002) proved the dock works **standalone**,
with the canonical contract mirrored as plain dataclasses rather than imported from
Meridian.

Two facts force a home/ingestion decision before initiative I-2 proceeds:

1. **The neutral core already exists upstream.** Per `PRODUCT_PLAN.md` §0, Meridian's I-1
   shipped the canonical-core + source/target adapter pattern (its ADR-0036/0037),
   Greenfield-standalone-validated, with a conformance kit. The Superversion work is
   therefore *"dock ALUCA onto that spine"*, **not** *"rebuild a canonical engine in
   ALUCA"*. Copying Meridian's engine into ALUCA would fork the very substrate both
   products are converging on and recreate the drift this library exists to prevent.

2. **ALUCA must stay standalone (P5 / premium floor F4).** `PRODUCT_PLAN.md` §2 F4 requires
   every layer tool to run against a bare stack with **zero ALUCA-core dependency**; the
   project's invariant I4 demands "standalone AND integratable". A fresh ALUCA clone must
   build a `CanonicalModel` and run its tests **without** network access, a Meridian
   checkout, or a submodule init. The spike already honours this via the mirrored
   `canonical_contract`; the parity test `test_contract_parity_with_meridian` activates
   only when a Meridian checkout happens to be reachable.

So the question is not *whether* to depend on Meridian's engine, but **where the
Superversion lives** and **how the Meridian core is referenced** so that (a) it is never
copied/forked, (b) ALUCA still runs standalone, and (c) the contract cannot silently drift
from Meridian's real model.

## Decision

**ALUCA is the home of the Superversion source-adapter. Meridian's canonical core is
*vendored and pinned* — never copied into the tree as owned code and never a hard runtime
import. The mirrored `canonical_contract` is the standalone substrate; when the vendored
core is present it is imported instead, with a soft fallback to the mirror.**

Six rules:

1. **Home = ALUCA.** The Superversion source-adapter (ALUCA meaning/visual → canonical
   model) lives in ALUCA under `tooling/superversion/`. ALUCA owns the *source* side
   (`from_aluca`) and the *contract mirror*; it does **not** own the canonical engine or
   the *target* (stack) adapters — those are Meridian's, brought in by vendoring.

2. **Meridian core is ingested, not copied.** `core/pbi_engine` (model + parsers) is made
   reachable as a **pinned, vendored** dependency — a fixed upstream revision recorded in a
   pin file, never hand-edited in place, never re-committed as ALUCA-authored source. This
   ratifies *vendored/pinned*; the concrete mechanism is fixed in I-2.2 (see *Mechanism*).

3. **`canonical_contract` is the standalone mirror, parity-gated in CI.** It stays a
   structure-identical mirror of Meridian's `CanonicalModel` / parser dataclasses (same
   field names), so ALUCA builds and tests with **no** Meridian present (F4). The mirror is
   authoritative *only* in standalone mode. `test_contract_parity_with_meridian` is the
   drift guard. **Today it is a stub** — it checks only the `Measure` dataclass, in one
   direction, and locates Meridian via a hardcoded path, so it *skips* on virtually every
   machine. Hardening it to a real field-for-field guard is part of I-2.2's DoD (see
   *Mechanism*). Because the guard skips whenever the vendored core is absent (the normal
   fresh-clone / F4 case), **parity is enforced in CI, where the vendored core is present
   and the test is non-skippable**; the standalone mirror is therefore only as fresh as the
   last green CI parity run at the current pin. This is the accepted correctness boundary,
   not a gap to close later.

4. **Import originals when present, soft-fallback to mirror.** Code consumes the contract
   through one seam (the `canonical_contract` module). When the vendored core is available,
   that module **re-exports Meridian's originals**; when it is absent, it exposes the
   mirror. No call site imports `core.pbi_engine` directly. A missing vendored core is a
   **soft-skip + ⚠️**, never a hard error (I-2.2 DoD).

5. **Neutral core is preserved across the seam (invariant I1).** Vendoring the engine does
   **not** introduce a DAX/dialect primacy into the source adapter: measures still carry
   meaning dialect-neutrally (`expressions{}` empty at the source). I1 requires that dialect
   rendering remain a *target/stack* concern (its own design is decided in I-3, not here).
   The `test_neutral_core_no_dax_primacy` family continues to gate this regardless of
   whether the mirror or the originals are in use.

6. **The pin is drift-sensed, never auto-bumped (I-2.4).** An ALUCA-side sensor reports when
   the Meridian-core pin (or the vendored `osi-schema.json`) lags **upstream**; it
   **reports, never bumps**. Bumps are deliberate, reviewed commits that move the pin and
   re-run the parity/conformance tests. Note this senses *upstream* lag only — detecting
   *local* edits to the vendored subtree is a **distinct** mechanism (a checked-in manifest/
   hash of the synced subtree), assigned to I-2.2/I-2.4; the read-only CONTRIBUTING note
   alone is advisory and does not enforce it.

### Mechanism — vendor-sync with a pin file (recommended), finalized in I-2.2

The two viable mechanisms are a **git submodule** and a **`vendor/`-sync with a pin file**.
This ADR **recommends vendor-sync** and ratifies it as the default; I-2.2 implements it and
records the concrete pin-file format. Rationale:

- **Standalone-first (F4) wins with vendor-sync.** A fresh `git clone` of ALUCA is
  immediately runnable — no `git submodule update --init`, no recursive clone, no network.
  A submodule leaves an empty directory until initialized, which silently breaks the "clone
  and it works" guarantee and CI ergonomics.
- **Only the needed subtree is vendored.** ALUCA needs `core/pbi_engine` (model + parsers),
  not all of Meridian. Vendor-sync copies just that subtree under `vendor/meridian/` with a
  pin file (`{repo, ref/commit, synced_at, subtree}`); a submodule drags the whole upstream
  repo.
- **Drift is contained, not prevented-by-friction.** The submodule's "exact SHA" advantage
  is matched by the pin file plus the I-2.4 drift sensor and the parity test — drift is
  *detected mechanically*, so the looser coupling costs nothing in correctness.
- **Cost acknowledged:** a vendored subtree *can* be locally edited (governance risk a
  submodule resists). Mitigation: the vendored tree is treated as read-only (CONTRIBUTING
  note + the drift sensor flags unexpected local divergence), and bumps go through the
  deliberate pin-move path in rule 6.

## What this ratifies vs. defers

- **Ratified now:** ALUCA = home; Meridian core is vendored+pinned (not copied, not a hard
  dep); `canonical_contract` is the parity-gated standalone mirror with import-originals-
  when-present + soft-fallback; neutral core preserved across the seam; pin is
  drift-sensed. Vendor-sync is the recommended/default mechanism.
- **Deferred to I-2.2 (implementation):** the concrete vendoring wiring (the `vendor/`
  layout, the pin-file schema, the `canonical_contract` re-export shim) and **hardening**
  `test_contract_parity_with_meridian` into a real guard — it must (a) cover **all**
  `canonical_contract` dataclasses, not just `Measure`, (b) assert **both directions**
  (mirror missing AND extra/renamed/retyped fields vs. Meridian), and (c) locate Meridian
  via the **vendor pin path**, not a hardcoded absolute path — then prove it green against
  the ingested source in CI. A local-divergence manifest for the vendored subtree (rule 6)
  is part of the same wiring.
- **Deferred to I-2.4:** the upstream pin-drift sensor for the Meridian pin and
  `osi-schema.json`.
- **Out of scope:** the *target* (PBI/OSI stack) adapters and their contract — those are
  initiative I-3 (ADR to follow), not this ADR.

## Consequences

**Positive**
- One canonical engine, two products: ALUCA never forks Meridian's core, so the merged
  product line shares a single substrate and the Golden Thread is not duplicated.
- ALUCA stays premium-floor F4 (standalone) and F2 (deterministic): the mirror keeps clones
  runnable offline; the parity test keeps the mirror honest.
- The contract seam (`canonical_contract` as the only import point) makes the eventual
  Meridian merge a one-module swap, not a refactor — the "dock, don't rebuild" thesis is
  preserved in code structure.

**Negative / cost**
- A vendored subtree is a standing sync obligation; without the I-2.4 sensor it could drift
  silently. The sensor + parity test are therefore not optional follow-ups but part of the
  decision's integrity.
- Two code paths (mirror vs. originals) must stay behaviourally identical; the CI parity
  test (once hardened, I-2.2) is the only thing preventing them from diverging, so it must
  stay meaningful and must run where the vendored core is present. Standalone correctness
  inherits from the last green CI parity run at the current pin — not from the local clone.

**Neutral**
- The mirror remains in the tree even after ingestion (it is the standalone fallback), so
  ALUCA carries a small amount of deliberately duplicated structure by design, not by
  accident.

## Alternatives considered

- **Copy Meridian's `pbi_engine` into ALUCA as owned source.** Rejected: forks the shared
  canonical core, guarantees drift, and contradicts `PRODUCT_PLAN.md` §0 ("dock onto the
  spine, don't rebuild it").
- **Hard runtime dependency on Meridian (e.g. `pip install meridian-core`).** Rejected:
  breaks F4/I4 standalone — a bare ALUCA clone would not run; also couples release cadences.
- **Git submodule instead of vendor-sync.** Rejected as default (kept as the documented
  alternative): breaks "clone and it works", drags the whole upstream repo, and adds CI/
  contributor friction; its only edge (exact SHA pin) is already covered by the pin file +
  drift sensor + parity test.
- **Drop the mirror, depend only on the ingested core.** Rejected: the mirror *is* the
  standalone substrate (F4) and the parity oracle; removing it would make ALUCA un-runnable
  without Meridian and remove the drift guard.

## References

- Internal: [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md) (I-2.1/I-2.2/I-2.4),
  [`../../../PRODUCT_PLAN.md`](../../../PRODUCT_PLAN.md) (§0, §2 F2/F4),
  [`../../../SYNERGY_ALUCA_MERIDIAN.md`](../../../SYNERGY_ALUCA_MERIDIAN.md),
  [`../../../tooling/superversion/_INDEX.md`](../../../tooling/superversion/_INDEX.md),
  [`../../../tooling/superversion/canonical_contract.py`](../../../tooling/superversion/canonical_contract.py),
  [`../../../tooling/superversion/from_aluca.py`](../../../tooling/superversion/from_aluca.py),
  [`0004-industry-variant-use-case-tier-taxonomy.md`](0004-industry-variant-use-case-tier-taxonomy.md)
- External (Meridian, by reference — vendored, not in this repo): Meridian ADR-0036/0037
  (canonical-core + source/target adapter pattern), Meridian I-1 conformance kit.
</content>
</invoke>
