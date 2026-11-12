---
last-reviewed: 2026-11-12
shelf-life-days: 90
---
# internal — Zentraler Anlaufpunkt (_INDEX)

> Einstieg in `internal/` — **Maintainer-Material**, kein Kunden-Deliverable: die
> Fehler-Wissensbasis, Desktop-/Fabric-gated Aufgaben, Ausführungspläne, Backlog
> und Metriken (die Angebotskalkulation liegt seit 12.11.2026 unter
> `../products/proposal_costing/`). Laut Ownership-Matrix in
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
> Abgelöstes liegt seit 12.11.2026 unter `../_archiv/internal/` (v1.0-Plan, DoD-Walkthrough,
> Gap-Analyse, Doku-Audits 02–03/2026, Präsentationsstand, `ci/`, `vision/`,
> `ux_layout_builder_contract.md`) — nicht navigiert. Das frühere `archive/` ist gelöscht; sein
> Stand liegt im Git-Ref `archiv/vor-entschlacken-2026-11-12`.

## 1. „Lies-wenn"-Routing

| Deine Aufgabe ist … | Lies | NICHT nötig |
|---|---|---|
| **Fehler beheben** — Pipeline-, TMDL-/PBIR-, DAX-, Studio- oder Power-BI-Desktop-Fehler (immer zuerst hier!) | `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (Abschnitt nach Fehlerklasse) → Diagnose-Workflow `skills/fix-pbi-report-errors.md`; danach neue Zeile in `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` | `continuity/`, `metrics/`, `skills/` |
| Power-BI-Report oder Semantikmodell generieren und vor dem Schreiben validieren | `skills/generate-and-validate-pbi-report.md` → `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` („Report visuals", „TMDL / PBIP") | `continuity/`, `metrics/` |
| Aufgabe übernehmen oder abgeben, die Power BI Desktop auf der Windows-Dev-Box braucht (Linux-Sitzung kann Laden/Rendern nicht bestätigen) | `project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md` (Pickup-Brief + Prompt) → bei KPI-Twins `project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md` | `skills/`, `continuity/` |
| Prüfen, ob ein Problem schon als Lücke/deferred bekannt ist; fehlende Aurora-Daten für HR-001, COM-005, FIN-003, SCM-004 | `project_mgmt/KNOWN_GAPS.md` (vorher gegen aktuellen Code verifizieren) → `project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md` | `continuity/`, `skills/` |
| Technischen TODO/Stub finden oder eintragen | `technical_backlog.md` | `project_mgmt/`, `continuity/` |
| Fabric-Neuerungen der FabCon Europe 2026 umsetzen oder eine offene Aufgabe daraus übernehmen (Pins, Capacity, Speichermodus, Copilot-Readiness, PBIR) | `project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md` (Pickup-Brief mit Status-Tabelle + Prompt) → bei Validierung `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` | `continuity/`, `skills/` |
| Page-Scaffold (ux_layout_rules) oder die 300s-Evidence-Tabelle ändern | `evidence_grain_audit_results.md` (Evidence-Grain je Use Case) | `continuity/`, `metrics/` |
| Monatliche Guardrail-Retrospektive oder Stage-1-Fehlerquoten auswerten | `metrics/README.md` → `metrics/retrospective_template.md` | `skills/`, `continuity/` |
| Neue:n Engineer onboarden oder die Systemarchitektur für eine Übergabe verstehen | `continuity/README.md` → `continuity/handover_guide.md` → `continuity/architecture_overview.md` | `project_mgmt/`, `continuity/` |
| Betrieb/Deployment ohne Originalteam oder Vendor-Escrow durchführen bzw. Kunden-Eigentum verifizieren | `continuity/runbook.md` → `continuity/escrow_checklist.md` | `skills/`, `metrics/` |

## 2. Dokument-Register (vollständig — Drift-Gate erzwingt das)

> Gruppiertes Register: eine Zeile je Unterordner/Thema (erste Spalte = Ordner; `internal/`
> = Wurzel dieses Bereichs), die Docs mit vollem Pfad (relativ zu `internal/`) und
> Kurzzweck in der zweiten Spalte, die letzte Spalte sagt, wann die Gruppe relevant ist.
> `README.md` ist exempt; `metrics/runs/` navigiert über seine `README.md`.

| Gruppe | Docs — Zweck | Lies-wenn (Gruppe) |
|---|---|---|
| `project_mgmt/` — Fehler-Wissensbasis & bekannte Lücken | `project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — **zentrale Wissensbasis** für PBI/PBIP-, TMDL-, DAX-, Generator-, Studio- und Gate-Fehler (Symptom / Ursache / Fix); Pflicht-Update nach jedem Fix<br>`project_mgmt/KNOWN_GAPS.md` — bekannte Limitierungen, Platzhalter und deferred Aktivierungsschritte (Audit-Stand 2026-03-27, Resolved-Items als Historie)<br>`project_mgmt/AURORA_SYNTHETIC_DATA_GAPS.md` — synthetische Aurora-Tabellen/-Spalten für HR-001, COM-005, FIN-003, SCM-004 (Status: generiert 2026-07-19) | Etwas ist kaputt oder fehlt, und vor eigener Analyse soll geklärt sein, ob es schon bekannt ist |
| `project_mgmt/` — Desktop-/Fabric-gated Aufgaben | `project_mgmt/CLAUDE_CLI_PBI_DESKTOP_TASKS.md` — Pickup-Brief + Prompts für Aufgaben, die Power BI Desktop im Claude CLI (VS Code, Windows) brauchen<br>`project_mgmt/KPI_DEDUP_MIGRATION_RUNBOOK.md` — Runbook: physische Entfernung doppelter KPIs (Twin → canonical), nur mit Desktop zertifizierbar | Eine Änderung lässt sich auf Linux nicht abschließend prüfen und muss an die Windows-Umgebung übergeben werden |
| `project_mgmt/` — Fabric-Neuerungen | `project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md` — Aufgaben aus den Fabric-Neuerungen der FabCon Europe 2026 (Wellen W0–W7, Nachmessung 01.10. und Nachprüfung 07.10.2026, Status je Aufgabe, Parität zu Meridian I-21) | Eine Fabric-Neuerung umsetzen oder ihren Stand prüfen |
| `skills/` — tool-agnostische PBI-Workflows | `skills/fix-pbi-report-errors.md` — Diagnose-/Reparatur-Workflow für Report- und Modellfehler, dokumentiert jeden Fix in der Wissensbasis<br>`skills/generate-and-validate-pbi-report.md` — iterativer Workflow: Report/Modell generieren, vor dem Schreiben validieren, neue Fehlerklassen festhalten | Report-Arbeit als festen Ablauf ausführen statt ad hoc (für Claude Code, Codex, Copilot oder Mensch) |
| `internal/` (Wurzel) — Backlog | `technical_backlog.md` — technische TODOs/Stubs, un-wired Tooling (wire-or-remove), Stand 2026-06-17 | Entscheiden, ob eine Idee schon als technischer Rest geplant ist |
| `internal/` (Wurzel) — Audits | `evidence_grain_audit_results.md` — niedrigster gemeinsamer Evidence-Grain der 300s-Tabelle je Use Case (Audit 2026-02-13) und Eignung für die Kreuztabelle (Nachtrag 24.10.2026) | Scaffold-Generator oder die Detailseite eines Use Cases anfassen |
| `metrics/` — Guardrail-Metriken | `metrics/retrospective_template.md` — Vorlage für die monatliche Guardrail-Retrospektive (Stage-1-Fehlerquote, Top-Fehlermodi) | Wirkung der Guardrails messen oder die Monatsauswertung schreiben |
| `continuity/` — Vendor-Continuity-Dossier (geht per Escrow an den Kunden) | `continuity/architecture_overview.md` — Systemarchitektur, kritische Abhängigkeiten, Regenerierungs-Voraussetzungen<br>`continuity/handover_guide.md` — Zwei-Wochen-Curriculum für neue Engineers<br>`continuity/runbook.md` — Betrieb & Deployment: Provisioning, Credential-Rotation, Validierung<br>`continuity/escrow_checklist.md` — Kunden-Eigentum, Verifikation und Aktivierung im Escrow-Fall | ALUCA muss ohne das Originalteam betrieben, übergeben oder im Escrow-Fall aktiviert werden |
