# ADR 0017 — Generator v2: Insight-Scoring, Verification, Composition (Two-Stage)

- **Status:** Proposed — the five open decisions are **resolved (proposed 2026-07-18)** below,
  pending maintainer ratification to flip to Accepted. Stage 1 is now **prototyped**
  (`tooling/storyline/score_insights.py`), so the resolutions are grounded in working output, not
  speculation.
- **Date:** 2026-07-09 (decisions drafted 2026-07-18)
- **Scope:** How report narrative content (Header `big_idea`, Smart_Narrative, KPI-card
  emphasis) gets derived and rendered — architecture only, not an implementation plan
- **Supersedes:** —
- **Related:** [`0008-ai-orchestration-routing-tokens-tracking-roi-config.md`](0008-ai-orchestration-routing-tokens-tracking-roi-config.md),
  [`0009-wirkungs-loop-action-kpi-attribution.md`](0009-wirkungs-loop-action-kpi-attribution.md),
  [`0010-kpi-calculation-dsl-and-dax-synthesis.md`](0010-kpi-calculation-dsl-and-dax-synthesis.md)–[`0013`](0013-kpi-calculation-dsl-remaining-11-use-cases.md),
  [`../../../core/templates/page_templates/Storytelling_Principles.md`](../../../core/templates/page_templates/Storytelling_Principles.md),
  [`../../../products/fabric/powerbi/tooling/judge/llm_judge_prompt_v1.md`](../../../products/fabric/powerbi/tooling/judge/llm_judge_prompt_v1.md) (R4.2, unrelated post-hoc check, see Consequences),
  [`../../../UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`](../../../UMSETZUNGSPLAN_REPORT_EXZELLENZ.md) (Cut C5, task R5.2)

---

## Context

**What v1 actually does today (verified against the real generator code, not assumed):**
the report generator (`products/fabric/powerbi/tooling/page_scaffold_generator/`) is
**100% deterministic template/string composition of already-governed Bracket fields** —
`config_loader.py::_format_smart_narrative()` concatenates `title`/`domain`/
`strategic_kpi_id`/`evidence_grain` into a fixed f-string; `get_action_panel_content()`
formats action-code YAML fields. No LLM call exists anywhere in the generation path
(`tooling/generator_core/`, `tooling/superversion/`, and `products/` were searched;
the only LLM-adjacent artifact in the tree is the R4.2 judge prompt, which is a
post-hoc, human-gated **acceptance check**, never part of generation).

**A real, previously undocumented gap surfaced while researching this ADR:**
`core/templates/page_templates/Storytelling_Principles.md` §2 prescribes that the
Header zone render `big_idea` "verbatim from `UseCase_Bracket.yaml`" — but **no Header
visual-builder exists anywhere in `page_scaffold_generator/*.py`**. R1.1 (this plan's
own ledger) wired a Header textbox for COM-002 specifically, but as a one-off,
hand-applied PBIR edit — not through the reusable generator path. So today,
`big_idea` is a **static, hand-authored string that the generator pipeline never
actually reads**. Even once wired (C2/R2.x's job, not this ADR's), a hand-authored
string has a correctness problem this ADR exists to name: nothing recomputes it, so
it silently goes stale the moment underlying data patterns shift — a report could
keep claiming "margin is under price pressure" for months after the driver changed.

**The plan's own guardrail #2 is a hard constraint on any fix:**

> Template + Regeln, keine freie LLM-Generierung. Mehrstufig-verifiziert schlägt
> One-Shot belegt \[15]; unser deklarativer Bracket-Ansatz ist das richtige Muster
> (Inforiver-Prinzip: Standard einmal kodieren, nie pro Report \[5]).

Any redesign of how `big_idea`-class content gets produced must stay template/rule
based for the actual **text** — it may not introduce free-form LLM prose generation
into the build pipeline. The plan's own citations for R5.2 (A2P-Vis, DataNarrative)
point at architectures that separate *insight mining/ranking* from *narration* —
which is exactly the shape that fits inside this constraint, provided narration
stays template-driven.

**What already exists that Stage 1 can reuse, so this needs no new subsystem:**
ADR-0009's Wirkungs-Loop already computes governed KPI snapshots deterministically
(the `refcalc` mechanism) with an explicit honesty rule — *"Fehlt ein Snapshot →
UNCOMPUTED, nie 0"* — and ADR-0010–0013's KPI Calculation DSL is the governed,
deterministic source of the KPI values and deltas themselves. Nothing here requires
a new AI subsystem; it requires a **selection layer** on top of computation that
already exists.

