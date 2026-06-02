# Studio Rebuild — Progress Tracker

**Branch:** `rebuild/studio-v2`  
**Last updated:** 2026-06-01  
**Agent program:** See plan `studio_agent_program` + `AGENT_BRIEF.md`.

---

## Documentation gate (R0 + E0)

| Artefact | Status | Notes |
|----------|--------|-------|
| `STUDIO_UX_RESEARCH.md` | Done | Comparable tools + UX methodologies |
| `DETAIL_IA.md` | Done | Entity kinds, routes, tabs |
| `PROGRESS.md` | Done | This file |
| PM sign-off Ziel-IA | Pending | Flo: confirm §3 in STUDIO_UX_RESEARCH + PD-1 default |

---

## Phase checklist (REBUILD_PLAN)

| Phase | Goal | Status | Last verified |
|-------|------|--------|---------------|
| 0 | Safety nets, baseline | Partial | BASELINE.md — Studio build not re-run on Windows |
| 1 | Shell + tokens + routing | Done | StudioAppShell wired; redirects + `/templates` |
| 1.5 A | Library Metrics + Sidebar | Done | PHASE_1_5_SPRINT_A_SUMMARY.md |
| 1.5 B | Detail polish | Partial | DetailClient UI; no persist |
| 2 | Library full (5 tabs) | Done | 5 tabs + loaders |
| 3 | Use Case Detail + Cascading AI | Done | Tabs, compare, reconcile, audit |
| 4 | Canvas lineage | Done | Lineage + Golden Thread tabs |
| 5 | Overview / Dashboard v3 | Done | Real audit, drift, Golden 20 |
| 6 | Wizard full | Done | AI draft + `/api/ai/wizard/save` |
| 7 | Report Templates | Done | T1–T4 gallery + Tweaks |
| 8 | API audit + archive | Partial | `docs/api-inventory.md` |

---

## Agent program — Epic status

| Epic | Description | Status |
|------|-------------|--------|
| **R0** | UX research persist | **Done** |
| **E0** | Detail IA contract | **Done** |
| **0** | PROGRESS + baseline + prompts | **Done** (build PASS 2026-05-29) |
| **1** | P0 Integration (AppShell live) | **Done** (pending lint/e2e gate) |
| **2** | Canvas + Library + Detail persist | **Done** |
| **3** | Use Case Detail + Cascading AI | **Done** |
| **5** | Overview v3 (audit + drift) | **Done** |
| **6** | Wizard + persist API | **Done** |
| **7** | Report Templates gallery | **Done** |
| **8** | API inventory doc | **Partial** |

---

## Epic 1 slices (next work)

| Slice | Task | Status | Verifier |
|-------|------|--------|----------|
| 1.1 | `(studio)/layout` → `AppShell` | Done | StudioLayoutShell |
| 1.2 | Settings / events fix | Done | Topbar → Settings modal |
| 1.3 | Legacy redirects + `/templates` | Done | next.config redirects |
| 1.4 | `e2e/studio-v3-shell.spec.ts` | Done | Run gate below |

**Go/No-Go Epic 1:** build + lint + e2e green; Settings, ⌘K, N, Library→Detail manual smoke.

---

## Validation commands (from repo root)

```powershell
cd studio
npm run build
npm run lint
npm test
npm run test:e2e
```

```powershell
# Optional full repo gate
.\tooling\quality\run_quality_gate.ps1 -Summary -SkipStage1
```

Record results below after each epic.

### Last gate run

| Command | Date | Result |
|---------|------|--------|
| `npm run build` | 2026-05-30 | PASS (Epic 5 Overview + Canvas focus) |
| `npm run lint` | 2026-05-29 | FAIL — `next lint` CLI bug (invalid `studio/lint` dir) |
| `npm test` | — | Not run |
| `npm run test:e2e` | — | Not run |

---

## Agent prompt checklist (per slice)

**Implementer must read:**

1. `REBUILD_DECISIONS.md` (relevant §)
2. `DATA_WIRING.md` (relevant §)
3. `STUDIO_UX_RESEARCH.md` (§5 anti-patterns)
4. `DETAIL_IA.md` (if touching routes/Detail/Library)
5. `design-reference/README.md` (if touching UI)

**Verifier must check:**

- Anti-patterns in `STUDIO_UX_RESEARCH.md` §5
- `DETAIL_IA.md` §8 when routes/Detail change
- `PHASE1_AUDIT.md` §9 for visual parity
- No `any`; no mock FRAMEWORK data

---

## Blockers / decisions

| ID | Item | Owner |
|----|------|-------|
| PD-1 | Overview: admin vs mockup dashboard | Flo |
| P0 | AppShell not in production layout | Resolved Epic 1 |
| P0 | Settings button broken (`studio:open-tweaks`) | Resolved Epic 1 |

---

## Change log

| Date | Change |
|------|--------|
| 2026-05-29 | R0+E0 docs; PROGRESS initial |
| 2026-05-29 | Epic 3: Use Case Detail tabs, compare, cascading reconcile, audit |
| 2026-05-29 | Epic 5: Overview audit/drift/Golden 20; Canvas `?focus=` deep link |
| 2026-05-31 | Epic 6–7: Wizard save, templates gallery; API inventory |
| 2026-06-01 | Baukasten Gate 0: PAGE_TEMPLATE_DOCTRINE, PAGE_TYPE_TAXONOMY, VISUAL_BAUKASTEN, REPORT_ENGINE_TARGET_ARCHITECTURE, IMPLEMENTATION_ROADMAP docs |
| 2026-06-01 | Baukasten Gate 1: template_manifest.yaml + visual_registry.yaml + JSON schemas + TS types + ir/specs.py alignment; all 16 brackets patched with page_type + template_variant |
| 2026-06-01 | PBIP Enforcement: run_fabric_checks + check_pbir_schema; _speaking_report_name sanitizes; test_dist_report_coverage.py CI gate; COM-001 structure fixed; XD-004 stub |
| 2026-06-01 | Schema hardening: category_field + comparison + status_logic in component_30s; evidence_pack in documentation; all 16 brackets 0 errors |
