# Grain Compatibility Reference

Quick reference for analysts joining fact tables at different grains.

## Common Fact Table Grains

| Grain | One row per | Example fact tables |
|-------|-------------|---------------------|
| `invoice_line` | Invoice line item | fact_sales (commercial) |
| `location_sku_month` | Location + product + month | fact_inventory, fact_cogs |
| `location_sku_day` | Location + product + day | fact_stockout, fact_replenishment |
| `sku_location_month` | Product + location + month | fact_forecast |
| `sku_month` | Product + month | fact_sales (SCM view) |
| `customer_month` | Customer + month | fact_crm, fact_nps |
| `order` | Order / shipment | fact_fulfillment |
| `purchase_order_line` | PO line item | fact_procurement |
| `shipment_line` | Shipment line | fact_logistics |
| `warehouse_day` | Warehouse + day | fact_warehouse |
| `month_org` | Month + org unit | fact_hr, fact_it, fact_survey, fact_gl |
| `day` | Calendar day | fact_web_traffic |
| `risk_item_period` | Risk item + period | fact_risk_register |
| `control_period` | Control + period | fact_control_effectiveness |
| `incident` | Single incident | fact_risk_incidents |

## Rules for Safe Joins

### Same grain -- direct join
Facts that share the same grain and the same dimension keys can be joined directly.

```
fact_inventory (location_sku_month)
  JOIN fact_cogs (location_sku_month)
    ON DateKey, OrgKey, ProductKey          -- safe: identical grain
```

### Finer grain joins to coarser grain -- aggregate first
When joining a finer-grain fact to a coarser-grain fact, always aggregate the finer table up to the coarser grain **before** joining.

```
-- CORRECT: aggregate daily stockouts to monthly before joining inventory
WITH stockout_monthly AS (
    SELECT OrgKey, ProductKey, MonthKey, SUM(Lost_Demand_Units) AS Lost_Demand
    FROM fact_stockout
    GROUP BY OrgKey, ProductKey, MonthKey
)
SELECT ...
FROM fact_inventory i
JOIN stockout_monthly s ON i.OrgKey = s.OrgKey
    AND i.ProductKey = s.ProductKey AND i.DateKey = s.MonthKey
```

### Coarser grain joins to finer grain -- aggregate the fine side
Never broadcast a coarser-grain row across finer-grain rows without aggregation. If you need monthly plan numbers alongside daily actuals, keep them in separate query branches and combine at reporting grain.

## Required Aggregation Matrix

| Source grain | Target grain | Aggregation needed |
|--------------|-------------|-------------------|
| `invoice_line` | `customer_month` | SUM by customer + month |
| `location_sku_day` | `location_sku_month` | SUM by location + product + month |
| `order` | `sku_month` | SUM by product + month |
| `day` | `month_org` | SUM by org + month |
| `purchase_order_line` | `sku_month` | SUM by product + month |

## Common Pitfalls

1. **Fan-out from grain mismatch.** Joining `invoice_line` (many rows per customer-month) directly to `customer_month` (one row per customer-month) inflates the coarser-grain measures. Always aggregate the finer side first.

2. **Plan vs. actual at different grains.** Forecast facts (`sku_location_month`) joined to daily stockout facts (`location_sku_day`) will duplicate forecast numbers once per day. Aggregate actuals to monthly before comparing.

3. **Nullable foreign keys.** Some facts have nullable dimension keys (e.g., `fact_fulfillment.LaneKey`). A standard inner join silently drops those rows. Use LEFT JOIN when the nullable key is on the fact side.

4. **Semi-additive measures.** Snapshot measures like `Average Inventory Amount` and `Headcount` use AVG (not SUM) across time. Summing a monthly inventory snapshot across months double-counts stock.

5. **Multiple facts on one report page.** When a report visual pulls from two fact tables at different grains through shared dimensions, the BI engine may produce a cross-join. Use explicit measures scoped to one fact table or create a pre-aggregated intermediate table.
