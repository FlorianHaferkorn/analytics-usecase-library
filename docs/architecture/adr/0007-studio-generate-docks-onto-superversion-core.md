# ADR 0007 — Studio Generate Docks onto the Superversion Core

- **Status:** Accepted
- **Date:** 2026-06-24
- **Scope:** Where the Studio cockpit's **deliverables** come from — the *generate* seam between the `studio/` web app and the governed Python Superversion (I-1…I-5). Ratifies decision **E-1** raised by the I-6.1 inventory. Defines the direction + contract of the seam; the concrete bridge is implemented in I-6.2/6.3.
- **Supersedes:** —
- **Related:** [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md), [`0006-superversion-target-adapter-contract.md`](0006-superversion-target-adapter-contract.md), [`../studio-capability-inventory.md`](../studio-capability-inventory.md) (I-6.1, decision E-1), [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../../UMSETZUNGSPLAN_SUPERVERSION.md) (I-6.2/6.3 implement), [`../../../tooling/superversion/_INDEX.md`](../../../tooling/superversion/_INDEX.md)

---

## Context

The I-6.1 Studio-Inventur ([`../studio-capability-inventory.md`](../studio-capability-inventory.md))
established the Studio is a real app: Blueprint/Authoring, Approvals, and Catalog
all EXIST and are wired to Core artifacts. But **Generate** runs through a
**parallel TypeScript path**: an in-app IR-builder (`studio/src/lib/delivery/ir-builder.ts`)
feeds `fabric-adapter.ts` (TMDL/PBIP), `oss-adapter.ts` (SQL/Evidence), and
`cicd-adapter.ts` — none of which call the governed Python Superversion that
I-1…I-5 built and tested (`from_aluca` → `CanonicalModel`, the target-adapter
registry of ADR-0006, the TMDL/PBIR emitters with official validators I-3.2/3.3,
the Golden-Thread gate I-3.4, the E2E smoke I-3.5, the gov/eng/arch engines I-5.3,
the tool packs I-5.4).

That is **two sources of truth** for "what a bracket produces". It violates the
Golden-Thread principle (one governed definition; reference, don't re-define) and
duplicates exactly the surface that I-1…I-5 hardened. Left unresolved, I-6.2/6.3
would build the customer-facing flow on the **un-governed** seam.

This ADR decides which seam I-6 builds on.

## Decision

**The Studio's authoritative generation docks onto the Python Superversion core.
The Studio calls the governed pipeline (`from_aluca` → `targets.render` (ADR-0006)
→ Golden-Thread gate I-3.4 → E2E smoke I-3.5) through a thin bridge and surfaces
its artifacts + gate report. The existing TypeScript adapters are demoted to a
non-authoritative *preview* renderer — never the deliverable a customer ships.**

Five rules:

1. **One source of generated truth.** Customer-shippable deliverables (TMDL, PBIR,
   target artifacts) and their pass/fail come from the Python Superversion, not from
   the TS adapters. The Studio **calls** the core; it never re-derives `emit`.

2. **Thin bridge, contract-shaped.** The Studio→Python boundary returns the same
   shape the core already produces — the target contract's `{relative_path: content}`
   (ADR-0006) plus the E2E gate report (per-stage PASS/FAIL/SKIP, I-3.5). Generation
   stays pure/deterministic (Invariant I2) and official-first validation (Invariant I3)
   runs **in Python**, where the official validators already live. The bridge transport
   (subprocess/CLI vs. local HTTP) is an implementation detail of I-6.2/6.3, not fixed here.

3. **TS adapters = preview only, labeled, non-authoritative.** They may render a fast
   in-UI preview, but every preview is marked as such and is never presented as a
   gate-validated artifact. If preview and core diverge, the **core wins** by definition.

4. **Gate report is visible (I-6.3).** The Golden-Thread gate (I-3.4) and E2E smoke
   (I-3.5) results are surfaced in the UI so the customer sees *why* a deliverable is
   green/red — the gate is a first-class output of Generate, not a hidden CI step.

5. **Honest degradation (no fake-green).** If the Python bridge is unavailable
   (standalone/offline, I-6.5), the Studio shows the **preview** explicitly flagged
   "not gate-validated" and offers no shippable deliverable — it never passes preview
   off as validated output (Ehrlichkeit v3). This is the rollback: the un-bridged Studio
   degrades to preview, it does not silently emit un-governed artifacts.

## What this ratifies vs. defers

- **Ratified now:** the *direction* (Studio docks onto the Python core), the
  bridge **shape** (`{path:content}` + gate report), TS-adapters-as-preview, the
  gate-report-visible requirement, and honest degradation.
- **Deferred:** the concrete bridge implementation and transport (I-6.2 ingest-side,
  I-6.3 target-side + gate-report UI), how the TS preview is kept from masquerading as
  truth (a label/contract detail of I-6.3), and any later mechanical drift guard between
  preview and core.

## Consequences

**Positive**
- One governed truth: the work of I-1…I-5 (validators, gates, engines, packs) becomes
  the Studio's engine instead of being shadowed — the Golden Thread holds end-to-end.
- The customer sees the *real* gate result (I-3.4/I-3.5), not a TS approximation.
- New stacks added to the Python target registry (ADR-0006, I-7) appear in the Studio
  for free — no second adapter to write in TS.

**Negative / cost**
- A Studio→Python bridge must exist and be operable in the customer's environment
  (local-first, I-6.5) — added moving part vs. the all-in-TS status quo.
- The TS adapters are not deleted (they keep value as preview), so a *preview-vs-core*
  divergence is possible; rule 3 makes the core authoritative and rule 5 forbids
  fake-green, but a mechanical drift guard is deferred (named here, not yet built —
  same posture as ADR-0006's parity boundary).

**Neutral**
- Bridge transport is deliberately unspecified; I-6.2/6.3 pick subprocess/CLI vs. local
  HTTP on the standalone (BYO-key, local-first) constraints of I-6.5.

## Alternatives considered

- **Keep both paths (TS for UI speed, Python for CI/service gate).** Rejected as the
  authoritative seam: two truths is precisely the drift the Golden Thread forbids, and it
  would have the customer ship TS-emitted artifacts the Python gate never saw. Retained
  only in the demoted, non-authoritative *preview* role (rule 3).
- **Rip out the TS adapters entirely.** Rejected: they give a genuinely useful instant
  in-UI preview without a round-trip to Python; deleting them costs UX for no governance
  gain once they are non-authoritative.
- **Port the Python core to TypeScript.** Rejected: re-implements (and must re-test) the
  emitters, official validators, gates, engines, and packs in a second language — a third
  truth, the opposite of docking.

## References

- Internal: [`../studio-capability-inventory.md`](../studio-capability-inventory.md) (I-6.1, E-1),
  [`0006-superversion-target-adapter-contract.md`](0006-superversion-target-adapter-contract.md),
  [`0005-superversion-home-and-meridian-vendoring.md`](0005-superversion-home-and-meridian-vendoring.md),
  [`../../../tooling/superversion/e2e_smoke.py`](../../../tooling/superversion/e2e_smoke.py) (gate report, I-3.5),
  [`../../../tooling/superversion/_INDEX.md`](../../../tooling/superversion/_INDEX.md)
