# COM-004 — Promotion Effectiveness  
## Technical Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Domain:** Commercial
- **Technical Owner:** Trade Marketing / BI Lead
- **Model ID:** promotion_effectiveness
- **Source Systems:** ERP (sales), Promo Mgmt, DWH
- **Business Factsheet:** usecases/core/COM-004_Promotion_Effectiveness/Business_Factsheet.md

---

## 1. Model References
- **Domain Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Source Data Contract:** data_contracts/sources/commercial.yaml (promo details if present)
- **Semantic Model Definition:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/domain_kpi_catalog.md
- **Measure Dictionary:** framework/kpi_catalog/domain_measure_dictionary.md
- **Action Codes:** framework/action_codes/ActionCodes_v2_Portfolio.md

---

## 2. Required KPIs → Measure Mapping (Mandatory)
```yaml
kpi_to_measure_mapping:
  - kpi_id: sales.promo.roi.pct
    kpi_name: Promotion ROI %
    measure_name: [Promotion ROI %]
    format: 0.0%
    folder: 04_Promo
  - kpi_id: sales.promo.incremental.amount
    kpi_name: Incremental Sales Amount
    measure_name: [Incremental Sales Amount]
    format: €#,0
    folder: 04_Promo
  - kpi_id: margin.promo.gm.pct
    kpi_name: Promo Gross Margin %
    measure_name: [Promo Gross Margin %]
    format: 0.0%
    folder: 02_Margin
  - kpi_id: sales.price.realization_pct
    kpi_name: Price Realization %
    measure_name: [Price Realization %]
    format: 0.0%
    folder: 03_Pricing
  - kpi_id: sales.promo.cannibalization.pct
    kpi_name: Cannibalization %
    measure_name: [Cannibalization %]
    format: 0.0%
    folder: 04_Promo
```

---

## 3. Data Contract Scope (Subset YAML)
```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Quarter, type: text}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgCode, type: text}
      - {name: OrgName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: Brand, type: text}

  - name: dim_promo
    columns:
      - {name: PromoKey, type: int, role: key}
      - {name: Promotion, type: text}
      - {name: PromoType, type: text}
      - {name: Mechanic, type: text}
      - {name: StartDateKey, type: int, ref: dim_date}
      - {name: EndDateKey, type: int, ref: dim_date}
      - {name: FundedByVendor, type: boolean, nullable: true}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}
      - {name: Plant, type: text, nullable: true}
      - {name: Line, type: text, nullable: true}
      - {name: Channel, type: text, nullable: true}

fact:
  - name: fact_sales
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: PromoKey, type: int, ref: dim_promo, nullable: true}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity, type: decimal, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: Cost of Goods Sold Amount, type: currency, agg: sum}
      - {name: Promo Flag, type: boolean}

  - name: fact_promo
    grain: promotion
    columns:
      - {name: PromoKey, type: int, ref: dim_promo}
      - {name: Promo Cost, type: currency}
      - {name: Funding Amount, type: currency, nullable: true}
      - {name: Baseline Sales Amount, type: currency, nullable: true}
      - {name: Baseline Quantity, type: decimal, nullable: true}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables
- fact_sales  
- fact_promo  
- dim_date  
- dim_org  
- dim_product  
- dim_promo  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)
- dim_date (1) → fact_sales on DateKey; dim_date (1) → dim_promo on Start/End if modeled; use role-played date if needed.  
+- dim_org (1) → fact_sales on OrgKey  
- dim_product (1) → fact_sales on ProductKey  
- dim_promo (1) → fact_sales on PromoKey  
- fact_promo (1) → dim_promo on PromoKey  
- security_user_org filters dim_org (Region/Country/Channel/OrgKey) → cascades to fact_sales; use same filter context for promo views.
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies
- Date: Year → Quarter → Month  
- Org: Region → Country → Channel → OrgName  
- Product: Category → Subcategory → ProductName  
- Promo: PromoType → Mechanic → Promotion

### 4.4 Sort-by Columns
- Month → MonthNumber  
- Promotion → PromoKey (or StartDate)  

### 4.5 Modeling Constraints
- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; handle many-to-many only via bridge if needed (avoid).

---

## 5. Measures (DAX)

### 5.1 Measure Inventory
| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Promotion ROI % | sales.promo.roi.pct | Promo profitability | 04_Promo | 0.0% | KPI |
| Incremental Sales Amount | sales.promo.incremental.amount | Uplift sizing | 04_Promo | €#,0 | KPI |
| Promo Gross Margin % | margin.promo.gm.pct | Profit quality | 02_Margin | 0.0% | KPI |
| Price Realization % | sales.price.realization_pct | Discount discipline | 03_Pricing | 0.0% | KPI |
| Cannibalization % | sales.promo.cannibalization.pct | Net effect | 04_Promo | 0.0% | KPI |
| Net Sales Amount | Supporting | Revenue base | 01_Revenue | €#,0 | Supporting |
| Gross Margin Amount | Supporting | Margin base | 02_Margin | €#,0 | Supporting |

### 5.2 DAX Definitions
```DAX
/// Supporting — Revenue
Net Sales Amount :=
    SUM ( fact_sales[Net Sales Amount] )