## Decision

**Adopt a two-stage Generator v2 pipeline for narrative/insight content, with a
deterministic verification gate between the two stages. Neither stage is a free-form
LLM call.**

### Stage 1 — Insight Scoring (deterministic, not LLM)

For a report's governed KPI set (`orchestration.influencing_kpi_ids` and any PVM/driver
measures the Bracket references), compute each candidate's current value/delta via the
**existing** KPI Calculation DSL (ADR-0010–0013) for the report's active period, and
score each candidate on the four dimensions the plan names for this task:

- **Depth** — how much of the causal chain is explained (a named PVM driver — price/
  volume/mix effect — outranks a raw aggregate delta).
- **Correctness** — is the underlying calculation governed and resolved, never an
  `hitl`-placeholder KPI (ADR-0013's honesty rule: an unresolved calc must never be
  silently treated as a real signal).
- **Specificity** — is the candidate concrete (a named driver, segment, or SKU) rather
  than a generic top-line number.
- **Actionability** — is there a linked, executable Action Code (reuses
  `core/action_codes/` governance and ADR-0009's Wirkungs-Loop linkage) — an insight
  with a concrete next step outranks one with none.

Output: a **ranked list of structured candidate records** — `{kpi_id, direction,
magnitude, driver_ref, linked_action_code_id?}` — never prose. This is a selection
problem, not a writing problem.

### Verification gate (between Stage 1 and Stage 2, deterministic)

Before the top-ranked candidate may reach composition:

1. Its referenced measure(s) resolve in TMDL (reuse `dax_reference_validator.py`,
   already built and CI-wired in Cut C3).
2. Its snapshot is not `UNCOMPUTED` (ADR-0009's rule applies here verbatim — an
   uncomputed candidate is disqualified, never coerced to zero or skipped silently).
3. Data freshness is within tolerance (reuse the existing `Last Refresh` measures).

A candidate that fails verification is dropped and the next-ranked candidate is
tried. If none verify, composition falls back to the existing static template (no
narrative claim is rendered without a passing verification — never a guess).

### Stage 2 — Composition (still template-based — this is the guardrail-preserving part)

Map the verified, top-ranked insight record onto one of the **existing governed
narrative templates** (`Storytelling_Principles.md`'s per-page-type Big Idea
templates) via a deterministic selection rule keyed on the record's shape (e.g. a
driver-plus-linked-action-code record selects the "X is under pressure because of Y;
Z is the priority lever" template shape; a no-clear-driver record selects the
"X is on/off track vs. plan" shape). The template is filled with the record's
already-verified values — **no free text is generated at this stage either.**

This closes the real gap found above (Header/`big_idea` never wired) by replacing a
static, hand-authored, unverifiable string with a value that is **recomputed and
re-verified on every generation run** — strictly more governed than today's approach,
not less.

The R4.2 LLM Judge remains entirely outside this pipeline: a **post-hoc**, human-gated
acceptance check on the rendered screenshot, unrelated to how the content was produced.

## What this ratifies vs. defers

