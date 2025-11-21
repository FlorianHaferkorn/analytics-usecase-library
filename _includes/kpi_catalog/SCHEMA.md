# KPI Catalog Schema

Purpose: Single source of truth for KPI entry structure and ID conventions across all domain catalogs.

Each KPI is a YAML block inside a list:

```yaml
- kpi_id: "sales.net_sales.amount"          # Required; stable machine ID (dot-separated, lowercase)
  kpi_key: "Net Sales Amount"              # Required; human-readable label
  kpi_type: "strategic"                    # Required; {strategic|diagnostic|supporting}
  strategic_ref: "Net Sales Amount"        # Optional; reference name for strategic KPI
  impact_dimension: "Growth"               # Required; {Growth|Profitability|Liquidity|Efficiency|Customer|ESG|Governance|Risk|InnovationPeople}
  domain_tag: ["Commercial"]               # Required; 1..n tags, e.g. ["Commercial","SupplyChain"]
  use_case_ref:                            # Optional; related use cases
    - "COM-001"
    - "COR-001"
  depends_on:                              # Optional; human-readable dependencies
    - "Invoice Net Sales Amount"
  depends_on_ids:                          # Optional; KPI-IDs of dependencies
    - "sales.net_sales.amount"
  calc_type: "amount"                      # Required; {amount|rate|ratio|count}
  refresh: "monthly"                       # Optional; {daily|weekly|monthly|quarterly}

  business:
    purpose: "1-sentence business purpose."
    definition: "Calculation logic in business terms."
    grain_scope: "Aggregation grain & scope (e.g. invoice_line aggregated to Month, Org, Product)."
    unit_format: "€, % (1 decimal), pcs, etc."
    interpretation: "How to read the KPI; good/bad ranges, typical use."

  technical:
    dax_name: "Net Sales Amount"
    dax_expression: "SUM(fact_sales[Net Sales Amount])"
    formatString: "€ #,0.00"
    description: "Short technical description (Copilot-optimized)."
    lineage:
      - "fact_sales.Net Sales Amount"
    source_grain: "invoice_line"
    source_column_ref: "fact_sales[Net Sales Amount]"

  governance:
    business_owner: "Head of Controlling"
    data_owner: "Finance BI"
    steward: "Financial Analyst"
    review_cycle: "quarterly"
    validation_process: "Reconcile with P&L during month-end close."
    qa_rules:
      - "Reconcile with P&L within ±0.5 %"
      - "Non-negative; check for extreme outliers."
    version: "v1.0"

  metadata_quality:
    completeness_score: 0.95              # 0..1; see rules below
    last_review: "21.11.2025"

  aliases:                                # Optional; alternative labels
    - "Revenue"
    - "Net Revenue"
```

## 1. Fields

Jeder KPI-Eintrag ist ein YAML-Objekt in einer Liste.

### Top-Level

- `kpi_id` (required, string)  
  Stabile, maschinenlesbare ID im Format `domain.subdomain.metric` (lowercase, dot-separated). Muss über alle Kataloge eindeutig sein.

- `kpi_key` (required, string)  
  Menschlich lesbarer Name der Kennzahl. Wird als Standard-Anzeigename im Modell verwendet.

- `kpi_type` (required, enum)  
  Typ der Kennzahl: `strategic`, `diagnostic` oder `supporting`.

- `strategic_ref` (optional, string)  
  Referenziert den übergeordneten strategischen KPI-Namen, falls dieser KPI eine Detail- oder Teilkennzahl ist.

- `impact_dimension` (required, enum)  
  Zu welcher Impact-Dimension der KPI gehört (z. B. Growth, Profitability, Liquidity).

- `domain_tag` (required, list<string>)  
  1..n Domänen-Tags (z. B. `["Commercial"]`, `["SupplyChain","Retail"]`), dienen zum Filtern und Clustern.

- `use_case_ref` (optional, list<string>)  
  IDs der Use Cases (z. B. `COM-001`), in denen der KPI zentral genutzt wird.

