# AI-Readiness & PBIR Tooling — Implementation Plan

> **Status:** Proposed · **Owner:** Analytics Platform · **Created:** 2026-06-11
> **Source inputs:** [`pbir.tools`](https://github.com/maxanatsko/pbir.tools) (PBIR automation CLI) and
> [Tabular Editor — *AI readiness and best practices for semantic models*](https://tabulareditor.com/blog/ai-readiness-and-best-practices-for-semantic-models-a-comprehensive-guide).
> **Builds on:** the AI-description standard merged in PR #283 (`ai_description.py`, `AI_Description_Standard.md`, H7 binding integrity).

---

## 1. Background & problem statement

PR #283 made semantic-layer descriptions a **governed projection** of the catalog: KPI catalog + measure dictionaries + data contracts → TMDL `///` blocks and viz tooltips. The Tabular Editor AI-readiness guide validates that direction and exposes one structural gap and several smaller ones:

- **The synonyms/Values we author land only as `///` description *text*.** Native Power BI Q&A and Copilot consume the model's **linguistic schema** (`cultures` / `linguisticMetadata`), not description prose. So an LLM that is *handed the TMDL file* sees our synonyms, but in-product natural-language (Copilot/Q&A) does **not**. This is the headline gap.
- **Grounding anchors are partial.** Column `Values:` exist; the optional `example_question` catalog field is defined but unwired.
- **No AI-surface hygiene gate.** Nothing flags visible key/technical columns or descriptions that merely restate the object name (both called out by the guide as anti-patterns).

`pbir.tools` is a Python PBIR-automation CLI ("built for agents") that overlaps our existing stack (`pbi-quality validate`, `page_scaffold_generator`, H7, orchestrator publish). Its **non-commercial license** rules it out as a shipped dependency — consistent with our standing position (no third-party install requirement for customers). It is valuable as a **capability benchmark** for our own validator and agent-read ergonomics, nothing more.

## 2. Goals / Non-goals

**Goals**
- G1 — Governed synonyms & values reach the **actual linguistic schema**, so in-product Copilot/Q&A natural-language works, not just file-level LLM reasoning.
- G2 — Strengthen grounding anchors (example questions, complete enumerated values) from the governed source.
- G3 — Make AI-readiness **measurable and gated** (a scorecard metric + validator checks), the same way H7 made binding integrity enforceable.
- G4 — Match the useful agent-read/bulk-edit ergonomics of `pbir.tools` in our **own** tooling, with no external runtime dependency.

**Non-goals**
- N1 — Adopting `pbir.tools` (or any non-commercial third-party) as a runtime/build dependency.
- N2 — Auto-generating synonyms with an LLM at build time. Synonyms remain **curated in the governed catalog** (the guide explicitly warns AI-generated synonyms are suggestions, not truth).
- N3 — Authoring the 47 missing non-Commercial DAX expressions (tracked separately as the golden-build content gap).

## 3. Guiding principles

1. **One governed source, many projections.** The catalog/contracts stay the SSOT; the linguistic schema becomes a *third* projection alongside `///` and viz tooltips. No new hand-authored truth.
2. **Prove on Aurora.** Every task ships with an Aurora Commercial demonstration (the only fully golden-build domain).
3. **Gate what we claim.** Each readiness property gets a check; "done" means the gate is green and red when the property is removed.
4. **Benchmark, don't depend.** `pbir.tools` informs parity targets; we never bundle it.

## 4. Success metrics

| Metric | Baseline (today) | Target |
|---|---|---|
| Q&A/Copilot synonym coverage (governed synonyms present in linguistic schema) | 0% | 100% of Commercial entities with catalog synonyms |
| `example_question` projected onto strategic measures | 0% | 100% of Commercial strategic/influencing measures with the field |
| Enumerated `Values:` coverage on Commercial dimension columns | partial | 100% of enumerable columns |
| AI-surface hygiene violations (visible keys / name-restating descriptions) on Commercial | unmeasured | 0 |
| Health scorecard | H1–H7 PASS | H1–H8 PASS (new **H8 AI-Readiness**) |
| H7 Report Binding Integrity | 100% | 100% (must not regress) |

## 5. Workstreams, tasks & DoDs

Effort key: **S** ≤0.5d · **M** ~1–2d · **L** ~3–5d. Priority: P0 (do first) … P2.

### Epic A — Linguistic schema projection (Copilot/Q&A readiness) · **P0**

> Closes the headline gap: governed synonyms/values → the model's `cultures`/`linguisticMetadata`, not just `///` text.

| ID | Task | DoD / Acceptance criteria | Size | Deps |
|---|---|---|---|---|
| **A1** | Confirm/extend the governed source: `synonyms` on KPIs (exists) and on data-contract columns; document the linguistic-schema target format. | Aurora `dim_org.Region`, `Channel`, and strategic measures carry curated synonyms in catalog/contract; schema validates; format note added to `AI_Description_Standard.md`. | S | — |
| **A2** | Generator: emit a linguistic-schema artifact (TMDL `cultures` / `linguisticMetadata` synonyms) in the PBIP adapter, sourced from A1. Idempotent; round-trips through the generator. | Regenerating `Commercial.SemanticModel` produces a linguistic schema where `Region → {Sales Region, Geo}`, `Net Sales Amount → {Revenue, Umsatz}`, etc.; re-run yields identical output; PBIR/TMDL hooks pass. | L | A1 |
| **A3** | Gate: add **H8 "AI-Readiness / Linguistic Coverage"** to the health scorecard + a `pbi-quality` check. | H8 computes coverage; PASS on Commercial; turns red when a governed synonym is dropped from the linguistic schema (proven by a fixture toggle). | M | A2 |
| **A4** | Docs: define linguistic-schema projection as the **third projection** in `AI_Description_Standard.md`; update the Linux-generation doc. | Standard shows source → `///` + viz + linguistic; reviewer can trace one Aurora entry end-to-end. | S | A2 |

**Aurora proof (Epic A):** in `Commercial.SemanticModel`, NL phrases "Umsatz" and "Sales Region" resolve to `Net Sales Amount` / `Region` via the committed linguistic schema; H8 green.

### Epic B — Grounding anchors & examples · **P1**

| ID | Task | DoD / Acceptance criteria | Size | Deps |
|---|---|---|---|---|
| **B1** | Wire the optional `example_question` catalog field into the measure `///` block + annotation, via the enricher. | `margin.gm.pct` renders its example question; enricher idempotent; no `///` style-hook violations. | M | — |
| **B2** | Complete enumerated `Values:` on Commercial dimension columns from the data contracts. | Every enumerable Commercial dim column carries `Values:`; gap reported, then 0. | S | — |
| **B3** | *(Stretch)* Instruction annotations: a small set of governed NL→measure example pairs for the strategic KPI. | One example-pair block on `margin.gm.pct`; documented as optional. | M | B1 |

**Aurora proof (Epic B):** `margin.gm.pct` shows definition + example question + drivers; Commercial dims fully enumerated.

### Epic C — AI-surface hygiene (model clarity) · **P1**

| ID | Task | DoD / Acceptance criteria | Size | Deps |
|---|---|---|---|---|
| **C1** | Hidden-by-default check for key/technical columns; flag visible surrogate/FK keys. | Validator lists visible keys on Commercial; after cleanup, 0; folded into H8. | M | A3 |
| **C2** | Description-quality lint: flag descriptions that merely restate the name or are below a minimum-information bar. | Lint runs over Commercial measures/columns; 0 violations after fixes; CI-runnable. | M | A3 |

**Aurora proof (Epic C):** Commercial passes hygiene with 0 visible keys and 0 name-restating descriptions.

### Epic D — Agent-read ergonomics (benchmark `pbir.tools`, no dependency) · **P2**

| ID | Task | DoD / Acceptance criteria | Size | Deps |
|---|---|---|---|---|
| **D1** | Read commands over our `dist/` (parity with `pbir ls`/`tree`/`model`): list pages, visuals, measures, bindings — agent-friendly output. | `pbi inspect` enumerates Commercial report pages/visuals + semantic model measures from `dist/`; no third-party dep. | M | — |
| **D2** | Wildcard bulk-set for visual properties (parity with `pbir set`). | Bulk-set a format property across Commercial visuals; `dist` diff reviewed; H7 still 100%. | M | D1 |

**Aurora proof (Epic D):** `pbi inspect` reproduces the Commercial report tree; a bulk-set leaves H7 at 100%.

## 6. Sequencing & milestones

```
M1 (Readiness core)   : A1 → A2 → A3 → A4        [P0]  ← unlocks the Copilot/Q&A gap
M2 (Anchors+Hygiene)  : B1, B2 ‖ C1, C2          [P1]  ← parallelizable after A3
M3 (Agent ergonomics) : D1 → D2                  [P2]  ← benchmark parity
```

- **M1** is the critical path and the highest-value increment; it is independently shippable.
- **M2** runs in parallel once H8 (A3) exists to gate it.
- **M3** is optional polish; defer if priorities shift.

## 7. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Linguistic-schema TMDL format complexity (`cultures`/`linguisticMetadata`) | Med | Med | Reference MS Learn TMDL/TOM docs; build a round-trip test in A2 before wiring breadth. |
| Over-synonyming degrades NL (guide's warning) | Med | Med | Governed catalog only (N2); no build-time LLM generation; curate per business usage. |
| Scope creep into the 47 missing-DAX content gap | Med | Med | Explicit non-goal (N3); A–D are metadata/tooling, not DAX authoring. |
| `pbir.tools` non-commercial license contamination | Low | High | Benchmark only (N1); never import/bundle; D-epic is independent code. |
| H7 regression from generator changes | Low | High | H7 stays a required gate; re-run scorecard on every A2/D2 change. |

## 8. Out of scope / future

- Authoring missing non-Commercial DAX (separate golden-build content track).
- Full all-domain golden-build re-baseline (tracked in `linux-generation.md`).
- Packaging our agent commands as a published plugin (revisit after D).

## 9. Open questions / decisions

- **D-1 (decision):** Confirm the linguistic-schema emission target — TMDL `cultures` block in the SemanticModel definition (preferred) vs. a separate linguistic file. *Default: TMDL `cultures` in-definition.*
- **D-2 (input):** Source of curated synonyms — extend data contracts with a `synonyms` list per column (preferred), or a dedicated synonyms registry. *Default: data-contract `synonyms`.*

---

### Definition of Done (program level)
H1–H8 all PASS on Commercial (H7 still 100%); Aurora Commercial demonstrates in-product NL resolution via the committed linguistic schema; every new gate proven to fail when its property is removed; no third-party runtime dependency introduced.
