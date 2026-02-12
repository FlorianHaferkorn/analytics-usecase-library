---
id: COM-003
factsheet_type: business
---

# COM-003 - Customer Value  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-003
- **Domain:** Commercial / CustomerValue
- **Business Owner:** CCO / Head of Sales Ops / Marketing Lead
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales & Marketing Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** core/core/core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** core/core/core/semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Maximise customer lifetime value by improving retention, reducing churn, and prioritising profitable segments.  
**Business Value:** Higher CLV and margin through targeted retention/upsell actions; reduced revenue leakage from churn; better allocation of sales/marketing spend.  
**Out of Scope:** Promotion ROI deep dives (COM-004); acquisition funnel specifics (CST-010); win-loss pipeline (COM-010).

---

## 2. Core Business Questions

- Which customers/segments drive the highest and lowest CLV and margin?
- Where is churn rising and what are the leading indicators?
- Which actions (retention, upsell, pricing) drive the best improvement in CLV and GM?
- How concentrated is revenue/margin across the base (top-N analysis)?
- Which products/channels deliver the best CLV uplift opportunities?

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

- Customer Lifetime Value Amount  
- Customer Retention %  
- Churned Customers Count  
- Revenue at Risk Amount  
- Active Customers Count  
- NPS Score  
- Customer Complaints Count  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| CLV by Segment/Channel | Column | dim_customer[Segment] | [Customer Lifetime Value Amount] | Channel | Current quarter | Identify low CLV |
| Retention & Churn vs Target | Column | dim_customer[Segment] | [Customer Retention %], target | Channel | L6M | Highlight risk |
| Revenue at Risk | Column | dim_customer[Segment] | [Revenue at Risk Amount] | Region/Channel | Current quarter | Prioritise retention |
| Complaints vs NPS | Scatter | dim_customer[Segment] | [Customer Complaints Count] | NPS as color | Current quarter | CX risk signals |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Customer Segment  
- Product Category (optional)

### 5.4 300-Second Layer (Diagnostics)

- Top-N customers by revenue at risk and declining CLV.
- Cohort trend tables (retention, churned count, active base).
- Complaint root-cause table (category, product, channel) linked to NPS.
- Price/mix and COGS views for margin guardrails (link to COM-002 action P2).

---

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_sales

  - fact_customer_events

  - fact_customer_value

  - fact_experience

  - fact_nps
required_dimensions:

  - dim_date

  - dim_org

  - dim_customer

  - dim_product

  - security_user_org
required_grain: customer_month (for retention/churn/risk), invoice_line for revenue/margin
required_time_range: 24 months history
required_slicers: Date, Region/Channel, Customer Segment, Product Category
```

---

## 7. Dependencies, Assumptions & Constraints

- Churn/retention definitions must be consistent (active vs inactive flags).
- CLV methodology agreed (horizon, discount rate, margin basis).
- Customer hierarchy/segment stable; new customers excluded from early churn logic.
- OneLake canonical dims (dim_date, dim_org, dim_product, security_user_org) used.

---

## 8. Success Criteria

- Impact: CLV uplift in priority segments; churn reduced vs target; margin improvement on low-margin high-revenue accounts.  
- Adoption: Used in monthly account/retention reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across COM-001/002/003; reconciled revenue/margin to source totals.  
- Decision Frequency: Monthly account performance review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassifying churn due to timing of inactivity flags.  
- Over-discounting to "save" churn without margin guardrails.  
- Using inconsistent CLV models across segments leading to false comparisons.

---





