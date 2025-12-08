# <UC-ID> – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/<domain_file>.yaml`
- **Semantic Model Definition:**  
  `semantic_models/<model_path>/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: <UC-ID>)

---

## 1. Data Contract (YAML – <UC-ID> Scope)

```yaml
dimension:
  - name: dim_<dimension>
    columns:
      - {name: <Column>, type: <type>, role: <key/attribute>}
      # add additional columns as needed

  # repeat dim blocks as needed

  - name: security_user_org    # only if RLS Enterprise is required
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_<factname>
    grain: <grain>
    columns:
      - {name: <Column>, type: <type>, ref: <dimension>}
      # add fact columns as required

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_<fact> → `lh_<domain>.fact_<fact>`  
- dim_<dimension> → `lh_shared.dim_<dimension>`  
- security_user_org → `lh_security.security_user_org` (falls benötigt)

---

## 2. Semantic Model Requirements

### Model Name
`<model_name>`

### Tables
- fact_<fact>  
- dim_<dimension>  
- weitere dims abhängig vom UC  
- security_user_org (hidden, optional)

### Relationships
- fact_<fact>[<Key>] → dim_<dimension>[<Key>] (1:* | single direction)
- mindestens eine DateKey-Beziehung  
- alle konformen Dimensionen verwenden Surrogate Keys

### Hierarchies
- Org, Product, Date oder UC-spezifische Hierarchien  
- Beispiel:
  - Org: Region → Country → OrgName  
  - Date: Year → Quarter → Month → Date  

### Sort-by Columns
- Month → MonthNumber  
- Produktname → Produktcode  
- <weitere UC-spezifische SortBy-Felder>

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name      | kpi_id                    | Type        | Folder               | Format     |
|-------------------|---------------------------|------------|----------------------|-----------|
| <Measure>         | <kpi_id>                  | KPI        | <Folder>             | <Format>  |
| <Measure>         | <kpi_id>                  | Supporting | <Folder>             | <Format>  |
| ...               | ...                       | ...        | ...                  | ...       |

### PEVM (optional)
Falls Price/Volume/Mix benötigt wird:

- Template:  
  `framework/templates/measure_templates/pevm_sales_delta.md`

- QA:  
  *Price + Volume + Mix ≈ Δ Sales (±1 %).*

---

## 4. Measures (DAX)

```DAX
<Measure Name> =
    <DAX Expression>
```

```DAX
<Measure Name> =
    <DAX Expression>
```

*Hinweis:*  
UC-spezifische Measures vollständig dokumentieren.  
Wiederverwendbare Standard-Patterns nur verlinken.

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder        |
|---------------|----------|---------------|------------------------|
| Amounts       | €#,0.00  | Sum           | <Folder>               |
| Percentages   | 0.0 %    | None          | <Folder>               |
| Qty           | #,0      | Sum           | <Folder>               |
| ...           | ...      | ...           | ...                    |

---

## 6. Visual Requirements (Technical)

### KPI Cards
- <KPI 1>  
- <KPI 2>  
- <KPI 3>  

### Trend (Line Chart)
- Axis: dim_date[Month]
- Values: <Measures>

### Contribution (Waterfall)
- optional: Price/Volume/Mix

### Ranking
- Horizontal Bar (Region / Channel / Product)

### Detail (Matrix)
- Dimension-Hierarchien (Region → Country → ...)
- Export enabled

---

## 7. RLS / OLS

### Demo RLS (falls Security Table fehlt)
```DAX
dim_org[Region] = "Europe"
```

### Enterprise RLS (empfohlen)
Requires: `security_user_org`

```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### Optional OLS
- Sensitive fields über Rollen ausblenden.

---

## 8. Performance & Refresh

- Storage Mode: Import oder Direct Lake  
- Incremental Refresh:
  - Monthly partitions
  - History: 24–36 Monate
- Page Load Targets:
  - KPI Page < 2s  
  - Detail Page < 3s  
- Technical columns hidden  
- No calculated columns  
- Aggregations optional

---

## 9. QA & Validation

| Check Type              | Object             | Rule                           | Tolerance |
|-------------------------|--------------------|--------------------------------|-----------|
| Referential Integrity   | fact → dims        | ≥ 99.9 %                       | 0.1 %     |
| Reconciliation          | KPIs vs Source     | Match Source                   | ±0.5 %    |
| Variance Consistency    | Δ-KPIs             | Sum(Driver KPIs) ≈ Δ KPI       | ±1 %      |
| Plausibility Checks     | UC-spezifisch      | industry/logic dependent       | manual    |
