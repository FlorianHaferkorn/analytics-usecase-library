---
id: OPS-003
factsheet_type: business
---

# OPS-003 - Quality & Yield  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-003
- **Domain:** Operations
- **Business Owner:** COO / Head of Quality
- **KPI Owner:** Quality Manager / Ops Controlling
- **Decision Owner:** Operations & Quality Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/operations.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Operations.SemanticModel (domain model for OPS-*).

---

## 1. Business Summary

**Purpose:** Improve first pass yield and reduce scrap/rework by identifying top defect drivers and cost of poor quality.  
**Business Value:** Higher yield, lower scrap/rework cost, fewer customer complaints, more stable throughput and margin.  
**Out of Scope:** Supplier PPV and compliance (OPS-002 scope); predictive maintenance (OPS-013); logistics quality (OPS-011).

---

## 2. Core Business Questions

- What is FPY and scrap/rework performance by line, product, and shift?
- Which defect types and steps drive the most quality losses and COPQ?
- How do complaints correlate with plant/line/product performance?
- Which actions reduce defects fastest with minimal throughput impact?

**Example Query Patterns (optional):**

- "Which lines have FPY below target and scrap > target in the last 4 weeks?"
- "What are the top 5 defect causes by cost for product family X?"

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

- First Pass Yield %  
- Scrap Rate %  
- Rework Rate %  
- COPQ (EUR)  
- Complaint Rate %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| FPY vs Target by Line | Column | dim_org[Line] | [FPY %], [Target] | Plant | Current month | Core ranking |
| Scrap & Rework Trend | Line | dim_date[Week] | [Scrap %], [Rework %] | Line/Plant | L12W | Stability |
| COPQ by Cause/Product | Bar (horizontal) | fact_quality_costs[Cause/Product] | [COPQ] | Line/Plant | Last quarter | Pareto |
| Complaint Rate vs FPY | Scatter | [FPY %] | [Complaint %] | Product Family | Current quarter | Field impact |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Product Family  
- Defect Type / Cause  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_quality (units, good, scrap, rework, defects)

  - fact_quality_costs (COPQ)

  - fact_complaints (field complaints)

  - fact_shipments (for complaint rate)
required_dimensions:

  - dim_date

  - dim_org (plant/line/shift)

  - dim_product

  - security_user_org
required_grain: line_day for quality; complaint_month for complaints
required_time_range: 12-24 months history
required_slicers: Date, Plant/Line/Shift, Product, Defect Type
```

---

## 7. Dependencies, Assumptions & Constraints

- Defect and cause coding available; scrap/rework measured at line/product level.
- Complaint data linked to product and period; shipments available.
- COPQ captures scrap, rework, warranty/complaint costs.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Success Criteria

- Impact: FPY improves to targets; scrap/rework reduced; COPQ reduced; complaint rate lowered.  
- Adoption: Used in weekly quality/ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; reconciled units with production totals.  
- Decision Frequency: Weekly and monthly quality review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misattributing scrap to wrong cause/product due to coding gaps.  
- Understating complaint rate if shipment linkage is weak.  
- Overreacting to short-term FPY dips without considering planned trials.  





