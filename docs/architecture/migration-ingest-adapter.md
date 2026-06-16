# Design sketch — Migration Ingest Adapter (reverse adapter into the ALUCA IR)

> **Status:** Sketch / forward-looking. Not yet scheduled.
> **Decision context:** [`adr/0002-official-first-agent-integration-and-guided-workflow.md`](adr/0002-official-first-agent-integration-and-guided-workflow.md) (migration corollary).

## Why

"Rebuild a Tableau dashboard in Power BI without writing code" is, framed
generically, **model once → generate many**. ALUCA already has the second half:
the `generator_core` IR (BracketCompiler → DashboardSpec → adapters) **emits** to
Power BI (PBIP) and to Metabase / Superset / Grafana (`products/oss_adapters/`).
What is missing is the **first half** — a way to *ingest* an existing
third-party artifact into that same IR.

As vendor agents (Power BI Agentic, etc.) make target-tool generation a
commodity, the durable value moves to the **governance-bearing IR + Studio**:
KPI semantics, lineage, and decision logic that survive a tool switch. A
migration adapter turns ALUCA from a generator into a **migration hub**.

## Shape

Today's data flow (emit-only):

```
UseCase_Bracket.yaml ──► BracketCompiler ──► DashboardSpec (IR) ──► PBIPAdapter ──► Power BI
                                                              └────► oss_adapters ──► Metabase / Superset / Grafana
```

Proposed addition (ingest):

```
Tableau .twb/.twbx ──► TableauIngestAdapter ──► DashboardSpec (IR) ──► (existing emit path, any target)
                                           └──► draft UseCase_Bracket.yaml (KPIs, fields, layout) for human review
```

The reverse adapter is the **mirror image** of an emit adapter: instead of
`IR → tool format`, it does `tool format → IR`. The IR (`DashboardSpec`) and the
bracket schema are already the contract, so an ingest adapter plugs into the
existing pipeline without touching downstream code.

## What it would extract (and what it deliberately would not)

| Extract from source → IR | Notes |
|---|---|
| Worksheets / dashboards → pages + visual slots | maps to 3-30-300 page model where possible |
| Fields / pills → candidate KPI ids | proposed, **not** auto-bound; routed through the governed KPI catalog for human confirmation |
| Calculated fields → candidate measures | surfaced as drafts; DAX/TMDL authoring is left to the Stage-2 vendor skill (GADW) |
| Filters / parameters → slicer + filter intent | structural only |

**Deliberately not migrated automatically:** tool-specific pixel formatting,
proprietary calc semantics, and anything that would bypass KPI governance. The
adapter produces a **draft `UseCase_Bracket.yaml` + IR** for review, not a
silent 1:1 clone. Governance is the point; a lossy, reviewable bridge into the
governed model is the feature, not a bug.

## How it rides the rest of the architecture

1. **Ingest** (this adapter) → draft bracket + IR.
2. **Stage 0 gate** (`aluca preflight`) forces the draft to become a *governed*
   use case (KPIs bound, Golden Thread intact) before anything is generated.
3. **GADW Stages 1–5** then (re)generate the target — Power BI via the official
   skills, or an OSS target — from the now-governed bracket.

So migration is not a special pipeline; it is **a new entry point into the
existing one**. The reverse adapter only has to reach a valid `DashboardSpec` +
draft bracket; everything after Stage 0 is already built.

## Open questions (for a future ADR if pursued)

- Source priority: Tableau first (the PDF's case), or a more neutral source
  (e.g., a generic dashboard JSON) to avoid over-fitting one vendor's format?
- Parsing strategy for `.twb` XML: hand-rolled vs. an existing OSS parser
  (subject to the same "optional dependency, Tier-0 floor" rule as ADR-0001).
- How much layout fidelity is worth keeping vs. re-deriving from the 3-30-300
  page model on emit.
