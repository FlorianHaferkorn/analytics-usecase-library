# Core Content Review – Anpassungen pro Dokument

**Datum:** 2026-02-17  
**Behoben am:** 2026-02-17 (Blocker und Pfade); verbleibende Stil-/Link-back-/Encoding-Anpassungen mit Issue #17 (2026-02-22).  
**Scope:** Alle .md unter core/ (101 Dokumente)  
**Referenz:** SSOT, Golden Thread, ACTIONREADY Manifesto, company_strategy, reporting_principles

---

## 1. Zusammenfassung

| Cluster | Anzahl Docs | Mit Anpassungen | Blocker |
|---------|-------------|-----------------|---------|
| Strategy & Operating Model | 20 | 4 | 1 |
| Use Cases | 17 | 13 | 1 |
| KPI Catalog & Action Codes | 5 | 2 | 0 |
| Semantic Models | 19 | 1 | 0 |
| Data Contracts | 4 | 1 | 0 |
| Templates & Governance | 20 | 0 | 0 |
| Implementation Guides | 2 | 0 | 0 |
| Organization / Sonstige | 5 | 0 | 0 |
| **Gesamt** | **101** | **21** | **2** |

**Sprache/Stil:** Framework-Docs unter core/ einheitlich Englisch. Ausnahme: ACTIONREADY Manifesto (internal/vision) bleibt Deutsch. Abweichungen (z. B. „EUR“-Encoding-Fehler) sind unter Stil/Verständlichkeit erfasst.

**Vollständigkeit:** Alle unter `core/**/*.md` gefundenen 101 Dokumente wurden einem Cluster zugeordnet und geprüft; Dokumente ohne Befunde sind pro Cluster unter „Keine Anpassungen“ gelistet.

---

## 2. Prüfkriterien (Kurzreferenz)

- **Zielbild:** SSOT-Konformität, Rolle im Golden Thread (Manifest: Bracket = Dirigent, KPI Catalog = Vertrag), keine Widersprüche zum Manifest.
- **Fachlich:** Verweise (KPI-IDs, Action-Code-IDs, Rollen) existieren in Katalog bzw. org_roles.yaml; keine KPI-Definitionen außer im KPI Catalog.
- **Ineinandergreifen:** Strategy → KPI → Use Case → Action erkennbar; Link-backs bei abgeleiteten Views (SSOT); korrekte Pfade zu Data Contracts/Semantic Models.
- **Verständlichkeit:** Purpose/Scope klar, Leserführung, Terminologie konsistent (z. B. „Use Case Bracket“, „Golden Thread“).
- **Stil:** Einheitliche Sprache (EN in core/), sachlich, keine Encoding-Fehler („EUR“ statt Em-Dash etc.).

---

## 3. Anpassungen nach Cluster

### 3.1 Strategy & Operating Model

#### core/strategy_operating_model/company/company_strategy.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Zielbild/SSOT) **Blocker.** SSOT-Tabelle verweist auf Anker `#5-strategic-kpis`, `#6-executive-key-questions`, `#7-strategic-alignment-inputs-to-the-golden-thread`. Diese Abschnitte fehlen; das Dokument ist ein Placeholder mit nur Beispiel-Struktur. **Empfehlung:** Entweder die drei Abschnitte (5. Strategic KPIs, 6. Executive key questions, 7. Strategic alignment inputs to the Golden Thread) ergänzen oder die SSOT-Tabelle auf „placeholder“ anpassen und Anker-Verweise entfernen/aussetzen.
  - (Ineinandergreifen) Abschnitt „KPI alignment“ verweist auf `core/kpi_catalog/KPI_Catalog.md` – korrekt. Keine konkreten KPI-IDs genannt; für vollständige Golden-Thread-Nutzung sollten strategische KPIs und Alignment-Map einmal ausformuliert werden.

#### core/strategy_operating_model/company/reporting_principles.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Stil/Verständlichkeit) Abschnitt 5: „3EUR"30EUR"300“ ist ein Encoding-Fehler; gemeint ist „3–30–300“ (Sekunden). **Empfehlung:** Zu „3–30–300“ oder „3 / 30 / 300“ korrigieren.

#### core/strategy_operating_model/company/domains.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Stil) Zeile 22: „interpretation EUR" independent“ – „EUR"“ ist Encoding-Fehler (vermutlich Em-Dash). **Empfehlung:** Durch „—“ oder „ – “ ersetzen.

#### core/strategy_operating_model/operating_model/reference/single_source_of_truth.md
- **Status:** Keine inhaltlichen Anpassungen. Hinweis: SSOT-Tabelle referenziert company_strategy.md#5, #6, #7 – solange diese Anker fehlen, sind Link-Ziele defekt (siehe Querschnitt 4).

