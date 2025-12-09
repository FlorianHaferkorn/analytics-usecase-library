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
Describe the relevant slice, incl. security table, keys, and required fields.

```yaml
dimension:
  - name: <dim_x>
    columns:
      - {name: <Key>, type: int, role: key}
      - {name: <BusinessCode>, type: text}
      - {name: <Name>, type: text}
      - {name: <Attribute>, type: text}

  - name: security_user_org   # if RLS needed
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

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

### Source Mapping (Physical Layer)
- fact_<...> → `<physical_db.schema.table_or_view>`
- dim_<...> → `<physical_db.schema.table_or_view>`
- security_<...> → `<physical_db.schema.table_or_view>`

> Do: refer back to domain-level contracts.  
> Don’t: redefine the same logic per Use Case.

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_<...>
- dim_<...>
- security_<...> (if used)

### 3.2 Relationships
- fact ↔ dim only via surrogate keys (1:* | single to fact)
- No bidirectional or ambiguous paths

### 3.3 Hierarchies
- Date: Year → Quarter → Month → Date
- Org: Region → Country → OrgName (or Plant/BU/…)
- Product/Customer/etc.: <hierarchy>

### 3.4 Sort-by Columns
- Month → MonthNumber
- Name → Code (if needed)

### 3.5 Modeling Rules (Mandatory)
- No calculated columns (business logic in ETL or measures)
- Default summarization set correctly; technical fields hidden
- Display folders aligned with domain conventions
- Naming conventions (Amount/Qty/%/Rate etc.) enforced

---

## 4. Measure Inventory
Every measure has a KPI ID or is Supporting. Single source of truth.

| Measure Name | KPI ID (or Supporting) | Purpose | Display Folder | Format | Type (KPI/Supporting) |
|--------------|------------------------|---------|----------------|--------|-----------------------|
| <Measure> | <kpi_id or Supporting> | <why> | <01_Sales / 02_Margin / …> | <€, %, days> | <KPI/Supporting> |
| … | … | … | … | … | … |

---

## 5. Measures (DAX)
List all measures with short comments.

```DAX
/// <kpi_id or Supporting> – <short purpose>
<Measure Name> =
    <DAX expression>
```

> Do: reuse supporting measures; link to templates (PVM/PEVM/Accuracy/Bias) where applicable.  
> Don’t: build monolithic KPI formulas without supporting layers.

---

## 6. Defaults & Formatting
- Currency: `€,#,0.00` | Percent: `0.0 %` | Qty/Count: `#,0` | Days: `#,0` | Score/Index: `0.00`
- Summarization: Amounts/Qtys = Sum; Percent/Rate = None/Average (choose explicitly); Date fields = None.

---

## 7. Visual Requirements
Required visuals with fields/axes (no TBD).

| Visual Name | Type | X-Axis / Category | Y-Axis / Value | Segment / Legend | Filters / Defaults |
|-------------|------|-------------------|----------------|------------------|--------------------|
| <Trend> | Line | dim_date[Month] | <KPI/Measure> | <Region/Channel> | Last 12–24M |
| <Ranking> | Bar | <Dim> | <KPI> | <Segment> | Top/Bottom N |
| <Waterfall/Bridge> | Waterfall | <Category> | <Variance drivers> | n/a | <Period> |
| <Matrix> | Table/Matrix | <Dim drill path> | KPIs | <Segment> | Export enabled |

---

## 8. RLS / OLS Rules

### 8.1 RLS Pattern (mandatory if sensitive)
Standard: security table + DAX filter, no hardcoded users.

```DAX
dim_org[Region] IN
    CALCULATETABLE(
        VALUES(security_user_org[Region]),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
    )
```

### 8.2 OLS (optional)
- Which measures/fields are hidden per role?

---

## 9. Performance & Refresh
- Storage Mode: <Import / Direct Lake / …>
- Partitioning: <grain, history e.g., 24–36M>
- No calculated columns; technical fields hidden; consider aggregations/MVs for long history.

---

## 10. QA & Validation Rules
At least 3–5 hard rules with tolerances.

| Check Name | Object | Rule | Threshold | Automated (Y/N) | Owner |
|------------|--------|------|-----------|------------------|-------|
| RI Check | facts vs dims | ≥ 99.9 % matched keys | 99.9 % | Y | Data Engineer |
| KPI Reconciliation | <KPI> vs source | Δ ≤ 0.5 % | 0.5 % | Y | Controller |
| Decomposition Check | Drivers sum to Δ KPI | | 1.0 % | Y | BI Dev |
| Outlier Check | key KPI | within business-defined range | domain-specific | N | Business Owner |

> Do: specify concrete tolerances; Don’t: leave QA as “manual” only.
