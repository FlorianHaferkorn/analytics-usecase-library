# Promotion Effectiveness (ROI & Uplift) – Technical Factsheet

## 0. Metadata & KPI Binding
- dataset_model: `Contoso Sales Sample for Power BI Desktop.SemanticModel`
- qa_asserts: `RI_OK`, `Promo_Baseline_Validated`, `Promo_Cost_Linked`
- required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.uplift_pct
  - sales.promo.incremental.amount
  - margin.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.promo.cost.amount
- required_kpis:
  - `sales.promo.roi.pct` → Promo ROI %
  - `sales.promo.uplift_pct` → Promo Uplift %
  - `sales.promo.incremental.amount` → Incremental Sales Amount
  - `margin.promo.incremental.amount` → Incremental GM Amount
  - `margin.promo.gm.pct` → GM % During Promo
  - `sales.promo.cost.amount` → Promo Cost Amount

## 1. Data Contract (YAML)
```yaml
facts:
  - name: fact_sales
    grain: invoice_line
    primary_key: [InvoiceLineID]
    columns:
      - { name: Date, type: date_key, role: key }
      - { name: OrgID, type: string, role: org_key }
      - { name: ProductID, type: string, role: product_key }
      - { name: Channel, type: string, role: channel_key }
      - { name: PromoID, type: string, role: promo_key }
      - { name: Net Sales Amount, type: currency, agg: sum }
      - { name: Units Qty, type: decimal, agg: sum }
      - { name: COGS Amount, type: currency, agg: sum }
      - { name: PromoFlag, type: boolean }
  - name: fact_promo_events
    grain: promo_product_day
    primary_key: [PromoID, ProductID, Date]
    columns:
      - { name: PromoID, type: string, role: promo_key }
      - { name: ProductID, type: string, role: product_key }
      - { name: Date, type: date_key, role: key }
      - { name: Promo Type, type: string }
      - { name: Promo Mechanic, type: string }
      - { name: Promo Cost Amount, type: currency, agg: sum }
      - { name: Discount %, type: decimal }
  - name: fact_promo_baseline
    grain: promo_product_day
    primary_key: [PromoID, ProductID, Date]
    columns:
      - { name: Baseline Sales Amount, type: currency, agg: sum }
      - { name: Baseline Units Qty, type: decimal, agg: sum }
      - { name: Baseline GM Amount, type: currency, agg: sum }
dims:
  - name: dim_date
    grain: date
    primary_key: [Date]
    attributes:
      - { name: Year, type: int }
      - { name: Month, type: int }
      - { name: Week, type: int }
  - name: dim_org
    grain: org
    primary_key: [OrgID]
  - name: dim_product
    grain: product
    primary_key: [ProductID]
  - name: dim_channel
    grain: channel
    primary_key: [Channel]
  - name: dim_promo
    grain: promo
    primary_key: [PromoID]
    attributes:
      - { name: Promo Name, type: string }
      - { name: Promo Calendar Bucket, type: string }
settings:
  timezone: Europe/Berlin
  currency: EUR
relationships:
  - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
  - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
  - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
  - { from: fact_sales.Channel, to: dim_channel.Channel, cardinality: many-to-one, direction: single }
  - { from: fact_sales.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
  - { from: fact_promo_events.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
  - { from: fact_promo_events.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
  - { from: fact_promo_events.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
  - { from: fact_promo_baseline.PromoID, to: dim_promo.PromoID, cardinality: many-to-one, direction: single }
  - { from: fact_promo_baseline.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
```

## 2. Model Mapping
- `fact_sales[Net Sales Amount]` → Actual promo sales
- `fact_sales[Units Qty]` → Promo units
- `fact_sales[COGS Amount]` → Promo COGS
- `fact_promo_events[Promo Cost Amount]` → Trade spend
- `fact_promo_baseline[Baseline Sales Amount]` → Baseline revenue
- `fact_promo_baseline[Baseline GM Amount]` → Baseline gross margin
- `dim_promo[Promo Mechanic]`, `dim_channel[Channel]`, `dim_org[OrgID]`, `dim_product[ProductID]` for slicing
- `dim_date[Date]` (with Year/Month/Week hierarchies)

## 3. Measures / DAX
```DAX
Promo Cost Amount =
VAR PromoCost =
    SUM ( 'fact_promo_events'[Promo Cost Amount] )
RETURN
    PromoCost
```

