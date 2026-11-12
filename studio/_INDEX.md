---
last-reviewed: 2026-11-12
shelf-life-days: 90
---
# studio — ALUCA Studio (_INDEX)

> ALUCA Studio ist die Next.js-App über den Artefakten in `../core/`: lesen, gegen die Schemas
> prüfen, bearbeiten, an Adapter übergeben. Im Code heißt sie noch „ActionReady Studio“. Sie ist
> das Nagarro-Produkt dieses Repos und bleibt ein **eigenständiges Produkt** (Entscheidung Florian,
> 12.11.2026): kein Teil des Emissionskerns `../tooling/superversion/`, eigener Build, eigene Tests,
> eigene Doku. Für Code ist `README.md` der Einstieg (Quick start, Skripte, Ordnerkarte), für
> Konventionen `CLAUDE.md`; dieser Index routet in die Doku und hält ihr Register.

| Feld | Wert |
|---|---|
| Stand | 2026-11-12 |
| Rolle | L0-Navigation für `studio/`; Register aller `.md` außer `README.md` |
| Abgelöst | Der Marker `.claude-no-index` (Studio war bis 12.11.2026 vom Drift-Gate ausgenommen) ist durch diesen Index ersetzt |
| Typen | `src/lib/schemas/` wird aus `../tooling/generator/schemas/` erzeugt (`npm run generate:types`), nie von Hand |

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| Studio lokal starten oder einrichten | `README.md` → `SETUP_STANDALONE.md` | docs/rebuild/ |
| Konventionen (TypeScript, Komponenten, Store, Design-System) | `CLAUDE.md` | docs/design/ |
| Eine API-Route finden oder ändern | `docs/api-inventory.md` | docs/rebuild/ |
| Design-Tokens prüfen oder Token-Schulden abbauen | `docs/design-system-enforcement.md` → `docs/rebuild/TOKEN_SPEC.md` → `docs/rebuild/TYPOGRAPHY_SPACING_SPEC.md` | docs/design/PROJECT_* |
| Ein Feature mit Systemgrenze verstehen (Runner, Deployment, Discovery, Schätzung, Impact) | `docs/design/STUDIO_E2E_DELIVERY.md` → das passende `docs/design/PROJECT_*.md` | docs/rebuild/ |
| Qualitätsmaßstab einer Studio-Änderung | `docs/design/STUDIO_QUALITY_STANDARD.md` | docs/rebuild/PROGRESS.md |
| Warum die Oberfläche so aussieht (Rebuild 2026, gesperrte Produktentscheidungen) | `docs/rebuild/REBUILD_DECISIONS.md` → `docs/rebuild/PAGE_TEMPLATE_DOCTRINE.md` | docs/design/ |

## 2. Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Pfade relativ zu `studio/`. `README.md` (auch `docs/rebuild/MOCKUP_REFERENCE/README.md`) ist ausgenommen.

| Gruppe | Docs | Lies-wenn (Gruppe) |
|---|---|---|
| Wurzel und `docs/` | `CLAUDE.md` — Konventionen für Agenten<br>`SETUP_STANDALONE.md` — Standalone-Setup, lokal zuerst, mit eigenem API-Key<br>`docs/api-inventory.md` — Verzeichnis der API-Routen<br>`docs/design-system-enforcement.md` — wie Design-Tokens erzwungen werden | Studio betreiben oder ändern |
| `docs/design/` — Feature-Entwürfe und Systemgrenzen | `docs/design/AI_POLICY_REVIEW.md`<br>`docs/design/DISCOVERY_PACKAGE_TRANSFER.md`<br>`docs/design/DISCOVERY_PERSISTENCE.md`<br>`docs/design/EXTERNAL_DELIVERY_HANDOFF.md`<br>`docs/design/PROJECT_ALTERNATIVE_IMPACT.md`<br>`docs/design/PROJECT_ARCHITECTURE_COMPILATION.md`<br>`docs/design/PROJECT_AUTHORITY_AND_VIEWS.md`<br>`docs/design/PROJECT_BATCH_INGESTION.md`<br>`docs/design/PROJECT_COMMERCIAL_IMPACT_PLAN.md`<br>`docs/design/PROJECT_DECISION_DERIVATION.md`<br>`docs/design/PROJECT_DEPLOYMENT_SAFETY.md`<br>`docs/design/PROJECT_ESTIMATION.md`<br>`docs/design/PROJECT_INPUT_RELEASE.md`<br>`docs/design/PROJECT_LOCAL_REFERENCE.md`<br>`docs/design/PROJECT_NATIVE_ITEM_GENERATION.md`<br>`docs/design/PROJECT_PROTECTED_RUNNER.md`<br>`docs/design/PROJECT_RUNNER_ACCEPTANCE.md`<br>`docs/design/PROJECT_RUNNER_HOST.md`<br>`docs/design/PROJECT_RUNNER_HOST_READINESS_2026-09-09.md`<br>`docs/design/PROJECT_RUN_COST_DELTA.md`<br>`docs/design/STUDIO_DIALOG.md`<br>`docs/design/STUDIO_E2E_DELIVERY.md`<br>`docs/design/STUDIO_QUALITY_STANDARD.md`<br>`docs/design/STUDIO_REMEDIATION_2026-09-07.md` | Ein bestehendes Feature erweitern oder seine Grenze (Runner, Freigabe, Deployment, Kosten) prüfen |
| `docs/rebuild/` — Rebuild 2026 (Plan, Entscheidungen, Specs, Fortschritt) | `docs/rebuild/AGENT_BRIEF.md`<br>`docs/rebuild/BASELINE.md`<br>`docs/rebuild/DATA_WIRING.md`<br>`docs/rebuild/DETAIL_IA.md`<br>`docs/rebuild/IMPLEMENTATION_ROADMAP.md`<br>`docs/rebuild/PAGE_TEMPLATE_DOCTRINE.md`<br>`docs/rebuild/PAGE_TYPE_TAXONOMY.md`<br>`docs/rebuild/PHASE1_AUDIT.md`<br>`docs/rebuild/PHASE_1_5_SPRINT_A_SUMMARY.md`<br>`docs/rebuild/PROGRESS.md`<br>`docs/rebuild/REBUILD_DECISIONS.md`<br>`docs/rebuild/REBUILD_PLAN.md`<br>`docs/rebuild/REPORT_ENGINE_TARGET_ARCHITECTURE.md`<br>`docs/rebuild/STUDIO_UX_RESEARCH.md`<br>`docs/rebuild/TOKEN_SPEC.md`<br>`docs/rebuild/TYPOGRAPHY_SPACING_SPEC.md`<br>`docs/rebuild/VISUAL_BAUKASTEN.md` | Eine Gestaltungs- oder Strukturentscheidung zurückverfolgen; Plan und Fortschritt sind Arbeitsstand des Rebuilds, keine laufende Planung |
