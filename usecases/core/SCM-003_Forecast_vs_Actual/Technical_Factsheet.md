# SCM-003 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/supply_chain.yaml`
- **Semantic Model Definition:**  
  `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: SCM-003)

---

## 1. Data Contract (YAML – SCM-003 Scope)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_org
    columns:
      - {name: OrgKey, type: int, role: key}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: Channel, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: SKU, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}

fact:
  - name: fact_forecast
    grain: sku_channel_month_version
    columns:
      - {name: DateKey, type: int, ref: dim_date}     # period
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Forecast Qty, type: number, agg: sum}
      - {name: Forecast Version, type: text}
      - {name: Forecast Created At, type: datetime}

  - name: fact_actuals
    grain: sku_channel_month
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Actual Qty, type: number, agg: sum}
      - {name: Stockout Flag, type: boolean}
      - {name: Expedite Flag, type: boolean}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_forecast → `lh_scm.fact_forecast`
- fact_actuals → `lh_scm.fact_actuals`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`scm_forecast_vs_actual`

### Tables
- fact_forecast  
- fact_actuals  
- dim_date  
- dim_org  
- dim_product  

### Relationships
- fact_forecast[DateKey] → dim_date[DateKey] (1:* | single)
- fact_actuals[DateKey] → dim_date[DateKey] (1:* | single)
- fact_forecast[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_actuals[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_forecast[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_actuals[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Channel
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name            | kpi_id                        | Type        | Folder         | Format |
|-------------------------|-------------------------------|-------------|----------------|--------|
| Forecast Accuracy %     | plan.forecast.accuracy.pct    | KPI         | 01_Forecast    | 0.0 %  |
| MAPE %                  | plan.forecast.mape.pct        | KPI         | 01_Forecast    | 0.0 %  |
| Bias %                  | plan.forecast.bias.pct        | KPI         | 01_Forecast    | 0.0 %  |
| Service Impact %        | plan.forecast.service_impact.pct | KPI     | 02_Service     | 0.0 %  |
| Re-plan Frequency       | plan.replan.count             | KPI         | 03_Process     | #,0    |

---

## 4. Measures (DAX)

Assuming a selected forecast version (latest or filtered):

```DAX
Forecast Qty :=
    SUM ( fact_forecast[Forecast Qty] )
```

```DAX
Actual Qty :=
    SUM ( fact_actuals[Actual Qty] )
```

```DAX
Forecast Error % :=
    DIVIDE ( [Actual Qty] - [Forecast Qty], [Actual Qty] )
```

```DAX
Forecast Accuracy % :=
    1 - ABS ( [Forecast Error %] )
```

```DAX
MAPE % :=
    AVERAGEX (
        VALUES ( dim_product[ProductKey] ),
        ABS ( [Forecast Error %] )
    )
```

```DAX
Bias % :=
    DIVIDE ( [Forecast Qty] - [Actual Qty], [Actual Qty] )
```

```DAX
Service Impact % :=
    DIVIDE (
        SUMX ( fact_actuals, IF ( fact_actuals[Stockout Flag], fact_actuals[Actual Qty], 0 ) ),
        SUM ( fact_actuals[Actual Qty] )
    )
```

```DAX
Re-plan Frequency :=
    DISTINCTCOUNT ( fact_forecast[Forecast Version] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format | Summarization | Display Folder |
|---------------|--------|---------------|----------------|
| Percentages   | 0.0 %  | None          | Forecast/Service |
| Quantities    | #,0    | Sum           | Volume          |
| Counts        | #,0    | Count         | Process         |

---

## 6. Visual Requirements (Technical)

- KPI cards: Accuracy, MAPE, Bias, Service Impact, Re-plan Frequency.
- Bar: Accuracy/Bias by product/channel/region.
- Line: Accuracy/Bias trend.
- Pareto: Service impact by SKU.
- Matrix: Region → Channel → SKU with KPIs; export enabled.

---

## 7. RLS / OLS

- Region/country/channel-based RLS via dim_org.
- Optional OLS to hide forecast versions for external parties.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (24–36 months).  
- Keep multiple forecast versions; mark latest; consider snapshotting to reduce volume.  
- Avoid calculated columns; precompute version flags upstream.

---

## 9. QA & Validation

| Check Type              | Object                      | Rule                                    | Tolerance |
|-------------------------|-----------------------------|-----------------------------------------|-----------|
| Referential Integrity   | fact tables → dims          | ≥ 99.9 % matched keys                   | 0.1 %     |
| Version Integrity       | Forecast versions           | Latest version identified correctly     | manual    |
| Accuracy/Bias Calc      | Error measures              | Match planning system definitions       | ±0.5 pp   |
| Service Impact Capture  | Stockout/Expedite flags     | Correctly populated                     | ±1.0 pp   |
