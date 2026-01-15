---
id: COM-003
factsheet_type: business
---

# COM-003 - Customer Value  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-003
- **Domain:** Commercial / CustomerValue
- **Business Owner:** CCO / Head of Sales Ops / Marketing Lead
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales & Marketing Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

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

```yaml
required_kpis:

  - id: crm.clv.amount
    name: Customer Lifetime Value Amount
    purpose: Long-term economic value per customer
    definition_short: Present value of expected future contribution margin per customer
    unit: "EUR"
    grain: customer_month
    agg: sum
    target: Grow in priority segments
    interpretation: Higher is better; declining CLV signals retention/upsell action
    lineage: fact_customer_value[CLV Amount]

  - id: crm.lifetime_revenue.amount
    name: Customer Lifetime Revenue Amount
    purpose: Realised revenue across lifecycle
    definition_short: Sum of revenue from first purchase to date
    unit: "EUR"
    grain: customer
    agg: sum
    target: Grow revenue base with margin discipline
    interpretation: Base for concentration and CLV inputs
    lineage: fact_sales[Net Sales Amount], dim_customer[CustomerKey]

  - id: crm.retention.pct
    name: Customer Retention %
    purpose: Retain profitable customers
    definition_short: Retained Customers / Active Customers at period start
    unit: "%"
    grain: month
    agg: avg
    target: Meet segment retention targets
    interpretation: Lower retention drives CLV erosion
    lineage: fact_customer_events[Customer Status]

  - id: crm.churned_customers.count
    name: Churned Customers Count
    purpose: Quantify customers lost in period
    definition_short: Count of customers with churn flag = 1
    unit: count
    grain: month
    agg: sum
    target: Minimise churn volume
    interpretation: Rising churn indicates urgent retention playbooks
    lineage: fact_customer_events[Churn Flag]

  - id: crm.revenue_at_risk.amount
    name: Revenue at Risk Amount
    purpose: Size revenue exposure from churn-risk customers
    definition_short: CLV remaining * Attrition Risk %
    unit: "EUR"
    grain: month
    agg: sum
    target: Reduce exposure vs tolerance
    interpretation: High exposure prioritises retention actions
    lineage: fact_customer_value[CLV Remaining Amount], fact_customer_events[Attrition Risk %]

  - id: crm.active_customers.count
    name: Active Customers Count
    purpose: Base for retention/churn KPIs
    definition_short: Distinct customers with activity > 0 in period
    unit: count
    grain: month
    agg: sum
    target: Maintain stable active base
    interpretation: Denominator for retention/churn; falling base signals broader risk
    lineage: fact_customer_events[Activity Flag]

  - id: crm.nps.index
    name: NPS Score
    purpose: Measure advocacy and experience quality
    definition_short: %Promoters - %Detractors
    unit: score
    grain: month
    agg: avg
    target: Meet CX target
    interpretation: Higher is better; track with complaints and churn
    lineage: fact_nps[NPS Score]

  - id: crm.complaint.count
    name: Customer Complaints Count
    purpose: Volume of customer complaints
    definition_short: Count of complaint events
    unit: count
    grain: month
    agg: sum
    target: Reduce complaints vs baseline
    interpretation: Rising complaints signal service/quality issues affecting churn
    lineage: fact_experience[Complaint ID]
```

---

## 4. Business Logic & Thresholds

- Flag segments with retention below target or churned count rising for 2 consecutive months.
- Prioritise high revenue-at-risk segments for retention playbooks.
- Target top-N customers with declining CLV and rising complaints.
- Price/mix changes applied only where margin guardrails hold (via COM-002/P2).

```yaml
triggers:

  - kpi: crm.retention.pct
    condition: below_target
    threshold: retention_target_pct
    scope: segment_channel
    exclusion: new_customers < 3 months
    action_code: C1

  - kpi: crm.churned_customers.count
    condition: above_target
    threshold: churn_volume_target
    scope: segment_channel
    exclusion: strategic_accounts
    action_code: C1

  - kpi: crm.clv.amount
    condition: below_target
    threshold: clv_target
    scope: priority_segments
    exclusion: none
    action_code: M3

  - kpi: crm.revenue_at_risk.amount
    condition: above_target
    threshold: risk_tolerance_amount
    scope: segment_channel
    exclusion: none
    action_code: C1
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| C1 | Retention Playbook | retention below target or churn above target | Targeted retention offers/CSM outreach | Reduce churn, lift retention | L2 | Sales / CS |
| P2 | Margin Realisation Guardrails | margin guardrails required for offers | Tighten discounting, enforce floors/approvals | Improve margin, stabilise CLV | L2 | Pricing / Sales Ops |
| M3 | Mix Optimisation | CLV below target in priority segments | Shift to higher-margin SKUs/bundles | Improve CLV and margin | L2 | Category Mgmt |
| D1 | Cost Take-Out / COGS Control | Margin erosion due to COGS for key customers | Negotiate terms, switch inputs/logistics | Improve margin amount | L2 | Procurement / Ops |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Customer Lifetime Value Amount  
- Customer Retention %  
- Churned Customers Count  
- Revenue at Risk Amount  
- Active Customers Count  
- NPS Score  
- Customer Complaints Count  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| CLV by Segment/Channel | Column | dim_customer[Segment] | [Customer Lifetime Value Amount] | Channel | Current quarter | Identify low CLV |
| Retention & Churn vs Target | Column | dim_customer[Segment] | [Customer Retention %], target | Channel | L6M | Highlight risk |
| Revenue at Risk | Column | dim_customer[Segment] | [Revenue at Risk Amount] | Region/Channel | Current quarter | Prioritise retention |
| Complaints vs NPS | Scatter | dim_customer[Segment] | [Customer Complaints Count] | NPS as color | Current quarter | CX risk signals |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Customer Segment  
- Product Category (optional)

### 6.4 300-Second Layer (Diagnostics)

- Top-N customers by revenue at risk and declining CLV.
- Cohort trend tables (retention, churned count, active base).
- Complaint root-cause table (category, product, channel) linked to NPS.
- Price/mix and COGS views for margin guardrails (link to COM-002 action P2).

---

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- Churn/retention definitions must be consistent (active vs inactive flags).
- CLV methodology agreed (horizon, discount rate, margin basis).
- Customer hierarchy/segment stable; new customers excluded from early churn logic.
- OneLake canonical dims (dim_date, dim_org, dim_product, security_user_org) used.

---

## 9. Success Criteria

- Impact: CLV uplift in priority segments; churn reduced vs target; margin improvement on low-margin high-revenue accounts.  
- Adoption: Used in monthly account/retention reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across COM-001/002/003; reconciled revenue/margin to source totals.  
- Decision Frequency: Monthly account performance review.

---

## 10. Risks & Wrong Interpretations (Short)

- Misclassifying churn due to timing of inactivity flags.  
- Over-discounting to "save" churn without margin guardrails.  
- Using inconsistent CLV models across segments leading to false comparisons.

---


