# FIN-001 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/finance.yaml`
- **Semantic Model Definition:**  
  `semantic_models/domains/finance/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: FIN-001)

---

## 1. Data Contract (YAML – FIN-001 Scope)

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
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: BU, type: text}

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

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_cash → `lh_finance.fact_cash`
- fact_wc → `lh_finance.fact_working_capital`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`

---

## 2. Semantic Model Requirements

### Model Name
`finance_cash_liquidity`

### Tables
- fact_cash  
- fact_wc  
- dim_date  
- dim_org  

### Relationships
- fact_cash[DateKey] → dim_date[DateKey] (1:* | single)
- fact_cash[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_wc[DateKey] → dim_date[DateKey] (1:* | single)
- fact_wc[OrgKey] → dim_org[OrgKey] (1:* | single)

### Hierarchies
- Org: Region → Country → BU → OrgName
- Date: Year → Quarter → Month

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name             | kpi_id                       | Type        | Folder      | Format   |
|--------------------------|------------------------------|-------------|-------------|----------|
| Cash Balance             | fin.cash.balance             | KPI         | 01_Cash     | €#,0.0   |
| Operating Cash Flow      | fin.cash.ocf                 | KPI         | 01_Cash     | €#,0.0   |
| Liquidity vs Plan %      | fin.cash.vs_plan.pct         | KPI         | 01_Cash     | 0.0 %    |
| Cash Conversion Cycle    | wc.ccc.days                  | KPI         | 02_WC       | #,0      |
| DSO / DIO / DPO          | wc.dso.days / wc.dio.days / wc.dpo.days | KPI | 02_WC | #,0 |

---

## 4. Measures (DAX)

```DAX
Cash Balance =
    SUM ( fact_cash[Cash Balance Amount] )
```

```DAX
Operating Cash Flow =
    SUM ( fact_cash[Operating Cash Flow Amount] )
```

```DAX
Liquidity vs Plan % =
    DIVIDE ( [Cash Balance] - SUM ( fact_cash[Cash Plan Amount] ),
             SUM ( fact_cash[Cash Plan Amount] ) )
```

```DAX
DSO Days = AVERAGE ( fact_wc[DSO Days] )
```

```DAX
DIO Days = AVERAGE ( fact_wc[DIO Days] )
```

```DAX
DPO Days = AVERAGE ( fact_wc[DPO Days] )
```

```DAX
Cash Conversion Cycle =
    [DSO Days] + [DIO Days] - [DPO Days]
```

---

## 5. Defaults & Formatting

| Field/Measure | Format  | Summarization | Display Folder |
|---------------|---------|---------------|----------------|
| Amounts       | €#,0.0  | Sum           | Cash           |
| Percentages   | 0.0 %   | None          | Cash           |
| Days          | #,0     | Average       | WorkingCapital |

---

## 6. RLS / OLS

- Org-based RLS (Region/Country/BU) via dim_org.  
- Optional OLS to hide cash balance for restricted roles; show CCC/DSO/DIO/DPO only.

Example RLS:
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. Performance & Refresh

- Storage: Import; incremental by month (36–60 months).  
- Month-grain facts only; no daily granularity required.  
- Hide technical columns; no calculated columns.

---

## 8. QA & Validation

| Check Type              | Object                  | Rule                                   | Tolerance |
|-------------------------|-------------------------|----------------------------------------|-----------|
| Referential Integrity   | fact tables → dims      | ≥ 99.9 % matched keys                  | 0.1 %     |
| Cash Reconciliation     | Cash Balance            | Matches GL/bank statements             | ±0.5 %    |
| OCF Reconciliation      | OCF                     | Matches cash flow statement            | ±0.5 %    |
| CCC Calculation         | DSO+DIO-DPO             | Aligns with WC reporting               | ±1 day    |
