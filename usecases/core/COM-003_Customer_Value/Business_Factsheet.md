# COM-003 – Customer Value (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-003
- **Domain:** Commercial
- **Owner (Business):** CCO / Sales Ops / Marketing Lead
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Summary
**Purpose:** Grow customer lifetime value by focusing on profitable segments and reducing churn.  
**Business Value:** Higher CLV and margin, reduced churn, better allocation of sales/marketing spend.  
**Out of Scope:** Detailed campaign attribution (covered in campaign UC), pricing strategy (COM-002).

---

## 2. Core Questions
- Which customers/segments deliver the highest contribution and CLV?
- Where do we see churn risk or declining engagement?
- Which products/offers lift margin per customer?
- How should we prioritize retention vs acquisition spend?
- Which actions raise CLV fastest?

**Example Queries:**  
- “Which segments have CLV decline with flat revenue?”  
- “Where is churn rising with low GM per customer?”  
- “Which cross-sell offers improve CLV and GM %?”  

---

## 3. KPI Set (Business View)

| KPI Name                  | KPI ID (mandatory)          | Purpose                           | Definition (short)                         | Unit / Format | Target / Threshold     | Interpretation                  |
|---------------------------|-----------------------------|-----------------------------------|--------------------------------------------|---------------|------------------------|---------------------------------|
| Customer Lifetime Value   | crm.clv.amount              | Profitability over lifecycle      | Margin per customer over expected lifetime | €             | ↑ vs plan/LY          | Higher = better ROI             |
| Gross Margin per Customer | margin.customer.amount      | Margin quality by customer        | GM / Active Customers                      | €             | ≥ target band         | Margin health per customer      |
| Retention Rate %          | crm.retention.pct           | Stickiness/loyalty                | Retained / Starting customers              | %             | >92–95 %              | Lower = churn risk              |
| Churn Rate %              | crm.churn.pct               | Loss indicator                    | Lost customers / Starting customers        | %             | <8 % (segment-based)  | High churn = leakage            |
| Revenue per Customer      | sales.customer.revenue.amount | Monetization level              | Net Sales / Active Customers               | €             | ↑ vs plan/LY          | Growth vs LY signals upsell     |

> Do: keep KPI IDs and targets/bands; no technical fields as KPIs.

---

## 4. Business Logic & Thresholds
- Retention Rate <92 % for 2 periods → churn program.
- CLV declining with stable revenue → margin leakage.
- GM per Customer down >5 % → price/discount review.
- High churn + low revenue/customer in a segment → deprioritize spend.

**Trigger (formal):**
```
WHEN crm.retention.pct < 92
OR   margin.customer.amount < target - 5 %
OR   crm.churn.pct > 8
THEN propose C1/P2/M3/D2 as applicable
```

---

## 5. Action Codes

| Code | Name                  | Trigger (formal, KPIs)                  | Description (business action)                   | Expected KPI Impact          |
|------|-----------------------|-----------------------------------------|-------------------------------------------------|------------------------------|
| C1   | Retention Play        | retention.pct < target or churn rising  | Targeted outreach/incentives                    | +2–4 pp retention            |
| P2   | Price/Discount Review | margin.customer.amount ↓                | Align price to value; reduce leakage            | +0.5–1.0 pp GM %             |
| M3   | Mix Shift             | CLV stagnating, mix weak                | Promote higher-margin SKUs to key segments      | +5–10 % CLV                  |
| D2   | Targeted Campaign     | revenue/customer flat                   | Upsell/cross-sell to precise segments           | +3–5 % revenue/customer      |

> Do: use ActionCodes_Portfolio; keep KPI-based triggers.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- CLV | Retention % | Churn % | GM/Customer | Revenue/Customer

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name            | Type  | X-Axis / Category      | Y-Axis / Value                           | Segment / Legend | Filters         |
|------------------------|-------|------------------------|------------------------------------------|------------------|-----------------|
| CLV & Retention Trend  | Line  | dim_date[Month]        | [CLV], [Retention %], [Churn %]          | Segment/Region   | Last 12–24M     |
| Segment Ranking        | Bar   | dim_customer[Segment]  | [CLV], [GM/Customer], [Retention %]      | Region/Channel   | Top/Bottom N    |
| CLV Driver Bridge      | Waterfall | Drivers (Price, Mix, Tenure, Cross-Sell) | Δ CLV vs Plan/LY                     | n/a              | Period selector |
| Detail Matrix          | Matrix| Segment → Customer     | CLV, GM/Customer, Churn flag, basket mix | Segment/Region   | Export enabled  |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Segment → Customer; product mix per segment; churn/retention cohorts.
- Export: customer list for campaign activation with KPIs/flags.

---

## 7. Dependencies, Assumptions & Constraints
- Data: Customer master with segment tags; tenure/lifecycle events; discount/rebate mapping per customer; product mix and margin by customer.
- Assumptions: Retention/churn definitions consistent; CLV calc method agreed (horizon, discount rate).
- Constraints: Missing churn flags or tenure reduce quality; ensure privacy where needed.

---

## 8. Success Criteria
- Leading: >80 % usage in monthly Sales/Marketing/CS reviews; campaign lists consumed.
- Lagging: CLV uplift in priority segments; retention +2–4 pp in at-risk cohorts; GM/Customer up with stable/lower discount rate.
- Cadence/Quality: Monthly review; no KPI definition conflicts.
