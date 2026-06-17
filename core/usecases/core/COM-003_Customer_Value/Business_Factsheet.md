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
**Out of Scope:** Promotion ROI deep dives (COM-004); acquisition funnel specifics (planned: CST-010); win-loss pipeline (planned: COM-010).

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
| crm.active_customers.count | Influencing |
| crm.nps.index | Influencing |
| crm.complaint.count | Influencing |
| crm.revenue_at_risk.amount | Supporting |
| sales.net_sales.amount | Supporting |
| cost.cogs.amount | Supporting |

**Action Codes:** C-C3.1, C-C3.2

**CLV Definition:** `crm.clv.amount` represents 12-month forward gross margin per customer, discounted at the company's cost of capital. It combines predicted retention probability, expected purchase volume, and net margin per unit — not lifetime revenue alone. This forward-looking definition allows CLV to be used as both a retention-priority signal and a margin-guardrail input.

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

**C-C3.1 — Customer Retention Intervention**
Fires when customer retention deteriorates persistently below target for two or more consecutive months while revenue at risk is materially increasing, signalling that the customer base is losing material accounts without a coordinated response. Owned by the Commercial Controlling Lead. Identifies segments or customers with sustained retention deterioration, prioritises the book of business by revenue at risk and CLV, assigns targeted recovery actions to account and CRM owners, and reviews retention and CLV recovery monthly. Expected to improve retention by 1–4 pp within 1–3 months. Not triggered for new customers in their first 90 days of onboarding, customers under active contractual lock-in, or segments with an approved strategic exit decision.

**C-C3.2 — Complaint & Advocacy Recovery**
Fires when NPS falls persistently below threshold or complaint volume rises for two or more consecutive months, indicating that an unresolved service or product issue is eroding customer advocacy before it converts into visible churn. Owned by the Commercial Controlling Lead. Identifies segments and products with falling advocacy and rising complaints, maps the complaint pattern to channel, product, and account ownership, executes recovery actions closing the highest-value issue clusters first, and reviews complaint volume, NPS, and retention monthly. Expected to recover NPS by 5–15 index points within 1–3 months. Not triggered if complaints are already covered by an open major-incident workflow, if a spike is caused by a known one-off product recall with separate governance, or if survey coverage in the segment is below the agreed minimum sample size.

> Full machine-readable trigger conditions, thresholds, and routing in `UseCase_Bracket.yaml` (SSOT).


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Customer Lifetime Value Amount  
- Customer Retention %  
- Churned Customers Count  
- Revenue at Risk Amount  
- Active Customers Count  
- NPS Index  
- Customer Complaints Count  

_Filter Interaction: Customer Segment slicer cascades to all CLV and churn visuals. Region slicer is independent and applies to the 30-second distribution chart only._

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

- Top-N customers and segments by revenue at risk, declining CLV, and retention deterioration over the last 3 periods.
- Cohort trend tables linking active base, churned customers, and retention to re-engagement opportunities rather than only historical churn reporting.
- Complaint and advocacy root-cause matrix by region, channel, product category, and customer segment, combining complaint volume with NPS deterioration.
- Margin guardrail view showing whether low-value or low-margin segments should be protected, repriced, or deprioritized before retention spend is committed.

---

## 6. Data Requirements Summary

- Required facts: fact_customer_events, fact_customer_value, fact_experience, fact_nps, and fact_sales for revenue and margin context.
- Required dimensions: dim_date, dim_org, dim_customer, dim_product, and security_user_org.
- Required grain: customer_month for retention, churn, CLV, and at-risk prioritization, with invoice-line sales detail available for margin guardrails.
- Required time range: 24 months history to distinguish structural erosion from temporary customer noise.
- Required slicers: Date, Region/Channel, Customer Segment, Product Category.
- **Data latency SLA:** Customer activity and CLV data refreshed monthly within 3 business days of period close; churn flags updated daily; any CLV data >5 business days stale triggers data quality alert before monthly review.


### Evidence grain

customer_month grain is provided by domain contract facts fact_customer_value and fact_customer_events (commercial_sales.yaml). Revenue components can be derived from fact_sales (grain: invoice_line) via customer-month aggregation if needed.

---

## 7. Dependencies, Assumptions & Constraints

- Churn/retention definitions must be consistent (active vs inactive flags).
- CLV methodology agreed (horizon, discount rate, margin basis).
- Customer hierarchy/segment stable; new customers excluded from early churn logic.
- OneLake canonical dims (dim_date, dim_org, dim_product, security_user_org) used.

### 7.4 Data Protection & Privacy (DSGVO / GDPR)

This use case processes customer-level personal data and is subject to DSGVO (GDPR) obligations. The following controls are mandatory before go-live:

**Legal basis:** Analytics processing relies on legitimate interest (Art. 6(1)(f) DSGVO) for internal CRM segmentation. Customer-level CLV and churn scoring does not constitute automated decision-making with legal effects (Art. 22 DSGVO) provided the score is used only to prioritise human-initiated outreach — not to refuse service or assign pricing automatically. Legal basis review required if scope changes.

**Data minimisation:** Only the minimum customer attributes required for CLV and RFM scoring are retained in the analytical layer. Name, address, and contact fields are not included in the semantic model. The customer identifier is a pseudonymous internal ID; re-identification requires a separate key held by the Data Protection Officer.

**Retention:** Customer scoring data is retained for a maximum of 36 months in the analytical environment. Source transaction data follows the applicable retention schedule in the data contract. Purge processes are automated and documented in the data retention register.

