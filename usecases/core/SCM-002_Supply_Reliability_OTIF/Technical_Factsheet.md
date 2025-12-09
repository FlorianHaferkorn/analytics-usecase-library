# SCM-002 – Supply Reliability & OTIF (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/supply_chain.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: SCM-002)

---

## 1. Data Contract (Scope for SCM-002)

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
      - { name: Week, type: int }

  - name: dim_supplier
    columns:
      - { name: SupplierKey, type: int, role: key }
      - { name: SupplierCode, type: text }
      - { name: SupplierName, type: text }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Tier, type: text }

  - name: dim_lane
    columns:
      - { name: LaneKey, type: int, role: key }
      - { name: Origin, type: text }
      - { name: Destination, type: text }
      - { name: Mode, type: text }

  - name: dim_dc
    columns:
      - { name: DcKey, type: int, role: key }
      - { name: DcCode, type: text }
      - { name: DcName, type: text }
      - { name: Region, type: text }
      - { name: Country, type: text }

  - name: dim_product
    columns:
      - { name: ProductKey, type: int, role: key }
      - { name: SKU, type: text }
      - { name: ProductName, type: text }
      - { name: Category, type: text }
      - { name: Subcategory, type: text }

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: DcName, type: text }

fact:
  - name: fact_shipments
    grain: shipment_line
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: SupplierKey, type: int, ref: dim_supplier }
      - { name: LaneKey, type: int, ref: dim_lane }
      - { name: DcKey, type: int, ref: dim_dc }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: ShippedQty, type: number, agg: sum }
      - { name: DeliveredQty, type: number, agg: sum }
      - { name: PlannedDeliveryDate, type: date }
      - { name: ActualDeliveryDate, type: date }
      - { name: OnTimeFlag, type: boolean }
      - { name: InFullFlag, type: boolean }
      - { name: OTIFRootCause, type: text }
      - { name: PenaltyAmount, type: currency, agg: sum }
      - { name: ExpediteCostAmount, type: currency, agg: sum }

  - name: fact_customer_orders
    grain: order_line
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: DcKey, type: int, ref: dim_dc }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: OrderQty, type: number, agg: sum }
      - { name: DeliveredQty, type: number, agg: sum }
      - { name: StockoutImpactFlag, type: boolean }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_shipments → `scm.fact_shipments`
- fact_customer_orders → `scm.fact_customer_orders`
- dim_date → `shared.dim_date`
- dim_supplier → `scm.dim_supplier`
- dim_lane → `scm.dim_lane`
- dim_dc → `scm.dim_dc`
- dim_product → `shared.dim_product`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `scm_supply_reliability_otif`

**Tables:** fact_shipments, fact_customer_orders, dim_date, dim_supplier, dim_lane, dim_dc, dim_product, security_user_org (RLS only)

