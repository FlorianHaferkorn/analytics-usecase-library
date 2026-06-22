# ALUCA → Premium Product: Build Plan to Customer-Shippable

> **Status:** Product/build plan · 2026-06-22 · grounded in repo state (ALUCA +
> Meridian) and the honest readiness map (`KPI_Framework_Discovery_ALUCA_EN_v3.xlsx`).
>
> **⚠️ UPDATE 2026-06-22 — Meridian moved (origin/main 18.06. + branch
> `meridian-competitive-analysis` 19.06.). The local mount was on 17.06.; several
> assumptions below are now outdated IN OUR FAVOUR. Reconciliation in §0 before reading
> the rest — some phases shrink or are already partly done.**
> **Decision inputs (from owner):** tool-agnostic from day one; customer-operable once
> set up; flexible **compiler** over data-gov/eng/arch + semantic model + tool stack;
> **Power BI/Fabric as first E2E sample stack**; first use cases = cross-industry, later
> industry packs; every layer generator (report-gen, visual library, page templates,
> documenter — incl. gov/eng/arch) **standalone AND integratable**; **Studio = the
> cockpit** for the core and everything before/after it; **merge the ALUCA + Meridian
> visions**; binding constraint = **premium quality bar**.
> Assumptions flagged **⚠️ UNKLAR**.

