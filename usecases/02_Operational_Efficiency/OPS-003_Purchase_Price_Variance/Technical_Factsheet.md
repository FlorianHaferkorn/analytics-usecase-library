# OPS-003 – Technical Factsheet

## 1. Data Contract (YAML)
```yaml
dimension:
  - name: dim_date
    columns:
      - { name: Date, type: date, role: key }
      - { name: Year, type: int }
      - { name: Month, type: int }
  - name: dim_org
    columns:
      - { name: OrgID, type: string, role: key }
      - { name: Region, type: string }
      - { name: Plant, type: string }
  - name: dim_supplier
    columns:
      - { name: SupplierID, type: string, role: key }
      - { name: SupplierGroup, type: string }
      - { name: CategoryManager, type: string }
  - name: dim_material
    columns:
      - { name: MaterialID, type: string, role: key }
      - { name: MaterialGroup, type: string }
      - { name: Category, type: string }
fact:
  - name: fact_purchase_orders
    grain: po_line_receipt
    columns:
      - { name: PONumber, type: string }
      - { name: POLine, type: int }
      - { name: ReceiptID, type: string, role: key }
      - { name: ReceiptDate, type: date, ref: dim_date }
      - { name: OrgID, type: string, ref: dim_org }
      - { name: SupplierID, type: string, ref: dim_supplier }
      - { name: MaterialID, type: string, ref: dim_material }
      - { name: Actual Unit Price, type: decimal }
      - { name: Contract Unit Price, type: decimal }
      - { name: Quantity, type: decimal }
      - { name: Currency, type: string }
      - { name: Delivery Date, type: date }
  - name: fact_contracts
    grain: contract_material
    columns:
      - { name: ContractID, type: string, role: key }
      - { name: MaterialID, type: string, ref: dim_material }
      - { name: SupplierID, type: string, ref: dim_supplier }
      - { name: ContractEffectiveDate, type: date }
      - { name: ContractPrice, type: decimal }
      - { name: IndexationType, type: string }
settings:
  currency_reporting: EUR
  timezone: Europe/Berlin
```

## 2. Semantic Model Requirements
- **Facts:** `fact_purchase_orders` (primary), `fact_contracts` for reference/lookup.
- **Dimensions:** Date, Org, Supplier, Material (optional Currency, Contract Type).
- **Relationships:** PO fact -> dims (many-to-one single direction). Contract fact links to Supplier & Material with inactive relationship, used via LOOKUPVALUE or bridging table.
- **Role playing:** Date dimension reused for ReceiptDate and ContractEffectiveDate (create inactive relationship for contract).
- **Sort-by:** MonthName sorted by MonthNumber; SupplierGroup sort by custom order.
- **Hidden fields:** Raw unit prices, contract IDs, currency for QC.
- **Hierarchies:** Org (Region > Plant > Company), Supplier (Group > Vendor), Material (Category > MaterialGroup > Material).

## 3. Measures (DAX + Description)

```
Actual Unit Price (LC) =
AVERAGE(fact_purchase_orders[Actual Unit Price LC])
```
(LC = reporting currency; preprocess via FX conversion.)

```
Contract Unit Price (LC) =
AVERAGE(fact_purchase_orders[Contract Unit Price LC])
```

```
PPV % =
VAR _actual = [Actual Unit Price (LC)]
VAR _contract = [Contract Unit Price (LC)]
RETURN DIVIDE(_actual - _contract, _contract)
```
Description: Relative deviation, formatted `0.0 %`, QA clamp [-50 %, +100 %].

```
PPV Amount =
VAR _delta = [Actual Unit Price (LC)] - [Contract Unit Price (LC)]
RETURN _delta * [Quantity]
```
Description: Monetary effect; format `EUR #,0`.

```
Contract Spend =
SUMX(
    fact_purchase_orders,
    fact_purchase_orders[Contract Unit Price LC] * fact_purchase_orders[Quantity]
)
```

```
Total Spend =
SUMX(
    fact_purchase_orders,
    fact_purchase_orders[Actual Unit Price LC] * fact_purchase_orders[Quantity]
)
```

```
Contract Compliance % =
DIVIDE([Contract Spend],[Total Spend])
```

```
Supplier OTIF % =
DIVIDE([OnTimeFull Receipts],[Total Receipts])
```
(Requires OTIF classification flag in PO fact or separate OTIF fact.)

Savings Verified % measure placeholder, depending on savings tracking fact (TODO).

Each measure includes metadata in documentation table (Purpose, Definition, Grain, Unit, Lineage, QA).

## 4. Defaults & Formatting

| Field / Measure | Setting | Notes |
|-----------------|---------|-------|
| Actual/Contract Unit Price LC | Average, Currency `EUR #,0.000` | Hidden in visuals; display folder `01_PP/base`. |
| Quantity | Sum, Decimal `#,0` | Hidden. |
| PPV % | Percentage `0.0 %` | Folder `02_PP/KPI`. |
| PPV Amount | Currency `EUR #,0` | Folder `02_PP/KPI`. |
| Contract Compliance % | Percentage `0.0 %` | Folder `02_PP/KPI`. |
| Supplier OTIF % | Percentage `0.0 %` | Folder `03_Supplier/KPI`. |
| Savings Verified % | Percentage `0.0 %` | Folder `02_PP/KPI`. |

## 5. Visual Requirements (Technical)

| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | PPV %, PPV Amount, Compliance, OTIF, Savings | Measures + Plan/LY. |
| Line Chart | PPV trend | Date hierarchy + PPV %, PPV Amount. |
| Waterfall | PPV Amount variance vs Plan | Measures per dimension (Supplier, Material). |
| Matrix / Heatmap | Supplier × Material PPV | Supplier & Material dims, PPV %, Amount. |
| Scatter | Supplier OTIF % vs PPV % | Supplier fields, measures. |
| Detail table | Export-ready | PO, Supplier, Material, measures, actions. |

## 6. Performance & Refresh
- Storage mode: Import.
- Refresh cadence: daily (nightly PO load + contract master).
- Partitioning: by Month on `fact_purchase_orders`; contract table full load (smaller).
- Performance guards: Pre-calc FX conversion, avoid LOOKUPVALUE per row by staging contract price in ETL.

## 7. RLS/OLS Requirements
- RLS by Org (Region/Plant). Expression: `dim_org[Region] IN USERORG()`.
- Optional Supplier-based restriction for partner portals.
- Roles: `Global_Procurement`, `Region_Procurement`, `Plant_Controller`.

## 8. QA & Validation Rules

| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | PO fact → dims | ≥ 99.9 % matched keys | 0.1 % missing |
| Value Bounds | Actual/Contract price | Must be > 0 | Hard fail |
| PPV % clamp | KPI result | Between -50 % and +100 % | Flag outside range |
| Compliance calc | Spend share | Reconciles to GL spend | ±0.5 % |
| Contract link | PO lines | ContractID not null when contract expected | Alert |
