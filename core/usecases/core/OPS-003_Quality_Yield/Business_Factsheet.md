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
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Operations.SemanticModel (domain model for OPS-*).

---

## 1. Business Summary

**Purpose:** Improve first pass yield and reduce scrap/rework by identifying top defect drivers and cost of poor quality.  
**Business Value:** Higher yield, lower scrap/rework cost, fewer customer complaints, more stable throughput and margin.  
**Out of Scope:** Supplier PPV and compliance (OPS-002 scope); predictive maintenance (OPS-013); logistics quality (OPS-011).

---

## 2. Core Business Questions

- What is FPY and scrap/rework performance by line, product, and shift?
- How large is the gap between FPY and final yield? (the "hidden factory" — reworked units that pass eventually but failed first time, masking the true first-pass defect rate)
- What is Rolled Throughput Yield across all process steps? (cumulative first-pass yield the per-step FPY hides — e.g. ten steps at 90% FPY give only ~35% RTY)
- Which defect types and steps drive the most quality losses and COPQ?
- How does COPQ split between internal failure (scrap, rework, retest) and external failure (complaints, returns, warranty)? (a rising external-failure share signals escapes reaching customers, not just an internal-yield problem)
- How do complaints correlate with plant/line/product performance?
- Which actions reduce defects fastest with minimal throughput impact?

**Example Query Patterns (optional):**

- "Which lines have FPY below target and scrap > target in the last 4 weeks?"
- "What are the top 5 defect causes by cost for product family X?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| quality.fpy.pct | Strategic |
| quality.scrap.pct | Influencing |
| quality.rework.pct | Influencing |
| quality.copq.amount | Influencing |
| quality.complaint.pct | Influencing |
| quality.defect_density | Influencing |
| ops.planned_output.units | Supporting |
| sales.units | Supporting |
| crm.complaint.count | Supporting |

**Action Codes:** O-Q3.1, O-Q3.2, O-Q3.3, O-Q3.4, O-Q3.5

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

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

- Defect decomposition by line, product family, and defect type with absolute scrap/rework units and relative contribution to the FPY and COPQ gap vs target.
- Quality guardrail table linking FPY drop, scrap rate spike, and complaint rate to the specific line/product clusters that trigger O-Q3.1 (root cause analysis), O-Q3.2 (containment action), or O-Q3.3 (process parameter review).
- Top-N product/line combinations with the highest defect density and COPQ, including the last 4 weekly observations to separate batch-specific anomalies from persistent process drift.

---

## 6. Data Requirements Summary

- Required facts: fact_quality, fact_quality_costs, fact_complaints, and fact_shipments.
- Required dimensions: dim_date, dim_org, dim_product, and security_user_org.
- Required grain: line_day for internal quality signals and complaint-level aggregation to month/product for field quality.
- Required time range: 12-24 months history.
- Required slicers: Date, Plant/Line/Shift, Product/Product Family, Defect Type/Cause.

---

## 7. Dependencies, Assumptions & Constraints

- Defect and cause coding available; scrap/rework measured at line/product level.
- Complaint data linked to product and period; shipments available.
- COPQ captures scrap, rework, warranty/complaint costs.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Success Criteria

- Impact: FPY improves to targets; scrap/rework reduced; COPQ reduced; complaint rate lowered.  
- Benchmark targets: FPY ≥ 95% in most manufacturing, world-class high-volume discrete ≥ 99% (Six Sigma 99.99966%, i.e. 3.4 DPMO reference). Scrap < 0.5% world-class discrete / < 2% acceptable for most processes (ISO 22400-2 / benchmark data). COPQ runs 15–20% of sales when unmanaged (Juran/Crosby/ASQ); world-class quality programmes hold it < 5% of sales.  
- Adoption: Used in weekly quality/ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; reconciled units with production totals.  
- Decision Frequency: Weekly and monthly quality review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misattributing scrap to wrong cause/product due to coding gaps.  
- Understating complaint rate if shipment linkage is weak.  
- Overreacting to short-term FPY dips without considering planned trials.  






## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: FPY Drop After Raw Material Supplier Change

**Situation:** First pass yield dropped from 94% to 87% two weeks after switching to a new material supplier. Scrap rate doubled on the affected product line. Defect density is concentrated in a specific process step.

**Decision question:** Is the yield drop caused by material specification variance, process parameter mismatch, or operator adjustment lag?

**Who decides:** Quality Manager + Process Engineer.

**Consequence of inaction:** Each 1pp FPY drop equals ~€50K/month in scrap and rework costs on this line.

**Action Code triggered:** O-Q3.1 (Yield Recovery) — activates defect Pareto analysis and process parameter correlation.

### Scenario B: Rising Cost of Poor Quality Despite Stable FPY

**Situation:** FPY is holding at 92%, but COPQ has increased 20% due to rising rework costs. Complaint rate from customers is also up 10%.

**Decision question:** Are rework loops hiding quality issues that eventually reach customers? Is FPY being artificially maintained through excessive inspection?

**Who decides:** Quality Manager + Production Manager.

**Consequence of inaction:** COPQ erodes margin; customer complaints damage brand trust and trigger contractual penalties.

**Action Code triggered:** O-Q3.2 (COPQ Reduction) — activates hidden factory analysis and rework loop identification.