```DAX
Incremental Sales Amount =
VAR PromoSales =
    SUM ( fact_sales[Net Sales Amount] )
VAR BaselineSales =
    SUM ( fact_promo_baseline[Baseline Sales Amount] )
RETURN
    PromoSales - BaselineSales
```

```DAX
Incremental GM Amount =
VAR PromoGM =
    SUM ( fact_sales[Net Sales Amount] ) - SUM ( fact_sales[COGS Amount] )
VAR BaselineGM =
    SUM ( fact_promo_baseline[Baseline GM Amount] )
RETURN
    PromoGM - BaselineGM
```

```DAX
Promo Uplift % =
VAR BaseSales =
    SUM ( fact_promo_baseline[Baseline Sales Amount] )
RETURN
    DIVIDE ( [Incremental Sales Amount], BaseSales )
```

```DAX
GM % During Promo =
VAR PromoSales =
    SUM ( fact_sales[Net Sales Amount] )
VAR PromoCOGS =
    SUM ( fact_sales[COGS Amount] )
RETURN
    DIVIDE ( PromoSales - PromoCOGS, PromoSales )
```

```DAX
Promo ROI % =
VAR IncrementalGM =
    [Incremental GM Amount]
VAR PromoCost =
    [Promo Cost Amount]
RETURN
    DIVIDE ( IncrementalGM - PromoCost, PromoCost )
```

### Measure Notes
- All measures scoped by `PromoID` to avoid double counting overlapping events.
- Baseline measures should use inactive relationships if baseline tables are modeled as separate fact tables; activate via `CALCULATE` with `USERELATIONSHIP` when needed.
- Add calculation groups for Plan vs Actual vs LY deltas once core measures validate.

## 4. Formatting, Display Folders & Defaults
| Field / Measure | Format | Display Folder | Notes |
|-----------------|--------|----------------|-------|
| Promo Cost Amount | Currency, 0 decimals | 01_Promo | Sum aggregation |
| Incremental Sales Amount | Currency, 0 decimals | 01_Promo | Sum |
| Incremental GM Amount | Currency, 0 decimals | 01_Promo | Sum |
| Promo Uplift % | Percentage, 1 decimal | 02_Ratios | Non-additive |
| GM % During Promo | Percentage, 1 decimal | 02_Ratios | Non-additive |
| Promo ROI % | Percentage, 1 decimal | 02_Ratios | Non-additive |
| Promo Mechanic | Text | 00_Slicers | Sort by desired priority |

Default summarization for ratios should be `Do not summarize`. Ensure `Promo Mechanic` sorted by a hidden numeric column to keep ranking (e.g., `dim_promo[MechanicSort]`).

## 5. Visual Requirements
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI cards | 3-second insight | Promo ROI %, Promo Uplift %, Incremental Sales, Incremental GM, Promo Cost | Show Plan/LY deltas |
| Waterfall | ROI variance drivers | Promo ROI %, Promo Cost Amount, Incremental GM Amount | Break down by mechanic |
| Scatter | Discount depth vs ROI | Discount %, Promo ROI %, Promo Type | Color by channel |
| Matrix | Promo by Org × Product | Promo ROI %, Promo Uplift %, GM % During Promo | Conditional formatting thresholds |
| Trend line | ROI over time | Date hierarchy, Promo ROI % | 12‑24 months; add reference line for target ROI |

## 6. RLS / Security
- RLS inherits from `dim_org` (region-based) and `dim_channel` (channel lead) roles. Use bridge table for multi-select responsibilities.
- Sensitive promo cost fields only visible to Marketing Controlling and Finance; enforce via object-level security on `fact_promo_events[Promo Cost Amount]`.

## 7. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_sales → dim_promo | ≥ 99.9 % of promo transactions map to a PromoID | 0.1 % unmatched |
| Baseline sanity | fact_promo_baseline | Baseline Sales within ±20 % of median pre-promo sales | Manual review otherwise |
| ROI positivity | Promo ROI % | Flag ROI > 500 % or < −100 % | Investigate tagging / cost capture |
| Spend linkage | Promo Cost Amount | ≥ 90 % of trade spend entries mapped to PromoID | 10 % unmatched |

## 8. Implementation Notes
- Calculated tables for promo calendars may be required to explode multi-week events into daily records for alignment with baseline windows.
- Use `Calculation Groups` for Plan/LY comparison once KPIs validated.
- Keep DAX free of `FORMAT` and prefer `DIVIDE` for all ratios to avoid division-by-zero.
