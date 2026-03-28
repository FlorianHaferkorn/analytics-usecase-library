# COM-EXT-001 — Advanced Customer Segmentation (RFM + CLV)

**Status:** Draft scaffold — not yet build-ready
**Domain:** Commercial
**Prerequisites:** COM-001 (Sales Performance), COM-003 (Customer Value)

---

## Business Problem

Standard sales reporting shows aggregate revenue but masks which customer segments are driving profitable growth, which are at risk of churning, and where retention investment yields the highest return. Without segment-level intelligence, commercial teams treat all customers equally — overspending on low-value segments and under-investing in high-CLV accounts.

## Strategic KPI

**Customer Lifetime Value (CLV)** — the discounted net margin expected from a customer relationship over the forecast horizon. Maximising portfolio CLV is the North Star for commercial segmentation.

## Value Driver Logic

CLV is driven by RFM (Recency, Frequency, Monetary) composite scores:

- **Recency** — days since last purchase; low recency = churn signal
- **Frequency** — number of transactions in period; high frequency = loyalty signal
- **Monetary** — average transaction value; high monetary + high frequency = champion segment

Segments at high churn risk (predicted score > threshold) are escalated to retention action codes.

## Key Actions

| Action Code | Description |
|---|---|
| C-M2.1 | Pricing intervention — protect margin on at-risk champions |
| C-S1.2 | Sales channel activation — re-engage lapsed segments |

## Scope & Limits

- Requires customer-level transaction data (grain: `customer_transaction`)
- RFM scoring computed in semantic model via DAX measures (not real-time)
- CLV is a 12-month forward estimate using trailing 24-month actuals
- Not a real-time recommendation engine — batch scoring refreshed daily

## Out of Scope (→ industry layer)

- Loyalty programme integration (→ Retail COM-IND-R001)
- NPS-linked CLV modelling (→ XD-001 extension)
