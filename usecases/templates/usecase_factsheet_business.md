---
id: <USE CASE ID>
factsheet_type: business
---

# <USE CASE ID> - <USE CASE NAME>

## Business Factsheet (v1.2)

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

```yaml
required_kpis:

  - id: <domain.topic.metric>
    name: <KPI Name>
    purpose: <short purpose>
    definition_short: <business definition>
    unit: <EUR, %, qty, days, index>
    grain: <day/week/month>
    agg: <sum/avg/lnb>
    target: <value or range>
    interpretation: <how to read>
    lineage: <source table/field list>

  - ...
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- <Description of performance rules>
- <Exceptions / Exclusions>

### 4.2 Formal Action Code Rules (Machine-Readable)

```yaml
triggers:

  - kpi: <domain.topic.metric>
    condition: <operator>
    threshold: <value>
    scope: <dimension/filter>
    exclusion: <optional>
    action_code: <AC-XX>

  - ...
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

- **AC-XX - <Name>**
  - Trigger (formal): From section 4
  - Description: <What happens>
  - Expected KPI Impact: <+%, -%, stabilize>
  - Level (L1/L2/L3): L1
  - Owner: <Team>

- **...**
  - Trigger (formal): ...
  - Description: ...
  - Expected KPI Impact: ...
  - Level (L1/L2/L3): ...
  - Owner: ...

All referenced Action Codes must comply with the Prescriptive Standard
(Trigger, Interpretation, Prescriptive Actions, Expected Impact, Risk).

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- <KPI 1>
- <KPI 2>
- <KPI 3>
- <KPI 4>
- <Optional 5>

### 6.2 30-Second Layer (Main Visuals)

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

### 6.3 Required Slicers (Mandatory)

- <Slicer 1>  
- <Slicer 2>  
- <Max 3 slicers>

### 6.4 300-Second Layer (Diagnostics)

- <Diagnostic view 1>
- <Diagnostic view 2>

---

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- <Business assumptions>
- <Data limitations>
- <Latency rules>
- <Currency conversion assumptions>

---

## 9. Success Criteria

- <Impact KPI>
- <Adoption KPI>
- <Quality KPI>
- <Decision Frequency>

---

## 10. Risks & Wrong Interpretations (Short)

- <Risk 1>
- <Risk 2>
- <Misinterpretation to avoid>

---

