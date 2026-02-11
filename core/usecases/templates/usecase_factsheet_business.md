---
id: <USE CASE ID>
factsheet_type: business
---

# <USE CASE ID> - <USE CASE NAME>

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** <COM-001 / FIN-001 ...>
- **Domain:** <Commercial / Finance / Operations / Supply Chain / XD>
- **Business Owner:** <Role>
- **KPI Owner:** <Role>
- **Decision Owner:** <Role>
- **Reporting Level:** <Strategic / Tactical / Operational>
- **Analytics Stage:** <Descriptive / Diagnostic / Predictive / Prescriptive>
- **Related Data Contract:** <path/to/data_contract>
- **Related Semantic Model:** <path/to/model_definition>

---

## 1. Business Summary

**Purpose:** One clear sentence describing the business objective.  
**Business Value:** 1-2 sentences describing measurable impact (growth, margin,
cost, risk, liquidity, customer value).  
**Out of Scope:** 2-3 bullets.

---

## 2. Core Business Questions

List the key questions the use case must answer.

- <Question 1>  
- <Question 2>  
- <Question 3>  
- ...

**Example Query Patterns (optional):**

- "How did <KPI> vs Plan develop across <dimension> over <period>?"
- "Which entities contribute most to <KPI deviation>?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.
Use case factsheets may reference KPIs but must not redefine KPI meaning, targets, or lineage.

```yaml
required_kpis:

  - id: <domain.topic.metric>
    name: <KPI Name>
    kpi_catalog_id: <Growth | Profitability | Liquidity | CustomerValue | Service | Efficiency | Risk | Governance | ESG | InnovationPeople>

  - ...
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: <AC-XX>
    name: <Action Code Name>
    purpose: <short purpose>
    status: <active | planned>
    owner: <Role>
    trigger_kpis: [<kpi_id_1>, <kpi_id_2>]
    guardrail_kpis: [<kpi_id_1>, <kpi_id_2>]
    outcome_kpis: [<kpi_id_1>, <kpi_id_2>]
    impact_range: <kpi_id: range>
    levels: <L1-L3>
    definition: <core/action_codes/...yaml>

  - ...
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- <KPI 1>
- <KPI 2>
- <KPI 3>
- <KPI 4>
- <Optional 5>

### 5.2 30-Second Layer (Main Visuals)

- **<Trend>**
  - Visual Type: Line
  - X-Axis: Date[Month]
  - Y-Axis: [Net Sales Amount]
  - Segment: Region
  - Default Filter: L12M
  - Notes: mandatory

- **<Ranking>**
  - Visual Type: Bar (horizontal)
  - X-Axis: Org[Channel]
  - Y-Axis: [GM %]
  - Segment: Region
  - Default Filter: none
  - Notes: top/bottom logic

- **...**
  - Visual Type: ...
  - X-Axis: ...
  - Y-Axis: ...
  - Segment: ...
  - Default Filter: ...
  - Notes: ...

### 5.3 Required Slicers (Mandatory)

- <Slicer 1>  
- <Slicer 2>  
- <Max 3 slicers>

### 5.4 300-Second Layer (Diagnostics)

- <Diagnostic view 1>
- <Diagnostic view 2>

---

## 6. Data Requirements Summary

```yaml
required_facts:

  - <fact_table>
required_dimensions:

  - <dim_table>
required_grain: <invoice_line / customer_day / asset_day / store_day>
required_time_range: <e.g., 24 months>
required_slicers: <e.g., Org, Region, Product>
```

---

## 7. Dependencies, Assumptions & Constraints

- <Business assumptions>
- <Data limitations>
- <Latency rules>
- <Currency conversion assumptions>

---

## 8. Success Criteria

- <Impact KPI>
- <Adoption KPI>
- <Quality KPI>
- <Decision Frequency>

---

## 9. Risks & Wrong Interpretations (Short)

- <Risk 1>
- <Risk 2>
- <Misinterpretation to avoid>

---

