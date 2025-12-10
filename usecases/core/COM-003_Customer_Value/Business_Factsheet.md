# COM-003 — Customer Value  
## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-003
- **Domain:** Commercial
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

**Example Query Patterns (optional):**
- “Which top 20 customers by revenue have CLV declining vs last year?”
- “Where is churn > target and GM % below threshold by segment/channel?”

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: crm.clv.amount
    name: Customer Lifetime Value
    purpose: Long-term profitability per customer
    definition_short: Present value of expected customer margin over horizon
    unit: €
    grain: customer
    agg: sum
    target: Grow CLV in priority segments
    interpretation: Higher is better; focus on profitable retention
    lineage: fact_customer_value[CLV Amount], dim_customer x dim_org
  - id: margin.customer.amount
    name: Customer Margin Amount
    purpose: Current margin pool per customer
    definition_short: Net Sales – COGS per customer
    unit: €
    grain: customer_month
    agg: sum
    target: Improve vs Plan/LY
    interpretation: Low margin signals price/mix/cost issues
    lineage: fact_customer_value[Margin Amount] or fact_sales aggregated by customer
  - id: crm.retention.pct
    name: Retention Rate %
    purpose: Retain profitable customers
    definition_short: Retained customers / Active prior period
    unit: %
    grain: month
    agg: avg
    target: ≥ target per segment
    interpretation: Low retention drives CLV erosion
    lineage: fact_customer_activity[Active Flag], dim_customer
  - id: crm.churn.pct
    name: Churn Rate %
    purpose: Control loss of customers
    definition_short: Churned customers / Active prior period
    unit: %
    grain: month
    agg: avg
    target: ≤ target per segment
    interpretation: High churn destroys CLV and revenue stability
    lineage: fact_customer_activity[Churn Flag], dim_customer
  - id: sales.customer.revenue.amount
    name: Customer Revenue Amount
    purpose: Revenue base per customer
    definition_short: Net Sales per customer
    unit: €
    grain: customer_month
    agg: sum
    target: Grow with margin discipline
    interpretation: High revenue with low margin needs action
    lineage: fact_sales[Net Sales Amount] grouped by customer
```

---

## 4. Business Logic & Thresholds
Formal rules that define performance and action triggers.

### 4.1 Logic Description
- Flag segments with Churn % above target or Retention % below target for 2 consecutive months.
- Prioritise customers with high revenue but low margin for price/mix actions.
- Focus on top-N customers with declining CLV and margin.

### 4.2 Formal Trigger Rules (Machine-Readable)
```yaml
triggers:
  - kpi: crm.churn.pct
    condition: >
    threshold: segment_target
    scope: segment_channel
    exclusion: new_customers < 3 months
    action_code: C1
  - kpi: margin.customer.amount
    condition: <
    threshold: margin_floor
    scope: top_revenue_customers
    exclusion: strategic_accounts
    action_code: P2
  - kpi: crm.clv.amount
    condition: <
    threshold: clv_target
    scope: priority_segments
    exclusion: none
    action_code: M3
```

---

## 5. Action Codes (Mandatory)
Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| C1 | Retention Playbook | crm.churn.pct > target | Targeted retention offers/CSM outreach | Reduce churn %, lift retention | L2 | Sales / CS |
| P2 | Price Realisation Guardrails | margin.customer.amount below floor | Tighten discounting, enforce floors/approvals | Improve margin amount and GM % | L2 | Pricing / Sales Ops |
| M3 | Mix Optimisation | crm.clv.amount < target in priority segments | Shift to higher-margin SKUs/bundles | Improve CLV and margin | L2 | Category Mgmt |
| D1 | Cost Take-Out / COGS Control | Margin erosion due to COGS for key customers | Negotiate terms, switch inputs/logistics | Improve margin amount | L2 | Procurement / Ops |

---

## 6. 3–30–300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Customer Lifetime Value  
- Retention Rate %  
- Churn Rate %  
- Customer Margin Amount  
- Customer Revenue Amount  

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| CLV by Segment/Channel | Column | dim_customer[Segment] | [CLV Amount] | Channel | Current quarter | Identify low CLV |
| Churn vs Target by Segment | Column | dim_customer[Segment] | [Churn %], [Target] | Channel | L6M | Highlight risk |
| Margin vs Revenue Quadrant | Scatter | [Revenue] | [Margin Amount] | Segment | Top customers | Flag high-revenue low-margin |
| Retention Trend | Line | dim_date[Month] | [Retention %] | Segment | L12M | Trend on retention |

### 6.3 Required Slicers (Mandatory)
- Date (Month/Quarter)  
- Region / Channel  
- Customer Segment  
- Product Category (optional)

---

## 7. Data Requirements Summary
```yaml
required_facts:
  - fact_sales
  - fact_customer_activity
  - fact_customer_value (if separate CLV calc)
required_dimensions:
  - dim_date
  - dim_org
  - dim_customer
  - dim_product
  - security_user_org
required_grain: customer_month (for retention/churn), invoice_line for revenue/margin
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
- Over-discounting to “save” churn without margin guardrails.  
- Using inconsistent CLV models across segments leading to false comparisons.  
