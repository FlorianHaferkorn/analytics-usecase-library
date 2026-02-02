---
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
---

# COM-003 - Customer Value  

## Business Factsheet

---
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
---

## 1. Business Summary

**Purpose:** Maximise customer lifetime value by improving retention, reducing churn, and prioritising profitable segments.  
**Business Value:** Higher CLV and margin through targeted retention/upsell actions; reduced revenue leakage from churn; better allocation of sales/marketing spend.  
**Out of Scope:** Promotion ROI deep dives (COM-004); acquisition funnel specifics (CST-010); win-loss pipeline (COM-010).

---
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: crm.clv.amount
    kpi_catalog_id: CustomerValue
    name: Customer Lifetime Value Amount
    purpose: Long-term economic value per customer
    agg: sum

  - id: crm.lifetime_revenue.amount
    name: Customer Lifetime Revenue Amount
    purpose: Realised revenue across lifecycle
    agg: sum

  - id: crm.retention.pct
    name: Customer Retention %
    purpose: Retain profitable customers
    agg: avg

  - id: crm.churned_customers.count
    name: Churned Customers Count
    purpose: Quantify customers lost in period
    agg: sum

  - id: crm.revenue_at_risk.amount
    name: Revenue at Risk Amount
    purpose: Size revenue exposure from churn-risk customers
    agg: sum

  - id: crm.active_customers.count
    name: Active Customers Count
    purpose: Base for retention/churn KPIs
    agg: sum

  - id: crm.nps.index
    name: NPS Score
    purpose: Measure advocacy and experience quality
    agg: avg

  - id: crm.complaint.count
    name: Customer Complaints Count
    purpose: Volume of customer complaints
    agg: sum
```

---
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
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
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
---

## 7. Dependencies, Assumptions & Constraints

- Churn/retention definitions must be consistent (active vs inactive flags).
- CLV methodology agreed (horizon, discount rate, margin basis).
- Customer hierarchy/segment stable; new customers excluded from early churn logic.
- OneLake canonical dims (dim_date, dim_org, dim_product, security_user_org) used.

---
id: COM-003
factsheet_type: business
required_kpi_ids:
  - crm.clv.amount
  - crm.lifetime_revenue.amount
  - crm.retention.pct
  - crm.churned_customers.count
  - crm.revenue_at_risk.amount
  - crm.active_customers.count
  - crm.nps.index
  - crm.complaint.count
---

## 9. Risks & Wrong Interpretations (Short)

- Misclassifying churn due to timing of inactivity flags.  
- Over-discounting to "save" churn without margin guardrails.  
- Using inconsistent CLV models across segments leading to false comparisons.

---





