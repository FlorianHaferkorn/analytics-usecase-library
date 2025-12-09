# OPS-003 – Quality & Yield (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/operations.yaml`
- **Semantic Model Definition:** `semantic_models/domains/scm/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: OPS-003)

---

## 1. Data Contract (Scope for OPS-003)

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
      - { name: Shift, type: text }

  - name: dim_org
    columns:
      - { name: OrgKey, type: int, role: key }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }
      - { name: Line, type: text }

  - name: dim_product
    columns:
      - { name: ProductKey, type: int, role: key }
      - { name: ProductCode, type: text }
      - { name: ProductName, type: text }
      - { name: Category, type: text }
      - { name: Subcategory, type: text }
      - { name: UoM, type: text }

  - name: dim_defect
    columns:
      - { name: DefectKey, type: int, role: key }
      - { name: DefectCategory, type: text }
      - { name: DefectReason, type: text }
      - { name: SourceType, type: text } # process, equipment, supplier, handling

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }
      - { name: Plant, type: text }
      - { name: Line, type: text }

fact:
  - name: fact_quality
    grain: line_shift_product
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: DefectKey, type: int, ref: dim_defect, nullable: true }
      - { name: GoodUnits, type: number, agg: sum }
      - { name: ReworkUnits, type: number, agg: sum }
      - { name: ScrapUnits, type: number, agg: sum }
      - { name: ScrapCostAmount, type: currency, agg: sum }
      - { name: ReworkCostAmount, type: currency, agg: sum }

  - name: fact_complaints
    grain: complaint
    columns:
      - { name: ComplaintId, type: text, role: key }
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: ProductKey, type: int, ref: dim_product }
      - { name: ComplaintCount, type: int, agg: sum }
      - { name: ShipmentCount, type: int, agg: sum }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_quality → `ops.fact_quality`
- fact_complaints → `ops.fact_complaints`
- dim_date → `shared.dim_date`
- dim_org → `shared.dim_org`
- dim_product → `shared.dim_product`
- dim_defect → `ops.dim_defect`
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `operations_quality_yield`

**Tables:** fact_quality, fact_complaints, dim_date, dim_org, dim_product, dim_defect, security_user_org (RLS only)

**Relationships**
- fact_quality[DateKey] → dim_date[DateKey] (1:* | single)
- fact_quality[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_quality[ProductKey] → dim_product[ProductKey] (1:* | single)
- fact_quality[DefectKey] → dim_defect[DefectKey] (1:* | single, optional)
- fact_complaints[DateKey] → dim_date[DateKey] (1:* | single)
- fact_complaints[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_complaints[ProductKey] → dim_product[ProductKey] (1:* | single)
- security_user_org attribute join to dim_org by Region/Country/Plant/Line (RLS mapping)

**Hierarchies**
- Org: Region > Country > Plant > Line
- Product: Category > Subcategory > ProductName
- Date: Year > Quarter > Month > Date > Shift
- Defect: Category > Reason

**Display Folders**
- 01_Quality: FPY, Scrap %, Rework %, Defect Density
- 02_Cost: Cost of Poor Quality, Scrap/Rework Costs
- 03_Complaints: Complaint Rate %, Complaint Counts

---

## 3. Measure Inventory

| Measure Name           | kpi_id                      | Type       | Folder       | Format  |
|------------------------|-----------------------------|------------|--------------|---------|
| First Pass Yield %     | quality.fpy.pct             | KPI        | 01_Quality   | 0.0 %  |
| Scrap Rate %           | quality.scrap.pct           | KPI        | 01_Quality   | 0.0 %  |
| Rework Rate %          | quality.rework.pct          | KPI        | 01_Quality   | 0.0 %  |
| Cost of Poor Quality   | quality.copq.amount         | KPI        | 02_Cost      | €#,0.00|
| Complaint Rate %       | quality.complaint.pct       | KPI        | 03_Complaints| 0.0 %  |
| Defect Density         | quality.defect_density      | KPI        | 01_Quality   | #,0.0  |
| Scrap Units            | quality.scrap.units         | Supporting | 01_Quality   | #,0    |
| Complaints Count       | quality.complaint.count     | Supporting | 03_Complaints| #,0    |

---

## 4. Measures (DAX)

```DAX
First Pass Yield % =
DIVIDE (
    SUM ( fact_quality[GoodUnits] ),
    SUM ( fact_quality[GoodUnits] ) +
    SUM ( fact_quality[ReworkUnits] ) +
    SUM ( fact_quality[ScrapUnits] )
)
```

```DAX
Scrap Rate % =
DIVIDE (
    SUM ( fact_quality[ScrapUnits] ),
    SUM ( fact_quality[GoodUnits] ) +
    SUM ( fact_quality[ReworkUnits] ) +
    SUM ( fact_quality[ScrapUnits] )
)
```

```DAX
Rework Rate % =
DIVIDE (
    SUM ( fact_quality[ReworkUnits] ),
    SUM ( fact_quality[GoodUnits] ) +
    SUM ( fact_quality[ReworkUnits] ) +
    SUM ( fact_quality[ScrapUnits] )
)
```

```DAX
Cost of Poor Quality =
SUM ( fact_quality[ScrapCostAmount] ) + SUM ( fact_quality[ReworkCostAmount] )
```

```DAX
Complaint Rate % =
DIVIDE (
    SUM ( fact_complaints[ComplaintCount] ),
    SUM ( fact_complaints[ShipmentCount] )
)
```

```DAX
Defect Density =
DIVIDE (
    SUM ( fact_quality[ScrapUnits] ) + SUM ( fact_quality[ReworkUnits] ),
    SUM ( fact_quality[GoodUnits] )
) * 1000
```

```DAX
Scrap Units = SUM ( fact_quality[ScrapUnits] )
```

```DAX
Complaints Count = SUM ( fact_complaints[ComplaintCount] )
```

---

## 5. Defaults & Formatting

| Field/Measure                 | Format  | Summarization | Display Folder  |
|-------------------------------|---------|---------------|-----------------|
| FPY %, Scrap %, Rework %, Complaint Rate % | 0.0 % | None | 01_Quality / 03_Complaints |
| Cost of Poor Quality, ScrapCostAmount, ReworkCostAmount | €#,0.00 | Sum | 02_Cost |
| Defect Density                | #,0.0   | None          | 01_Quality      |
| Units (Good, Scrap, Rework)   | #,0     | Sum           | 01_Quality      |

---

## 6. Visual Requirements (Technical)
- KPI cards: FPY %, Scrap %, Rework %, COPQ, Complaint Rate %, Defect Density.
- Trend line: FPY %, Scrap %, Rework % by dim_date[Month]; Complaint Rate % by Month.
- Pareto bar: Scrap Units by dim_defect[DefectReason] with DefectCategory legend.
- Column: FPY % and Scrap % by dim_org[Line] and dim_date[Shift].
- COPQ bar: by driver (scrap, rework, complaints) and by dim_product[Category].
- Matrix: Region > Plant > Line > Product with FPY %, Scrap %, Rework %, COPQ, Complaint Rate %; export enabled.
- Optional scatter: FPY % vs Volume (GoodUnits) by Line to spot stability issues.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; apply Region/Country/Plant/Line filters on dim_org and propagate to fact tables.
- OLS (optional): hide defect reason text for external users; hide complaint details for restricted roles.

---

## 8. Performance & Refresh
- Storage: Import; incremental by month, retain 36 months.
- Partition by dim_date[Month]; summarise fact_quality older than 18 months to Month x Line x Product.
- Avoid calculated columns for costs; ensure scrap and rework costs provided at source.
- Maintain small target table per line/product for FPY/Scrap thresholds (do not hardcode in DAX).

---

## 9. QA & Validation

| Check Type                | Object                                   | Rule                                          | Tolerance |
|---------------------------|------------------------------------------|-----------------------------------------------|-----------|
| Referential Integrity     | fact_quality/fact_complaints → dimensions| ≥ 99.9 % matched keys                         | 0.1 %     |
| FPY/Scrap/Rework Balance  | Good + Rework + Scrap                    | Total units accounted; difference < 0.1 %     | ±0.1 %    |
| COPQ Reconciliation       | Scrap + Rework cost vs source            | Matches finance/production cost records       | ±0.5 %    |
| Complaint Rate Calculation| Complaints vs Shipments                  | Valid denominator; shipment count > 0         | n/a       |
| Defect Coding Coverage    | fact_quality rows with DefectKey         | Coverage ≥ 95 %                               | 5 % gap   |
