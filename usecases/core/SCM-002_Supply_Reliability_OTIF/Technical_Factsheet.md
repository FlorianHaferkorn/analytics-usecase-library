# SCM-002 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: SCM-002)

---

## 1. Data Contract (YAML – SCM-002 Scope)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_supplier
    columns:
      - {name: SupplierKey, type: int, role: key}
      - {name: SupplierCode, type: text}
      - {name: SupplierName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}

  - name: dim_lane
    columns:
      - {name: LaneKey, type: int, role: key}
      - {name: Origin, type: text}
      - {name: Destination, type: text}
      - {name: Mode, type: text}

  - name: dim_dc
    columns:
      - {name: DcKey, type: int, role: key}
      - {name: DcCode, type: text}
      - {name: DcName, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: SKU, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}

fact:
  - name: fact_shipments
    grain: shipment_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: SupplierKey, type: int, ref: dim_supplier}
      - {name: LaneKey, type: int, ref: dim_lane}
      - {name: DcKey, type: int, ref: dim_dc}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Shipped Qty, type: number, agg: sum}
      - {name: Delivered Qty, type: number, agg: sum}
      - {name: On Time Flag, type: boolean}
      - {name: In Full Flag, type: boolean}
      - {name: Penalty Amount, type: currency, agg: sum}
      - {name: Expedite Cost Amount, type: currency, agg: sum}
      - {name: Stockout Flag, type: boolean}
      - {name: Root Cause, type: text}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_shipments → `lh_scm.fact_shipments`
- dim_date → `lh_shared.dim_date`
- dim_supplier → `lh_scm.dim_supplier`
- dim_lane → `lh_scm.dim_lane`
- dim_dc → `lh_scm.dim_dc`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`scm_supply_reliability_otif`

### Tables
- fact_shipments  
- dim_date  
- dim_supplier  
- dim_lane  
- dim_dc  
- dim_product  

### Relationships
- fact_shipments[DateKey] → dim_date[DateKey] (1:* | single)
- fact_shipments[SupplierKey] → dim_supplier[SupplierKey] (1:* | single)
- fact_shipments[LaneKey] → dim_lane[LaneKey] (1:* | single)
- fact_shipments[DcKey] → dim_dc[DcKey] (1:* | single)
- fact_shipments[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Supplier: Region → Country → SupplierName
- Lane: Origin → Destination → Mode
- DC: Region → Country → DC
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month → Date

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name           | kpi_id                        | Type        | Folder         | Format   |
|------------------------|-------------------------------|-------------|----------------|----------|
| OTIF %                 | supply.otif.pct               | KPI         | 01_Reliability | 0.0 %    |
| On-Time %              | supply.on_time.pct            | KPI         | 01_Reliability | 0.0 %    |
| In-Full %              | supply.in_full.pct            | KPI         | 01_Reliability | 0.0 %    |
| Stockout Rate %        | supply.stockout.pct           | KPI         | 02_Service     | 0.0 %    |
| Penalties Amount       | supply.penalty.amount         | KPI         | 03_Cost        | €#,0.00  |
| Expedite Cost Amount   | supply.expedite.amount        | Supporting  | 03_Cost        | €#,0.00  |

---

## 4. Measures (DAX)

```DAX
OTIF % =
    DIVIDE (
        SUMX ( fact_shipments, IF ( fact_shipments[On Time Flag] && fact_shipments[In Full Flag], 1, 0 ) ),
        COUNTROWS ( fact_shipments )
    )
```

```DAX
On-Time % =
    DIVIDE (
        SUMX ( fact_shipments, IF ( fact_shipments[On Time Flag], 1, 0 ) ),
        COUNTROWS ( fact_shipments )
    )
```

```DAX
In-Full % =
    DIVIDE (
        SUMX ( fact_shipments, IF ( fact_shipments[In Full Flag], 1, 0 ) ),
        COUNTROWS ( fact_shipments )
    )
```

```DAX
Stockout Rate % =
    DIVIDE (
        SUMX ( fact_shipments, IF ( fact_shipments[Stockout Flag], fact_shipments[Delivered Qty], 0 ) ),
        SUM ( fact_shipments[Shipped Qty] )
    )
```

```DAX
Penalties Amount =
    SUM ( fact_shipments[Penalty Amount] )
```

```DAX
Expedite Cost Amount =
    SUM ( fact_shipments[Expedite Cost Amount] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Percentages   | 0.0 %    | None          | Reliability/Service |
| Amounts       | €#,0.00  | Sum           | Cost           |
| Quantities    | #,0      | Sum           | Volume         |

---

## 6. Visual Requirements (Technical)

- KPI cards: OTIF, On-Time, In-Full, Stockout %, Penalties.
- Bar: OTIF by supplier/lane/DC with variance vs target.
- Pareto: Root causes from `Root Cause`.
- Line: OTIF trend over time.
- Matrix: Supplier → Lane/DC → SKU with KPIs; export enabled.

---

## 7. RLS / OLS

- Region/country-based RLS on suppliers and DCs.  
- Optional OLS to hide penalty/expedite amounts for external views.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (24–36 months).  
- Partition large fact_shipments by month; consider aggregations by month/lane for history.  
- Avoid calculated columns; precompute flags upstream if possible.

---

## 9. QA & Validation

| Check Type              | Object                 | Rule                                   | Tolerance |
|-------------------------|------------------------|----------------------------------------|-----------|
| Referential Integrity   | fact → dims            | ≥ 99.9 % matched keys                  | 0.1 %     |
| OTIF Calculation        | On Time & In Full flags| Matches operational SLA reporting      | ±1.0 pp   |
| Penalty/Expedite Capture| Amount fields          | Matches finance/sourcing records       | ±0.5 %    |
| Root Cause Coding       | Root Cause             | % shipments with valid cause ≥ 90 %    | threshold |
