# KPI Catalog

This catalog defines the standard KPIs used across the Analytics Use Case Library.  
Each KPI entry includes purpose, definition, grain, unit, lineage, and QA rules.

---

## Example Structure
```
KPI Name: Net Sales Amount
Purpose: Measure total invoiced sales excluding returns and taxes.
Definition: Sum(fact_sales[Net Sales Amount])
Grain & Scope: Invoice line; applicable to Actuals and Plan.
Unit/Format: € (0–2 decimals)
Lineage: fact_sales.Net Sales Amount
QA: Should be positive and reconcile with GL totals.
```

---

## Sales & Revenue

### Net Sales Amount
- **Purpose:** Track total sales value excluding returns.  
- **Definition:** SUM(fact_sales[Net Sales Amount]).  
- **Grain & Scope:** Invoice line; Actuals.  
- **Unit:** € (0–2 decimals).  
- **Lineage:** fact_sales.Net Sales Amount.  
- **QA:** Values reconcile to P&L revenue.

### Δ Net Sales Amount
- **Purpose:** Measure deviation from Plan or LY in € terms.  
- **Definition:** [Net Sales Amount] − [Net Sales Amount Plan or LY].  
- **Unit:** € (0–2 decimals).  
- **QA:** Variance reconciles with Plan version control.

### Δ% Net Sales
- **Purpose:** Percentage deviation from Plan or LY.  
- **Definition:** ([Net Sales Amount] − [Net Sales Amount Plan]) ÷ [Net Sales Amount Plan].  
- **Unit:** %.  
- **QA:** Handle divide-by-zero cases (Plan ≠ 0).

### Price Realization %
- **Purpose:** Measure net price discipline vs list price.  
- **Definition:** [Net Sales Amount] ÷ [List Price Amount].  
- **Unit:** %.  
- **QA:** Must be between 0% and 150%.

---

## Margin & Profitability

### Gross Margin %
- **Purpose:** Measure gross profitability after cost of goods.  
- **Definition:** ([Net Sales Amount] − [COGS Amount]) ÷ [Net Sales Amount].  
- **Unit:** %.  
- **Lineage:** fact_sales.COGS Amount.  
- **QA:** GM % must be within [−100%; 100%].

### Δ% Gross Margin
- **Purpose:** Show percentage change in GM vs Plan/LY.  
- **Definition:** ([Gross Margin %] − [Gross Margin % Plan]) ÷ [Gross Margin % Plan].  
- **Unit:** %.  
- **QA:** Validate Plan exists for period.

---

## Cash & Working Capital

### DSO (Days Sales Outstanding)
- **Purpose:** Measure average collection time for receivables.  
- **Definition:** (Receivables ÷ Net Sales) × Days in Period.  
- **Unit:** Days.  
- **Lineage:** fact_ar_balances.  
- **QA:** Exclude credit balances.

### DPO (Days Payables Outstanding)
- **Purpose:** Measure average payment time to suppliers.  
- **Definition:** (Payables ÷ COGS) × Days in Period.  
- **Unit:** Days.  
- **Lineage:** fact_ap_balances.  
- **QA:** Must reconcile to AP ledger.

### Inventory Days
- **Purpose:** Measure average days of stock coverage.  
- **Definition:** (Inventory Value ÷ Daily COGS).  
- **Unit:** Days.  
- **Lineage:** fact_inventory_snapshot.  
- **QA:** No negative inventory.

---

## Customer & Market

### Retention %
- **Purpose:** Measure share of customers retained from prior period.  
- **Definition:** Retained Customers ÷ Customers (Prior Period).  
- **Unit:** %.  
- **QA:** Must be within 0–100%.

### Churn %
- **Purpose:** Measure share of customers lost.  
- **Definition:** 1 − Retention %.  
- **Unit:** %.  
- **QA:** Derived metric, validated via cohort data.

### CLV (Customer Lifetime Value)
- **Purpose:** Calculate long-term customer value based on GM.  
- **Definition:** Discounted sum of Gross Margin per customer.  
- **Unit:** €.  
- **QA:** Discount factor verified with finance.

---

## Procurement & Cost

### PPV % (Purchase Price Variance %)
- **Purpose:** Measure variance between actual and contract purchase prices.  
- **Definition:** (Actual Price − Contract Price) ÷ Contract Price.  
- **Unit:** %.  
- **Lineage:** fact_procurement_po.  
- **QA:** Exclude one-time items.

### OTIF % (On Time In Full)
- **Purpose:** Supplier delivery reliability.  
- **Definition:** Delivered on time and in full ÷ Total deliveries.  
- **Unit:** %.  
- **QA:** Values between 0–100%.

---

Last updated: 07.10.2025