- **Keine Anpassungen (Strategy & Operating Model):** core/strategy_operating_model/README.md, core/strategy_operating_model/operating_model/README.md, operating_model_overview.md, data_governance.md, golden_thread_strategy_to_action.md, ownership_raci_golden_thread.md, maturity_model_action_ready_analytics.md, strategy_patterns.md, company/README.md, lakehouse_architecture.md, data_layers_standard.md, measure_system.md, ux_design_system.md, distribution_architecture.md, ai_readiness.md, semantic_layer.md, reference/ActionReady_SemanticModel_Blueprint.md, reference/TMDL_Official_Refs.md, reference/TMDL_Allowed_Subset.md, decision_taxonomy.md.

---

### 3.2 Use Cases

#### core/usecases/core/*/Business_Factsheet.md (alle 13 Use Cases)
- **Status:** Anpassungen erforderlich
- **Anpassungen (alle Factsheets):**
  - (Fachlich/Ineinandergreifen) **Blocker.** In Abschnitt „0. Metadata“ stehen **Related Data Contract** und **Related Semantic Model** mit falschem Pfad: `core/core/core/data_contracts/...` bzw. `core/core/core/semantic_models/...`. Korrekt ist genau ein „core/“ (z. B. `core/data_contracts/domains/...`). **Empfehlung:** Alle 13 Facts sheets: „core/core/core/“ durch „core/“ ersetzen. Betroffen: COM-001, COM-002, COM-003, COM-004, FIN-001, FIN-002, OPS-001, OPS-002, OPS-003, SCM-001, SCM-002, SCM-003, XD-001, XD-002, XD-003.

#### core/usecases/core/XD-003_Executive_KPI_Overview/Business_Factsheet.md
- **Status:** Zusätzlich zu obiger Pfad-Korrektur
- **Anpassungen:**
  - (Zielbild/SSOT) SSOT verlangt für „Domain KPI overview (executive lens)“: „Must be explicitly derived view, not redefining KPIs.“ **Empfehlung:** Link-back-Block nahe Dokumentanfang ergänzen, z. B.: „Canonical KPI definitions: core/kpi_catalog/KPI_Catalog.md. This document is a derived/aggregation view and must not redefine KPI semantics.“

- **Keine Anpassungen (Use Cases):** core/usecases/UseCase_Inventory.md (generiert), core/usecases/README.md, core/usecases/usecase_DoD_Core.md, core/usecases/core/README.md, core/usecases/templates/README.md, core/usecases/templates/usecase_factsheet_business.md, core/usecases/templates/UC-000_Template.md (sofern vorhanden).

---

### 3.3 KPI Catalog & Action Codes

#### core/kpi_catalog/KPI_Catalog.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Ineinandergreifen) Schema-Referenz: „Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`“. Dieser Pfad liegt außerhalb von core und entspricht nicht der SSOT (canonical: core/templates/kpi_catalog_templates/). **Empfehlung:** Auf `core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md` verweisen (tatsächlicher Dateiname: kpi_catalog_SCHEMA.md).

#### core/action_codes/README.md
- **Status:** Keine Anpassungen. Inhaltlich konsistent mit Manifest und SSOT (Action Codes als eigenständige Assets, Use Cases konsumieren).

- **Keine Anpassungen:** core/action_codes/Action_Code_Patterns.md, core/kpi_catalog/README.md, core/templates/action_codes/ActionCode_TEMPLATE.md, core/templates/action_codes/README.md.  
- **Hinweis (YAML, außer Scope .md-Review):** In core/action_codes/ verweisen drei YAML-Dateien auf `framework/usecases/...` statt `core/usecases/...`: X-R2.2.yaml, S-R2.5.yaml, XS-S.1.1.yaml. Sollten in einem separaten Pass korrigiert werden.

---

### 3.4 Semantic Models

#### core/semantic_models/domains/Domain_Measure_Dictionary_Schema.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Fachlich) Beispiele nennen „Measure_Dictionary_Customer.md“, „Measure_Dictionary_Corporate.md“. Unter core/semantic_models/domains/ existieren u. a. Commercial, Operations, SupplyChain, Finance – nicht „Customer“ oder „Corporate“. **Empfehlung:** Beispiele auf existierende Dateien umstellen (z. B. Measure_Dictionary_Commercial.md, Measure_Dictionary_Operations.md).

- **Keine Anpassungen:** core/semantic_models/README.md, core/semantic_models/core_action_ready/README.md, core/semantic_models/domains/README.md, alle Measure_Dictionary_*.md (Commercial, Operations, SupplyChain, Service, Risk, Profitability, People, Liquidity, InnovationPeople, Growth, Governance, Finance, ESG, Efficiency, CustomerValue).

---

### 3.5 Data Contracts

#### core/data_contracts/domains/README.md
- **Status:** Anpassungen erforderlich
- **Anpassungen:**
  - (Verständlichkeit/Stil) Zeile 86: „**Location:** `core/core/data_contracts/domains/README.md`“ – doppeltes „core“. **Empfehlung:** Zu „core/data_contracts/domains/README.md“ korrigieren.
  - (Verständlichkeit) „core/TEMPLATES/data_contract_TEMPLATES/“ – Großschreibung weicht von tatsächlichem Pfad ab (core/templates/data_contract_templates/). **Empfehlung:** Kleinschreibung verwenden.

