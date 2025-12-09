# FIN-001 – Technical Factsheet

## 0. Metadata (Mandatory)
- **Domain:** Finance
- **Technical Owner:** Treasury / Finance Data Lead
- **Data Product / Model ID:** `finance_cash_liquidity`
- **Source Systems:** ERP (FI/CO), Treasury, DWH
- **Use Case Business Factsheet:** `usecases/core/FIN-001_Cash_Liquidity_Performance/Business_Factsheet.md`

---

## 1. Model References
- **Data Contract (Domain):** `data_contracts/domains/finance.yaml`
- **Data Contract (Sources):** `data_contracts/sources/finance.yaml` (if available)
- **Semantic Model Definition:** `semantic_models/domains/finance/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`

---

## 2. Data Contract Scope (YAML – FIN-001)
Cash & Working Capital slice incl. security table.

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}
      - {name: Quarter, type: text}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: OrgCode, type: text}
      - {name: OrgName, type: text}
      - {name: BU, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}

  - name: security_user_org   # RLS
    columns:
      - {name: UserPrincipalName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: OrgKey, type: int, ref: dim_org}

fact:
  - name: fact_cash
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Cash Balance Amount, type: currency, agg: sum}
      - {name: Operating Cash Flow Amount, type: currency, agg: sum}
      - {name: CapEx Amount, type: currency, agg: sum}
      - {name: Financing Flow Amount, type: currency, agg: sum}
      - {name: Cash Plan Amount, type: currency, agg: sum}

  - name: fact_wc
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: DSO Days, type: number, agg: avg}
      - {name: DIO Days, type: number, agg: avg}
      - {name: DPO Days, type: number, agg: avg}
      - {name: WC Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_cash → `lh_finance.fact_cash`
- fact_wc → `lh_finance.fact_working_capital`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- security_user_org → `lh_security.security_user_org`

---

## 3. Semantic Model Requirements

### 3.1 Tables
- fact_cash
- fact_working_capital (fact_wc)
- dim_date
- dim_org
- security_user_org (RLS)

### 3.2 Relationships
- fact_cash[DateKey] → dim_date[DateKey] (1:* | single)
- fact_cash[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_wc[DateKey] → dim_date[DateKey] (1:* | single)
- fact_wc[OrgKey] → dim_org[OrgKey] (1:* | single)

### 3.3 Hierarchies
- Org: Region → Country → BU → OrgName
- Date: Year → Quarter → Month

### 3.4 Sort-by
- Month → MonthNumber
- OrgName → OrgCode (if needed)

### 3.5 Modeling Rules
- No calculated columns; business logic in measures/ETL.
- Default summarization correct; technical fields hidden.
- Display folders: 01_Cash, 02_WC, 03_Plan.

---

## 4. Measure Inventory

| Measure Name             | KPI ID / Supporting          | Purpose                     | Display Folder | Format  | Type |
|--------------------------|------------------------------|-----------------------------|----------------|---------|------|
| Cash Balance             | fin.cash.balance             | Liquidity headroom          | 01_Cash        | €#,0.0  | KPI  |
| Operating Cash Flow      | fin.cash.ocf                 | Cash generation             | 01_Cash        | €#,0.0  | KPI  |
| Liquidity vs Plan %      | fin.cash.vs_plan.pct         | Plan attainment             | 01_Cash        | 0.0 %   | KPI  |
| Working Capital Amount   | fin.wc.amount                | WC absolute                 | 02_WC          | €#,0.0  | KPI  |
| DSO / DIO / DPO          | wc.dso/dio/dpo.days          | WC drivers                  | 02_WC          | #,0     | KPI  |
| Cash Conversion Cycle    | wc.ccc.days                  | Rotation speed              | 02_WC          | #,0     | KPI  |

---

## 5. Measures (DAX)

```DAX
/// fin.cash.balance – Liquidity headroom
Cash Balance =
    SUM ( fact_cash[Cash Balance Amount] )
```

```DAX
/// fin.cash.ocf – Operating cash generation
Operating Cash Flow =
    SUM ( fact_cash[Operating Cash Flow Amount] )
```

```DAX
/// fin.cash.vs_plan.pct – Plan attainment
Liquidity vs Plan % =
    DIVIDE ( [Cash Balance] - SUM ( fact_cash[Cash Plan Amount] ),
             SUM ( fact_cash[Cash Plan Amount] ) )
```

```DAX
/// fin.wc.amount – Working capital absolute
Working Capital Amount =
    SUM ( fact_wc[WC Amount] )
```

```DAX
/// wc.dso.days – Receivables efficiency
DSO Days =
    AVERAGE ( fact_wc[DSO Days] )
```

```DAX
/// wc.dio.days – Inventory efficiency
DIO Days =
    AVERAGE ( fact_wc[DIO Days] )
```

```DAX
/// wc.dpo.days – Payables efficiency
DPO Days =
    AVERAGE ( fact_wc[DPO Days] )
```

```DAX
/// wc.ccc.days – Cash rotation speed
Cash Conversion Cycle =
    [DSO Days] + [DIO Days] - [DPO Days]
```

---

## 6. Defaults & Formatting
- Currency: `€#,0.0` | Percent: `0.0 %` | Days: `#,0`
- Summarization: Amounts = Sum; Percent = None; Days = Average.
- Display folders: 01_Cash, 02_WC, 03_Plan.

---

## 7. Visual Requirements

| Visual Name        | Type      | X-Axis / Category  | Y-Axis / Value                              | Segment / Legend | Filters / Defaults |
|--------------------|-----------|--------------------|---------------------------------------------|------------------|--------------------|
| Cash & OCF Trend   | Line      | dim_date[Month]    | [Cash Balance], [Operating Cash Flow], Plan | Region/BU        | Last 12–24M        |
| CCC by BU          | Bar       | dim_org[BU]        | [Cash Conversion Cycle]                     | Region           | Top/Bottom N       |
| WC Drivers Bridge  | Waterfall | Drivers            | Δ Cash vs Plan (DSO, DIO, DPO, CapEx, Tax)  | n/a              | Period selector    |
| Aging & Overdues   | Matrix    | Customer/Supplier  | Aging buckets, DSO/DPO, exposure            | Region/BU        | Export enabled     |

---

## 8. RLS / OLS Rules

### 8.1 RLS Pattern
Region/Country/BU-based RLS via security table:
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

### 8.2 OLS (optional)
- Hide sensitive fields (Cash Balance, OCF) for non-finance roles; leave WC/CCC visible.

---

## 9. Performance & Refresh
- Storage Mode: Import.
- Partitioning: monthly; history 36–60 months.
- No calculated columns; technical fields hidden; consider aggregations for long history.

---

## 10. QA & Validation Rules

| Check Name             | Object                | Rule                                       | Threshold | Automated | Owner          |
|------------------------|-----------------------|--------------------------------------------|-----------|-----------|----------------|
| RI Check               | fact → dims           | ≥ 99.9 % matched keys                      | 99.9 %    | Y         | Data Engineer  |
| Cash Reconciliation    | Cash Balance          | vs GL/bank statements                      | ±0.5 %    | Y         | Controller     |
| OCF Reconciliation     | Operating Cash Flow   | vs cash flow statement                     | ±0.5 %    | Y         | Controller     |
| CCC Consistency        | DSO+DIO-DPO = CCC     | within tolerance                           | ±1 day    | Y         | BI Dev         |
| Plan vs Actual Gap     | Liquidity vs Plan %   | within defined band (±5 %)                 | ±5 %      | Y         | Finance Lead   |