/// Supporting — Gross margin
Gross Margin Amount :=
    SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_sales[Cost of Goods Sold Amount] )

/// margin.promo.gm.pct — Promo GM%
Promo Gross Margin % :=
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )

/// sales.price.realization_pct — During promo
Price Realization % :=
    DIVIDE ( SUM ( fact_sales[Net Price Amount] ), SUM ( fact_sales[List Price Amount] ) )

/// sales.promo.incremental.amount — Uplift vs baseline (placeholder if baseline provided)
Incremental Sales Amount :=
    SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_promo[Baseline Sales Amount] )

/// sales.promo.roi.pct — ROI
Promotion ROI % :=
    DIVIDE ( [Gross Margin Amount] - SUM ( fact_promo[Baseline Sales Amount] - fact_promo[Promo Cost] ), SUM ( fact_promo[Promo Cost] ) )

/// sales.promo.cannibalization.pct — Cannibalization (placeholder)
Cannibalization % :=
    // TODO: requires baseline and related-item mapping
    BLANK ()
```

---

## 6. RLS / OLS Requirements

### 6.1 Security Table Pattern
```yaml
security_table:
  name: security_user_org
  keys:
    - UserPrincipalName
    - Region
    - Country
    - OrgKey
    - Channel
  mapping_target: dim_org[OrgKey]
  fallback_behavior: deny_all_if_no_match
```

### 6.2 RLS Rule (Fabric / Power BI)
```DAX
dim_org[OrgKey] IN
    CALCULATETABLE (
        VALUES ( security_user_org[OrgKey] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME()
    )
```

### 6.3 OLS (optional)
- None required; consider masking promo cost if sensitive (TODO based on client policy).

---

## 7. Technical Assumptions
- Baseline/uplift logic provided or computed upstream; cannibalization requires related-item mapping.
- Promo cost/funding captured; price realization fields populated.
- Data latency ≤24h; currency EUR.
- OneLake canonical dims used; promo calendar consistent with date dimension.

---

## 8. Deployment Requirements
- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, monthly partitions for last 24 months.  
- Aggregations: optional for large volumes.  
- Workspace/naming: `ARF – Commercial` dataset/model per governance.

---

## 9. QA & Validation Rules
| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org/Product/Promo keys non-null in facts | 100% | Y | Data Engineering |
| ROI Integrity | Promo ROI calc reconciles GM uplift vs promo cost | Residual < 0.5% | Y | BI |
| Baseline Consistency | Baseline present for all measured promos | 100% measured promos | Y | BI |
| Price Realization | Net Price within policy bands vs List | ≤0.5% exceptions | Y | BI |
| Cannibalization | Calculation coverage for related items | TODO coverage target | N (baseline dependency) | BI |
| RLS Coverage | Users see only authorised regions/channels | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md
