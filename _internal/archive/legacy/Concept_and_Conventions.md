Status: Archive
Note: This file was moved to /archive because it does not fit the current target structure. Review and delete or migrate if still needed.

# Analytics Use Case Library â€“ Concept & Conventions

---

## 1. End-to-End Flow (Top-down)

1. **Strategic KPIs**
   - File: `_includes/Strategic_KPIs.md`
   - Defines the canonical strategic KPIs per dimension (Growth, Profitability, Liquidity, Efficiency, Customer, ESG, Governance, Innovation & People).

2. **Strategic Alignment Map**
   - File: `_includes/Strategic_Alignment_Map.md`
   - Links each Strategic KPI to one or more **Use Case IDs** (e.g. `COM-001`, `COR-004`), with primary/secondary links.

3. **Use Case Inventory**
   - File: `_includes/UseCase_Inventory.md`
   - Source of truth for all Use Cases (ID, Title, Purpose, Strategic KPIs, Action Codes, Expected Impact, Status).

4. **Use Case Factsheets**
   - Folder: `usecases/<Cluster>/<UC-ID>_<Title>/Business_Factsheet.md` (front-matter + business narrative) and `Technical_Factsheet.md` (data contract, semantic model).
   - Legacy stub: `FactSheet.md` stays for compatibility and redirects tooling to the Business factsheet.
   - Template seed: `usecases/UC-000_Template.md` (front-matter now sits in the Business factsheet).
   - Minimum fields (in Business front-matter):
     - `id`, `title`, `domain`, `owner`, `impact`, `status`, `last_update`, `supports_strategic_kpi`, `supports_strategic_kpi_ids`, `action_codes`, `expected_impact`, `dataset_model`, `page_template`, `segments`, `filters_default`, `qa_asserts`, `required_kpi_ids`, `required_kpis`, `data_requirements`, `model_mapping`.
   - Body: business sections in `Business_Factsheet.md`, technical deep-dive in `Technical_Factsheet.md`.

5. **KPI Catalogs**
   - Folder: `_includes/kpi_catalog/`
   - Schema: `_includes/kpi_catalog/SCHEMA.md`
   - Domain catalogs (Growth, Profitability, Liquidity, Efficiency, CustomerValue, ESG, Governance, InnovationPeople) contain one `yaml` block per KPI with:
     - `kpi_id` (stable ID), `kpi_key` (readable name), `kpi_type`, `impact_dimension`, `domain_tag`, `use_case_ref`, `business`, `technical`, `governance`.
   - `required_kpi_ids` from FactSheets **must** exist as `kpi_id` in one of these catalogs.

6. **Semantic Models / Measures (TMDL)**
   - Folder: `dist/<UC-ID>/*SemanticModel/definition/tables/_Measures.tmdl`
   - Generated from KPI Catalogs (via tools) und bei Bedarf manuell verfeinert.
   - All measures referenced in `_Measures.tmdl` must be either:
     - KPI measures with `kpi_id` in a catalog, or
     - Explicit Supporting-Measures defined in the same `_Measures.tmdl` table.

---

## 2. Authoring Process â€“ New Use Case

1. **Inventory & Strategy**
   - Add a row to `_includes/UseCase_Inventory.md` with:
     - `ID`, `Use Case Title`, `Purpose / Goal`, `Strategic KPIs`, `Key Drivers`, `Main Action Codes`, `Expected Impact`, `Status`.
   - Ensure `ID` is referenced in `_includes/Strategic_Alignment_Map.md` under the relevant Strategic KPI(s).

2. **Create Factsheets from Template**
   - Preferred: run `tools/new_usecase.ps1 -Id <UC-ID> -Title "<Title>"` to scaffold:
     - `Business_Factsheet.md` (front-matter + business outline)
     - `Technical_Factsheet.md`
     - `FactSheet.md` (stub pointing to both)
   - Manual path: copy `usecases/UC-000_Template.md` front-matter into `Business_Factsheet.md` and replace placeholders:
     - `id`, `title`, `domain`, `owner`, `impact`, `status`, `last_update`.
     - `supports_strategic_kpi` + `supports_strategic_kpi_ids` aligned to Alignment Map.
     - `action_codes`, `expected_impact`.
     - `dataset_model`, `page_template`, `segments`, `filters_default`, `qa_asserts`.
     - `required_kpi_ids`: list of KPI IDs you need for the use case.
     - `required_kpis`: mapping from `kpi_id` to short label.
     - `data_requirements`, `model_mapping`.

3. **Define / Extend KPIs**
   - For each `required_kpi_id`:
     - If it already exists in a catalog, reuse.
     - Otherwise, add a KPI block in the appropriate catalog under `_includes/kpi_catalog/` following `SCHEMA.md`:
       - Choose `kpi_id` (ASCII, dot-separated namespace, e.g. `ops.capacity.utilization.pct`).
       - Set `kpi_key` (may contain symbols like `Î”`, `%`, `â‚¬`).
       - Fill `business` and `technical` with purpose, definition, grain, unit, `formatString`, and lineage.
       - Set `use_case_ref` to include the new Use Case ID.

