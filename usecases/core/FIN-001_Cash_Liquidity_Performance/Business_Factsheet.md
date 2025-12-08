# FIN-001 – Cash Liquidity Performance – Business Factsheet

## 1. Summary
- **Business Goal:** Monitor and optimize short-term liquidity by tracking cash position, working capital drivers (AR, AP, Inventory), and key liquidity ratios.
- **Target Audience:** CFO, Finance Leadership, Treasury, Controlling, FP&A.
- **Business Priority:** Critical (liquidity = operational stability).
- **Expected Impact:** Improved cash visibility, reduced working capital, earlier detection of liquidity risks, more accurate cash planning.

## 2. Core Questions
- What is our current and projected short-term liquidity position?
- Which components of Working Capital tie up the most cash?
- Are we improving or deteriorating on DSO, DPO, and DIO?
- Which customers drive AR aging problems? Which suppliers create AP bottlenecks?
- How do inventory levels impact liquidity and cash conversion?
- What concrete actions release cash fastest?

## 3. KPI Set (Business View)

| KPI Name                 | Purpose                             | Definition                                                  | Interpretation                            | Decision Relevance          |
|--------------------------|-------------------------------------|--------------------------------------------------------------|--------------------------------------------|-----------------------------|
| Cash Position Amount     | short-term solvency indicator       | Cash & equivalents                                          | lower values = potential risk             | liquidity steering          |
| Working Capital Amount   | cash tied up in operations          | AR + Inventory − AP                                         | high values = capital inefficiency         | operational + financial     |
| DSO                      | collection efficiency               | AR / daily Net Sales                                        | high = long collection cycles             | credit mgmt actions         |
| DPO                      | payment discipline & leverage       | AP / daily COGS                                             | low = paying too early                    | AP optimization             |
| DIO                      | inventory efficiency                | Inventory / daily COGS                                      | high = slow inventory rotation            | stock optimization          |
| Cash Conversion Cycle    | end-to-end capital speed            | DSO + DIO − DPO                                             | long cycles = cash locked in operations   | strategic cash freeing      |

## 4. Business Logic & Thresholds
- DSO above target (industry benchmark ±10 %) = credit control action.
- DPO significantly below target = negotiating disadvantage.
- DIO > industry tolerance = inventory optimization needed.
- CCC positive and increasing = deteriorating liquidity.
- High AR aging (>60 days) = urgent cash-collection focus.

## 5. Action Codes

| Code | Name                  | Description                                 | Trigger                      | Expected Effect                   |
|------|------------------------|---------------------------------------------|-------------------------------|-----------------------------------|
| F1   | AR Collection Action   | targeted overdue collection                  | DSO ↑, aging >60 days         | faster cash inflow                |
| F2   | AP Terms Negotiation   | extend payment terms                          | DPO ↓                          | slow down cash outflow            |
| F3   | Inventory Reduction    | reduce non-moving stock                       | high DIO                       | free tied-up cash                 |
| F4   | Cash Planning Review   | improve accuracy of short-term planning       | volatile cash position         | higher planning reliability       |

## 6. 3–30–300 Page Layout

### **6.1 3-Second Layer**
- Cash Position Amount  
- Working Capital Amount  
- Cash Conversion Cycle  
- DSO / DPO / DIO trend indicators  

### **6.2 30-Second Layer**
- Working Capital Waterfall (AR → Inventory → AP)
- Aging curves for AR and AP
- Inventory rotation by category/warehouse
- Trend lines: CCC, DSO, DPO, DIO (12–24 months)

### **6.3 300-Second Layer**
- Customer-level AR aging  
- Supplier-level AP aging  
- Inventory detail per product/location  
- Cash sensitivity analysis  
- Exportable finance/treasury worksheets  

## 7. Dependencies & Constraints
- AR, AP, Inventory must come from reliable ERP sources.
- Daily/Monthly AR and AP balances required.
- COGS must be consistent across domains for DPO/DIO.
- Aging buckets must be derived in ETL or model.

## 8. Success Criteria
- Reduction in DSO / DIO / CCC vs baseline.
- Cash released from AR/AP/Inventory.
- Improved accuracy of cash planning.
- ≥80 % adoption in monthly finance reviews.
