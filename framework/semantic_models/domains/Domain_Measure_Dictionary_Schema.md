# Domain Measure Dictionary Schema

Purpose: Define a consistent structure for documenting all measures  
(base, supporting, KPI-implementing measures) inside a **Domain Semantic Model**.

This schema is used in files like:

- `framework/semantic_models/domains/Commercial/Measure_Dictionary_Commercial.md`
- `framework/semantic_models/domains/Operations/Measure_Dictionary_Operations.md`
- `framework/semantic_models/domains/Customer/Measure_Dictionary_Customer.md`
- `framework/semantic_models/domains/Corporate/Measure_Dictionary_Corporate.md`

Each file contains a YAML list of measures inside ```yaml code fences.

## 1. Fields per Measure

Each measure is a YAML object with the following fields.

### 1.1 Top-level

- `measure_name` (required, string)  
  Name of the measure in the semantic model (exact DAX name).

- `is_kpi_measure` (required, bool)  
  - `true` → this measure directly implements a KPI from the KPI Catalog.  
  - `false` → base/supporting/time-intelligence/helper measure.

- `kpi_id_ref` (optional, string)  
  `kpi_id` from the KPI Catalog, if `is_kpi_measure = true`.  
  Empty or omitted for non-KPI measures.

- `semantic_model` (required, string)  
  Name of the semantic model, e.g. `Commercial_SemanticModel`.

- `display_folder` (optional, string)  
  Display folder in the model, e.g. `"01_Sales"`, `"02_Margin"`.

- `category` (optional, string)  
  Logical category, e.g.:
  - `Base`
  - `KPI`
  - `TimeIntelligence`
  - `Helper`
  - `Technical`

### 1.2 `expression` section (required)

- `expression.dax` (required, string; multiline allowed)  
  Full DAX expression of the measure.

- `expression.formatString` (required, string)  
  Power BI format string, e.g.:
  - `"€ #,0.00"`
  - `"0.0 %"`
  - `"#,0"`

### 1.3 `documentation` section (required)

- `documentation.description` (required, string)  
  Short, Copilot-friendly description of what the measure does and how it is used.

- `documentation.notes` (optional, string)  
  Additional comments, caveats, or implementation details.

### 1.4 `dependencies` section (optional but recommended)

- `dependencies.measures` (optional, list<string>)  
  Names of other measures referenced by this measure.

- `dependencies.columns` (optional, list<string>)  
  Columns referenced directly in the expression,  
  e.g. `"fact_sales[Net Sales Amount]"`.

### 1.5 `governance` section (optional but recommended)

- `governance.owner` (optional, string)  
  Technical owner or responsible team, e.g. `"Commercial BI"`.

- `governance.status` (optional, string)  
  Lifecycle status, e.g.:
  - `active`
  - `deprecated`
  - `experimental`

- `governance.version` (optional, string)  
  Semantic version of this measure definition, e.g. `"v1.0"`.

- `governance.last_review` (optional, string, date)  
  Date of last technical review, format `DD.MM.YYYY`.

## 2. Example: Base and KPI Measure

```yaml
- measure_name: "Net Sales Amount"
  is_kpi_measure: false
  kpi_id_ref: ""
  semantic_model: "Commercial_SemanticModel"
  display_folder: "01_Sales"
  category: "Base"

  expression:
    dax: "SUM(fact_sales[Net Sales Amount])"
    formatString: "€ #,0.00"

  documentation:
    description: "Base measure summing Net Sales Amount from fact_sales."
    notes: ""

  dependencies:
    measures: []
    columns:
      - "fact_sales[Net Sales Amount]"

  governance:
    owner: "Commercial BI"
    status: "active"
    version: "v1.0"
    last_review: "21.11.2025"

- measure_name: "Gross Margin %"
  is_kpi_measure: true
  kpi_id_ref: "margin.gm.pct"
  semantic_model: "Commercial_SemanticModel"
  display_folder: "02_Margin"
  category: "KPI"

  expression:
    dax: "DIVIDE([Net Sales Amount] - [COGS Amount],[Net Sales Amount])"
    formatString: "0.0 %"

  documentation:
    description: "KPI measure implementing Gross Margin % based on Net Sales and COGS."
    notes: ""

  dependencies:
    measures:
      - "Net Sales Amount"
      - "COGS Amount"
    columns:
      - "fact_sales[Net Sales Amount]"
      - "fact_sales[COGS Amount]"

  governance:
    owner: "Commercial BI"
    status: "active"
    version: "v1.0"
    last_review: "21.11.2025"
```

## 3. Best Practices

- Jede Domain hat genau ein Measure Dictionary (eine MD-Datei pro Semantic Model).

- Alle DAX-Ausdrücke stehen im Measure Dictionary oder direkt im TMDL, nicht im KPI-Katalog.

- is_kpi_measure = true nur dort, wo das Measure direkt eine KPI aus dem KPI-Katalog implementiert.

- kpi_id_ref muss dann exakt zur kpi_id im KPI-Katalog passen.

- DAX folgt den DAX-Best-Practices (DIVIDE statt /, keine FORMAT in Rechenmeasures, sinnvolle VAR/RETURN bei komplexen Measures).