**Ratified here:** the two-stage-plus-verification *architecture*; that Stage 1 is a
selection/scoring problem over already-governed, already-computed values (no new
computation subsystem); that Stage 2 stays template-only (no free LLM generation,
consistent with guardrail #2); that a failing verification always falls back to the
existing static template rather than rendering an unverified claim.

**Explicitly deferred (not decided by this ADR):**

- The exact scoring formula/weights for the four dimensions — needs calibration
  against real multi-report data, not invented in a Discovery ADR.
- The template-selection rule taxonomy (how many template shapes, what triggers
  each) — a content-design task.
- Whether Stage 1 runs at generator build-time (requiring computed KPI values to be
  available then, likely via a snapshot mechanism analogous to the Wirkungs-Loop's)
  or as a separate pre-generation step — an open implementation question, see below.
- Migration path for the 16 existing Brackets' static `big_idea` fields (deprecate?
  keep as a fallback when Stage 1 has no verified candidate?).
- The actual Header visual-builder implementation and any other C2 work
  (R2.1–R2.4: Bracket-Schema erweitern, Generator erzwingt Regeln, 17 Brackets
  nachziehen) — this ADR's Stage 2 assumes that code path exists; building it is
  Cut C2's job, not this ADR's.

## Consequences

**Positive**

- Closes a real, previously silent gap: `big_idea` becomes a computed, re-verified
  value instead of a static string the pipeline never actually reads.
- No new AI/LLM subsystem — Stage 1 is a selection layer over infrastructure
  (ADR-0009 Wirkungs-Loop, ADR-0010–0013 KPI DSL) that already exists and is already
  governed, deterministic, and tested.
- Stays inside guardrail #2 (template + rules, no free LLM generation) end to end —
  Stage 1 selects, the gate verifies, Stage 2 fills a pre-approved template.
- The R4.2 LLM Judge stays a clean, separate concern (post-hoc human-gated check),
  not entangled with generation — no risk of the judge's opinion silently becoming a
  generation input, which would have reintroduced free-form generation by the back
  door.

**Negative / cost**

- The scoring rubric needs real calibration work (four dimensions, relative
  weights) before Stage 1 can run for real — non-trivial design effort, out of this
  ADR's scope.
- Stage 1 needs computed KPI values available **at generation time**, which today's
  generator does not require (it runs offline against static Bracket/TMDL content).
  Whether that means a live semantic-model connection, a pre-computed snapshot file,
  or reusing the Wirkungs-Loop's snapshot mechanism is an open question this ADR
  does not resolve.

**Neutral**

- Does not touch R4.1/R4.2 (Desktop Bridge screenshot, LLM Judge) at all — those
  remain a separate, already-scoped visual-acceptance track.
- Does not touch the semantic-model/TMDL layer — Stage 1 only *reads* already-computed
  values via the existing DSL, it does not compute anything new.

## Alternatives considered

- **Keep static, hand-authored `big_idea` strings indefinitely (status quo).**
  Rejected: doesn't scale past a handful of hand-curated pilot reports, goes stale
  by construction, and — per this ADR's own research — isn't even wired into the
  generator today, so the status quo is arguably already broken, just silently.
- **Free-form LLM narrative generation at build time (single LLM call writes the
  Big Idea from KPI data).** Rejected outright: violates guardrail #2 directly, and
  is exactly the "One-Shot" approach the plan's own cited research \[15] found
  inferior to multi-stage, verified generation.
- **Single-stage "LLM both selects and writes" (skip the split).** Rejected:
  conflates *which fact matters* with *how to phrase it*, so the output can't be
  deterministically verified — a factually-wrong sentence and a factually-right one
  are indistinguishable without re-deriving the fact from the sentence. The
  two-stage split with a hard verification gate between selection and composition is
  what makes verification possible at all, and is what the plan's cited research
  (A2P-Vis, DataNarrative) recommends this shape for.

## Open decisions (before any implementation)

1. Scoring weights for depth/correctness/specificity/actionability — calibration
   spike needed against real Bracket/KPI data across several reports, not one.
2. Generation-time vs. pre-computed-snapshot architecture for Stage 1's KPI access.
3. Template-selection rule taxonomy for Stage 2 (content-design task).
4. `big_idea` field migration/fallback policy for the 16 existing Brackets.
5. Sequencing against C2 (R2.1–R2.4): this ADR assumes a Header visual-builder code
   path that must be built there first; confirm ordering before scheduling
   implementation work against this ADR.

## Resolved decisions (proposed 2026-07-18 — pending maintainer ratification)

Grounded in a **working Stage-1 prototype built since this ADR was written**: the storyline
contract `tooling/storyline/derive_storyline.py --json` (structured findings per use case) and the
deterministic scorer `tooling/storyline/score_insights.py` (ranks findings, picks the verified
headline). The four dimensions in the prototype map to this ADR's names as: **depth** = depth,
**specificity** = specificity, **actionability** = actionability, **correctness** = the prototype's
`grounding` (KPI resolves in the catalog + is audit-grade via `standard_ref`), which is *also* the
verification gate. Every field is derived from governed Bracket/KPI data — no LLM, nothing invented.

**D1 — Scoring weights.** *Resolve:* ship the prototype's v0 weights as a **governed config**, not a
hardcoded constant — depth 0.30 / specificity 0.25 / actionability 0.30 / correctness 0.15. The low
correctness weight is deliberate: correctness is decisive as a **hard gate** (grounding == 0 ⇒
finding is ineligible to lead, ADR-0009), so it need not dominate the tiebreak score. The
calibration spike (tuning against real multi-report snapshots) stays open but **no longer blocks
build** — v0 defaults ship and produce sensible headlines today (FIN-001 leads on the OCF
"driven by collections not cost" finding; COM-002 on "concentrated in a few BUs").

**D2 — Generation-time vs. snapshot.** *Resolve:* **snapshot, not a live connection.** Split Stage 1:
(a) *narrative-structure scoring* (depth/specificity/actionability/correctness over the storyline
contract) is **offline, generation-time, needs no live data** — already built; (b) *data-magnitude
scoring* (which finding carries the biggest actual delta this period) reads a **pre-computed snapshot
via ADR-0009's Wirkungs-Loop `refcalc`**, never a live semantic-model/Fabric connection at build time.
This keeps the generator offline and deterministic (its current property) and adds no Fabric
dependency to the build.

**D3 — Template-selection taxonomy.** *Resolve:* a **small closed set of 3 shapes + static fallback**,
selected **deterministically from the insight record's shape** (which the scorer already computes):
`driver→lever` (finding on the causal thread + a linked action code) → "X is under pressure because
of Y; Z is the priority lever"; `concentration` (high specificity / named locus) → "X is concentrated
in <locus>; focus there"; `trajectory-vs-plan` (level/trend, no clear driver) → "X is on/off track vs
plan"; else the static fallback (D4). No new judgment layer — the taxonomy keys off the four
dimensions already scored.

**D4 — `big_idea` migration/fallback.** *Resolve:* **keep the 16 static `big_idea` fields as the
explicit verified-failure fallback — do not deprecate.** Stage 2 fills the selected template from the
verified top insight; if no candidate verifies, it renders the static `big_idea` (the human-curated
safety net). This makes the ADR's own "falls back to the existing static template" rule concrete and
keeps a hand-authored floor under every report.

**D5 — Sequencing vs. C2 (Header visual-builder).** *Resolve:* **decouple.** Stage 1
(selection + scoring + verification) is independent of *where* the output renders and **ships now**
(built). Stage 2 rendering into the **existing** `component_30s` `message`/`so_what` fields needs no
Header visual-builder and can follow immediately. The Header visual-builder (C2 / R2.1–R2.4) is
required **only** for the `big_idea` *Header* placement specifically → it stays a later, separate
target. Stage 1 does **not** block on C2.

**Scope note on LLM (important).** This ADR is deliberately **LLM-free end to end** (guardrail #2):
Stage 1 deterministic selection, Stage 2 template fill. The prototype's `Scorer` protocol is the seam
where a **bounded, verified LLM scorer could slot in later** — but introducing an LLM into generation
exceeds this ADR's ratified scope and must be its **own future ADR** (semantic re-scoring of
depth/specificity/actionability only, with `correctness`/grounding staying deterministic as the gate).
ADR-0017 stays deterministic; the LLM is a separate decision, not an amendment here.

**What is built vs. still to build after ratification.** Built (2026-07-18): the storyline contract,
the deterministic Stage-1 scorer with all four dimensions + the verification gate, and tests. To build
after ratification: D2(b) snapshot wiring for data-magnitude, the D3 three template shapes, and Stage 2
rendering the verified record into the `component_30s`/`big_idea` fields.

## References

| Source | What it grounds |
|---|---|
| `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` §2 (guardrail #2), Cut C5 / R5.2 row | The task definition, the four scoring dimensions, and the hard "no free LLM generation" constraint |
| `products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py` | Verified v1 state: template/string composition only, Header/`big_idea` never wired |
| `core/templates/page_templates/Storytelling_Principles.md` §2, §13 | Big Idea doctrine and the existing AI-generated-narrative grounding/provenance rules (§13) this design must stay compatible with |
| `0009-wirkungs-loop-action-kpi-attribution.md` | The `UNCOMPUTED, nie 0` honesty rule reused verbatim in the verification gate; the snapshot mechanism Stage 1 may build on |
| `0010`–`0013-kpi-calculation-dsl-*.md` | The governed, deterministic KPI value/delta source Stage 1 scores over |
| `products/fabric/powerbi/tooling/judge/llm_judge_prompt_v1.md` (R4.2) | Confirmed as an unrelated, post-hoc, human-gated check — explicitly not a generation input |
