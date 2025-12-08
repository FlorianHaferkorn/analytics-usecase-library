# XD-001 – Technical Factsheet

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
  `usecases/UseCase_Inventory.md` (ID: XD-001)

---

## 1. Data Contract (YAML – XD-001 Scope)

```yaml
dimension:
  - name: dim_date
    columns:
      - {name: DateKey, type: int, role: key}
      - {name: Date, type: date}
      - {name: Year, type: int}
      - {name: Month, type: text}
      - {name: MonthNumber, type: int}

  - name: dim_customer
    columns:
      - {name: CustomerKey, type: int, role: key}
      - {name: CustomerCode, type: text}
      - {name: CustomerName, type: text}
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
  - name: fact_orders
    grain: order_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: CustomerKey, type: int, ref: dim_customer}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Ordered Qty, type: number, agg: sum}
      - {name: Delivered Qty, type: number, agg: sum}
      - {name: Requested Delivery Date, type: date}
      - {name: Actual Delivery Date, type: date}
      - {name: On Time Flag, type: boolean}
      - {name: In Full Flag, type: boolean}
      - {name: Order Accuracy Flag, type: boolean}
      - {name: Stockout Flag, type: boolean}
      - {name: Penalty Amount, type: currency, agg: sum}
      - {name: Credit Amount, type: currency, agg: sum}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_orders → `lh_scm.fact_orders`
- dim_date → `lh_shared.dim_date`
- dim_customer → `lh_shared.dim_customer`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`service_level_performance`

### Tables
- fact_orders  
- dim_date  
- dim_customer  
- dim_product  

### Relationships
- fact_orders[DateKey] → dim_date[DateKey] (1:* | single)
- fact_orders[CustomerKey] → dim_customer[CustomerKey] (1:* | single)
- fact_orders[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Customer: Region → Country → Channel → Customer
- Product: Category → Subcategory → SKU
- Date: Year → Quarter → Month → Date

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name         | kpi_id                        | Type        | Folder          | Format   |
|----------------------|--------------------------------|-------------|-----------------|----------|
| Service Level %      | service.level.pct             | KPI         | 01_Service      | 0.0 %    |
| Stockout Rate %      | service.stockout.pct          | KPI         | 01_Service      | 0.0 %    |
| OTIF %               | supply.otif.pct               | KPI         | 02_Reliability  | 0.0 %    |
| Order Accuracy %     | service.order_accuracy.pct    | KPI         | 03_Accuracy     | 0.0 %    |
| Penalties Amount     | service.penalty.amount        | KPI         | 04_Cost         | €#,0.00  |
| Credit Amount        | service.credit.amount         | Supporting  | 04_Cost         | €#,0.00  |

---

## 4. Measures (DAX)

```DAX
Service Level % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[On Time Flag] && fact_orders[In Full Flag], 1, 0 ) ),
        COUNTROWS ( fact_orders )
    )
```

```DAX
Stockout Rate % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[Stockout Flag], fact_orders[Ordered Qty], 0 ) ),
        SUM ( fact_orders[Ordered Qty] )
    )
```

```DAX
OTIF % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[On Time Flag] && fact_orders[In Full Flag], 1, 0 ) ),
        COUNTROWS ( fact_orders )
    )
```

```DAX
Order Accuracy % =
    DIVIDE (
        SUMX ( fact_orders, IF ( fact_orders[Order Accuracy Flag], 1, 0 ) ),
        COUNTROWS ( fact_orders )
    )
```

```DAX
Penalties Amount = SUM ( fact_orders[Penalty Amount] )
```

```DAX
Credit Amount = SUM ( fact_orders[Credit Amount] )
```

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Percentages   | 0.0 %    | None          | Service/Reliability |
| Amounts       | €#,0.00  | Sum           | Cost           |
| Quantities    | #,0      | Sum           | Volume         |

---

## 6. Visual Requirements (Technical)

- KPI cards: Service Level, Stockout %, OTIF %, Order Accuracy %, Penalties.
- Bar: Service by region/channel/customer.
- Line: Service and OTIF trend.
- Pareto: Penalties/credits by cause.
- Matrix: Region → Channel → Customer with KPIs; export enabled.

---

## 7. RLS / OLS

- Region/country/channel-based RLS on customers.  
- Optional OLS to hide penalty/credit amounts for external stakeholders.

---

## 8. Performance & Refresh

- Storage: Import; incremental by month (24–36 months).  
- Pre-aggregate older order history if very large; keep 12–18 months detail.  
- Avoid calculated columns; precompute flags upstream.

---

## 9. QA & Validation

| Check Type              | Object                 | Rule                                   | Tolerance |
|-------------------------|------------------------|----------------------------------------|-----------|
| Referential Integrity   | fact → dims            | ≥ 99.9 % matched keys                  | 0.1 %     |
| OTIF/Service Consistency| On Time & In Full flags| OTIF aligns with service definition    | ±1.0 pp   |
| Stockout Capture        | Stockout flag          | Correctly populated                    | ±1.0 pp   |
| Penalties/Credits       | Amount fields          | Match finance records                  | ±0.5 %    |
