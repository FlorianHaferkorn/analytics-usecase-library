---
id: OPS-001
factsheet_type: business
---

# OPS-001 - Operations Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-001
- **Domain:** Operations
- **Business Owner:** COO / Plant Manager / Ops Excellence Lead
- **KPI Owner:** Operations Controlling / OEE Lead
- **Decision Owner:** Operations Leadership Team
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic
- **Related Data Contract:** core/data_contracts/domains/operations.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Operations.SemanticModel (domain model for OPS-*).

---

## 1. Business Summary

**Purpose:** Improve overall equipment effectiveness and throughput by addressing availability, performance, and quality losses.  
**Business Value:** Higher OEE, more stable throughput, reduced downtime, and better cost efficiency without additional CAPEX.  
**Out of Scope:** Predictive maintenance specifics (OPS-013); logistics/warehouse performance (OPS-011); detailed cost modeling (OPS-008).

---

## 2. Core Business Questions

- What is OEE and its components (availability, performance, quality) by line/plant?
- Where are the largest downtime and speed losses, and what are the top causes?
- How does throughput vary by shift, line, and product mix?
- Which targeted actions will lift OEE fastest with minimal risk?

**Example Query Patterns (optional):**

- "Which lines have availability < target in the last 4 weeks and what are the top 3 downtime reasons?"
- "Where is performance loss >5% vs standard for top products?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- OEE %  
- Availability %  
- Performance %  
- Quality %  
- Downtime %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| OEE vs Target by Line | Column | dim_org[Line] | [OEE %], [Target] | Plant | Current month | Core ranking |
| Downtime by Cause | Bar (horizontal) | fact_ops[Cause] | [Downtime Minutes] | Line/Plant | Last 4 weeks | Pareto |
| Performance Loss vs Standard | Column | dim_org[Line] | [Performance %] | Shift | Last 4 weeks | Speed losses |
| Quality Trend | Line | dim_date[Week] | [Quality %] | Line/Plant | L12W | Stability view |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Category (if applicable)  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_ops (production events/OEE)
required_dimensions:

  - dim_date

  - dim_org (plant/line/shift)

  - dim_product (if needed)

  - security_user_org
required_grain: line_day (or line_shift if available)
required_time_range: 12-24 months history
required_slicers: Date, Plant/Line/Shift, Product (optional)
```

---

## 7. Dependencies, Assumptions & Constraints

- Standard cycle times and planned production time defined; changeovers classified.
- Downtime coded with cause categories; trial runs flagged.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_product optional).
- Data latency =24h; plan vs actual for throughput if used.

---

## 8. Success Criteria

- Impact: OEE uplift toward target; reduced downtime minutes; improved throughput vs plan.  
- Adoption: Used in weekly ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly ops and daily tiered meetings.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime distorts availability.  
- Ignoring product mix/standard rate differences when reading performance %.  
- Quality issues masked if rework/scrap not fully captured.  





