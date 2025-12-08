# COM-002 – Technical Factsheet

## 0. Model References
- **Data Contract:**  
  `data_contracts/domains/commercial_sales.yaml`
- **Semantic Model Definition:**  
  `semantic_models/core_action_ready/commercial_sales/model_definition.yaml`
- **KPI Catalog:**  
  `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:**  
  `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:**  
  `usecases/UseCase_Inventory.md` (ID: COM-002)

---

## 1. Data Contract (YAML – COM-002 Scope)

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
      - {name: Channel, type: text}

  - name: dim_product
    columns:
      - {name: ProductKey, type: int, role: key}
      - {name: ProductCode, type: text}
      - {name: ProductName, type: text}
      - {name: Category, type: text}
      - {name: Subcategory, type: text}
      - {name: Brand, type: text}
      - {name: UoM, type: text}

fact:
  - name: fact_margin
    grain: invoice_line
    columns:
      - {name: DateKey, type: int, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: ProductKey, type: int, ref: dim_product}
      - {name: Net Sales Amount, type: currency, agg: sum}
      - {name: Quantity Qty, type: number, agg: sum}
      - {name: List Price Amount, type: currency, agg: sum}
      - {name: Net Price Amount, type: currency, agg: sum}
      - {name: Discount Amount, type: currency, agg: sum}
      - {name: COGS Amount, type: currency, agg: sum}
      - {name: Plan GM Amount, type: currency, agg: sum}
      - {name: Plan GM %, type: number, agg: avg}
      - {name: GM Target %, type: number, agg: avg}

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_margin → `lh_commercial_sales.fact_margin`
- dim_date → `lh_shared.dim_date`
- dim_org → `lh_shared.dim_org`
- dim_product → `lh_shared.dim_product`

---

## 2. Semantic Model Requirements

### Model Name
`commercial_margin_performance`

### Tables
- fact_margin  
- dim_date  
- dim_org  
- dim_product  

### Relationships
- fact_margin[DateKey] → dim_date[DateKey] (1:* | single)
- fact_margin[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_margin[ProductKey] → dim_product[ProductKey] (1:* | single)

### Hierarchies
- Org: Region → Country → Channel → OrgName
- Product: Category → Subcategory → Brand → ProductName
- Date: Year → Quarter → Month → Date

---

## 3. Measure Inventory (KPI + Supporting)

| Measure Name          | kpi_id                        | Type        | Folder              | Format    |
|-----------------------|-------------------------------|-------------|---------------------|-----------|
| Gross Margin %        | margin.gm.pct                 | KPI         | 01_Margin           | 0.0 %     |
| Gross Margin Amount   | margin.gm.amount              | KPI         | 01_Margin           | €#,0.00   |
| Price Realization %   | sales.price.realization_pct   | KPI         | 02_Price            | 0.0 %     |
| Discount %            | sales.discount.pct            | Supporting  | 02_Price            | 0.0 %     |
| Mix Effect Amount     | sales.mix_effect.amount       | KPI         | 03_Mix              | €#,0.00   |
| COGS per Unit         | cost.cogs_per_unit.amount     | KPI         | 04_Cost             | €#,0.000  |
| GM vs Plan %          | margin.gm.vs_plan.pct         | KPI         | 01_Margin           | 0.0 %     |

---

## 4. Measures (DAX)

```DAX
Gross Margin Amount =
    [Net Sales Amount] - [COGS Amount]
```

```DAX
Gross Margin % =
    DIVIDE ( [Gross Margin Amount], [Net Sales Amount] )
```

```DAX
Price Realization % =
    DIVIDE ( [Net Price Amount], [List Price Amount] )
```

```DAX
Discount % =
    1 - [Price Realization %]
```

```DAX
COGS per Unit =
    DIVIDE ( [COGS Amount], [Quantity Qty] )
```

```DAX
GM vs Plan % =
    DIVIDE ( [Gross Margin Amount] - SUM ( fact_margin[Plan GM Amount] ),
             SUM ( fact_margin[Plan GM Amount] ) )
```

```DAX
Mix Effect Amount =
    CALCULATE ( [Gross Margin Amount] ) - [Price Effect Amount] - [Volume Effect Amount]
```

*(Price/Volume/Mix pattern per `framework/templates/measure_templates/pevm_sales_delta.md`.)*

---

## 5. Defaults & Formatting

| Field/Measure | Format   | Summarization | Display Folder |
|---------------|----------|---------------|----------------|
| Amounts       | €#,0.00  | Sum           | Margin/Price   |
| Percentages   | 0.0 %    | None          | KPI folders    |
| Qty           | #,0      | Sum           | Volume         |

---

## 6. RLS / OLS

- **Org-based RLS:** Region/Country/Channel/Org via dim_org.  
- **Optional OLS:** Hide cost fields (COGS, GM) for non-finance roles; expose only price/volume.

Example RLS (region-based):
```DAX
dim_org[Region] IN
    CALCULATETABLE (
        VALUES ( security_user_org[Region] ),
        security_user_org[UserPrincipalName] = USERPRINCIPALNAME ()
    )
```

---

## 7. Performance & Refresh

- Storage: Import; incremental by month (24–36 months).  
- Pre-aggregate very granular invoice data if needed.  
- No calculated columns; hide technical fields.

---

## 8. QA & Validation

| Check Type              | Object               | Rule                                   | Tolerance |
|-------------------------|----------------------|----------------------------------------|-----------|
| Referential Integrity   | fact → dims          | ≥ 99.9 % matched keys                  | 0.1 %     |
| Margin Reconciliation   | GM Amount            | Matches source within tolerance        | ±0.5 %    |
| Plan Reconciliation     | Plan GM vs planning  | Matches planning system                | ±0.5 %    |
| PVM Consistency         | Price+Volume+Mix     | ≈ Δ GM within rounding                 | ±1.0 %    |