- **Keine Anpassungen:** core/data_contracts/README.md, core/data_contracts/sources/README.md, core/data_contracts/sources/synthetic/README.md, core/data_contracts/sources/synthetic/synthetic_data_readme.md.

---

### 3.6 Templates & Governance

- **Keine Anpassungen (Templates):** core/templates/README.md, core/templates/page_templates/README.md, Slot_Definitions.md, Page_DoD.md, Visual_Whitelist.md, ActionPanel_Spec.md, page_types (README, T1–T4), measure_templates/README.md, measure_template.md, kpi_catalog_templates/README.md, kpi_catalog_SCHEMA.md, KPI_Catalog_Maintenance_OnePager.md, silver_to_gold/README.md, data_contract_templates/README.md.

- **Hinweis:** SSOT nennt „core/templates/KPI_Catalog_templates/KPI_Catalog_SCHEMA.md“; tatsächlicher Dateiname ist `kpi_catalog_SCHEMA.md`. Für konsistente Verlinkung ggf. in SSOT oder Verweisen „kpi_catalog_SCHEMA.md“ verwenden (case-sensitive Repo).

---

### 3.7 Implementation Guides

- **Keine Anpassungen:** core/implementation_guides/playbook_strategy_to_first_report.md, core/implementation_guides/README.md.

---

### 3.8 Organization / Sonstige

- **Keine Anpassungen:** core/README.md, core/organization/README.md, core/agents/Commercial/Commercial_Sales_Agent_COM-002.system_prompt.md (agent-spezifisch), core/kpi_catalog/KPI_Taxonomy.md.

---

## 4. Querschnittsbefunde

### Fehlende oder defekte Anker (SSOT)
- **company_strategy.md:** SSOT verweist auf `#5-strategic-kpis`, `#6-executive-key-questions`, `#7-strategic-alignment-inputs-to-the-golden-thread`. Diese Abschnitte existieren nicht. Alle Links auf diese Anker sind derzeit defekt.

### Falsche Pfade (bereits in 3.1–3.2 erfasst)
- Alle 13 Business_Factsheet.md: `core/core/core/` → `core/`.
- data_contracts/domains/README.md: `core/core/` → `core/`; TEMPLATES → templates.

### Verweise auf nicht-core-Pfade
- KPI_Catalog.md: `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md` – außerhalb core; auf core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md umstellen.

### Inkonsistente Begriffe
- Keine systematische Abweichung (z. B. „Bracket“ vs „Use Case Bracket“) festgestellt; vereinzelt „Action-Ready“ vs „ActionReady“ – einheitlich „ActionReady“ laut Repo-Konvention.

### YAML-Dateien (außer Scope, zur Kenntnis)
- framework/usecases/ in drei Action-Code-YAMLs (X-R2.2, S-R2.5, XS-S.1.1) → sollte core/usecases/ sein.

---

## 5. Golden-Thread-Walk (Protokoll)

**Datum:** 2026-02-17  
**Beispielkette:** company_strategy → UseCase_Inventory (COM-001) → Bracket → KPI Catalog / action_codes

**Ablauf:**

1. **company_strategy.md §5 (Strategic KPIs)** verweist explizit auf `core/kpi_catalog/KPI_Catalog.md` und „operational mapping (Strategic KPI column)“ in `core/usecases/UseCase_Inventory.md`. Keine Auflistung konkreter KPI-IDs in §5 (bewusst: Vermeidung von Duplikation; Inventory ist operationale Quelle).
2. **company_strategy.md §7 (Strategic alignment)** verweist auf `core/usecases/UseCase_Inventory.md` als „operational master list“ und auf `golden_thread_strategy_to_action.md`. Leser wird klar auf Inventory verwiesen.
3. **UseCase_Inventory.md** (Beispiel COM-001): Zeile enthält Strategic KPI `margin.gm.pct`, Influencing KPIs, Action Codes (C-M2.1, C-S1.1, C-S1.2). Datei ist generiert (registry_builder.py).
4. **COM-001 UseCase_Bracket.yaml**: Enthält dieselben IDs (strategic_kpi_id, influencing_kpi_ids, action_code_ids). Verweist auf Business_Factsheet.md.
5. **Stage 1** prüft: Alle in Bracket/Factsheet referenzierten KPI-IDs existieren im KPI Catalog (check_factsheet_vs_kpi); alle action_code_ids existieren in core/action_codes (check_factsheet_action_codes).

**Ergebnis:** Die Kette Strategy → §5/§7 → UseCase_Inventory → Bracket → KPI Catalog / action_codes ist für einen Leser nachvollziehbar. Kein fehlender Verweis; company_strategy nennt bewusst keine eigene KPI-Liste, sondern verweist auf Inventory und Katalog. Keine Anpassung nötig.