4. **Create / Regenerate `_Measures.tmdl`**
   - Standardweg ist der Generator:
     - Einzelner Use Case:
       - `.\tools\generate\generate_tmdl_measures.ps1 -UseCase COM-001 -OverwriteExisting`
     - Alle Use Cases (nur Stubs, bestehende Dateien bleiben):
       - `.\tools\generate_all_measures.ps1 -StubOnly`
   - Der Generator:
     - liest `required_kpi_ids` und `required_kpis` aus dem Business_Factsheet (Ã¼ber den `FactSheet.md`-Stub),
     - holt die Definitionen aus den KPI-Katalogen,
     - erzeugt je `kpi_id` genau eine Measure mit Kommentar  
       `/// <kpi_id> - <kpi_key>` und passenden `formatString`/`displayFolder`.
   - Add explicit Supporting-Measures for any composite logic:
     - Keine â€žhiddenâ€œ `SUM`/`CALCULATE`-Logik in KPI-Measures, sondern eigenstÃ¤ndige Supporting-Measures (z.B. `Net Sales Amount`, `Baseline Sales Amount`).

5. **Validation**
   - Run (wenn Execution Policy erlaubt):
     - `.\tools\run_all_checks.ps1`
       - `validate_factsheets.ps1`
       - `validate_kpi_catalog.ps1`
       - `check_factsheet_vs_kpi.ps1`
       - `check_measures_vs_kpi.ps1`
   - Fix any missing or inconsistent `required_kpi_ids` / `kpi_id` / measure references.

---

## 3. Naming & Format Conventions

### 3.1 KPI IDs & Measure Names

- `kpi_id`:
  - ASCII, dot-separated: `<domain>.<topic>.<measure>.(amount|pct|count|days|...)`.
  - Beispiele:
    - `sales.net_sales.amount`
    - `margin.gm.pct`
    - `ops.oee.pct`
    - `crm.clv.amount`
    - `people.digital_adoption.pct`

- Measure-Namen in `_Measures.tmdl`:
  - Verbale Namen fÃ¼r Endnutzer, inkl. Symbole:
    - Delta: immer `Î”` im Namen (z.B. `Î” Net Sales Amount`, `Î”% Net Sales`).
    - Prozent: Suffix `%` (z.B. `Gross Margin %`).
    - WÃ¤hrung: keine â€žEURâ€œ im Namen, sondern im `formatString` mit `â‚¬`.
  - Supporting-Measures klar benennen:
    - `Net Sales Amount`, `Net Sales Amount LY`, `Baseline Sales Amount`, `Promo Sales Amount`.
    - Keine verschachtelten, schwer lesbaren DAX-AusdrÃ¼cke direkt in KPI-Measures, wenn sie mehrfach benÃ¶tigt werden.

### 3.2 Formatstrings

- WÃ¤hrung:
  - BetrÃ¤ge mit zwei Nachkommastellen:  
    `formatString: "â‚¬ #,0.00"`
  - CLV oder grÃ¶ÃŸere Summen ohne Nachkommastellen (wenn sinnvoll):  
    `formatString: "â‚¬ #,0"`

- Prozent:
  - Standard: `formatString: "0.0 %"`

- Counts / StÃ¼ck / Stunden:
  - Ganze Zahlen: `formatString: "#,0"`
  - Stunden mit einer Stelle: `formatString: "#,0.0"` (bei Bedarf).

---

## 4. DisplayFolder-Konventionen (Semantic Model)

- Commercial:
  - `"01_Sales"`, `"02_Margin"`, `"03_Price_Promo"`, `"03_Customer"`.
- Operations:
  - `"01_Capacity"`, `"02_Inventory"`, `"03_SupplyChain"`.
- Corporate / Governance:
  - `"01_Strategy"`, `"01_Workforce"`, `"01_DataQuality"`, `"01_Compliance"`, `"01_RiskControl"`, `"01_Audit"`.
- ESG:
  - `"01_ESG"`, `"01_Energy"`.
- Innovation & People:
  - `"INN Digital"`, `"01_Innovation"`, `"01_Learning"`, `"01_Workforce"` (HR-KPIs).

Neue Measures sollten an diese Ordner angelehnt werden, um Konsistenz im PBIP-Model zu halten.

---

## 5. Cleaning & Best Practices

- **Keine â€žTBDâ€œ in Produktiv-Katalogen oder Use Cases**:
  - Wenn fachliche Klarheit fehlt, lieber konservative, aber sinnvolle Definition verfassen.

- **Konsistenz zwischen Factsheet (Business), KPI-Katalog und `_Measures.tmdl`**:
  - Jedem `required_kpi_id` aus einem Factsheet:
    - muss ein `kpi_id` in einem Katalog entsprechen und
    - genau eine Measure in `_Measures.tmdl` mit der Implementierung zugeordnet sein.

- **Keine Cross-Use-Case Measures**:
  - Jedes `dist/<UC-ID>`-Modell ist eigenstÃ¤ndig.
  - Measures werden nicht zwischen Use Cases geteilt; wiederverwendbare Logik gehÃ¶rt in KPI-Katalog + Generator, nicht durch Kopieren zwischen `_Measures.tmdl`.

