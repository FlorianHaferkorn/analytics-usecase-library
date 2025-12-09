# XD-003 – Executive KPI Overview (Technical Factsheet)

## 0. Model References
- **Data Contract:** `data_contracts/domains/executive.yaml`
- **Semantic Model Definition:** `semantic_models/domains/executive/model_definition.yaml`
- **KPI Catalog:** `framework/kpi_catalog/domain_kpi_catalog.md`
- **Measure Dictionary:** `framework/kpi_catalog/domain_measure_dictionary.md`
- **Use Case Inventory:** `usecases/UseCase_Inventory.md` (ID: XD-003)

---

## 1. Data Contract (Scope for XD-003)

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
      - { name: BusinessUnit, type: text }

  - name: dim_owner
    columns:
      - { name: OwnerKey, type: int, role: key }
      - { name: OwnerName, type: text }
      - { name: Function, type: text }

  - name: dim_kpi
    columns:
      - { name: KPIKey, type: int, role: key }
      - { name: KPIId, type: text }
      - { name: KPIName, type: text }
      - { name: Domain, type: text }
      - { name: Unit, type: text }
      - { name: TargetValue, type: number }
      - { name: TargetType, type: text } # absolute / %

  - name: security_user_org
    columns:
      - { name: UserObjectId, type: string, role: rls }
      - { name: Region, type: text }
      - { name: Country, type: text }

fact:
  - name: fact_kpi_values
    grain: kpi_org_month
    columns:
      - { name: DateKey, type: int, ref: dim_date }
      - { name: OrgKey, type: int, ref: dim_org }
      - { name: KPIKey, type: int, ref: dim_kpi }
      - { name: ActualValue, type: number, agg: avg }
      - { name: PlanValue, type: number, agg: avg }
      - { name: LyValue, type: number, agg: avg }
      - { name: OwnerKey, type: int, ref: dim_owner, nullable: true }
      - { name: ActionCode, type: text, nullable: true }
      - { name: FreshnessDate, type: date }

settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
```

### Source Mapping (Physical Layer)
- fact_kpi_values → `exec.fact_kpi_values`
- dim_* → shared/executive dimensions
- security_user_org → `sec.security_user_org`

---

## 2. Semantic Model Requirements

**Model Name:** `executive_kpi_cockpit`

**Tables:** fact_kpi_values, dim_date, dim_org, dim_kpi, dim_owner, security_user_org (RLS only)

**Relationships**
- fact_kpi_values[DateKey] → dim_date[DateKey] (1:* | single)
- fact_kpi_values[OrgKey] → dim_org[OrgKey] (1:* | single)
- fact_kpi_values[KPIKey] → dim_kpi[KPIKey] (1:* | single)
- fact_kpi_values[OwnerKey] → dim_owner[OwnerKey] (1:* | single, optional)
- security_user_org attribute join to dim_org by Region/Country (RLS mapping)

**Hierarchies**
- Org: Region > Country > BusinessUnit
- Date: Year > Quarter > Month
- KPI: Domain > KPIName

**Display Folders**
- 01_Exec: Revenue, Margin, EBITDA, Cash, OTIF, Turnover, NPS
- 02_Variance: Variance vs Plan, vs LY
- 03_Admin: Freshness, Owner, Action Code

---

## 3. Measure Inventory

| Measure Name              | kpi_id                         | Type       | Folder      | Format  |
|---------------------------|--------------------------------|------------|-------------|---------|
| Revenue Growth %          | sales.revenue.growth_pct       | KPI        | 01_Exec     | 0.0 %  |
| Gross Margin %            | margin.gm.pct                  | KPI        | 01_Exec     | 0.0 %  |
| EBITDA Margin %           | profit.ebitda_margin           | KPI        | 01_Exec     | 0.0 %  |
| Cash Conversion Cycle     | ops.working_capital.ccc.days   | KPI        | 01_Exec     | #,0    |
| OTIF %                    | supply.otif.pct                | KPI        | 01_Exec     | 0.0 %  |
| Employee Turnover %       | hr.turnover.pct                | KPI        | 01_Exec     | 0.0 %  |
| NPS / CSAT                | svc.nps.index                  | KPI        | 01_Exec     | #,0.0  |
| Variance vs Plan          | exec.variance.plan             | Supporting | 02_Variance | 0.0 %  |
| Variance vs LY            | exec.variance.ly               | Supporting | 02_Variance | 0.0 %  |
| Data Freshness (days)     | exec.freshness.days            | Supporting | 03_Admin    | #,0    |

---

## 4. Measures (DAX)

```DAX
Actual Value = AVERAGE ( fact_kpi_values[ActualValue] )
```

```DAX
Plan Value = AVERAGE ( fact_kpi_values[PlanValue] )
```

```DAX
LY Value = AVERAGE ( fact_kpi_values[LyValue] )
```

```DAX
Variance vs Plan = DIVIDE ( [Actual Value] - [Plan Value], [Plan Value] )
```

```DAX
Variance vs LY = DIVIDE ( [Actual Value] - [LY Value], [LY Value] )
```

```DAX
Data Freshness (days) =
VAR MaxDate = MAX ( fact_kpi_values[FreshnessDate] )
RETURN DATEDIFF ( MaxDate, TODAY (), DAY )
```

*Note:* KPI-specific formulas for Revenue Growth %, GM %, etc., should reference the domain models; fact_kpi_values should already supply consistent, validated values.

---

## 5. Defaults & Formatting

| Field/Measure                   | Format  | Summarization | Display Folder |
|---------------------------------|---------|---------------|----------------|
| Percentages (growth, margins, OTIF, Turnover, variances) | 0.0 % | None | 01_Exec / 02_Variance |
| Cash Conversion (days)          | #,0     | None          | 01_Exec        |
| NPS / CSAT                      | #,0.0   | None          | 01_Exec        |
| Freshness (days)                | #,0     | None          | 03_Admin       |

---

## 6. Visual Requirements (Technical)
- KPI cards: Revenue Growth %, GM %, EBITDA Margin %, Cash Conversion Cycle, OTIF %, Turnover %, NPS/CSAT, Data Freshness.
- Variance chart: Variance vs Plan/LY by KPI.
- Trend lines: KPIs by dim_date[Month].
- Waterfall: Cash Conversion drivers (precomputed or pulled from domain model).
- Table: KPI, Actual, Plan, LY, Variance, Owner, Action Code, Freshness; export enabled.
- Optional small multiples: KPI cards by BusinessUnit if allowed.

---

## 7. RLS / OLS
- RLS: security_user_org filtered by UserObjectId; restrict dim_org by Region/Country and propagate to fact_kpi_values.
- OLS (optional): hide owner names for external views; limit visibility of cost KPIs if required.

---

## 8. Performance & Refresh
- Storage: Import; incremental by month; small volume expected.
- Ensure upstream domain models deliver validated KPIs; avoid recalculating complex logic here.
- Maintain freshness checks; display warning if Data Freshness (days) > threshold.

---

## 9. QA & Validation

| Check Type                  | Object                     | Rule                                       | Tolerance |
|-----------------------------|----------------------------|--------------------------------------------|-----------|
| Referential Integrity       | fact_kpi_values → dimensions | ≥ 99.9 % matched keys                    | 0.1 %     |
| Variance Calculations       | Variance vs Plan/LY        | Matches domain KPIs                       | ±0.5 pp   |
| Freshness Check             | FreshnessDate              | Days since refresh within SLA             | threshold |
| KPI Coverage                | KPIKey mapping             | All listed exec KPIs available            | complete  |
