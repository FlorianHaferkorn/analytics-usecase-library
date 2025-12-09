# SCM-003 – Forecast vs Actual (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/supply_chain.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: SCM-003)

---

## 1. Data Contract (Scope for SCM-003)

```yaml
dimension:
  - name: dim_date
    columns:
      - { name: DateKey, type: int, role: key }
      - { name: Date, type: date }
      - { name: Year, type: int }
      - { name: Quarter, type: text }
      - { name: Month, type: text }
      - { name: MonthNumber, type: int }

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Channel, type: text }

  - name: dim_product
    columns:
      - { name: ProductKey, type: int, role: key }
      - { name: SKU, type: text }
      - { name: ProductName, type: text }
      - { name: Category, type: text }
      - { name: Subcategory, type: text }
      - { name: Class, type: text }   # ABC/XYZ

  - name: dim_forecast_version
    columns:
      - { name: ForecastVersion, type: text, role: key }
      - { name: CreatedAt, type: datetime }
      - { name: Horizon, type: text }   # e.g., M+1, M+3

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Channel, type: text }

fact:
  - name: fact_forecast
    grain: sku_channel_month_version
    columns:
      - { name: DateKey, type: int, ref: dim_date }     # period
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: ForecastVersion, type: text, ref: dim_forecast_version }
      - { name: ForecastQty, type: number, agg: sum }

  - name: fact_actuals
    grain: sku_channel_month
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: ActualQty, type: number, agg: sum }
      - { name: StockoutFlag, type: boolean }
      - { name: ExpediteFlag, type: boolean }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_forecast → `scm.fact_forecast`
- fact_actuals → `scm.fact_actuals`
- dim_forecast_version → `scm.dim_forecast_version`
- dim_date → `shared.dim_date`
- dim_org → `shared.dim_org`
- dim_product → `shared.dim_product`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `scm_forecast_vs_actual`

**Tables:** fact_forecast, fact_actuals, dim_date, dim_org, dim_product, dim_forecast_version, security_user_org (RLS only)

**Relationships**
- fact_forecast[DateKey] → dim_date[DateKey] (1:* | single)
- fact_actuals[DateKey] → dim_date[DateKey] (1:* | single)
- fact_forecast[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_actuals[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_forecast[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_actuals[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_forecast[ForecastVersion] → dim_forecast_version[ForecastVersion] (1:* | single)
- security_user_org attribute join to dim_org by Region/Country/Channel (RLS mapping)

**Hierarchies**
- Org: Region > Country > Channel
- Product: Category > Subcategory > SKU
- Date: Year > Quarter > Month

**Display Folders**
- 01_Forecast: Forecast Accuracy %, MAPE %, Bias %
- 02_Service: Service Impact %
- 03_Process: Re-plan Count

---

## 3. Measure Inventory

| Measure Name           | kpi_id                             | Type       | Folder       | Format |
|------------------------|------------------------------------|------------|--------------|--------|
| Forecast Accuracy %    | plan.forecast.accuracy.pct         | KPI        | 01_Forecast  | 0.0 % |
| MAPE %                 | plan.forecast.mape.pct             | KPI        | 01_Forecast  | 0.0 % |
| Bias %                 | plan.forecast.bias.pct             | KPI        | 01_Forecast  | 0.0 % |
| Service Impact %       | plan.forecast.service_impact.pct   | KPI        | 02_Service   | 0.0 % |
| Re-plan Frequency      | plan.replan.count                  | KPI        | 03_Process   | #,0   |
| Forecast Qty           | plan.forecast.qty                  | Supporting | 01_Forecast  | #,0   |
| Actual Qty             | plan.actual.qty                    | Supporting | 01_Forecast  | #,0   |

---

## 4. Measures (DAX)

```DAX
Forecast Qty = SUM ( fact_forecast[ForecastQty] )
```

```DAX
Actual Qty = SUM ( fact_actuals[ActualQty] )
```

```DAX
Forecast Error % =
DIVIDE ( [Actual Qty] - [Forecast Qty], [Actual Qty] )
```

```DAX
Forecast Accuracy % = 1 - ABS ( [Forecast Error %] )
```

```DAX
MAPE % =
AVERAGEX (
    VALUES ( dim_product[ProductKey] ),
    ABS ( [Forecast Error %] )
)
```

```DAX
Bias % =
DIVIDE ( [Forecast Qty] - [Actual Qty], [Actual Qty] )
```

```DAX
Service Impact % =
DIVIDE (
    SUMX ( fact_actuals, IF ( fact_actuals[StockoutFlag] || fact_actuals[ExpediteFlag], fact_actuals[ActualQty], 0 ) ),
    SUM ( fact_actuals[ActualQty] )
)
```

```DAX
Re-plan Frequency =
DISTINCTCOUNT ( fact_forecast[ForecastVersion] )
```

---

## 5. Defaults & Formatting

| Field/Measure                   | Format | Summarization | Display Folder |
|---------------------------------|--------|---------------|----------------|
| Forecast Accuracy %, MAPE %, Bias %, Service Impact % | 0.0 % | None | 01_Forecast / 02_Service |
| Re-plan Frequency               | #,0    | Count         | 03_Process     |
| Quantities (Forecast/Actual)    | #,0    | Sum           | 01_Forecast    |

---

## 6. Visual Requirements (Technical)
- KPI cards: Forecast Accuracy %, MAPE %, Bias %, Service Impact %, Re-plan Frequency.
- Trend line: Accuracy % and Bias % by dim_date[Month]; slicer for class and channel.
- Column: Accuracy % and MAPE % by dim_product[SKU] (focus A/B class); optional by dim_org[Channel].
- Bias distribution: Column showing Bias % by SKU/Channel; filter for over-/under-forecasting.
- Service Impact Pareto: impacted quantity by SKU/channel (from StockoutFlag/ExpediteFlag).
- Matrix: Region > Channel > SKU with Accuracy %, MAPE %, Bias %, Service Impact %, Re-plan Frequency; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; enforce Region/Country/Channel filters on dim_org and propagate to facts.
- OLS (optional): hide ForecastVersion details for external viewers; restrict access to class or product groups if required.

---

## 8. Performance & Refresh
- Storage: Import; incremental by month, retain 36 months of forecast/actuals.
- Partition by dim_date[Month]; keep only selected/latest forecast versions or flag the “latest” version in source to reduce DAX complexity.
- Avoid calculated columns; pre-clean forecast versions and ensure ActualQty and ForecastQty share grain.
- If volume high, aggregate older history to Month x Channel x Category for MAPE/Bias trending.

---

## 9. QA & Validation

| Check Type                  | Object                               | Rule                                        | Tolerance |
|-----------------------------|--------------------------------------|---------------------------------------------|-----------|
| Referential Integrity       | facts → dimensions                   | ≥ 99.9 % matched keys                       | 0.1 %     |
| Version Integrity           | fact_forecast vs dim_forecast_version| Latest version flag set; no orphan versions | n/a       |
| Accuracy/Bias Calculation   | Error measures                       | Matches planning system definitions         | ±0.5 pp   |
| Service Impact Calculation  | Stockout/Expedite flag coverage      | Coverage ≥ 95 %                             | 5 % gap   |
| Class Coverage              | dim_product[Class] completeness      | ≥ 95 % populated                            | 5 % gap   |
