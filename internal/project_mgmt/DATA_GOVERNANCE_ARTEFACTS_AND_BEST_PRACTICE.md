# Data Governance im Projekt: Umsetzung und Artefakte

Dieses Dokument ordnet den **Best-Practice-Ansatz** für Data Governance (strategische Verankerung, Rollen, Verträge, Glossar, Data Dictionary, KPI-Katalog) der **konkreten Umsetzung** in diesem Cursor-Projekt (Analytics Use Case Library) zu. Es definiert, **welche Bestandteile** die jeweiligen Artefakte **zwingend** haben müssen.

---

## 1. Die drei zentralen Artefakte (Best Practice) und ihre Projekt-Entsprechung

| Best Practice | Projekt-Entsprechung | Ort / Verantwortung |
|---------------|----------------------|----------------------|
| **Business Glossary** (fachliche Begriffe, Top-Down) | Fachliche Definitionen in **KPI Catalog** (`business:` pro KPI), **Use Case Business Factsheets**, **Action Code**-Beschreibungen; Begriffe und Verantwortlichkeiten in **company_strategy**, **domains.md** | `core/kpi_catalog/KPI_Catalog.md`, `core/usecases/**/Business_Factsheet.md`, `core/strategy_operating_model/company/` |
| **Data Dictionary** (technische Struktur, Bottom-Up) | **Domain Data Contracts** (Schema, Typen, Grain, Spalten); technische KPI-Spezifikation unter `technical:` (dax_expression, lineage, formatString) | `core/data_contracts/domains/*.yaml`, `core/kpi_catalog/KPI_Catalog.md` (technical-Block) |
| **Datenkatalog / KPI-Katalog** (Inventar, Auffindbarkeit, Lineage) | **KPI Catalog** als zentrales KPI-Inventar; **Data Contracts** als Inventar der Datensätze; **Registry** (`master_registry.json`, `value_map.json`) für Verknüpfungen und Trust | `core/kpi_catalog/`, `core/data_contracts/`, `tooling/ontology/out/` |

**Hinweis:** In diesem Projekt sind **KPI-Katalog** und **Data Contracts** die zentralen SSOT-Artefakte. Das **Measure Dictionary** pro Domain (`core/semantic_models/domains/*/Measure_Dictionary_*.md`) ist die dokumentierte Schnittstelle zwischen KPI-Katalog und technischer Umsetzung (TMDL/DAX) und gehört inhaltlich zwischen Business Glossary (fachliche Bedeutung) und Data Dictionary (Formel, Abhängigkeiten).

---

## 2. Zwingende Bestandteile pro Artefakt

Die folgenden Bestandteile werden als **obligatorisch** betrachtet, damit Data Governance operativ handlungsfähig ist.

### 2.1 Strategiedokument (Data Policy)

- **Ziele und Geschäftstreiber** (Compliance, Prozessharmonisierung, BI, Kundennutzen).
- **Umfang:** Welche Systeme und Kerndatenobjekte werden betrachtet?
- **Definition von Datenqualität** und zu messende Dimensionen (z. B. Genauigkeit, Vollständigkeit, Aktualität).

**Projekt:** `core/strategy_operating_model/operating_model/data_governance.md` sowie `core/constitution` / Strategy-Layer; Ziele und Prinzipien sind dort festgehalten. Kerndatenobjekte = Domains und deren Data Contracts.

### 2.2 RACI / Rollenmodell

- Alle Rollen den Governance-Aufgaben zugeordnet.
- Kürzel: R (Responsible), A (Accountable), C (Consulted), I (Informed).

**Projekt:** `core/strategy_operating_model/operating_model/ownership_raci_golden_thread.md`. Rollen sind **rollenbasiert** (`owner_role`, `steward_role`) in KPI Catalog, Action Codes, Brackets; keine Personennamen (siehe data_governance.md §7.4).

### 2.3 Data Contracts (Datenverträge)

- **Semantik:** Geschäftliche Bedeutung und beabsichtigte Nutzung.
- **Schema:** Struktur, Datentypen, Nullability.
- **Validierungsregeln / Datenqualität:** Wertebereiche, Formate, referenzielle Integrität (ref).
- **SLAs:** (im Projekt optional) Verfügbarkeit, Aktualität; aktuell über Grain und Lineage abgebildet.
- **Governance & Ownership:** Ansprechpartner und Änderungsmanagement.

**Projekt:** `core/data_contracts/domains/*.yaml`. Enthalten: dimension/fact, name, columns (type, ref, agg, nullable), grain. Fehlen explizit: SLA-Felder, feste Owner-Felder pro Tabelle; Ownership liegt auf Domain-Ebene (README).

### 2.4 Business Glossary (Fachliches Glossar)

- **Informationslandkarte:** Definitionen von Geschäftsbegriffen, Entitäten, Attributen in nicht-technischer Sprache.
- **Verantwortlichkeiten:** Fachliche Data Stewards pro Begriff/Bereich.
- **Geschäfts- und Kontrollregeln:** Vorgaben zur Nutzung und wer Begriffe ändern darf.
- **Klassifizierung:** Sensibilität, Nutzung.