## Contents
1. [What we're building (one paragraph)](#1-product)
2. [Definition of "Premium" (the quality bar)](#2-premium)
3. [Product architecture (compiler + cockpit + layer tools)](#3-architecture)
4. [Where ALUCA stands vs. this target (grounded)](#4-gap)
5. [The shippable unit & first use cases](#5-shippable)
6. [Build roadmap (phases, DoD, gates)](#6-roadmap)
7. [Quality system (how "premium" is enforced, not promised)](#7-quality)
8. [Risks, sequencing, what we deliberately defer](#8-risks)

---

## 0. Reconciliation with latest Meridian (2026-06-22) {#0-reconcile}

The plan below was grounded on the 17.06. mount. `origin/main` (18.06., D-243..D-247) and
the branch `claude/meridian-competitive-analysis-gabisv` (19.06., initiative **I-10
"Produkt-Finalisierung & Reifegrad-Schließung"**) already advanced exactly this direction.
**Meridian is running its own product-finalization initiative that overlaps heavily with
this plan.** Honest deltas, code-verified against those refs:

| Plan assumption (17.06.) | Reality (18–19.06.) | Effect on plan |
|---|---|---|
| Multi-stack is "Meridian-only, unproven" | **OSI adapter now fully jsonschema-validated against the vendored official OSI schema** (`target/vendor/osi-schema.json`, greenfield+brownfield, 8/8 tests); DAX deliberately removed from OSI dialect enum (DAX = derived only) | **Phase 6 "agnostic proof" is partly DONE** — OSI is a real second, officially-validated target. Tool-agnostic claim is no longer just architecture. |
| Physical data layer (G4) is a gap | **Direct-Lake generation + per-domain star schema + OneLake load + dim_date/dim_user_access (RLS)** landed (origin/main) | G4 materially narrows; Fabric data layer is now generated, not just modelled. |
| gov/eng/arch + meaning tools "thin/Beta" | **M1/M2/M4/M5 (KPI-Catalog, Use-Cases, Action-Codes, Copilot-Readiness) bumped Beta→Production** after QA-review with DoD evidence (I-10.6) | §4 maturity table is too pessimistic; the meaning/governance tooling is closer to premium than stated. |
| "Premium = build the enforcement" | **Already built:** `make check-versions` (SemVer+changelog gate), `make check-hygiene`, `check-tmdl`, **ADR-0039 per-product maturity+roadmap status board**, **ADR-0040 Fabric-IQ deferred-with-trigger** | My §7 quality system largely EXISTS in Meridian; reuse it, don't design it. |
| "We need to decide the merge architecture" | Meridian's I-1 already shipped the canonical-core + source/target adapter pattern (ADR-0036/0037), Greenfield-standalone validated (I-4), conformance kit (I-1.4) | The **neutral core substrate exists**; Phase 0/1 shrink to "dock ALUCA onto it", not "build it". |

**Consequence — the plan is still right in shape, but the starting line is further along:**
1. **This is no longer "build a product from ALUCA"; it is "land the ALUCA meaning/visual
   layer onto Meridian's now-finalizing product spine".** Meridian's I-10 is the de-facto
   productization track — ALUCA work should plug into it, not run parallel.
2. **Phases 3, 6, 7 (value-cert evals, agnostic proof, quality system) are partly
   pre-built** (OSI validation, check-versions/hygiene, ADR-0039 board). Reuse.
3. **⚠️ UNKLAR / must-check before executing:** (a) the local ALUCA mount and the Meridian
   mount are different repos — confirm whether the merge target is Meridian's `main` or the
   `competitive-analysis` branch (it carries I-10 + the Wettbewerbsanalyse). (b) Whether
   `meridian-competitive-analysis` already contains an ALUCA-merge intent — its name
   suggests this exact analysis may already be in flight there. **Pull/diff that branch
   before starting Phase 0**, or risk duplicating work.
4. **Still genuinely open (unchanged by the update):** the **report/dashboard delivery gap
   (Q15)** — Direct-Lake is data-layer, not PBIR report rendering; **value certification
   against live data (Q29)**; **customer-operable Studio** (still cockpit, not self-serve);
   **ALUCA→core docking** itself.

**Net:** down-scope the plan — Phases 0/1 (core), 6 (agnostic), 7 (quality) are largely
absorbed by Meridian's I-1/I-10. The real remaining ALUCA-specific premium work is
**delivery (Q15), value-cert (Q29), the ALUCA meaning-layer dock, and the customer cockpit.**

---

## 1. What we're building {#1-product}

A **tool-agnostic analytics compiler** that turns governed business meaning
(strategy → KPIs → use cases) into validated, audited, shippable artifacts across the
full data stack — **data governance, data engineering, data architecture, semantic
model, and report/visual layers** — with **Power BI/Fabric as the first fully proven
target**. Each layer ships as a **standalone generator/auditor/documenter** that also
**plugs into the ALUCA core**. **Studio is the cockpit** the customer operates: it
maintains the core (the meaning) and connects everything *before* the core (sources,
ingest, gov/eng/arch reality) and *after* the core (semantic models, reports, deploy).
It is the **merged ALUCA + Meridian product**: ALUCA's meaning/visual layer + Meridian's
canonical engine, audit catalogs, multi-stack targets, and deliverable engine.

It is **not** a BI tool (Power BI/Tableau/Cube remain render targets), **not** an LLM
generator at runtime (LLM is authoring-only), and **not** a data platform (it models and
checks meaning, it does not host data).

---

## 2. Definition of "Premium" (the quality bar) {#2-premium}

"Premium" must be testable, not aspirational. A component is premium-ready only if it
passes **all six** floors — each is a gate that turns red, not a claim:

| # | Premium floor | How it's proven |
|---|---|---|
| F1 | **Passes the target platform's OFFICIAL validators, 0 errors** | e.g. `powerbi-report-author validate` / `check_pbir` green on every emitted artifact |
| F2 | **Deterministic & reproducible** | byte-stable re-run of the same approved spec; diffable; no LLM on the build/test path |
| F3 | **Semantically grounded** | every measure traces to a strategic anchor (Golden-Thread gate); every AI suggestion carries provenance |
| F4 | **Standalone-runnable** | the layer tool runs against a bare customer stack with zero ALUCA dependency (`check_core_independence` equivalent) |
| F5 | **Documented to handover standard** | branded docs (business + technical), per-layer documenter output, no "tribal knowledge" |
| F6 | **Tested with real evals, not just syntax** | value-level checks + ≥2 reference ontologies (not only one demo tenant) |

**Rule:** "client-ready" in any status report = passes F1–F6. The v3 readiness map showed
only 2/10 components clear that today honestly — premium is the work of getting the rest
there, not relabeling them.

---

## 3. Product architecture {#3-architecture}

Three planes, mapped to the merged vision. (Detailed engineering rationale: see
`SYNERGY_ALUCA_MERIDIAN.md` §6–§8.)

```
 BEFORE THE CORE            THE CORE (meaning)          AFTER THE CORE
 (sources / reality)        vendor-neutral compiler     (targets / delivery)
 ┌──────────────────┐       ┌────────────────────┐      ┌───────────────────────┐
 │ Brownfield ingest │ ──▶  │ Canonical model     │ ──▶  │ Semantic-layer targets │
 │ (PBI/Tableau/Qlik)│      │ strategy→KPI→UC→     │      │ PBI-TMDL · Cube · OSI · │
 │ Greenfield spec   │      │ measure→visual       │      │ Databricks · Snowflake  │
 │ Gov/Eng/Arch      │      │ — no stack primacy   │      │ Report/visual targets   │
 │ reality (audit)   │      │ expressions{} per    │      │ Documenter per layer    │
 └──────────────────┘       │ dialect              │      │ Deliverables (DOCX/XLSX)│
        ▲                    └─────────┬──────────┘      └───────────────────────┘
        │                              │
        └──────────  STUDIO = COCKPIT  ┴───────────────────────────────┘
           maintains the core · connects before & after · approvals · health
        ╔══════════════════════════════════════════════════════════════╗
        ║ CROSS-CUTTING: Quality floors F1–F6 · Golden-Thread gate ·      ║
        ║ official-first validators per stack · provenance · scorecard    ║
        ╚══════════════════════════════════════════════════════════════╝
```

**Layer tools (each standalone + integratable, F4):** report generator, visual library,
page-template engine, report documenter — and the **gov / eng / arch** auditor+documenter
per layer. ALUCA today has the semantic/visual layer tools and artifacts
(`visual_registry.yaml`, `layout_330300`, page_templates/, the generators); it has **no
gov/eng/arch engines** — those come from Meridian (`gov_engine`, `dataarch_engine`,
`dataeng_engine`). This is the single hardest dependency of the merge.

**Compiler principle:** the core is the IP. It stays neutral; each stack is an adapter.
"Flexible compiler over the stack" = the customer picks data store × semantic layer ×
viz tool independently, and the same core feeds all (synergy doc §7, three free axes).

---

## 4. Where ALUCA stands vs. this target (grounded) {#4-gap}

From code + the v3 readiness map. ⬤ premium-ready · ◑ exists, not premium · ○ missing.

| Capability | State | Gap to premium |
|---|---|---|
| Meaning core: KPI catalog, brackets, golden-thread | ⬤/◑ | schema-enforced + populated; completeness self-declared (validate vs real data) |
| Schema standard / structured definitions | ⬤ | meets F1–F3 already |
| Source→data mapping, data contracts | ⬤ | present, structured |
| KPI→TMDL generation (Power BI) | ◑ | **proven** (`dist/*.SemanticModel/_Measures.tmdl` exists), but only PBI; official-first not wired |
| Report/dashboard delivery (PBIR) | ○ | **prototype/template-copy — the hard gap (Q15)**; must adopt official MS skill |
| Value certification | ○ | no value-vs-live-data check (Q29); 103/127 "manual review" |
| Multi-stack targets (Cube/Databricks/Snowflake/OSI) | ○ in ALUCA / ⬤ in Meridian | **must come from Meridian** — core merge |
| Gov / Eng / Arch layer tools | ○ in ALUCA / ◑–○ in Meridian | **must come from Meridian**; tool-specific packs missing in both (G7) |
| Studio cockpit | ◑ | already routed (blueprint/generate/approvals/catalog…); needs the "after-core" deploy + the gov/eng/arch panels + premium UX |
| Deliverable engine (branded DOCX/XLSX) | ○ in ALUCA / ⬤ in Meridian | comes from Meridian |
| Tests/CI | ◑ | 57 tests + CI; needs value-level evals + ≥2 reference ontologies |

**The honest summary:** ALUCA owns a premium-grade *meaning + visual-definition* layer.
Everything from semantic-model-emit outward to a shippable, multi-stack, audited, branded
deliverable is **either prototype (PBIR) or lives only in Meridian**. So "make ALUCA a
premium product" = **execute the merge** (synergy doc), then **close delivery + value
certification**, then **harden for customer operation**.

---

## 5. The shippable unit & first use cases {#5-shippable}

**First shippable unit (MVP-premium):** *"Governed KPI framework → certified Power BI
semantic model + report, customer-operable via Studio, for a small set of universal use
cases — built tool-agnostic so the same core later emits other stacks."*

**First use cases (cross-industry, relevant to nearly every company):** start with 3–5
that every company recognizes and that exercise the full chain. Candidates from ALUCA's
existing brackets (verify against `core/usecases/UseCase_Inventory.md`):
- Revenue / Sales performance (net sales, margin)
- Cost / OPEX control (COGS, cost variance)
- Customer value & retention (CLV, retention, NPS)
- Operational reliability (OTIF / delivery)
- ⚠️ UNKLAR: a finance close / cash KPI set — confirm a bracket exists.

Rationale: these are universal, already partly defined in `golden_20.yaml`, and prove the
compiler on meaningful breadth before industry packs. Industry packs (manufacturing first
— Meridian already has a sketch) come **after** the universal set is premium-grade.

**Customer-operable means (the bar for "ship"):** install/setup path, Studio runs the
core, the customer can author a use case → approve → generate → validate → get a
deliverable, without you in the loop — and a bare-stack standalone mode per layer tool.

---

## 6. Build roadmap (phases, DoD, gates) {#6-roadmap}

Format per GOI §9: each phase has **Input · Output · Done-when · Rollback**. Risk-first.
Phases gate: do not start N+1 until N's "Done-when" is green. Maps to synergy-doc Z-stages.

### Phase 0 — Merge spike & decision (de-risk everything) → Z0  ✅ PASSED (2026-06-22)
**Result:** `tooling/superversion/from_aluca.py` builds a `CanonicalModel` from the COM-001
bracket + KPI catalog; **7/7 tests green** (`tooling/superversion/tests/test_from_aluca.py`),
incl. byte-stable determinism and **field-parity with Meridian's real `Measure`**. Output:
fact_sales with 10 measures (neutral, no DAX baked in), 2 governance roles, 2 report pages
with 5 measure-bound visuals from the 3-30-300 layout. **The merge thesis holds — ALUCA's
meaning/visual layer docks onto Meridian's canonical contract.** Remaining detail to wire:
the `component_300s` evidence grid maps to a non-binding card (acceptable for v0; refine in
Phase 2). Original spec below.

- **Build:** the W0 mapping spike (Bracket+golden_20 → Meridian `CanonicalModel`) on one
  use case, through `check_pbir`; decide core home (neutral module above `pbi_engine`).
- **Input:** COM-001 bracket + catalog. **Output:** valid CanonicalModel, `check_pbir`
  0 errors; written ADR fixing the merge architecture.
- **Done-when:** one universal use case round-trips Bracket→core→TMDL→validate green.
- **Rollback:** none (read-only spike). **Gate:** if it fails, the merge thesis is wrong —
  stop and redesign. *This is the single most important step; everything below assumes it passes.*

### Phase 1 — Neutral core + `from_aluca` + Golden-Thread gate → Z0/Z1
- **Build:** neutralize the DAX-primary measure model (`expressions{}` first-class);
  `from_aluca` source adapter (port the pure-Python IR compiler); `validate_golden_thread()`
  as a gate.
- **Done-when (F2,F3):** same approved spec re-runs byte-stable; every emitted measure has
  a strategic anchor or the gate fails; PBI emit still green.
- **Rollback:** `expression` stays as fallback field; adapter is additive (ALUCA standalone unaffected).

### Phase 2 — Close the delivery gap (PBIR, official-first) → Z1
- **Build:** replace ALUCA's prototype PBIR rendering with the **official MS skill**
  (`microsoft/skills-for-fabric` / `powerbi-report-authoring`) as the PBI stack adapter;
  wire report generator + visual library + page-template engine on top.
- **Done-when (F1):** a full report for a universal use case validates 0 errors via the
  official validator; generated deterministically (F2).
- **Rollback:** keep prototype renderer behind a flag until the official path is green.
- **This closes Q15 — the one "does not exist yet".**

### Phase 3 — Value certification + eval suite → Z2 (premium F6)
- **Build:** value-level verification (KPI numbers vs. a reference dataset, not just
  structure); ≥2 reference ontologies (not only one demo tenant) as a regression eval.
- **Done-when (F6):** a wrong KPI value is caught by an automated gate; evals run in CI.
- **Rollback:** mark value-cert as "advisory" until stable. **Closes Q29.**

### Phase 4 — Per-layer tools standalone+integratable, incl. gov/eng/arch → Z2 (F4)
- **Build:** bring Meridian's gov/eng/arch engines + deliverable (DOCX/XLSX) engine into
  the product; ensure each layer tool (report-gen, visual lib, page templates, documenter,
  gov/eng/arch auditor) runs **standalone** and **integrated**.
- **Done-when (F4,F5):** each tool runs against a bare stack with zero core dependency AND
  through the core; each emits branded handover docs.
- **Rollback:** ship the proven subset (PBI + semantic + report) first; gov/eng/arch as a
  later module if capacity-bound.

### Phase 5 — Studio as customer cockpit (premium UX) → customer-operable
- **Build:** elevate Studio from internal cockpit to customer-operable: before-core panels
  (connect sources, gov/eng/arch reality), after-core panels (target selection, deploy
  hand-off), authoring→approval→generate→validate→deliverable flow end-to-end; setup/onboarding.
- **Done-when:** a customer completes the full flow for a universal use case without the
  builder present; premium UX pass (no raw YAML editing required).
- **Rollback:** service-assisted mode (you operate Studio for the client) as interim.

### Phase 6 — Tool-agnostic proof (second stack) + packaging → ship
- **Build:** prove the neutral core with a **second semantic-layer target** (Cube or
  Databricks Metric Views) so "tool-agnostic from day one" is demonstrated, not just
  architected; package install/license/docs; pricing/offer.
- **Done-when:** the same approved core emits PBI **and** one other stack, both validating;
  a customer can install and run setup unaided.
- **Defer to LATER:** industry packs, closed-loop/impact (G2), team/multi-tenant (G5).

---

## 7. Quality system (premium enforced, not promised) {#7-quality}

Premium fails if quality is a phase instead of a constant. Mechanisms:

- **One gate layer over everything** (F1–F6): every layer tool, generator, and the Studio
  flow must pass the same conformance kit (Meridian `conformance.py` + ALUCA Stage-1/Drift
  merged). A red gate blocks ship — for skills, generators, grounding, and adapters alike.
- **Official-first per stack** (P1): adopt MS/dbt/Cube validators; never hand-roll what the
  vendor validates. Pin externals + drift sensor.
- **Determinism boundary** (P2): LLM only in authoring; HITL approval is the lock; build/test
  are byte-stable. KPI authoring may use **task-right model routing** (small model for
  extraction/classification, large only for synthesis) with a per-step token budget as a
  health metric.
- **Two reference ontologies minimum** (F6): regression evals beyond one demo tenant — this
  is what stops "looks done" from shipping.
- **QA+SA double-review** on every premium-gating deliverable (as applied to the synergy doc):
  QA = facts vs. code, SA = architecture/coherence.

---

## 8. Risks, sequencing, what we deliberately defer {#8-risks}

**Top risks:**
1. **Neutral core is harder than a field rename** — DAX-primacy may sit deep. *Mitigation:*
   Phase 0 spike measures it before committing Phase 1.
2. **Gov/eng/arch depth is thin in Meridian too** (pbi_engine ~80% of mass). *Mitigation:*
   ship PBI + semantic + report premium-grade first; gov/eng/arch as Phase 4 module, not MVP blocker.
3. **Premium bar vs. solo capacity** — six floors across many tools is large. *Mitigation:*
   narrow the MVP to 3–5 universal use cases on PBI; breadth (stacks, industries) is post-ship.
4. **Studio scope creep** — "cockpit for everything" is unbounded. *Mitigation:* Phase 5
   scopes Studio to exactly the one E2E flow; everything else stays service-assisted first.

**Sequencing logic:** de-risk the merge (P0) → make the core neutral + traceable (P1) →
**make it actually deliver** (P2, closes the one hard gap) → **make it certifiable** (P3) →
broaden tools incl. gov/eng/arch (P4) → make it customer-operable (P5) → prove agnostic +
package (P6). Revenue-capable earliest at end of P2–P3 (service-assisted), fully
customer-operable at P5–P6.

**Deliberately deferred (GOI §3 transparency):**
- **Industry packs** — after the universal use-case set is premium.
- **Closed-loop / impact analysis (G2)** — genuine new R&D; not in the ship path.
- **Team/multi-tenant/RBAC (G5)** — the Nagarro-scale concern; customer-operable-solo first.
- **Live deploy into tenant (G1)** — separate track, depends on tenant access; hand-off
  artifact ships first.
- **3rd+ stacks beyond the agnostic proof** — adapter work, demand-driven.

**Next concrete step:** run Phase 0 (the merge spike) on one universal use case. It is
small, read-only, and decides whether the whole product thesis holds. Everything in §6
is downstream of that one green check.
