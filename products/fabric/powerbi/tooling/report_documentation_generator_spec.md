# Report Documentation Generator Specification

## Purpose

Generate **standardized, human-readable report documentation** from a Power BI report (PBIP) or semantic model. The documentation serves as:
- **Traceability** — What does this report contain and why?
- **Onboarding** — How do users understand and use the report?
- **Governance** — What KPIs, measures, action codes, and use cases are referenced?
- **Quality assurance** — Definition of Done checklist and validation status

**Input:** PBIP report structure (`.pbir` definition) + semantic model metadata + use case factsheets  
**Output:** Markdown documentation file (e.g. `Report_Documentation_COM-001.md`)

**Reference:** Inspired by [Alex Badiu's PBI Documentation best practices](https://github.com/alexbadiu-insightsinmotion/PBI-Documentation/blob/main/06%20-%20Automated%20Testing%20in%20Power%20BI.md), adapted to the Action-Ready Analytics Framework.

---

## Documentation Structure

### 1. Report Metadata

```markdown
# Report Documentation: <Report Name>

**Use Case:** <Use Case ID> - <Use Case Title>  
**Domain:** <Domain>  
**Report Owner:** <Role/Name>  
**Last Updated:** <Date>  
**Version:** <Version>  
**Theme:** <Theme Name> (from Theme Generator or custom)

**Purpose:**  
<One-sentence purpose from Business Factsheet>

**Target Audience:**  
<Role/level from Business Factsheet: Executive / Management / Operational>

**Usage Rhythm:**  
<Frequency: Daily / Weekly / Monthly / Quarterly>
```

---

### 2. Report Overview

```markdown
## Report Overview

### Business Questions Answered

<From Business Factsheet section 2: Core Business Questions>
- Question 1
- Question 2
- Question 3

### Strategic Alignment

**Strategic KPIs:**  
<From Business Factsheet section 3: Required KPIs>
- KPI 1 (kpi_id)
- KPI 2 (kpi_id)

**Strategy Pattern:**  
<If applicable: Margin-First / Cash-First / Growth-First>

**Decision Type:**  
<From Decision Taxonomy: Steer / Diagnose / Allocate / Forecast / Intervene>
```

---

### 3. Page Documentation

For each page in the report:

```markdown
## Page: <Page Display Name>

**Page Type:** <T1 / T2 / T3 / T4>  
**Layer:** <3 / 30 / 300 or combination>  
**Template:** <Template Name from page_types/>

### Purpose

<One sentence: what decision does this page support?>

### Slots Activated

<From UseCase_Bracket.yaml (ux_layout_rules)>
- Slot 1: <Purpose>
- Slot 2: <Purpose>

### Visuals

| Visual # | Visual Type | Slot | Measures Used | Purpose |
|----------|-------------|------|---------------|---------|
| 1 | KPI Card | KPI Summary | [Net Sales Amount], [Gross Margin %] | Show core KPIs |
| 2 | Line Chart | Trend | [Net Sales Amount], [Plan Sales Amount] | Show trend vs plan |
| 3 | Waterfall | Variance | [PVM Bridge measures] | Explain variance |
| 4 | Horizontal Bar | Ranking | [Net Sales Amount] | Top performers |

**Visual Details:**

#### Visual 1: KPI Cards (KPI Summary Slot)
- **Type:** KPI Card
- **Measures:** 
  - `[Net Sales Amount]` (from `sales.net_sales.amount`)
  - `[Gross Margin %]` (from `margin.gm.pct`)
- **Formatting:** 
  - Show delta vs Plan (if available)
  - Color: Green if above target, Red if below target
- **Filters:** 
  - Time: Last 12 months (default)
  - Organization: All (user-selectable)

#### Visual 2: Trend Chart (Trend Slot)
- **Type:** Line Chart
- **Measures:**
  - `[Net Sales Amount]` (primary)
  - `[Plan Sales Amount]` (target line)
  - `[Last Year Sales Amount]` (comparison)
- **X-Axis:** Date (Month)
- **Formatting:**
  - Show target line (Plan)
  - Show comparison line (LY)
- **Filters:**
  - Time: Last 12 months (default)
  - Organization: All (user-selectable)

[... continue for each visual ...]

### Slicers

| Slicer | Type | Default Value | Purpose |
|--------|------|---------------|---------|
| Time | Relative Date | Last 12 months | Filter time period |
| Organization | Dropdown | All | Filter by org |
| Product Category | Dropdown | All | Filter by product |

### Action Panel / Action Signals

<If T4 or needs_action_panel = true>

**Action Codes Referenced:**
- `C-M2.1` — Price Realization Guardrails
- `C-S1.1` — Price Discipline Enforcement

**Action Panel Behavior:**
- Updates with current filter context
- Shows top recommendation first
- Links to action code definitions in `core/action_codes/`

</If>

---

### 4. Data Sources and Measures

```markdown
## Data Sources and Measures

### Semantic Model

**Model:** <Semantic Model Name>  
**Location:** <PBIP path or workspace reference>

### Measures Used

<Table of all measures referenced in the report>

| Measure Name | KPI ID | Purpose | Source Table |
|--------------|--------|---------|--------------|
| Net Sales Amount | sales.net_sales.amount | Core revenue control | fact_sales |
| Gross Margin % | margin.gm.pct | Profitability quality | Calculated |
| Price Effect Amount | sales.pvm.price_effect.amount | Driver analysis | Calculated |

**Measure Lineage:**
- All measures are defined in the semantic model
- Measures reference KPIs from `core/kpi_catalog/`
- No ad-hoc calculations in visuals

### Data Contracts

**Required Facts:**
- `fact_sales` (grain: invoice_line, aggregated to month)

**Required Dimensions:**
- `dim_date`
- `dim_org`
- `dim_product`

**Data Source:** <Lakehouse / Dataflow / DirectQuery reference>
```

---

### 5. Action Codes and Closed Loop

```markdown
## Action Codes and Closed Loop

**Action Codes Referenced:**  
<From Business Factsheet section 4 or UseCase_Bracket.yaml orchestration.action_code_ids>

| Action Code ID | Name | Purpose | Owner | Trigger KPIs |
|----------------|------|---------|-------|--------------|
| C-M2.1 | Price Realization Guardrails | Stop Discount Leakage | Pricing Lead | sales.price.realization_pct |
| C-S1.1 | Price Discipline Enforcement | Protect Gross Margin | Pricing Manager | margin.gm.pct |

**How Actions Are Triggered:**

<Description of how action codes are surfaced in the report>
- Action Panel (T4 pages)
- Action Teaser (T1–T3 pages)
- Drill-through to action detail pages

**Action Code Definitions:**  
See `core/action_codes/` for full definitions and trigger logic.
```

---

### 6. Testing and Validation

```markdown
## Testing and Validation

### Definition of Done Checklist

<From core/templates/page_templates/governance/Page_DoD.md>

- [x] Page uses exactly one allowed page type (T1, T2, T3, or T4)
- [x] Use case has a UseCase_Bracket.yaml with ux_layout_rules
- [x] Template assignment matches the mapping
- [x] Activated slots match the mapping exactly
- [x] Only whitelisted visuals are used
- [x] Visuals are allowed for the activated slot
- [x] Visuals are allowed for the selected page type
- [x] Maximum of 3 standard slicers used
- [x] Action Panel exists if T4 or needs_action_panel = true
- [x] The page answers the core question of its page type
- [x] Key insight is visible within 30 seconds

### Automated Tests (DAX Query View)

<Optional: Link to DAX Query View test queries or test results>

**Test Categories:**
- Data Quality Tests (e.g. distinct count of countries = 45)
- Referential Integrity Tests (e.g. no orphaned records)
- Calculation Consistency Tests (e.g. Total Sales = Sum of Quarters)
- Business Rule Tests (e.g. Gross Margin always positive)

**Test Results:**  
<Link to test results or "Tests defined in DAX Query View, run before deployment">

**Reference:**  
For testing methodology, see [Alex Badiu's PBI Documentation - Automated Testing](https://github.com/alexbadiu-insightsinmotion/PBI-Documentation/blob/main/06%20-%20Automated%20Testing%20in%20Power%20BI.md)
```

---

### 7. Governance and Maintenance

```markdown
## Governance and Maintenance

### Ownership

**Report Owner:** <Role/Name>  
**Domain Owner:** <From domains.md>  
**KPI Owner:** <From KPI Catalog>  
**Action Code Owner:** <From action_codes/>

### Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-02-05 | 1.0 | Initial report creation | <Name> |

### Review Cadence

**Review Frequency:** <Quarterly / Monthly>  
**Last Review:** <Date>  
**Next Review:** <Date>

### Dependencies

**Depends on:**
- Use Case: `<Use Case ID>` (`core/usecases/core/<ID>/`)
- Semantic Model: `<Model Name>`
- Theme: `<Theme Name>` (`products/fabric/powerbi/themes/`)
- Action Codes: `<List of Action Code IDs>`

**Used by:**
- <List of downstream reports or processes that reference this report>
```

---

### 8. User Guide (Optional but Recommended)

```markdown
## User Guide

### How to Use This Report

**Step 1: Set Time Period**  
Use the Time slicer to select your analysis period (default: Last 12 months).

**Step 2: Filter by Organization**  
Use the Organization slicer to focus on specific regions or business units.

**Step 3: Interpret KPIs**  
- Green KPI cards indicate performance above target
- Red KPI cards indicate performance below target
- Click on a KPI card to see trend details

**Step 4: Understand Variance**  
The Variance Waterfall shows how Price, Volume, and Mix contribute to the gap vs Plan.

**Step 5: Identify Actions**  
<If T4> Review the Action Panel (right side) for recommended actions based on current filters.

### Common Questions

**Q: Why is my number different from another report?**  
A: This report uses governed measures from the semantic model. Other reports may use different definitions. Contact the KPI Owner for clarification.

**Q: How often is data refreshed?**  
A: Data is refreshed <frequency>. Last refresh: <timestamp>.

**Q: Who do I contact for questions?**  
A: Contact the Report Owner: <contact> or Domain Owner: <contact>.
```

---

## Generator Implementation

### Input Sources

1. **PBIP Report Structure** (`.pbir` definition)
   - Page names, visual types, positions
   - Slicer definitions
   - Theme reference

2. **Semantic Model Metadata** (TMDL or model.json)
   - Measure definitions
   - Table definitions
   - Relationships

3. **Use Case Factsheets**
   - Business Factsheet: purpose, key questions, KPIs, action codes
   - UseCase_Bracket.yaml: technical configuration, KPI mappings, data requirements

4. **Framework Artifacts**
   - `UseCase_Bracket.yaml`: UX layout rules (3s/30s/300s intent)
   - `UseCase_Bracket.yaml`: action code references (orchestration.action_code_ids)
   - KPI Catalog: KPI definitions
   - Action Codes: action code definitions

### Output Format

**Markdown file** (`.md`) with:
- Standardized sections as defined above
- Tables for visuals, measures, action codes
- Links to framework artifacts (relative paths)
- Optional: embedded screenshots or diagrams

### Generator Tool Requirements

**Tool/script should:**
1. Parse PBIP report structure (JSON)
2. Extract visual types, measures, slicers
3. Match measures to KPI Catalog (via measure names or metadata)
4. Match pages to use cases (via naming convention or metadata)
5. Generate Markdown following the structure above
6. Validate completeness (warn if measures or action codes are missing from factsheets)

**Output location:**
- Same directory as PBIP report: `<report_name>.Report/Documentation/Report_Documentation.md`
- Or in repo: `showcases/<showcase>/reporting/documentation/<use_case_id>_Report_Documentation.md`

---

## Quality Standards

### Completeness Checklist

Documentation is complete when:

- [ ] Report metadata (name, use case, owner, version) is present
- [ ] All pages are documented with visuals and slots
- [ ] All measures are listed with KPI IDs
- [ ] All action codes are listed with owners and triggers
- [ ] Definition of Done checklist is completed
- [ ] Governance (ownership, review cadence) is documented
- [ ] Links to framework artifacts are valid

### Validation Rules

- Every measure used in visuals must have a KPI ID or be documented as "supporting measure"
- Every action code referenced must exist in `core/action_codes/`
- Every page must match the UX intent in the use case bracket (`UseCase_Bracket.yaml`)
- Every visual must be whitelisted in `Visual_Whitelist.md`

---

## Example Output Structure

See `showcases/aurora_group/reporting/documentation/COM-001_Report_Documentation.md` (to be created) for a complete example following this structure.

---

## References

- **Best Practice Example:** [Alex Badiu - Automated Testing in Power BI](https://github.com/alexbadiu-insightsinmotion/PBI-Documentation/blob/main/06%20-%20Automated%20Testing%20in%20Power%20BI.md)
- **Page Templates:** `core/templates/page_templates/`
- **Use Case Factsheets:** `core/usecases/core/`
- **KPI Catalog:** `core/kpi_catalog/`
- **Action Codes:** `core/action_codes/`
- **Page DoD:** `core/templates/page_templates/governance/Page_DoD.md`
