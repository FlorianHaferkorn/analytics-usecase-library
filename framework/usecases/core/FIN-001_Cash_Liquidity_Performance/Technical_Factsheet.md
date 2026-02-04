---
id: FIN-001
factsheet_type: technical
---

# FIN-001 - Cash & Liquidity Performance  

## Technical Factsheet

---

## 0. Metadata (Mandatory)

- **Domain:** Finance
- **Technical Owner:** Treasury / Finance BI Lead
- **Model ID:** finance_cash_liquidity
- **Source Systems:** ERP (FI/CO), Treasury, DWH
- **Business Factsheet:** framework/usecases/core/FIN-001_Cash_Liquidity_Performance/Business_Factsheet.md

---

## 1. Model References

- **Domain Data Contract:** framework/framework/framework/data_contracts/domains/finance.yaml
- **Source Data Contract:** framework/framework/framework/data_contracts/sources/finance.yaml (if present)
- **Semantic Model Definition:** framework/framework/framework/semantic_models/core_action_ready/model_definition.yaml
- **KPI Catalog:** framework/kpi_catalog/KPI_Catalog.md
- **Measure Dictionary:** framework/framework/framework/semantic_models/domains/Finance/Measure_Dictionary_Finance.md
- **Action Codes:** framework/action_codes/README.md

---

## 2. Required KPIs - Measure Mapping (Mandatory)

```yaml
kpi_to_measure_mapping:

  - kpi_id: fin.cash.balance
    kpi_name: Cash Balance
    measure_name: [Cash Balance]
    format: EUR#,0
    folder: 10_Finance

  - kpi_id: fin.cash.ocf
    kpi_name: Operating Cash Flow
    measure_name: [Operating Cash Flow]
    format: EUR#,0
    folder: 10_Finance

  - kpi_id: fin.cash.vs_plan.pct
    kpi_name: Cash vs Plan %
    measure_name: [Cash vs Plan %]
    format: 0.0%
    folder: 10_Finance

  - kpi_id: wc.ccc.days
    kpi_name: Cash Conversion Cycle (days)
    measure_name: [CCC Days]
    format: #,0.0
    folder: 10_Finance

  - kpi_id: wc.dso.days
    kpi_name: DSO (days)
    measure_name: [DSO Days]
    format: #,0.0
    folder: 10_Finance

  - kpi_id: wc.dio.days
    kpi_name: DIO (days)
    measure_name: [DIO Days]
    format: #,0.0
    folder: 10_Finance

  - kpi_id: wc.dpo.days
    kpi_name: DPO (days)
    measure_name: [DPO Days]
    format: #,0.0
    folder: 10_Finance
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
      - {name: Entity, type: text}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}

  - name: dim_customer   # for AR/DSO drill
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
      - {name: Region, type: text, nullable: true}

  - name: dim_supplier   # for AP/DPO drill
    columns:
      - {name: SupplierKey, type: int, role: key}
      - {name: SupplierCode, type: text}
      - {name: SupplierName, type: text}
      - {name: Region, type: text, nullable: true}

  - name: dim_product    # optional for DIO
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}

  - name: security_user_org   # canonical RLS
    columns:
      - {name: UserPrincipalName, type: string, role: rls}
      - {name: Region, type: text, nullable: true}
      - {name: Country, type: text, nullable: true}
      - {name: OrgKey, type: int, ref: dim_org, nullable: true}

fact:
  - name: fact_cash
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Cash Balance Amount, type: currency, agg: sum}
      - {name: Plan Cash Amount, type: currency, agg: sum, nullable: true}

  - name: fact_cashflow
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Operating Cash Flow Amount, type: currency, agg: sum}
      - {name: Plan OCF Amount, type: currency, agg: sum, nullable: true}

  - name: fact_ar
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: CustomerKey, type: int, ref: dim_customer, nullable: true}
      - {name: AR Amount, type: currency, agg: sum}
      - {name: Revenue Amount, type: currency, agg: sum}

  - name: fact_ap
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: SupplierKey, type: int, ref: dim_supplier, nullable: true}
      - {name: AP Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}

  - name: fact_inventory
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product, nullable: true}
      - {name: Inventory Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
```

---

## 4. Semantic Model Requirements

### 4.1 Tables

- fact_cash  
- fact_cashflow  
- fact_ar  
- fact_ap  
- fact_inventory  
- dim_date  
- dim_org  
- dim_customer  
- dim_supplier  
- dim_product (optional)  
- security_user_org (RLS)

### 4.2 Relationships (Mandatory)

- dim_date (1) -> all facts on DateKey  
- dim_org (1) -> all facts on OrgKey  
- dim_customer (1) -> fact_ar on CustomerKey  
- dim_supplier (1) -> fact_ap on SupplierKey  
- dim_product (1) -> fact_inventory on ProductKey (if used)  
- security_user_org filters dim_org -> cascades to facts  
- Single direction; avoid ambiguous paths; no bi-dir except RLS bridge.

### 4.3 Hierarchies

- Date: Year -> Quarter -> Month  
- Org: Region -> Entity  
- Customer: Region -> CustomerName (if used)  
- Supplier: Region -> SupplierName (if used)  
- Product (optional): Category -> ProductName

### 4.4 Sort-by Columns

- Month -> MonthNumber  
- Entity -> OrgKey  
- CustomerName -> CustomerCode  
- SupplierName -> SupplierCode  
- ProductName -> ProductCode

