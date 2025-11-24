# Cash Conversion Cycle (DSO + DIO - DPO) - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize working capital and liquidity by managing receivables, inventory, and payables efficiency - measured through the Cash Conversion Cycle (CCC).
- **Target Audience:** Head of Finance / Treasury
- **Business Priority:** High
- **Expected Impact:** DSO -5-10 days; DIO -3-7 days; DPO +5-10 days; CCC -5-8 days

## 2. Core Questions
- How long does it take to convert operational investments into cash?
- Which levers drive changes in DSO, DIO, and DPO?
- Which customers or suppliers cause high working capital requirements?
- How does inventory policy affect liquidity and service levels?
- What scenarios can shorten the CCC without harming service levels?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| DSO (Days) | Accounts Receivable / Net Sales * Days in Period | days | 0 decimals |
| DIO (Days) | Inventory / COGS * Days in Period | days | 0 decimals |
| DPO (Days) | Accounts Payable / COGS * Days in Period | days | 0 decimals |
| Cash Conversion Cycle (Days) | DSO + DIO - DPO | days | 0 decimals |
| Delta CCC (Days) | CCC variance vs Plan or LY | days | +/- sign |

## 4. Business Logic & Thresholds
- AR/AP balances cannot be negative.
- DSO bounded [0; 180] days, DIO bounded [0; 365] days, DPO bounded [0; 180] days.
- Delta CCC calculated only where Plan CCC > 0.
- Referential integrity >= 99.9 % across Date/Org.
- Manual adjustments documented in audit log; FX differences reconciled within +/- 0.5 %.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate collections via credit control and factoring | W1 | DSO -5-10 days |
| Optimize inventory levels and safety stocks | I1 | DIO -3-7 days |
| Negotiate extended supplier terms | W2 | DPO +5-10 days |
| Improve payment discipline and dunning automation | O2 | DSO -2 days; CCC -2 days |
| Align S&OP and Treasury on working capital targets | SP1 | CCC -5-8 days overall |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for DSO (Days), DIO (Days), DPO (Days), CCC (Days), Delta CCC (Days) with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- Balances are period-end values aligned with Financial Close.
- Net Sales and COGS derive from the same closing version to avoid mismatches.
- AR/AP balances reconciled with GL accounts; inventory snapshots at standard cost.
- Returns excluded from Net Sales and COGS.
- Currency = EUR; FX translation at closing rate.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Liquidity | CCC -5 to -8 days | vs Prior Quarter |
| Working Capital | DSO -5-10 days; DIO -3-7 days | vs Plan |
| Supplier Relations | DPO +5-10 days without penalty | vs Contract Baseline |
