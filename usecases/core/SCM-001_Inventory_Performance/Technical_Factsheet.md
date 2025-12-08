# SCM-001 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: SCM-001)

---

## 1. Data Contract (YAML – SCM-001 Scope)

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
      - {name: Location, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: SKU, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: UoM, type: text}

fact:
  - name: fact_inventory
    grain: sku_location_day
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: On Hand Qty, type: number, agg: avg}
      - {name: On Hand Value, type: currency, agg: avg}
      - {name: Aging Bucket, type: text}
      - {name: Obsolete Flag, type: boolean}

  - name: fact_orders
    grain: order_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Order Qty, type: number, agg: sum}
      - {name: Delivered Qty, type: number, agg: sum}
      - {name: OTIF Flag, type: boolean}
      - {name: Stockout Flag, type: boolean}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_inventory → `lh_scm.fact_inventory`
- fact_orders → `lh_scm.fact_orders`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`scm_inventory_performance`

### Tables
- fact_inventory  
- fact_orders  
- dim_date  
- dim_org  
- dim_product  

### Relationships
- fact_inventory[DateKey] → dim_date[DateKey] (1:* | single)
- fact_inventory[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_inventory[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_orders[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_orders[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_orders[DateKey] → dim_date[DateKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Location
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month → Date

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name                | kpi_id                         | Type        | Folder         | Format   |
|-----------------------------|--------------------------------|-------------|----------------|----------|
| Days in Inventory (DIO)     | inv.dio.days                   | KPI         | 01_Inventory   | #,0      |
| Inventory Turnover          | inv.turnover                   | KPI         | 01_Inventory   | #,0.0    |
| Stockout Rate %             | inv.stockout.pct               | KPI         | 02_Service     | 0.0 %    |
| OTIF %                      | inv.otif.pct                   | KPI         | 02_Service     | 0.0 %    |
| Obsolescence Risk %         | inv.obsolete.pct               | KPI         | 03_Risk        | 0.0 %    |
| On Hand Value               | inv.onhand.value               | Supporting  | 01_Inventory   | €#,0.00  |

---

## 4. Measures (DAX)

```DAX
On Hand Value =
    AVERAGE ( fact_inventory[On Hand Value] )
```

```DAX
Inventory Turnover =
    DIVIDE ( [COGS Amount], [Average Inventory Value] )
```

```DAX
Days in Inventory (DIO) =
    DIVIDE ( 365, [Inventory Turnover] )
```

```DAX
Stockout Rate % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[Stockout Flag], fact_orders[Order Qty], 0 ) ),
        SUM ( fact_orders[Order Qty] )
    )
```

```DAX
OTIF % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[OTIF Flag], 1, 0 ) ),
        COUNTROWS ( fact_orders )
    )
```

```DAX
Obsolescence Risk % =
    DIVIDE (
        SUMX ( fact_inventory, IF ( fact_inventory[Obsolete Flag], fact_inventory[On Hand Value], 0 ) ),
        SUM ( fact_inventory[On Hand Value] )
    )
```

*Note:* COGS Amount and Average Inventory Value are assumed from finance/supply chain integration; adjust if sourced separately.

---

## 5. Defaults & Formatting

| Field/Measure   | Format   | Summarization | Display Folder |
|-----------------|----------|---------------|----------------|
| Values/Amounts  | €#,0.00  | Average/Sum   | Inventory      |
| Percentages     | 0.0 %    | None          | Service/Risk   |
| Days/Turns      | #,0 / #,0.0 | None/Sum   | Inventory      |

---

## 6. Visual Requirements (Technical)

- KPI cards: DIO, Turnover, Stockout %, OTIF %, Obsolescence Risk %.
- Bar: DIO/Turnover by location/product.
- Line: DIO and Stockout trend.
- Pareto: Obsolescence value by SKU/category.
- Matrix: Location → Category → SKU with KPIs; export enabled.

---

## 7. RLS / OLS

- Org-based RLS (Region/Country/Location).  
- Optional OLS to hide value fields for external partners; keep quantities visible.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (24–36 months).  
- Pre-aggregate inventory snapshots by month where daily is too large.  
- Separate partitions for orders if volume-heavy.

---

## 9. QA & Validation

| Check Type              | Object                     | Rule                                    | Tolerance |
|-------------------------|----------------------------|-----------------------------------------|-----------|
| Referential Integrity   | fact tables → dims         | ≥ 99.9 % matched keys                   | 0.1 %     |
| DIO Calculation         | Turnover/DIO relationship   | 365 / Turnover ≈ DIO                    | ±0.5 days |
| OTIF Capture            | OTIF %                     | Matches logistics SLA reporting         | ±1.0 pp   |
| Stockout Recording      | Stockout %                 | Order lines flagged correctly           | ±1.0 pp   |
