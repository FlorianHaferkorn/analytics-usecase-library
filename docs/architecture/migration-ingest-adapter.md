# Design sketch — Migration Adapter Architecture (Hub-and-Spoke, N-to-M)

> **Status:** Sketch / forward-looking. Not yet scheduled.
> **Decision context:** [`adr/0002-official-first-agent-integration-and-guided-workflow.md`](adr/0002-official-first-agent-integration-and-guided-workflow.md) (migration corollary).

## Why

"Rebuild a Tableau dashboard in Power BI without writing code" is, framed
generically, **model once → generate many**. ALUCA already has the *emit* half:
the `generator_core` IR (BracketCompiler → DashboardSpec → adapters) emits to
Power BI (PBIP) and to Metabase / Superset / Grafana (`products/oss_adapters/`).
What is missing is the *ingest* half — and it must be **tool-agnostic on both
ends**: not Tableau→Power BI, but **Tableau / Qlik / Looker / … → Core →
visualization XYZ**.

As vendor agents (Power BI Agentic, etc.) make target-tool generation a
commodity, the durable value moves to the **governance-bearing IR + Studio**:
KPI semantics, lineage, and decision logic that survive a tool switch.

## Hub-and-spoke

```
  Tableau (.twb/.twbx) ┐                                           ┌─► Power BI (PBIP, via official skills)
  Qlik (.qvf / script) ├─► Ingest adapters ─► ALUCA IR ──────────► ├─► Metabase / Superset / Grafana
  Looker (LookML)      │       (N)        (DashboardSpec +         │   Emit adapters (M)
  Power BI (PBIP)      ┘                   draft UseCase_Bracket)   └─► visualization XYZ
                                           + Stage-0 governance gate
```

**The IR is the only lingua franca.** Adapters talk **tool ↔ IR**, never
tool ↔ tool. That is the classic compiler-IR / Pandoc-AST pattern, and it is the
whole economic argument:

- **N + M adapters, not N × M.** Add Qlik = *one* ingest adapter → instantly
  migratable to *every* existing target. Add a new target = *one* emit adapter →
  instantly reachable from *every* source. Point-to-point integrations would be
  N × M and unmaintainable.
- **The hub is the product; the spokes are replaceable.** Exactly the ADR-0002
  thesis, proven by migration.

## Two design rules that make it real

1. **The IR is the contract and must be a superset.** It has to represent (or
   carry as annotations) the union of concepts across all sources/targets. A
   **capability / feature matrix** documents what each adapter supports and where
   a mapping is **lossy** — by design and reviewable.

   | Concept | Tableau | Qlik | Looker | → IR | Notes |
   |---|---|---|---|---|---|
   | Worksheet/sheet → page + visual slots | ✓ | ✓ | ✓ | `page` + slots | map to 3-30-300 where possible |
   | Field/pill/dimension → candidate KPI id | ✓ | ✓ | ✓ (LookML) | proposed, **not** auto-bound | routed through KPI catalog |
   | Calculated field / expression → candidate measure | ✓ | ✓ | ✓ | draft only | DAX/TMDL left to GADW Stage 2 |
   | Filters / parameters → slicer + filter intent | ✓ | ✓ | ✓ | structural | no tool-specific pixel formatting |
   | Tool-specific formatting / proprietary semantics | — | — | — | **dropped** | re-derived on emit |

2. **Governance in the middle, not at the edges.** Migration is a **new entry
   point into the existing pipeline**, not a separate one:

   ```
   ingest adapter → draft UseCase_Bracket + IR → Stage-0 gate (aluca preflight) → GADW Stages 1–5 → any target
   ```

   The source tool's quirks die at the IR boundary; what flows downstream is
   **governed KPI semantics**. Every migration becomes a *governed* model
   regardless of source — and the output is a draft for human review, never a
   silent 1:1 clone.

## Open questions (for a future ADR if pursued)

- **Source priority:** Tableau first (the concrete case), or a neutral source
  format first to avoid over-fitting one vendor?
- **Parsing strategy per source** (`.twb` XML, `.qvf` / Qlik load script, LookML)
  — hand-rolled vs. an OSS parser, under the same "optional dependency, Tier-0
  floor" rule as ADR-0001.
- **Fidelity vs. re-derivation:** how much source layout to preserve vs.
  re-derive from the 3-30-300 page model on emit.
- **Round-trip:** is Power-BI-in / Power-BI-out (re-platform within the same tool)
  a first-class case, or only cross-tool migration?
