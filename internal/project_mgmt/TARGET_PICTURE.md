# Target picture

**Purpose:** Stable, testable definition of "what done looks like" for this repository. Used to align milestones and acceptance criteria. Not a roadmap (roadmap = how we get there; this = what we are building toward).

**Language:** English.

**Last updated:** 2026-02-20

---

## 1. North star (one sentence)

The Analytics Use Case Library is **complete** when the Golden Thread (Strategy → KPIs → Use Cases → Action Codes) is fully operational, all governed artifacts pass Stage 1 and the Registry Gate, and customers can implement decision-oriented use cases from specs and Aurora—including a fully generated 3-30-300 report layer and optional Strategy Pattern / AI-urgency tooling where scoped.

---

## 2. In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| Golden Thread integrity and traceability (KPI catalog, action codes, brackets, registry). | Custom deployment to customer tenants (we deliver specs and reference implementation). |
| 3-30-300 UX in the report (3s status, 30s diagnosis, 300s action + evidence). | Full productisation of proposal costing or Fabric Orchestrator beyond current CLI/scripts. |
| Stage 1 and Registry as mandatory gates; documentation and automation that keep the repo consistent. | Implementing every possible use case domain; we deliver framework + exemplar (e.g. Aurora). |
| Aurora as proof: open PBIP, report, semantic model, measures, RLS; extensible to more domains. | Non-Fabric reporting platforms (out of scope for this repo’s deliverables). |
| Strategy Pattern and AI-urgency as defined capabilities where documented in backlog/milestones. | |

---

## 3. Quality bar ("Done" means)

- **Stage 1 green:** `.\tooling\run_stage1_checks.ps1` passes (all 11+ checks).
- **Registry Gate:** `py tooling/ontology/registry_builder.py --out-dir tooling/ontology/out --strict` passes.
- **Docs:** No claims in key docs (e.g. presentation_status_and_roadmap, README) that contradict current behavior; doc references point to existing paths/artifacts.
- **Merge rule:** No merge to main without passing Stage 1 and (where required) human approval per CODEOWNERS.

---

## 4. Capability map (high level)

| Capability | Brief | Status today (reference) |
|------------|-------|---------------------------|
| Golden Thread | Strategy → KPIs → Use Cases → Action Codes; single KPI catalog; brackets as SSOT. | In production ([internal/presentation_status_and_roadmap.md](../presentation_status_and_roadmap.md)). |
| 3-30-300 | 3s status, 30s diagnosis, 300s action page with action payload and evidence. | Partially implemented; 300s page not yet fully generated from action-code YAML. |
| Registry & Stage 1 | Referential integrity, no orphans, governance checks; CI gate. | In production. |
| Fabric / Power BI | Code-first semantic model and report; Aurora PBIP; measures from KPI catalog. | In production (Aurora proof). |
| Strategy Pattern / AI urgency | Strategy patterns document; tooling for urgency/reasoning. | Conceptual; backlog. |
| Synthetic data & scaffold | Synthetic data generation; page scaffold generator. | Partial; stubs and TODOs in [internal/technical_backlog.md](../technical_backlog.md). |

---

## 5. Acceptance criteria (testable)

- **AC1:** Every use case in the inventory has a valid UseCase_Bracket and passes Stage 1 (factsheet vs KPI, action codes, governance roles).
- **AC2:** Aurora: opening `showcases/aurora_group/semantic_models/CoreActionReady.pbip` loads report and model; measures exist and display folders align with use cases.
- **AC3:** 300s page (when implemented): action text and evidence table can be sourced/generated from action-code YAML and layout config (per [internal/vision/phase2_backlog.md](../vision/phase2_backlog.md)).
- **AC4:** Project completion (current milestone): blockers from content review resolved; review adjustments and zero-tolerance documentation in place; CI/release without Stage-1 skip documented.

Use this document to align milestone goals and Epic acceptance criteria; update when the north star or scope changes formally.