**Data subject rights:** Customers exercising right of erasure (Art. 17 DSGVO) or right of access (Art. 15 DSGVO) must be removed or surfaced from all scoring tables within 30 days. The DPO owns the erasure workflow; the Data Engineering Lead is responsible for execution. A documented process for fulfilling these requests in the analytical layer is required before go-live.

**Access restriction:** Customer-level score data is classified as Confidential. Access is restricted to named roles (Commercial Controlling, CRM Analytics, Senior Sales Management) and enforced via Row-Level Security in the semantic model. Bulk data export is blocked at report level; any extract requires DPO co-approval and is logged.

**DSGVO owner:** Data Protection Officer. Review cycle: annual DPIA review; interim review required if processing scope changes.

---

## 8. Success Criteria

- **Impact:** Portfolio CLV stable or growing ≥5% year-over-year in top-20% customer segment; churn rate in high-CLV segment below 10% measured monthly.
- **Adoption:** Dashboard used in monthly Customer Value Review (Commercial Controlling Lead + Sales Director); ≥80% of at-risk customer flags result in documented C-C3.1 or C-C3.2 action within 10 business days.
- **Quality:** CLV calculation reconciles within ±5% of Finance-reported customer margin monthly; churn flag accuracy validated against CRM actuals quarterly with <2% misclassification rate.
- **Decision Frequency:** Monthly (Customer Value Review); quarterly CLV cohort analysis; Action Code closures tracked by Commercial Controlling within 45 days.

---

## 9. Risks & Wrong Interpretations (Short)

- **Risk:** CLV model uses trailing 24-month actuals — a recent churn spike is underweighted, leading to false confidence in portfolio CLV.
  **Owner:** Commercial Controlling Lead.
  **Detection:** CLV growth >5% in same month as churn count increase >20%.
  **Mitigation:** Add 3-month leading churn indicator alongside CLV in dashboard; alert when churn trend diverges from CLV trend.
  **Escalation:** If divergence persists 2 months, Analytics Lead reviews CLV model weighting with Finance.

- **Risk:** Customer segment labels change in CRM without notification, causing segment-level CLV comparisons to be distorted.
  **Owner:** Sales Ops BI Lead.
  **Detection:** Segment distribution shift >10pp month-over-month without business explanation.
  **Mitigation:** CRM segment taxonomy changes require Commercial Controlling sign-off before system update.
  **Escalation:** If unauthorized segment change detected, Sales Ops BI Lead freezes segment dimension until cause is confirmed.

- **Risk:** High-CLV customers with negative gross margin are retained without repricing, creating a portfolio CLV illusion.
  **Owner:** Pricing Lead.
  **Detection:** Customers in top-20% CLV with GM% below 10% for 3+ consecutive months.
  **Mitigation:** Monthly negative-margin audit for high-CLV accounts; repricing decision documented in Action Code log.
  **Escalation:** If negative-margin account not actioned within 60 days, Commercial Director reviews retention vs. repricing trade-off.

---






## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: CLV Decline in High-Value Segment

**Situation:** Average CLV has dropped 12% YoY in the top-20% customer segment. Retention rate is stable, but revenue per customer is declining. NPS is trending down in the same cohort.

**Decision question:** Is the revenue decline driven by reduced purchase frequency, lower basket size, or competitive switching?

**Who decides:** CRM Lead + Commercial Controlling.

**Consequence of inaction:** Accelerating value erosion in the most profitable segment; 1pp CLV drop in top segment equals ~€3M annual impact.

**Action Code triggered:** C-C3.1 (Customer Retention Intervention) — activates cohort-level CLV decomposition, at-risk prioritization, and targeted re-engagement planning.

### Scenario B: Rising Complaint Rate Despite Stable NPS

**Situation:** Complaint count has increased 25% in Q2 while NPS remains flat. Revenue at risk is climbing as complaints concentrate in a single product category.

**Decision question:** Is NPS masking a growing service gap, or are complaints isolated to a fixable product issue?

**Who decides:** CRM Lead + Service Manager.

**Consequence of inaction:** Unresolved complaints erode trust; revenue at risk compounds as dissatisfied customers churn silently.

**Action Code triggered:** C-C3.2 (Complaint & Advocacy Recovery) — activates root-cause analysis by product, channel, and customer segment with advocacy recovery follow-up.

### Scenario C: High-CLV Customer with Persistently Negative Gross Margin

**Situation:** A Key Account customer ranks in the top 5% by CLV (€420K 12-month forward GM). However, detailed margin analysis shows that the account is currently generating negative GM% of −3% due to a combination of deep contractual discounts, high logistics cost-to-serve, and low-margin product mix. Retention rate for this customer is 100% — they are not at churn risk.

**Decision question:** Should C-C3.1 be triggered to protect this account, or should a repricing conversation replace the retention intervention?

**Who decides:** CCO + Commercial Controlling Lead + Account Manager.

**When NOT to act:** If the account's negative margin is documented within an approved strategic account plan (e.g., anchor customer generating referrals, locking out a competitor, or supporting a market-entry objective), no corrective action should fire. CLV as a forward-looking metric will reflect recovery once the strategic rationale matures. The margin-guardrail trigger in C-C3.1 (`margin.gm.pct` as guardrail KPI) is specifically designed to block retention spend on structurally loss-making accounts — but that gating logic does not override an explicitly approved strategic exception. Verify the strategic account designation before launching any intervention.

**Action Code triggered:** None if within approved strategic account plan. If no strategic designation exists, initiate a repricing and cost-to-serve review with the account before triggering C-C3.1.

---