**Projekt:** Pro KPI im KPI Catalog: `business:` (purpose, definition, grain_scope, unit_format, interpretation). Pro Use Case: Business_Factsheet (Core Business Questions, Kontext). Rollen: `governance.business_owner`, `governance.data_owner`, `governance.steward`. Kein separates Glossar-Dokument; die fachlichen Definitionen leben im KPI Catalog und in den Factsheets.

### 2.5 Data Dictionary (Technisches Datenwörterbuch)

- **Feldnamen und Tabellenstrukturen** (exakt).
- **Datentypen und Feldgrößen.**
- **Wertebereiche (Domain)** wo sinnvoll.
- **Beziehungen** (ref zu anderen Tabellen).

**Projekt:** `core/data_contracts/domains/*.yaml` (columns: name, type, ref, agg, nullable). Technische KPI-Seite: `technical:` in KPI_Catalog.md (dax_expression, lineage, formatString, depends_on_measures). TMDL-Tabellen in dist sind generiert; Autorität liegt bei Data Contracts und KPI Catalog.

### 2.6 KPI-Katalog & KPI-Steckbriefe

- **Identifikation & Zweck:** KPI-ID, Name, geschäftliche Bedeutung.
- **Messung & Formel:** Wie berechnet (technical.dax_expression, technical.lineage).
- **Zielwert/Target:** (im Projekt optional pro KPI; bei Action Codes: levels L1/L2/L3.)
- **Datenquelle & Frequenz:** lineage; Frequenz über grain_scope/Reporting-Kontext.
- **Verantwortliche:** business_owner, data_owner, steward.

**Projekt:** `core/kpi_catalog/KPI_Catalog.md`. Jeder Eintrag enthält: kpi_id, kpi_key, business (purpose, definition, grain_scope, unit_format, interpretation), technical (dax_expression, lineage, formatString, depends_on_measures), governance (business_owner, data_owner, steward, review_cycle, qa_rules). Schema: `core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md` bzw. `tooling/ai/schemas`.

---

## 3. Kurz: Was das Projekt „immer haben“ muss

- **Data Policy / Governance-Prinzipien:** Vorhanden in `data_governance.md` und Golden-Thread-Dokumenten.
- **RACI / Rollen:** Vorhanden in `ownership_raci_golden_thread.md`; Rollen in Artefakten als owner_role/steward_role.
- **Data Contracts:** Pflicht für alle Domains mit Semantic Model; zwingend: domain, dimension/fact, name, grain, columns (name, type, ref wo nötig).
- **Business Glossary:** Im Projekt in **KPI Catalog (business:)** und **Business Factsheets** integriert; zwingend pro KPI: purpose, definition, grain_scope, Verantwortung (governance).
- **Data Dictionary:** In **Data Contracts** (Schema) und **KPI technical** (Formel, lineage); zwingend: konsistente Feldnamen, Typen, refs.
- **KPI-Katalog:** `KPI_Catalog.md`; zwingend pro KPI: kpi_id, business-Block, technical (mind. lineage bzw. dax_expression), governance (business_owner, steward), Referenzierbarkeit aus Brackets und Action Codes.

---

## 4. Terminologie im Projekt

Zur Vermeidung von Missverständnissen die hier verwendete Terminologie:

- **Data Governance** = Rahmen, Prinzipien, Rollen, SSOT (wer, was, wo); **Data Management** = operative Umsetzung (wie: Validierung, Lineage, Generierung). Vgl. data_governance.md.
- **Owner (Accountable)** = `business_owner` / `owner_role`; **Steward (Responsible für Qualität/Umsetzung)** = `data_owner` / `steward_role`. Beide Rollen pro Artefakt erforderlich, nicht identisch (data_governance.md §7.4).
- **KPI** = im Projekt eindeutig über `kpi_id` (z. B. sales.net_sales.amount); Definition nur im KPI Catalog, Use Cases und Action Codes referenzieren nur.
- **Data Contract** = Domain- oder Source-Level-Vertrag unter `core/data_contracts/` (YAML); definiert Schema und Grain für Silver-Layer.
- **Single Source of Truth (SSOT):** Pro Konzept genau ein autoritativer Ort (vgl. data_governance.md §7.2); abgeleitete Artefakte (z. B. Registry, generierte Measures) werden nicht hand-editiert.

Ein unternehmensweites **Business Glossary** im engeren Sinne (eigenes Dokument nur für Begriffe/Synonyme) existiert nicht als separates Deliverable; seine Funktion übernehmen KPI Catalog und Factsheets. Bei Einführung eines expliziten Glossars sollte es mit kpi_id und Bracket-Referenzen verknüpft werden, um Doppeldefinitionen zu vermeiden.

---

## 5. Referenzen

- Governance-Prinzipien und Artefakt-Gesetze: `core/strategy_operating_model/operating_model/data_governance.md`
- RACI und Golden Thread: `core/strategy_operating_model/operating_model/ownership_raci_golden_thread.md`
- KPI Catalog: `core/kpi_catalog/README.md`, `core/kpi_catalog/KPI_Catalog.md`
- Data Contracts: `core/data_contracts/domains/README.md`
- Validierung (Stage 1, Registry): `tooling/run_stage1_checks.ps1`, `tooling/ontology/registry_builder.py`; AGENTS.md