### 4.5 Modeling Constraints

- No calculated columns; no implicit measures.  
- Default summarization set; technical columns hidden; folders per dictionary.  
- Surrogate keys mandatory; avoid M2M.

---

## 5. Measures (DAX)

### 5.1 Measure Inventory

| Measure Name | KPI ID / Supporting | Purpose | Folder | Format | Type |
|--------------|---------------------|---------|--------|--------|------|
| Cash Balance | fin.cash.balance | Liquidity | 10_Finance | EUR#,0 | KPI |
| Cash vs Plan % | fin.cash.vs_plan.pct | Plan comparison | 10_Finance | 0.0% | KPI |
| Operating Cash Flow | fin.cash.ocf | Cash generation | 10_Finance | EUR#,0 | KPI |
| CCC Days | wc.ccc.days | WC cycle | 10_Finance | #,0.0 | KPI |
| DSO Days | wc.dso.days | Receivables efficiency | 10_Finance | #,0.0 | KPI |
| DIO Days | wc.dio.days | Inventory efficiency | 10_Finance | #,0.0 | KPI |
| DPO Days | wc.dpo.days | Payables efficiency | 10_Finance | #,0.0 | KPI |
| AR Amount | Supporting | DSO numerator | 10_Finance | EUR#,0 | Supporting |
| AP Amount | Supporting | DPO numerator | 10_Finance | EUR#,0 | Supporting |
| Inventory Amount | Supporting | DIO numerator | 10_Finance | EUR#,0 | Supporting |
| Revenue Amount | Supporting | DSO denominator | 10_Finance | EUR#,0 | Supporting |
| COGS Amount | Supporting | DIO/DPO denominator | 10_Finance | EUR#,0 | Supporting |

### 5.2 DAX Definitions

```DAX
/// fin.cash.balance - Liquidity
Cash Balance :=
    SUM ( fact_cash[Cash Balance Amount] )

/// fin.cash.vs_plan.pct - Plan comparison
Cash vs Plan % :=
    DIVIDE ( [Cash Balance] - SUM ( fact_cash[Plan Cash Amount] ), SUM ( fact_cash[Plan Cash Amount] ) )

/// fin.cash.ocf - Operating Cash Flow
Operating Cash Flow :=
    SUM ( fact_cashflow[Operating Cash Flow Amount] )

/// wc.dso.days - DSO
AR Amount :=
    SUM ( fact_ar[AR Amount] )

/// Supporting - Revenue Amount
Revenue Amount :=
    SUM ( fact_ar[Revenue Amount] )

/// Supporting - DSO Days
DSO Days :=
    DIVIDE ( [AR Amount], DIVIDE ( [Revenue Amount], 365 ) )

/// wc.dio.days - DIO
Inventory Amount :=
    SUM ( fact_inventory[Inventory Amount] )

/// Supporting - COGS Amount
COGS Amount :=
    SUM ( fact_inventory[COGS Amount] )

/// Supporting - DIO Days
DIO Days :=
    DIVIDE ( [Inventory Amount], DIVIDE ( [COGS Amount], 365 ) )

/// wc.dpo.days - DPO
AP Amount :=
    SUM ( fact_ap[AP Amount] )

/// Supporting - COGS Amount (AP)
COGS Amount (AP) :=
    SUM ( fact_ap[COGS Amount] )

/// Supporting - DPO Days
DPO Days :=
    DIVIDE ( [AP Amount], DIVIDE ( [COGS Amount (AP)], 365 ) )

/// wc.ccc.days - CCC
CCC Days :=
    [DSO Days] + [DIO Days] - [DPO Days]
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

- None required; cash-sensitive details could be masked by role if needed (TODO if client requests).

---

## 7. Technical Assumptions

- Plan cash/OCF provided; revenue/COGS aligned by period/entity with AR/AP/Inventory.
- Data latency <=24h; currency EUR.
- OneLake canonical dims used (dim_date, dim_org, dim_customer, dim_supplier, dim_product optional, security_user_org).

---

## 8. Deployment Requirements

- Mode: DirectLake or Import (prefer DirectLake if Fabric).  
- Incremental refresh: yes, by Month (cash daily if needed).  
- Aggregations: optional; consider monthly aggregates for large AR/AP detail.  
- Workspace/naming: `ARF - Finance` dataset/model per governance.

---

## 9. QA & Validation Rules

| Check | Rule | Threshold | Automated Y/N | Owner |
|-------|------|-----------|---------------|-------|
| Referential Integrity | Date/Org keys non-null in facts | 100% | Y | Data Engineering |
| Cash/Plan Alignment | Plan fields populated for plan periods | 100% plan scope | Y | Finance |
| DSO/DIO/DPO Validity | No div-by-zero; values within plausible bands | 0 errors | Y | BI/Finance |
| CCC Consistency | CCC recomputes from DSO/DIO/DPO | Exact | Y | BI |
| RLS Coverage | Users see only authorised entities | 0 leaks | Y | Security |
| Performance | Main visuals <2s on representative sample | <2s | Y | BI |

agent_hooks:
  validate: true
  generate_measures: true
  recommend_actions: true
  paths:
    business_factsheet: ./Business_Factsheet.md
    technical_factsheet: ./Technical_Factsheet.md



