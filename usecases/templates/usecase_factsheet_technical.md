# <UC-ID> – Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

```yaml
dimension:
  - name: dim_example
    columns:
      - {name: ExampleKey, type: int, role: key}
      - {name: ExampleCode, type: text}
      - {name: ExampleName, type: text}
fact:
  - name: fact_example
    grain: example_grain
    columns:
      - {name: DateKey, type: date_key, ref: dim_date}
      - {name: OrgKey, type: int, ref: dim_org}
      - {name: Example Amount, type: currency, agg: sum}
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 05-01
```

## 2. Semantic Model Requirements
- Required fact tables
- Required conformed dimensions
- Relationship structure (cardinality, cross-filter, role-playing dates)
- Sort-by columns
- Hidden technical fields
- Required hierarchies (Org, Product, Time)

## 3. Measures (DAX + Description)
Template for every measure:

```
<Measure Name> =
    <DAX code>

Description:
  Purpose: <What does the measure represent?>
  Definition: <Logic, numerator/denominator, filters>
  Grain & Scope: <Aggregation level, Actual/Plan>
  Unit/Format: <Currency/Qty/%>
  Lineage: <Fact + columns used>
  QA: <Validation rule or expected range>
```

Naming rules:
- Amount = currency (2 decimals)
- Qty / Count = integers
- % = ratios (1–2 decimals)
- Time variants: YTD, MTD, QTD, YoY, MoM

## 4. Defaults & Formatting
- Default summarization per field
- Format strings
- Display Folders
- Data Categories

Example:

| Field | Setting | Notes |
|-------|---------|-------|
| Net Sales Amount | Sum, Currency, 2 decimals | Folder: Sales |
| Gross Margin % | No summarization, Percentage | Folder: Margin |

## 5. Visual Requirements (Technical)

| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| Line Chart | Time trend | Date hierarchy + KPI | 12–24 months |
| Waterfall | Variance drivers | Actual, Plan, Variance | Delta logic required |

Include sort-by logic, drill hierarchies, tooltip fields as needed.

## 6. Performance & Refresh
- Recommended storage mode (Import/DirectLake)
- Incremental Refresh configuration
- Partitioning strategy
- Engine considerations (Memory, RLS, IR windows)
- Known performance risks

## 7. RLS/OLS Requirements
- Dimensions carrying RLS
- Example pseudo filter
- Roles needed & their access scope

## 8. QA & Validation Rules

| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact → dim | ≥ 99.9 % matches | 0.1 % missing |
| Measure Reconciliation | Net Sales Amount | Must match source | ±0.5 % |
