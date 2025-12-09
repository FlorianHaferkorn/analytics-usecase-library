# SCM-001 – Inventory Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** SCM-001
- **Domain:** Supply Chain
- **Owner (Business):** COO / Head of Supply Chain / Demand Planning Lead
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Optimize inventory while protecting service, reducing working capital and write-offs.  
**Business Value:** Lower DIO and obsolescence, higher turns, fewer stockouts, improved OTIF.  
**Out of Scope:** Long-term network redesign; vendor selection (handled in procurement).

---

## 2. Core Questions
- Where are DIO and Inventory Turnover off target by SKU/location/channel?
- Which SKUs carry high obsolescence or expiry risk?
- How do forecast accuracy and OTIF drive stockouts or excess?
- Which policy levers (safety stock, MOQ, lead time) fix the biggest gaps fastest?

**Example Queries:**
- “Which top 20 SKUs drive 80% of excess inventory value this month?”
- “Which locations have Stockout % >3% with stable demand?”

---

## 3. KPI Set (Business View)

| KPI Name               | KPI ID (mandatory)  | Purpose                      | Definition (short)                               | Unit / Format | Target / Threshold            | Interpretation                  |
|------------------------|---------------------|------------------------------|--------------------------------------------------|---------------|-------------------------------|---------------------------------|
| Days in Inventory      | inv.dio.days        | Inventory efficiency         | 365 / Inventory Turnover                         | days          | ≤ target by segment           | Speed of rotation               |
| Inventory Turnover     | inv.turnover        | Rotation speed               | COGS / Avg Inventory Value                       | turns         | ≥ target                      | Capital productivity            |
| Stockout Rate %        | inv.stockout.pct    | Service risk                 | Stockout lines / total order lines               | %             | ≤ 3% core SKUs                | Service leakage                 |
| OTIF %                 | supply.otif.pct     | Supply reliability           | On-Time In-Full lines / total lines              | %             | ≥ 97%                         | Supplier/logistics performance  |
| Obsolescence Risk %    | inv.obsolete.pct    | Write-off risk               | Obsolete/aging value / total inventory value     | %             | ≤ 8% value                    | Clearance/phase-out need        |
| Forecast Accuracy %    | plan.forecast.accuracy.pct | Demand signal quality | 1 - |Actual - Forecast| / Actual               | %             | ≥ 80–90% by class             | Demand signal health            |

> Use KPI IDs from the catalog; set targets by product class and location criticality.

---

## 4. Business Logic & Thresholds
- DIO > target by >10% for 2 periods → policy review and rebalancing.
- Stockout Rate % > 3% with OTIF < 97% → supply/lead-time escalation.
- Obsolescence Risk % > 8% of inventory value → markdown/phase-out.
- Forecast Accuracy % < 80% on A-items → segmentation and safety stock review.

**Trigger Logic (formal, for automation):**
```
WHEN inv.dio.days > target_dio_segment
OR   inv.stockout.pct > 3
OR   inv.obsolete.pct > 8
OR   plan.forecast.accuracy.pct < 80
THEN propose I1 (rebalance), I2 (policy tuning), PC4 (supplier/logistics fix), D1 (demand signal response)
```

---

## 5. Action Codes

| Code | Name                        | Trigger (formal, KPIs)                           | Description (business action)                      | Expected KPI Impact             |
|------|-----------------------------|--------------------------------------------------|----------------------------------------------------|---------------------------------|
| I1   | Inventory Rebalance         | dio.days > target AND stockout.pct > 0           | Reallocate stock across locations                  | Lower stockouts, lower DIO      |
| I2   | Policy Tuning               | dio.days > target OR stockout.pct > 3            | Adjust safety stock, MOQ, lead time, reorder point | Better service, lower WC        |
| PC4  | Supplier/Logistics Fix      | supply.otif.pct < 97 OR lead time variance high  | Enforce SLAs, stabilize lead time                  | Higher OTIF, fewer stockouts    |
| D1   | Demand Signal Response      | forecast accuracy < 80 for A-items               | Improve signal (POS/market), adjust forecast       | Lower excess/stockouts          |

> Use ActionCodes_Portfolio as the single source; triggers must reference KPIs.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- DIO, Inventory Turnover, Stockout %, OTIF %, Obsolescence Risk %, Forecast Accuracy %.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name              | Type    | X-Axis / Category           | Y-Axis / Value                                   | Segment / Legend | Filters / Defaults |
|--------------------------|---------|-----------------------------|--------------------------------------------------|------------------|--------------------|
| DIO & Turnover by Node   | Column  | dim_org[Location]           | [Days in Inventory], [Inventory Turnover]        | Region/Country   | Current / last month |
| Stockout & OTIF Trend    | Line    | dim_date[Month]             | [Stockout %], [OTIF %]                           | Channel          | Last 12–18 months  |
| Obsolescence Pareto      | Bar     | dim_product[SKU]            | [Obsolete Value]                                 | Category         | Top/Bottom N       |
| Forecast Accuracy by SKU | Column  | dim_product[SKU]            | [Forecast Accuracy %]                            | Class            | A/B items          |
| Detail Matrix            | Matrix  | Region > Location > Category > SKU | DIO, Turnover, Stockout %, OTIF %, Obsolescence %, Forecast Accuracy % | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Location → SKU → aging bucket and orders.
- Export: action list (rebalance, markdown, policy change) with owner and due date.

---

## 7. Dependencies, Assumptions & Constraints
- Data: daily inventory snapshots with quantity/value/aging, demand/orders with stockout flags, OTIF events, forecast data by SKU/location/channel, COGS for turnover.
- Assumptions: Targets per segment maintained; aging buckets standardized; lead times and safety stock parameters available.
- Constraints: Missing COGS or aging reduces DIO and obsolescence quality; poor forecast versioning lowers signal quality.

---

## 8. Success Criteria
- Leading: >80% usage in weekly S&OP/WC huddles; action log maintained; forecast accuracy tracked for A-items.
- Lagging: DIO reduces vs target; Stockout % ≤ 3%; OTIF ≥ 97%; obsolescence % declines without hurting service.
- Cadence/Quality: Weekly review; consistent KPI definitions across locations; aging coverage ≥95%.
