# XD-003 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/corporate.yaml`
- **Semantic Model Definition:**  
  `semantic_models/core_action_ready/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: XD-003)

---

## 1. Data Contract (YAML – XD-003 Scope)

Enterprise cockpit consumes conformed dimensions and key facts from finance, supply chain, and people domains.

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
      - {name: BU, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: CostCenter, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}

fact:
  - name: fact_finance
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: EBITDA Amount, type: currency, agg: sum}
      - {name: Working Capital Amount, type: currency, agg: sum}
      - {name: DSO Days, type: number, agg: avg}
      - {name: DIO Days, type: number, agg: avg}
      - {name: DPO Days, type: number, agg: avg}

  - name: fact_service
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Service Level Pct, type: number, agg: avg}
      - {name: OTIF Pct, type: number, agg: avg}

  - name: fact_people
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Headcount Avg, type: number, agg: avg}
      - {name: Leavers, type: number, agg: sum}

  - name: fact_esg
    grain: org_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ESG Revenue Amount, type: currency, agg: sum}
      - {name: Total Revenue Amount, type: currency, agg: sum}
```

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_finance → `lh_corp.fact_finance`
- fact_service → `lh_scm.fact_service`
- fact_people → `lh_hr.fact_people`
- fact_esg → `lh_esg.fact_revenue`
- dims → shared conformed dimensions

---

## 2. Semantic Model Requirements

### Model Name
`executive_kpi_overview`

### Tables
- fact_finance  
- fact_service  
- fact_people  
- fact_esg  
- dim_date  
- dim_org  
- dim_product (optional for revenue drill)

### Relationships
- Each fact links to dim_date and dim_org (1:* | single).
- Product relationship only if revenue drill is needed.

### Hierarchies
- Org: Region → Country → BU → CostCenter
- Date: Year → Quarter → Month
- Product: Category → ProductName (optional)

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name             | kpi_id                         | Type        | Folder           | Format   |
|--------------------------|--------------------------------|-------------|------------------|----------|
| Revenue Growth %         | fin.revenue.growth.pct         | KPI         | 01_Finance       | 0.0 %    |
| Gross Margin %           | margin.gm.pct                  | KPI         | 01_Finance       | 0.0 %    |
| EBITDA Margin %          | profit.ebitda_margin           | KPI         | 01_Finance       | 0.0 %    |
| Cash Conversion Cycle    | wc.ccc.days                    | KPI         | 02_Cash          | #,0      |
| Service Level %          | service.level.pct              | KPI         | 03_Service       | 0.0 %    |
| OTIF %                   | supply.otif.pct                | Supporting  | 03_Service       | 0.0 %    |
| Turnover %               | hr.turnover.pct                | KPI         | 04_People        | 0.0 %    |
| ESG-Aligned Revenue %    | esg.revenue.aligned.pct        | KPI         | 05_ESG           | 0.0 %    |

---

## 4. Measures (DAX)

```DAX
Gross Margin % =
    DIVIDE ( [Net Sales Amount] - [COGS Amount], [Net Sales Amount] )
```

```DAX
EBITDA Margin % =
    DIVIDE ( [EBITDA Amount], [Net Sales Amount] )
```

```DAX
Revenue Growth % =
    DIVIDE ( [Net Sales Amount] - CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ) ),
             CALCULATE ( [Net Sales Amount], DATEADD ( dim_date[Date], -1, YEAR ) ) )
```

```DAX
Cash Conversion Cycle =
    [DSO Days] + [DIO Days] - [DPO Days]
```

```DAX
Turnover % =
    DIVIDE ( [Leavers], AVERAGE ( fact_people[Headcount Avg] ) )
```

```DAX
ESG-Aligned Revenue % =
    DIVIDE ( [ESG Revenue Amount], [Total Revenue Amount] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Amounts       | €#,0.0   | Sum           | Finance/ESG    |
| Percentages   | 0.0 %    | None          | KPI folders    |
| Days          | #,0      | None          | Cash           |

---

## 6. Visual Requirements (Technical)

- KPI cards: top enterprise KPIs with Plan/LY deltas.
- Small multiples: trends by KPI.
- Waterfall/bridge for margin or cash where relevant.
- Heatmap/bar: KPI gaps by region/BU.
- Matrix: Region → BU with KPI set; drill to driver pages; export enabled.

---

## 7. RLS / OLS

- Org-based RLS (Region/Country/BU).  
- Optional OLS to hide sensitive finance fields for limited roles.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (36–60 months).  
- Keep facts at monthly grain; avoid daily granularity.  
- Pre-aggregate to BU/month to control size.

---

## 9. QA & Validation

| Check Type              | Object                  | Rule                                     | Tolerance |
|-------------------------|-------------------------|------------------------------------------|-----------|
| Referential Integrity   | fact tables → dims      | ≥ 99.9 % matched keys                    | 0.1 %     |
| Revenue/GM Reconciliation | Finance facts         | Matches GL/finance close                 | ±0.5 %    |
| CCC Calculation         | DSO+DIO-DPO             | Aligns with WC reporting                 | ±1 day    |
| ESG Share               | ESG %                   | Matches ESG reporting                    | ±0.5 pp   |
