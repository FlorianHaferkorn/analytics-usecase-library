# Phase 2 / Backlog

**Zweck:** Themen, die bewusst als Folgephase bzw. Backlog geführt werden; kein Muss für Projektabschluss. Das Projekt gilt mit Blocker-Behebung, Review-Anpassungen und Zero-Tolerance-Dokumentation (Punkte 1–3 des Projektabschluss-Plans) als inhaltlich und technisch abgeschlossen.

**Tracking:** Work items are tracked in the repo-scope GitHub Project. For migration to Issues/Epics, see [internal/project_mgmt/BACKLOG_MIGRATION.md](../project_mgmt/BACKLOG_MIGRATION.md).

---

## 3-30-300 vollständig

Vollständige Operationalisierung der 300s-Seite und durchgängige Nutzung der Action-Payload aus Action-Code-YAML in Reports. reporting_principles.md definiert 3–30–300; page_templates und Layouts operationalisieren bereits teilweise. Status: Zielbild / teilweise (siehe internal/docs_claims_checklist.md). Kein Muss für Projektabschluss.

---

## Builder Engine Phase 2

Nach Phase 1 (Registry als Build-Pflicht, Domain-Mode mit Report pro Use Case, UX Engine Full-Report, Hard Gates, Schema `ux_bindings`) bleiben für „world class“:

- **Measure/Dimension-Binding:** Visuals mit echten queryState/projections aus Registry bzw. _Measures.tmdl; `ux_bindings`-Overrides im Report-Compiler anwenden.
- **Action Codes im Report:** 30s Action Teaser und 300s Action Panel mit Inhalten aus `core/action_codes` (via Registry), gesteuert durch `payload_mode` im Bracket.
- **Streamlit UX Editor:** Tabs „Bindings“ (Axis/Legend/Rows/Values/TopN pro Slot) und „Actions“ (Reihenfolge/Visibility); Schreiben in `ux_bindings` im Bracket; Dropdown-Optionen aus Data Contract/Registry.
- **Deploy:** deploy.ps1 mit echter Fabric-Anbindung (FabricPS-PBIP oder REST: Workspace, Import Model, Import Report + Binding).
- **Optional:** Self-Healing-Schleife (regelbasiert), Snapshot-Tests für PBIP/TMDL, Service Principal für Deploy.

---

## Strategy Pattern / KI-Dringlichkeit

„Präzise genug für KI-Dringlichkeit / Automated Reasoning“ (Manifest § I) als Zielbild. core/strategy_operating_model/company/strategy_patterns.md existiert; KI-Dringlichkeit und Automated Reasoning sind konzeptionell, nicht im Tooling nachgewiesen. Keine Implementierungspflicht für Abschluss.
