# FIN-001 – Cash & Liquidity Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** FIN-001
- **Domain:** Finance
- **Owner (Business):** CFO / Treasury Lead
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** data_contracts/domains/finance.yaml
- **Related Semantic Model:** semantic_models/domains/finance/model_definition.yaml

---

## 1. Summary
**Purpose:** Safeguard liquidity by steering cash position, OCF, and CCC with clear drivers.  
**Business Value:** Fewer liquidity surprises, faster cash rotation, targeted WC actions, covenant protection.  
**Out of Scope:** Bank relationship management; long-term funding strategy.

---

## 2. Core Questions
- What is the current and expected cash position vs Plan/LY?
- How are OCF, CapEx, and financing flows trending vs Plan?
- Which BUs/regions lengthen CCC (DSO/DIO/DPO)?
- Which customers/suppliers need action to improve cash?
- Which receivables/payables are overdue and risky?

**Example Queries:**  
- “Which top-20 customers increased DSO by >3 days last quarter?”  
- “Which suppliers are below DPO policy and tie up working capital?”  

---

## 3. KPI Set (Business View)

| KPI Name              | KPI ID (mandatory)           | Purpose                       | Definition (short)                     | Unit / Format | Target / Threshold      | Interpretation                |
|-----------------------|------------------------------|-------------------------------|----------------------------------------|---------------|-------------------------|--------------------------------|
| Cash Balance          | fin.cash.balance             | Liquidity headroom            | Cash & equivalents period end         | €             | >= covenant buffer      | Immediate liquidity           |
| Operating Cash Flow   | fin.cash.ocf                 | Cash generation quality       | OCF from operations                   | €             | ≥ Plan; +YoY            | Core business generates cash  |
| Liquidity vs Plan %   | fin.cash.vs_plan.pct         | Target attainment             | (Cash – Cash Plan) / Cash Plan        | %             | ±5 % band               | Gap to plan                   |
| Cash Conversion Cycle | wc.ccc.days                  | Speed of cash rotation        | DSO + DIO – DPO                       | days          | < Plan; -5 to -10 vs LY | Faster rotation               |
| DSO / DIO / DPO       | wc.dso/dio/dpo.days          | WC levers                     | Standard WC methodology                | days          | DSO↓, DIO↓, DPO↑ policy | Levers for CCC                |

> Do: fill KPI-IDs; define targets/bands.  
> Don’t: add technical fields as KPIs.

---

## 4. Business Logic & Thresholds
- CCC > Plan by >5 days for 2 periods → WC taskforce.
- DSO +3 days with stable sales → collection focus.
- DPO below policy → start terms renegotiation.
- Cash Balance < covenant buffer → immediate mitigation plan.

**Trigger (formal):**
```
WHEN wc.ccc.days > plan + 5
OR   wc.dso.days - wc.dso.plan.days > 3
OR   wc.dpo.days < policy_floor
THEN propose W1/W2/PC2/SP1
```

---

## 5. Action Codes

| Code | Name                    | Trigger (formal, KPIs)                      | Description (business action)                            | Expected KPI Impact          |
|------|-------------------------|---------------------------------------------|----------------------------------------------------------|------------------------------|
| W1   | Working Capital Sprint  | wc.ccc.days > plan +5                       | Accelerate collections, stretch payables, lower stock    | -3 to -7 days CCC            |
| W2   | Terms Renegotiation     | wc.dpo.days < policy_floor                  | Improve supplier payment terms                           | +2–4 days DPO                |
| PC2  | Cost Out                | fin.cash.ocf < plan                         | Reduce discretionary/OpEx                                | Stabilize OCF                |
| SP1  | Forecast Discipline     | fin.cash.vs_plan.pct < -5 % or high var     | Tighten forecast cadence/quality                          | Fewer cash surprises         |

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- Cash Balance | Liquidity vs Plan % | OCF | CCC | DSO/DIO/DPO

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name        | Type  | X-Axis            | Y-Axis/Value                                | Segment      | Filters            |
|--------------------|-------|-------------------|---------------------------------------------|--------------|--------------------|
| Cash & OCF Trend   | Line  | dim_date[Month]   | [Cash Balance], [Operating Cash Flow], Plan | Region/BU    | Last 12–24M        |
| CCC by BU          | Bar   | dim_org[BU]       | [Cash Conversion Cycle]                     | Region       | Top/Bottom N       |
| WC Drivers Bridge  | Waterfall | Drivers (DSO,DIO,DPO,CapEx,Tax,Interest) | Δ Cash vs Plan | n/a          | Period selector    |
| Aging & Overdues   | Matrix| Customer/Supplier | Aging buckets, DSO/DPO                      | Region/BU    | Export enabled     |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → BU → Customer/Supplier; aging buckets; overdue % and exposure.
- Export: Collections/Payables action list with owner/due date.

---

## 7. Dependencies, Assumptions & Constraints
- Data: Timely AR/AP/inventory postings; aging buckets; plan/policy values maintained.
- Assumptions: Plan values frozen after month-end; DPO/DSO policy exists.
- Constraints: Data latency (≤1d), missing classifications → quality note; Owners: Treasury/Controlling.

---

## 8. Success Criteria
- Leading: >80 % usage in monthly treasury/finance reviews; action list maintained.
- Lagging: CCC -5 to -10 days vs LY/Plan; Liquidity vs Plan within ±5 %; DSO↓, DPO↑ per policy.
- Cadence/Quality: Monthly review; no KPI definition conflicts.