**Relationships**
- fact_shipments[DateKey] → dim_date[DateKey] (1:* | single)
- fact_shipments[SupplierKey] → dim_supplier[SupplierKey] (1:* | single)
- fact_shipments[LaneKey] → dim_lane[LaneKey] (1:* | single)
- fact_shipments[DcKey] → dim_dc[DcKey] (1:* | single)
- fact_shipments[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_customer_orders[DateKey] → dim_date[DateKey]; fact_customer_orders[DcKey] → dim_dc[DcKey]; fact_customer_orders[ProductKey] → dim_product[ProductKey] (1:* | single)
- security_user_org attribute join to dim_dc by Region/Country/DcName (RLS mapping)

**Hierarchies**
- Supplier: Region > Country > SupplierName
- Lane: Origin > Destination > Mode
- DC: Region > Country > DcName
- Product: Category > Subcategory > SKU
- Date: Year > Quarter > Month > Date

**Display Folders**
- 01_Reliability: OTIF %, On-Time %, In-Full %
- 02_Service: Stockout Impact %
- 03_Cost: Penalties, Expedite Cost

---

## 3. Measure Inventory

| Measure Name           | kpi_id                          | Type       | Folder        | Format  |
|------------------------|---------------------------------|------------|---------------|---------|
| OTIF %                 | supply.otif.pct                 | KPI        | 01_Reliability| 0.0 %  |
| On-Time %              | supply.on_time.pct              | KPI        | 01_Reliability| 0.0 %  |
| In-Full %              | supply.in_full.pct              | KPI        | 01_Reliability| 0.0 %  |
| Stockout Impact %      | supply.stockout_impact.pct      | KPI        | 02_Service    | 0.0 %  |
| Penalties Amount       | supply.penalty.amount           | KPI        | 03_Cost       | €#,0.00|
| Expedite Cost Amount   | supply.expedite.amount          | Supporting | 03_Cost       | €#,0.00|

---

## 4. Measures (DAX)

```DAX
OTIF % =
DIVIDE (
    SUMX ( fact_shipments, IF ( fact_shipments[OnTimeFlag] && fact_shipments[InFullFlag], 1, 0 ) ),
    COUNTROWS ( fact_shipments )
)
```

```DAX
On-Time % =
DIVIDE (
    SUMX ( fact_shipments, IF ( fact_shipments[OnTimeFlag], 1, 0 ) ),
    COUNTROWS ( fact_shipments )
)
```

```DAX
In-Full % =
DIVIDE (
    SUMX ( fact_shipments, IF ( fact_shipments[InFullFlag], 1, 0 ) ),
    COUNTROWS ( fact_shipments )
)
```

```DAX
Stockout Impact % =
DIVIDE (
    SUMX ( fact_customer_orders, IF ( fact_customer_orders[StockoutImpactFlag], fact_customer_orders[OrderQty], 0 ) ),
    SUM ( fact_customer_orders[OrderQty] )
)
```

```DAX
Penalties Amount = SUM ( fact_shipments[PenaltyAmount] )
```

```DAX
Expedite Cost Amount = SUM ( fact_shipments[ExpediteCostAmount] )
```

---

## 5. Defaults & Formatting

| Field/Measure                                 | Format  | Summarization | Display Folder  |
|-----------------------------------------------|---------|---------------|-----------------|
| OTIF %, On-Time %, In-Full %, Stockout Impact % | 0.0 % | None          | 01/02           |
| Penalties Amount, Expedite Cost Amount        | €#,0.00 | Sum           | 03_Cost         |
| Quantities                                    | #,0     | Sum           | Reliability     |

---

## 6. Visual Requirements (Technical)
- KPI cards: OTIF %, On-Time %, In-Full %, Stockout Impact %, Penalties, Expedite Cost.
- Trend line: OTIF %, On-Time %, In-Full % by dim_date[Week/Month].
- Column: OTIF % by dim_supplier[SupplierName] with variance to target; slicer for Region/Country.
- Pareto: Shipment lines by fact_shipments[OTIFRootCause] with OTIF % variance.
- Cost chart: Penalties and Expedite Cost by dim_supplier[SupplierName] and dim_lane[Mode].
- Matrix: Supplier > Lane > DC > SKU with OTIF %, On-Time %, In-Full %, Stockout Impact %, Penalties; export enabled.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; enforce Region/Country/DcName filters on dim_dc and propagate to facts.
- OLS (optional): hide cost fields (Penalties, Expedite Cost) for external/vendor views; restrict OTIFRootCause text if sensitive.

---

## 8. Performance & Refresh
- Storage: Import; incremental by month (24–36 months).
- Partition fact_shipments by Month; pre-calculate OnTimeFlag and InFullFlag in source to avoid DAX row scans.
- Consider aggregated table Month x Supplier x Lane for long history if >50M rows.
- Ensure timezone handling for promised vs actual timestamps before flag creation.

---

## 9. QA & Validation

| Check Type                  | Object                                 | Rule                                          | Tolerance |
|-----------------------------|----------------------------------------|-----------------------------------------------|-----------|
| Referential Integrity       | facts → dimensions                     | ≥ 99.9 % matched keys                         | 0.1 %     |
| OTIF Calculation            | OnTimeFlag & InFullFlag completeness   | Matches SLA reporting                         | ±1.0 pp   |
| Stockout Impact Calculation | StockoutImpactFlag coverage            | Coverage ≥ 95 % of impacted orders            | 5 % gap   |
| Cost Capture                | Penalties/Expedite vs finance records  | Differences within control band               | ±0.5 %    |
| Root Cause Coding           | OTIFRootCause completeness             | ≥ 90 % shipments with coded reason            | 10 % gap  |
