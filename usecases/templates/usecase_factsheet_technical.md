# <USE CASE ID> - <USE CASE NAME>

## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Domain:** <Commercial / Finance / Ops / SCM / XD>
- **Technical Owner:** <Role>
- **Model ID:** <model name>
- **Source Systems:** <ERP / CRM / POS / DWH>
- **Business Factsheet:** <relative path>

---

## 1. Model References

- **Domain Data Contract:** <path>
- **Source Data Contract:** <path>
- **Semantic Model Definition:** <path>
- **KPI Catalog:** <path>
- **Measure Dictionary:** <path>
- **Action Codes:** <path>

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: <domain.topic.metric>
    kpi_name: <KPI Name>
    measure_name: <Measure Name>
    format: <EUR, %, #, days>
    folder: <01_Sales / 02_Margin / ...>
    notes: <optional>
  - ...
```

---

## 3. Data Contract Scope (Subset YAML)

```yaml
dimension:
  - name: <dim_x>
    columns:
      - {name: <Key>, role: key, type: int}
      - {name: <BusinessCode>, type: text}
      - {name: <Name>, type: text}
      - {name: <Attribute>, type: text}

fact:
  - name: <fact>
    grain: <invoice_line / asset_day / customer_day>
    columns:
      - {name: <Amount>, type: currency, unit: EUR, agg: sum}
      - {name: <Qty>, type: number, agg: sum}
      - {name: <Status>, type: text}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_<...>  
- dim_<...>  
- security_<...> (if applicable)

### 4.2 Relationships (Mandatory)

- single direction  
- dim -> fact  
- no bi-directional relationships  
- no ambiguous paths  
- no M2M unless explicitly permitted

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month -> Day  
- Org: Region -> Country -> Store  
- Product/Customer hierarchies (if needed)

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- Name -> Code  

### 4.5 Modeling Constraints

- no calculated columns  
- no implicit measures  
- default summarization set  
- all technical columns hidden  
- display folders consistent with dictionary  
- surrogate keys mandatory  

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| <Measure> | <kpi_id> | <why> | 01_Sales | EUR#,0.00 | KPI |
| ... | ... | ... | ... | ... | ... |

### 5.2 DAX Definitions

```DAX
/// <kpi_id or Supporting> - <short purpose>
<Measure Name> =
    <DAX expression>
```

---

## 6. RLS / OLS Requirements

### 6.1 Security Table Pattern

```yaml
security_table:
  name: security_user_org
  keys:
    - UserPrincipalName
    - OrgKey
  mapping_target: dim_org[OrgKey]
  fallback_behavior: <deny all / limited>
```

### 6.2 RLS Rule (Fabric / Power BI)

```DAX
dim_org[OrgKey] IN
  CALCULATETABLE(
    VALUES(security_user_org[OrgKey]),
    security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
  )
```

### 6.3 OLS (optional)

- Sensitive measures: <list>
- Visibility rules per role.

---

## 7. Technical Assumptions

- data latency  
- refresh cadence  
- missing data handling  
- currency conversion  
- plan/forecast rules

---

## 8. Deployment Requirements

- DirectLake / Import / Hybrid  
- Incremental refresh required? <Y/N>  
- Aggregations? <Y/N>  
- Workspace standards  
- Naming standards  

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| RI Check | Refer. integrity | >= 99.9 % | Y | DE |
| KPI Match | KPI - measure present | 100 % | Y | BI |
| Outlier Check | KPI in valid range | domain-specific | Y/N | Analyst |
| Performance Check | Visual < 2s | 2s | Y | BI |

---
