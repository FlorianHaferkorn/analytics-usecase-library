# COM-IND-R001 — Basket & Category Cross-Sell Analysis

**Status:** Draft scaffold — not yet build-ready
**Vertical:** Retail & CPG
**Domain:** Commercial
**Prerequisites:** COM-001 (Sales Performance), COM-003 (Customer Value)

---

## Business Problem

Retail category managers need to understand which product categories are frequently bought together, and where cross-sell opportunities are being missed. Without basket-level analysis, promotional investment and in-store placement decisions are based on category-level averages rather than the actual shopping behaviour that drives basket size and margin.

## Strategic KPI

**Average Items per Transaction** — the mean number of SKUs per completed transaction in the reporting period.

## Value Driver Logic

- **Cross-sell rate** (% transactions spanning ≥2 categories) is the primary driver of items-per-transaction
- **Promotion attachment rate** measures how often a promotional item triggers an additional category purchase
- High-frequency customers (RFM) who already cross-buy are the best candidates for upsell

## Key Actions

| Action Code | Description |
|---|---|
| C-M2.1 | Promotional mechanics — bundle pricing to incentivise cross-category purchase |
| C-S1.2 | In-store placement — position high-affinity categories adjacent |

## Scope & Limits

- Requires basket-level transaction data (grain: `basket_item`) with category hierarchy
- Category affinity matrix is computed via association rules (Apriori/FP-Growth) — batch model, not real-time
- Applicable to brick-and-mortar and e-commerce channels; channel split must be available in data
- Not applicable to B2B / wholesale distribution (→ use COM-003 Customer Value instead)
