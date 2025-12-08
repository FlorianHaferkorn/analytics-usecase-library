# <USE CASE ID> – <USE CASE NAME>  

---

## 0. Metadata (Mandatory)
- **Domain:** <Commercial / Finance / Operations / …>  
- **Technical Owner:** <Role / Name>  
- **Data Product / Model ID:** <semantic model name / ID>  
- **Source Systems:** <ERP / CRM / DWH / …>  
- **Use Case Business Factsheet:** <relative path to Business_Factsheet.md>  

---

## 1. Model References
- **Data Contract (Domain):** <path/to/data_contracts/domains/...yaml>  
- **Data Contract (Sources):** <path/to/data_contracts/sources/...yaml>  
- **Semantic Model Definition:** <path/to/semantic_models/.../model_definition.yaml>  
- **KPI Catalog:** <path/to/framework/kpi_catalog/domain_kpi_catalog.md>  
- **Measure Dictionary:** <path/to/framework/kpi_catalog/domain_measure_dictionary.md>  

---

## 2. Data Contract Scope (YAML)
Describe the subset of the domain contract relevant for this use case.

```yaml
dimension:
  - name: <dim_x>
    columns:
      - {name: <Key>, type: int, role: key}
      - {name: <BusinessCode>, type: text}
      - {name: <Name>, type: text}
      - {name: <Attribute>, type: text}

fact:
  - name: <fact_x>
    grain: <invoice_line / customer_day / asset_day / ...>
    columns:
      - {name: <Measure 1>, type: currency, agg: sum, unit: EUR}
      - {name: <Measure 2>, type: number, agg: sum, unit: pcs}
      - {name: <Status>, type: text, agg: none}
      - …

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

> Do: refer back to domain-level contracts.  
> Don’t: definieren dieselbe Logik mehrfach pro Use Case.

---

## 3. Semantic Model Requirements

### 3.1 Tables
List all tables used in the semantic model for this use case.

- fact_<...>  
- dim_<...>  
- security_<...> (if used)  

### 3.2 Relationships
Define all relationships and rules.

- fact → dim on surrogate keys only  
- direction: Single, from dimension to fact  
- no bidirectional relationships  
- no ambiguous relationship paths  

### 3.3 Hierarchies
List hierarchies that must be created.

- Date: Year → Quarter → Month → Date  
- Org: Region → Country → OrgName  
- Product/Customer/etc.: …  

### 3.4 Sort-by Columns
- Month → MonthNumber  
- Name → Code (if required)  

### 3.5 Modeling Rules (Mandatory)
- No calculated columns (business logic in measures or ETL)  
- Measures > calculated columns  
- Default summarization set correctly  
- Technical columns hidden by default  
- Display folders aligned with domain conventions  
- Naming conventions (Amount/Qty/%/Rate etc.) enforced  

---

## 4. Measure Inventory
Every measure references a KPI ID or is a supporting measure.

| Measure Name | KPI ID (or Supporting) | Purpose | Display Folder | Format | Type (KPI/Supporting) |
|--------------|------------------------|---------|----------------|--------|------------------------|
| <Measure> | <kpi_id or Supporting> | <why> | <01_Sales / 02_Margin / …> | <€, %, days> | <KPI/Supporting> |
| … | … | … | … | … | … |

> Do: keep the list the single source of truth for measures.  
> Don’t: implement measures, die hier nicht dokumentiert sind.

---

## 5. Measures (DAX)
List all measures relevant for this use case.  
Each measure must be documented with Copilot-ready comments.

```DAX
/// <kpi_id or Supporting> – <short purpose>
<Measure Name> =
    <DAX expression>
```

> Do: reuse Supporting Measures for repeated logic.  
> Don’t: verschachtelte KPI-Monsterformeln ohne Supporting Layers.

---

## 6. Formatting
Define formats consistent with your global conventions:

- Currency: `€#,0.00`  
- Percent: `0.0 %`  
- Quantity / Count: `#,0`  
- Days: `#,0`  
- Scores / Index: `0.00`  

---

## 7. RLS / OLS Rules

### 7.1 RLS Pattern (Mandatory)
- RLS always applied on dimension or security table.  
- No hard-coded usernames, always via security table.

Example:

```DAX
dim_org[Region] IN
    CALCULATETABLE(
        VALUES(security_user_org[Region]),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
    )
```

### 7.2 OLS (Optional)
- Define if sensitive measures require OLS (e.g. salary, cost, margin).  
- Describe which roles see which measures.

---

## 8. QA & Validation Rules
Define checks that can be automated or at least systematically validated.

| Check Name | Object | Rule | Threshold | Automated (Y/N) | Owner |
|------------|--------|------|-----------|------------------|-------|
| RI Check | facts vs dims | referential integrity ≥ 99.9 % | 99.9 % | Y | Data Engineer |
| KPI Reconciliation | [Net Sales Amount] vs source | Δ ≤ 0.5 % | 0.5 % | Y | Controller |
| Decomposition Check | Drivers sum to Δ KPI | | 1.0 % | Y | BI Dev |
| Outlier Check | key KPI | within business-defined range | domain-specific | N | Business Owner |

> Do: define wenigstens 3–5 harte Regeln pro Use Case.  
> Don’t: “QA: manual only” ohne Spezifikation.