- `depends_on` (optional, list<string>)  
  Menschlich lesbare Abhängigkeiten (KPI-Namen oder Metriken).

- `depends_on_ids` (optional, list<string>)  
  KPI-IDs, von denen diese Kennzahl abhängt.

- `calc_type` (required, enum)  
  Art der Kennzahl: `amount`, `rate`, `ratio`, `count`.

- `refresh` (optional, enum)  
  Typische Aktualisierungsfrequenz: `daily`, `weekly`, `monthly`, `quarterly`.

### business

- `business.purpose` (required)  
  Kurzbeschreibung: Wozu existiert dieser KPI?

- `business.definition` (required)  
  Fachliche Definition / Berechnungslogik in Worten.

- `business.grain_scope` (required)  
  Aggregationskorn und Scope (z. B. „Invoice line aggregated by Date, Org, Product“).

- `business.unit_format` (required)  
  Einheit und Format (z. B. „€ (0–2 decimals)“, „% (1 decimal)“, „pcs“).

- `business.interpretation` (required)  
  Wie der KPI zu lesen ist (gut/schlecht, typische Wertebereiche).

### technical

- `technical.dax_name` (required)  
  Name der Measure im semantischen Modell (englisch, nach deinen Konventionen).

- `technical.dax_expression` (required für berechnete KPIs)  
  DAX-Formel laut DAX-Best-Practices (DIVIDE, VAR/RETURN etc.).

- `technical.formatString` (required)  
  Power BI FormatString passend zu `calc_type` und `unit_format`.

- `technical.description` (required)  
  Kurze technische Beschreibung, Copilot-optimiert.

- `technical.lineage` (required)  
  Liste der Quellfelder / Tabellen, die in die Kennzahl einfließen.

- `technical.source_grain` (optional)  
  Ursprüngliches Datenkorn (z. B. `invoice_line`, `daily_snapshot`).

- `technical.source_column_ref` (optional)  
  Referenz auf konkrete Spalten im physischen Modell.

### governance

- `governance.business_owner` (required)  
  Fachlich verantwortliche Rolle/Person.

- `governance.data_owner` (required)  
  Verantwortlicher für Datenqualität.

- `governance.steward` (optional)  
  Operativer Owner / Data Steward.

- `governance.review_cycle` (required)  
  Turnus der Überprüfung (z. B. `monthly`, `quarterly`).

- `governance.validation_process` (required)  
  Kurzbeschreibung, wie der KPI fachlich/technisch validiert wird.

- `governance.qa_rules` (required, list<string>)  
  Konkrete Qualitätsregeln (Bounds, Reconcile-Regeln, Ausreißerlogik).

- `governance.version` (required)  
  Semantische Version des KPI-Eintrags.

### metadata_quality

- `metadata_quality.completeness_score` (required, float 0..1)  
  Heuristik für Vollständigkeit; basiert auf Anteil befüllter Kernfelder.
  Basis: Anteil befüllter Kernfelder (kpi_, business., technical., governance., metadata_quality.last_review)
  - ≥0.95 → „Production-ready“
  - 0.8–0.95 → „Gut, aber noch Baustellen“
  - <0.8 → „Draft / Beta“

- `metadata_quality.last_review` (required, date)  
  Datum der letzten fachlichen/technischen Überprüfung (DD.MM.YYYY).

### aliases

- `aliases` (optional, list<string>)  
  Alternativenamen / Synonyme, die in Verwendung sind.

## 2. Allowed values

- `kpi_type`: `strategic`, `diagnostic`, `supporting`
- `impact_dimension`: `Growth`, `Profitability`, `Liquidity`, `Efficiency`, `Customer`, `ESG`, `Governance`, `Risk`, `InnovationPeople`
- `calc_type`: `amount`, `rate`, `ratio`, `count`
- `refresh`: `daily`, `weekly`, `monthly`, `quarterly`