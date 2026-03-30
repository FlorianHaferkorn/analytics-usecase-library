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
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Commercial.SemanticModel (domain model for COM-*).

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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| crm.clv.amount | Strategic |
| crm.lifetime_revenue.amount | Influencing |
| crm.retention.pct | Influencing |
| crm.churned_customers.count | Influencing |
| crm.revenue_at_risk.amount | Influencing |
| crm.active_customers.count | Influencing |
| crm.nps.index | Influencing |
| crm.complaint.count | Influencing |
| cost.cogs.amount | Supporting |
| sales.promo.baseline_sales.amount | Supporting |
| sales.promo.cost.amount | Supporting |
| sales.promo.incremental_gm.amount | Supporting |
| sales.pvm.price_effect.amount | Supporting |
| sales.pvm.volume_effect.amount | Supporting |

**Action Codes:** C-M2.2, C-P4.1, C-S1.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

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


### Evidence grain

customer_month grain is provided by domain contract facts fact_customer_value and fact_customer_events (commercial_sales.yaml). Revenue components can be derived from fact_sales (grain: invoice_line) via customer-month aggregation if needed.

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






## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: CLV Decline in High-Value Segment

**Situation:** Average CLV has dropped 12% YoY in the top-20% customer segment. Retention rate is stable, but revenue per customer is declining. NPS is trending down in the same cohort.

**Decision question:** Is the revenue decline driven by reduced purchase frequency, lower basket size, or competitive switching?

**Who decides:** CRM Lead + Commercial Controlling.

**Consequence of inaction:** Accelerating value erosion in the most profitable segment; 1pp CLV drop in top segment equals ~€3M annual impact.

**Action Code triggered:** C-M2.2 (Customer Value Recovery) — activates cohort-level CLV decomposition and churn risk scoring.

### Scenario B: Rising Complaint Rate Despite Stable NPS

**Situation:** Complaint count has increased 25% in Q2 while NPS remains flat. Revenue at risk is climbing as complaints concentrate in a single product category.

**Decision question:** Is NPS masking a growing service gap, or are complaints isolated to a fixable product issue?

**Who decides:** CRM Lead + Service Manager.

**Consequence of inaction:** Unresolved complaints erode trust; revenue at risk compounds as dissatisfied customers churn silently.

**Action Code triggered:** C-P4.1 (Complaint Resolution) — activates root-cause analysis by product and customer segment.
