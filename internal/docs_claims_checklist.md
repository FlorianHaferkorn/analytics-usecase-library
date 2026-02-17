# Docs Claims Checklist – Konzept-Docs vs. Implementierung

**Zweck:** Behauptungen in Konzept-Docs (Manifest, Golden Thread, SSOT, data_governance) mit Code/Tooling abgleichen oder als Zielbild kennzeichnen.  
**Status:** `umgesetzt` | `Zielbild` | `unklar` | `veraltet`  
**Aktualisierung:** Bei Release Candidate oder halbjährlich (siehe internal/docs_review_cadence.md).

**Manifest vs. Core:** Die Status-Spalte bildet den Abgleich ab: „umgesetzt“ = Aussage ist in tooling/core implementiert (Nachweis in Spalte Nachweis); „Zielbild“ = konzeptionelle Vision, (noch) nicht vollständig im Repo umgesetzt; „unklar“ = Prüfung in Pipeline/Produkt ausstehend.

---

## Quelle: ACTIONREADY HOLISTIC MANIFESTO (internal/vision)

| Claim (Kurzfassung) | Quelle (Abschnitt) | Status | Nachweis / Vermerk |
|---------------------|--------------------|--------|--------------------|
| Wenn ein Data Contract bricht, setzt die Registry den Trust-Score der davon abhängigen KPIs auf 0; Nutzer sieht Warnung im Report. | Manifest § V (Data Contracts), World-Class Merkmal | umgesetzt | tooling/ontology/registry_builder.py: trust_score = 0 if any(c in failed_contracts for c in linked_contracts) else 1 (Zeile 1422). generate_tmdl_measures.ps1 nutzt trust_score für DAX-Kommentar „UNTRUSTED“. |
| Output der Registry ist master_registry.json; Basis für Power BI Generierung, KI-Abfragen. | Manifest § VI (Registry Engine) | umgesetzt | registry_builder.py schreibt master_registry in out_dir (master_registry.json). generate_tmdl_measures.ps1, generate_all_measures.ps1 laden Registry. |
| Registry erkennt verwaiste Dateien (Ghosts), unbesetzte Rollen (Governance Gaps), logische Brüche im Golden Thread. | Manifest § VI, Verantwortung | umgesetzt | registry_builder.py: Ghost-Erkennung, Governance-Validierung, Issues-Liste; check_registry_builder.ps1 nutzt --strict. |
| Ein fehlerhafter Link in der Registry führt dazu, dass das gesamte Modul nicht „deployed“ wird. Zero-Tolerance. | Manifest § VI, World-Class Merkmal | umgesetzt (mit Einschränkung) | Stage 1 (inkl. registry_builder --strict) läuft in Azure-Pipeline-Build; bei Fehler schlägt Build fehl (kein Merge). Release-Skripte (fabric_release.py, fabric_setup.py) führen Stage 1 vor Release aus; mit --skip-stage1 kann übersprungen werden. Zero-Tolerance im Sinne „kein Merge bei fehlgeschlagener Registry“ ist in CI umgesetzt; striktes Blockieren von Deploy ohne Stage 1 ist konfigurierbar (Pipeline/Release ohne Skip). |
| Bracket ist „Single Point of Failure“: Wenn Bracket gelöscht wird, verschwindet Use Case aus Registry, Power BI, Dokumentation. | Manifest § II (Use Case Brackets) | umgesetzt | Registry und UseCase_Inventory werden aus Brackets/Facts sheets generiert; ohne Bracket kein Eintrag. Generierung/Tooling baut auf Bracket-Dateien auf. |
| Bracket ist reine Konfigurationsdatei (IDs, Value Driver Logic), keine langen Texte. | Manifest § II | umgesetzt | UseCase_Bracket.yaml pro Use Case; Struktur per usecase_bracket.schema.json; Business-Kontext im Business_Factsheet.md. |
| KPI Catalog ist einzige semantische Instanz für Berechnung und Bedeutung; Business Owner + Data Steward. | Manifest § III | umgesetzt | core/kpi_catalog/KPI_Catalog.md kanonisch; governance mit business_owner, data_owner, steward in KPI-Einträgen; Stage 1 prüft Referenzen. |
| Action Code: imperative Sprache, Trigger L1–L3; Payload für Dashboard/AI-Agent nutzbar. | Manifest § IV | umgesetzt | Action-Code-YAML mit steps, trigger_level; tooling liefert action text preview; Fabric/Power BI nutzen Action-Payload. |
| Data Contract: Fokus SLA (Frische, Vollständigkeit, Schema); maschinell prüfbar. | Manifest § V | umgesetzt | core/data_contracts/domains/*.yaml; registry_builder nutzt validation_results (data contract checks); trust_score-Kopplung. |
| 3-30-300: 3 s Status, 30 s Hebel, 300 s Action/Evidence. Report als Arbeitsplatz, Action-Text aus YAML. | Manifest § 3 (UX-Architektur) | Zielbild / teilweise | reporting_principles.md definiert 3–30–300; page_templates und Layouts operationalisieren; konkrete „300s-Seite“ und DAX-Injection aus Action-YAML in generate_tmdl_measures / Report-Generierung. |
| Strategy Pattern löst Zielkonflikte; präzise genug für KI-Dringlichkeit. | Manifest § I (Strategy Patterns) | Zielbild | core/strategy_operating_model/company/strategy_patterns.md existiert; „KI-Dringlichkeit“ und Automated Reasoning sind Zielbild, nicht im Tooling nachgewiesen. |
| Golden Thread: Top-Down und Bottom-Up traceability; Use Cases verknüpfen Strategy mit Action Codes. | Manifest § 1 (Paradigma) | umgesetzt | company_strategy §5–§7, UseCase_Inventory, Brackets mit required_kpi_ids und action_code_ids; Stage 1 prüft Kette. |

---

## Quelle: Golden Thread (core/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md)

| Claim (Kurzfassung) | Quelle | Status | Nachweis / Vermerk |
|---------------------|--------|--------|--------------------|
| Golden Thread ist geschlossenes Kausalsystem: Strategy → KPIs → Use Cases → Actions; operable, maintainable, scalable. | Golden Thread Einleitung | umgesetzt | company_strategy.md, UseCase_Inventory, Brackets, action_codes; Validierung durch Stage 1 (check_factsheet_vs_kpi, check_factsheet_action_codes). |
| Business Strategy verweist auf company_strategy.md; Outcome sind Strategic KPIs. | Golden Thread § 1 | umgesetzt | company_strategy.md §5 verweist auf KPI Catalog und UseCase_Inventory. |
| Key Questions strukturieren Übergang zu Use Cases; operationalisiert in Business Factsheets. | Golden Thread § 2 | umgesetzt | company_strategy §6; Use Case Facts sheets mit „Core Business Questions“. |
| Use Cases definieren Entscheidung, Kontext, required KPIs (aus Katalog), Actions (Action Codes); erfinden keine KPIs. | Golden Thread § 3 | umgesetzt | UseCase_Bracket.yaml + Business_Factsheet.md; Stage 1 prüft KPI- und Action-Code-Referenzen. |

---

## Quelle: SSOT / data_governance (optional ergänzen)

| Claim (Kurzfassung) | Quelle | Status | Nachweis / Vermerk |
|---------------------|--------|--------|--------------------|
| Ein Konzept → eine kanonische Datei; abgeleitete Views mit Link-back. | SSOT Rules | umgesetzt | check_docs_refs.ps1 prüft Referenzen; Link-back in XD-003 umgesetzt; Audit A.3 listet fehlende Link-backs. |
| Use Cases enthalten nur KPI-Referenzen (required_kpi_ids); keine KPI-Definitionen. | SSOT Rules | umgesetzt | Lean 2.0: Business_Factsheet Prosa; UseCase_Bracket.yaml IDs; check_factsheet_vs_kpi prüft gegen Katalog. |

---

## Phase 2 / Backlog

Themen, die bewusst als Folgephase geführt werden: siehe [phase2_backlog.md](vision/phase2_backlog.md) (3-30-300 vollständig, Strategy Pattern / KI-Dringlichkeit).

---

## Hinweis

Teil der Aussagen im Manifest beschreibt das **Zielbild** (z. B. KI-Dringlichkeit, strikte Zero-Tolerance im Deployment). Der Implementierungsstand ist in dieser Checkliste festgehalten. Bei Änderungen an Tooling oder Konzept-Docs: Status und Nachweis hier aktualisieren.
