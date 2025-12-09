# COM-001 – Sales Performance vs Plan & LY (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-001
- **Domain:** Commercial
- **Owner (Business):** CCO / Sales Mgmt / Commercial Controlling
- **Reporting Level:** Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Summary
**Purpose:** Measure and explain deviations in Net Sales vs Plan and Last Year; identify main growth drivers (price, volume, mix, channel, region).  
**Business Value:** Early detection of negative trends; targeted actions on price, mix, channel, region; improved revenue growth and margin stability.  
**Out of Scope:** Promotion ROI deep dive (COM-004); margin/price leakage root causes (COM-002).

---

## 2. Core Questions
- Where do Net Sales deviate most vs Plan and vs LY?
- What are the key drivers of Δ Net Sales (price, volume, mix)?
- Which regions/channels/products underperform?
- Which actions (pricing, promo, inventory) close the gaps?

**Example Queries:**  
- “Which channels show the largest NS gap vs Plan in the last 3 months?”  
- “How much of Δ NS is price vs volume vs mix by region?”  

---

## 3. KPI Set (Business View)

| KPI Name               | KPI ID (mandatory)         | Purpose                          | Definition (short)                          | Unit / Format | Target / Threshold   | Interpretation                  |
|------------------------|----------------------------|----------------------------------|---------------------------------------------|---------------|-----------------------|---------------------------------|
| Net Sales Amount       | sales.net.amount           | Commercial performance           | Invoice-level net revenue                  | €             | ≥ Plan; +YoY          | Higher = stronger sales         |
| Revenue Growth %       | growth.sales.yoy.pct       | Growth vs LY                     | (NS – NS LY) / NS LY                       | %             | >0 % trend            | Growth indicator                |
| Sales vs Plan %        | growth.sales.vs_plan.pct   | Target deviation                 | (NS – Plan) / Plan                         | %             | >0 %                  | Gap to plan                     |
| Gross Margin %         | margin.gm.pct              | Margin quality behind sales      | (NS – COGS) / NS                           | %             | ≥ target band         | Margin leakage if low           |
| Price/Volume/Mix Effect| sales.pvm.delta.amount     | Drivers of Δ Net Sales           | Price, volume, mix contribution            | €             | Reconciles Δ NS       | Dominant driver visible         |

> Do: use KPI IDs and targets/bands; no technical fields as KPIs.

---

## 4. Business Logic & Thresholds
- Revenue Growth % <0 % for 2 periods = critical trend.
- Sales vs Plan % < -5 % = management attention.
- GM % below target = pricing/mix issue.
- Price Effect negative & volume stable = price sensitivity; Volume negative & Price positive = demand/channel issue.

**Trigger (formal):**
```
WHEN growth.sales.vs_plan.pct < -5
OR   margin.gm.pct < target_band_low
THEN propose P1/P2/D1/I1 as applicable
```

---

## 5. Action Codes

| Code | Name                  | Trigger (formal, KPIs)          | Description (business action)              | Expected KPI Impact   |
|------|-----------------------|---------------------------------|--------------------------------------------|-----------------------|
| P1   | Price Review          | Negative Price Effect           | Review/adjust list/net prices              | GM stabilisation      |
| P2   | Discount Optimization | High discount / low price realization | Reduce undesired discounts           | Less leakage          |
| D1   | Demand Stimulation    | Negative Volume Effect          | Demand push in weak regions/channels       | Higher volume         |
| I1   | Inventory Rebalancing | Repeated stock-outs in hotspots | Reallocate stock to protect sales          | Lower sales loss      |

> Do: reference ActionCodes_Portfolio; KPI-based triggers.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- Net Sales | Revenue Growth % | Sales vs Plan % | GM % | Price/Volume/Mix Drivers

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name          | Type      | X-Axis / Category  | Y-Axis / Value                             | Segment / Legend | Filters          |
|----------------------|-----------|--------------------|--------------------------------------------|------------------|------------------|
| Sales Trend vs Plan  | Line      | dim_date[Month]    | [Net Sales Amount], Plan, LY               | Region/Channel   | Last 12–24M      |
| PVM Waterfall        | Waterfall | Drivers (Price, Volume, Mix) | Δ Net Sales vs LY/Plan            | n/a              | Period selector  |
| Ranking (Top/Bottom) | Bar       | Region/Channel/Product | [Net Sales Amount], [Sales vs Plan %], [GM %] | Region/Channel | Top/Bottom N     |
| Detail Matrix        | Matrix    | Region → Country → Customer / Category → Product | NS, Growth, Plan %, GM %, PVM | Channel/Region | Export enabled   |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Country → Customer; Category → Subcategory → Product.
- Export: Variance table and action list with owner/due date.

---

## 7. Dependencies, Assumptions & Constraints
- Data: Net Sales, Plan, LY, COGS; price/list, discounts; stable hierarchies (Org/Product).
- Assumptions: Plan frozen post-close; PVM method aligned with template.
- Constraints: If plan/LY missing at required grain, variance quality drops.

---

## 8. Success Criteria
- Leading: >80 % usage in sales/finance reviews; actions tracked.
- Lagging: Sales vs Plan gap closed; Revenue Growth back to positive trend; GM % meets target band.
- Cadence/Quality: Monthly review; no KPI definition conflicts.
