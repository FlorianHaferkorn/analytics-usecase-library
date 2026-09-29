---
last-reviewed: 2026-09-25
shelf-life-days: 90
---
# internal — Zentraler Anlaufpunkt (_INDEX)

> Einstieg in `internal/` — **Maintainer-Material**, kein Kunden-Deliverable: die
> Fehler-Wissensbasis, Desktop-/Fabric-gated Aufgaben, Ausführungspläne, Backlogs,
> Doku-Audits, Metriken und die Angebotskalkulation. Laut Ownership-Matrix in
> `continuity/escrow_checklist.md` erhält der Kunde aus `internal/` nur das
> Continuity-Dossier `continuity/` (Live-Repo- bzw. Escrow-Kopie) — alles andere hier ist
> Arbeitsmaterial des Teams. Ob das Export-Skript für das Kundenpaket (tooling/export_customer_package.ps1)
> `internal/` ausschließt, belegt kein Doc in diesem Bereich — vor einer Weitergabe im
> Skript selbst prüfen. Zuerst diese Datei, dann gezielt zum Doc — nicht den ganzen Ordner.
>
> **Bei jedem Validierungs-, Build- oder Desktop-Fehler zuerst
> `project_mgmt/KNOWN_ERRORS_AND_FIXES.md`** (Symptom | Ursache | Fix) — und nach jedem Fix
> einer neuen Fehlerklasse dort eine Zeile ergänzen (Pflicht laut Doc selbst).
>
> `archive/` ist ein historisches Archiv (Marker `.claude-no-index`) — nicht navigiert,
> nicht registriert, nur für Nachforschungen.

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| **Fehler beheben** — Pipeline-, TMDL-/PBIR-, DAX-, Studio- oder Power-BI-Desktop-Fehler (immer zuerst hier!) | `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Abschnitt nach Fehlerklasse) → Diagnose-Workflow `skills/fix-pbi-report-errors.md`; danach neue Zeile in `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` | `continuity/`, `proposal_costing/`, `vision/` |
| Power-BI-Report oder Semantikmodell generieren und vor dem Schreiben validieren | `skills/generate-and-validate-pbi-report.md` → `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` („Report visuals", „TMDL / PBIP") | `continuity/`, `metrics/` |
| Aufgabe übernehmen oder abgeben, die Power BI Desktop auf der Windows-Dev-Box braucht (Linux-Sitzung kann Laden/Rendern nicht bestätigen) | `project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md` (Pickup-Brief + Prompt) → bei KPI-Twins `project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md` | `vision/`, `proposal_costing/` |
| Prüfen, ob ein Problem schon als Lücke/deferred bekannt ist; fehlende Aurora-Daten für HR-001, COM-005, FIN-003, SCM-004 | `project_mgmt/KNOWN_GAPS.md` (vorher gegen aktuellen Code verifizieren) → `project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md` | `continuity/`, `skills/` |
| Technischen TODO/Stub finden oder eintragen, Phase-2-Thema einordnen, KI-/Automated-Reasoning-Scope abgrenzen | `technical_backlog.md` → `vision/phase2_backlog.md` → `vision/automated_reasoning_scope_and_limits.md` | `project_mgmt/`, `continuity/` |
| Fabric-Neuerungen der FabCon Europe 2026 umsetzen oder eine offene Aufgabe daraus übernehmen (Pins, Capacity, Speichermodus, Copilot-Readiness, PBIR) | `project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md` (Pickup-Brief mit Status-Tabelle + Prompt) → bei Validierung `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` | `continuity/`, `vision/` |
| Framework-v1.0-DoD („Lean Core & EcoPulse") nachvollziehen oder durchgehen | `project_mgmt/FRAMEWORK_V1_EXECUTION_PLAN.md` → `project_mgmt/DOD_WALKTHROUGH.md` | `skills/`, `proposal_costing/` |
| PBI Generator / Fabric Architecture Generator gegen microsoft/skills-for-fabric abgleichen | `project_mgmt/GAP_ANALYSIS_PBI_GENERATOR_VS_SKILLS_FOR_FABRIC.md` | `continuity/`, `metrics/` |
| Layout-Editor bzw. Page-Scaffold (ux_layout_rules) oder die 300s-Evidence-Tabelle ändern | `ux_layout_builder_contract.md` → `evidence_grain_audit_results.md` (Evidence-Grain je Use Case) | `continuity/`, `proposal_costing/` |
| Konzept-Docs reviewen (Release Candidate / halbjährlich): Claims vs. Implementierung, SSOT-Link-backs | `docs_review_cadence.md` → `docs_claims_checklist.md` → `docs_linkback_audit.md`; Befund-Historie für `core/`: `core_content_review_results.md` | `project_mgmt/`, `skills/` |
| Interne Präsentation oder Stakeholder-Update vorbereiten (Status, Metriken, Roadmap) | `presentation_status_and_roadmap.md` (nur Englisch pflegen) | `skills/`, `ci/`, `archive/` |
| Stage-2-Soft-Review (geplant, nicht blockierend) verstehen oder umsetzen | `ci/stage2_soft_review.md` | `proposal_costing/`, `continuity/` |
| Monatliche Guardrail-Retrospektive oder Stage-1-Fehlerquoten auswerten | `metrics/README.md` → `metrics/retrospective_template.md` | `vision/`, `continuity/` |
| Neue:n Engineer onboarden oder die Systemarchitektur für eine Übergabe verstehen | `continuity/README.md` → `continuity/handover_guide.md` → `continuity/architecture_overview.md` | `project_mgmt/`, `proposal_costing/` |
| Betrieb/Deployment ohne Originalteam oder Vendor-Escrow durchführen bzw. Kunden-Eigentum verifizieren | `continuity/runbook.md` → `continuity/escrow_checklist.md` | `skills/`, `metrics/` |
| Angebotskalkulation (Fabric-Kapazität, Power-BI-Lizenzen, Implementierung) erstellen oder Angebotstext befüllen | `proposal_costing/docs/README.md` → `proposal_costing/tooling/README.md` → `proposal_costing/templates/proposal_snippet.md` / `proposal_costing/templates/offer_snippet.md`; Beispiel-Output `proposal_costing/dist/aurora_calculation.md` | `project_mgmt/`, `continuity/` |
| Historischen Stand oder abgelöste Docs nachforschen | `archive/` (nicht navigiert — gezielt suchen, nicht scannen) | alles andere |

## 2. Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Gruppiertes Register: eine Zeile je Unterordner/Thema (erste Spalte = Ordner; `internal/`
> = Wurzel dieses Bereichs), die Docs mit vollem Pfad (relativ zu `internal/`) und
> Kurzzweck in der zweiten Spalte, die letzte Spalte sagt, wann die Gruppe relevant ist.
> `README.md` ist exempt; `proposal_costing/` (Code, Modell-YAML, Tests) und `metrics/runs/`
> navigieren über ihre `README.md`; `proposal_costing/dist/` ist generiert und vom Gate
> ausgenommen; `archive/` ist per `.claude-no-index` nicht navigiert.

| Gruppe | Docs — Zweck | Lies-wenn (Gruppe) |
|---|---|---|
| `project_mgmt/` — Fehler-Wissensbasis & bekannte Lücken | `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — **zentrale Wissensbasis** für PBI/PBIP-, TMDL-, DAX-, Generator-, Studio- und Gate-Fehler (Symptom / Ursache / Fix); Pflicht-Update nach jedem Fix<br>`project_mgmt/KNOWN_GAPS.md` — bekannte Limitierungen, Platzhalter und deferred Aktivierungsschritte (Audit-Stand 2026-03-27, Resolved-Items als Historie)<br>`project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md` — synthetische Aurora-Tabellen/-Spalten für HR-001, COM-005, FIN-003, SCM-004 (Status: generiert 2026-07-19) | Etwas ist kaputt oder fehlt, und vor eigener Analyse soll geklärt sein, ob es schon bekannt ist |
| `project_mgmt/` — Desktop-/Fabric-gated Aufgaben | `project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md` — Pickup-Brief + Prompts für Aufgaben, die Power BI Desktop im Claude CLI (VS Code, Windows) brauchen<br>`project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md` — Runbook: physische Entfernung doppelter KPIs (Twin → canonical), nur mit Desktop zertifizierbar | Eine Änderung lässt sich auf Linux nicht abschließend prüfen und muss an die Windows-Umgebung übergeben werden |
| `project_mgmt/` — v1.0-Plan & Gap-Analyse | `project_mgmt/FRAMEWORK_V1_EXECUTION_PLAN.md` — Ausführungsplan „Lean Core & EcoPulse DoD" (DoD, Wochenplan, Risiken, Rollback)<br>`project_mgmt/DOD_WALKTHROUGH.md` — Schritt-für-Schritt-Walkthrough der v1.0-DoD (Strategy → Forge → Registry → Measure → Deploy)<br>`project_mgmt/GAP_ANALYSIS_PBI_GENERATOR_VS_SKILLS_FOR_FABRIC.md` — PBI Generator + Fabric Architecture Generator vs. microsoft/skills-for-fabric (Stand 2026-04-04)<br>`project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md` — Aufgaben aus den Fabric-Neuerungen der FabCon Europe 2026 (Wellen W0–W3, Status je Aufgabe, Parität zu Meridian I-21) | Herkunft einer Architektur- oder Scope-Entscheidung der v1.0-Phase nachvollziehen |
| `skills/` — tool-agnostische PBI-Workflows | `skills/fix-pbi-report-errors.md` — Diagnose-/Reparatur-Workflow für Report- und Modellfehler, dokumentiert jeden Fix in der Wissensbasis<br>`skills/generate-and-validate-pbi-report.md` — iterativer Workflow: Report/Modell generieren, vor dem Schreiben validieren, neue Fehlerklassen festhalten | Report-Arbeit als festen Ablauf ausführen statt ad hoc (für Claude Code, Codex, Copilot oder Mensch) |
| `internal/` (Wurzel) + `vision/` — Backlogs & Scope | `technical_backlog.md` — technische TODOs/Stubs, un-wired Tooling (wire-or-remove), Stand 2026-06-17<br>`vision/phase2_backlog.md` — bewusst verschobene Folgephase-Themen (3-30-300 vollständig, Builder Engine Phase 2)<br>`vision/automated_reasoning_scope_and_limits.md` — was „automated reasoning" hier umfasst und was explizit nicht | Entscheiden, ob eine Idee schon geplant, bewusst verschoben oder außerhalb des Scopes ist |
| `internal/` (Wurzel) — Report-Bau-Verträge & Audits | `ux_layout_builder_contract.md` — Vertrag `ux_layout_rules`: Layout-Tool-Ergebnis 1:1 in den Power-BI-Report<br>`evidence_grain_audit_results.md` — niedrigster gemeinsamer Evidence-Grain der 300s-Tabelle je Use Case (Audit 2026-02-13) | Layout-/Scaffold-Generator oder die Detailseite eines Use Cases anfassen |
| `internal/` (Wurzel) — Doku-Qualität & Review-Kadenz | `docs_review_cadence.md` — wann Konzept-Check und SSOT-Review fällig sind<br>`docs_claims_checklist.md` — Claims aus Konzept-Docs vs. Implementierung (umgesetzt/Zielbild/unklar/veraltet)<br>`docs_linkback_audit.md` — SSOT-Link-back-Audit für abgeleitete Views (2026-02-17)<br>`core_content_review_results.md` — Core-Content-Review aller `core/`-Docs mit Anpassungen je Dokument (2026-02-17) | Einen Doku-Review-Zyklus fahren oder prüfen, ob eine Konzept-Aussage durch Code gedeckt ist |
| `internal/` (Wurzel) — Status & Präsentation | `presentation_status_and_roadmap.md` — Single Source für interne Präsentationen: Status, Metriken, Roadmap, Produktreife (English only) | Ein Stakeholder-Update oder eine interne Präsentation vorbereiten |
| `ci/` — geplante CI-Stufe | `ci/stage2_soft_review.md` — Stage 2: nicht blockierender Prosa-Review auf Diffs (Scope, Inputs, stabiles Output-Schema) | Die CI um einen weichen Review ergänzen, ohne Stage 1 zu duplizieren |
| `metrics/` — Guardrail-Metriken | `metrics/retrospective_template.md` — Vorlage für die monatliche Guardrail-Retrospektive (Stage-1-Fehlerquote, Top-Fehlermodi) | Wirkung der Guardrails messen oder die Monatsauswertung schreiben |
| `continuity/` — Vendor-Continuity-Dossier (geht per Escrow an den Kunden) | `continuity/architecture_overview.md` — Systemarchitektur, kritische Abhängigkeiten, Regenerierungs-Voraussetzungen<br>`continuity/handover_guide.md` — Zwei-Wochen-Curriculum für neue Engineers<br>`continuity/runbook.md` — Betrieb & Deployment: Provisioning, Credential-Rotation, Validierung<br>`continuity/escrow_checklist.md` — Kunden-Eigentum, Verifikation und Aktivierung im Escrow-Fall | ALUCA muss ohne das Originalteam betrieben, übergeben oder im Escrow-Fall aktiviert werden |
| `proposal_costing/` — Angebotskalkulation | `proposal_costing/templates/proposal_snippet.md` — Kostenübersicht-Vorlage je Szenario (Capacity, Lizenzen, Bausteine, Scope)<br>`proposal_costing/templates/offer_snippet.md` — Angebots-Vorlage (Kunde, Paket, Leistungsübersicht)<br>`proposal_costing/dist/aurora_calculation.md` — generierte Aurora-Beispielkalkulation (nicht von Hand editieren) | Einem Interessenten Plattform- und Implementierungskosten beziffern |
