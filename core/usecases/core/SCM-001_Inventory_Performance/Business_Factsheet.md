---
id: SCM-001
factsheet_type: business
---

# SCM-001 - Inventory Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** SCM-001
- **Domain:** Supply Chain
- **Business Owner:** COO / Head of Supply Chain
- **KPI Owner:** Supply Chain Controlling / Inventory Mgmt Lead
- **Decision Owner:** Supply Chain Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/SupplyChain.SemanticModel (domain model for SCM-*).

---

## 1. Business Summary

**Purpose:** Optimize inventory by balancing availability (service level) and working capital, reducing excess, stockouts, and obsolescence.  
**Business Value:** Lower working capital, fewer stockouts, higher OTIF, and reduced write-offs.  
**Out of Scope:** Detailed demand planning algorithm tuning (SCM-003); promotion-specific effects (COM-004); transport cost optimization (OPS-018).

---

## 2. Core Business Questions

- Where are inventory days and turnover off target by location/channel/category?
- Which items drive stockouts and OTIF misses?
- Where is excess/obsolete inventory accumulating?
- Which actions reduce inventory without hurting service level?
- How does forecast accuracy impact inventory KPIs?

**Example Query Patterns (optional):**

- "Which DCs have DIO above target and stockout > target in the last 8 weeks?"
- "Where is forecast accuracy low and driving excess or stockouts?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- DIO (days)  
- Inventory Turnover (x)  
- Stockout Rate %  
- OTIF %  
- Obsolete Inventory %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| DIO vs Target by Location/Category | Column | dim_org[Location] | [DIO], [Target] | Category | Current quarter | Core ranking |
| Stockout & OTIF Trend | Line | dim_date[Week] | [Stockout %], [OTIF %] | Location/Channel | L12W | Service stability |
| Obsolete Inventory by Category | Bar (horizontal) | dim_product[Category] | [Obsolete %] | Location | Current quarter | Excess risk |
| Forecast Accuracy vs DIO | Scatter | [Forecast Accuracy %] | [DIO] | Category | Current quarter | Planning impact |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Location / DC / Channel  
- Category / Product  
- ABC/XYZ (if available)

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_inventory

  - fact_cogs (or fact_sales for COGS proxy)

  - fact_fulfillment (OTIF)

  - fact_forecast

  - fact_sales (actuals for accuracy)
required_dimensions:

  - dim_date

  - dim_org (location/DC/channel)

  - dim_product

  - security_user_org
required_grain: location_sku_month for inventory; order for OTIF; day for stockouts
required_time_range: 12-24 months history
required_slicers: Date, Location/DC/Channel, Category/Product, ABC/XYZ
```

---

## 7. Dependencies, Assumptions & Constraints

- COGS/actuals available to compute DIO/turnover; inventory snapshots consistent.
- Stockout and OTIF flags available; forecast and actual aligned by SKU/location/time.
- Obsolescence flagged; ABC/XYZ classification optional but recommended.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Success Criteria

- Impact: Lower DIO/raise turnover to targets; reduce stockouts and OTIF misses; reduce obsolete %.  
- Adoption: Used in monthly S&OP/inventory reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across SCM UCs; reconciled to source totals.  
- Decision Frequency: Monthly S&OP and weekly inventory reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misstated DIO if COGS or inventory snapshots misaligned.
- Stockout flags incomplete, underreporting availability risk.
- Forecast accuracy misread without considering promotions or launches.

---

## 10. Typical Decision Scenarios

### Scenario A: DIO Spike Without OTIF Impact

**Situation:** DIO has risen from 55 to 71 days in 6 weeks across the Central Europe DC. Inventory value is up €12M. However, OTIF remains at 97.8% and stockout rate is 0.3% — both within targets.

**Decision question:** Is the inventory build intentional (S&OP-approved seasonal buffer) or unmanaged accumulation of slow-moving stock?

**Who decides:** Supply Chain Controlling Lead + Inventory Manager.

**Consequence of inaction:** If unmanaged, €12M excess inventory carries €600K annualized cost of capital (at 5%). If seasonal buffer is approved, this is the `when_not_to_act` condition — no corrective action needed.

**Action Code triggered:** S-I1.1 (Inventory Reduction) — only if confirmed as unmanaged excess after S&OP policy check.

### Scenario B: Stockout Rate Rising in Core SKUs Despite Adequate Total Inventory

**Situation:** Total DIO is 62 days (within target), but the stockout rate has risen to 4.2% on A-class SKUs in the Northern region. The root cause analysis shows inventory concentrated in slow-moving C-class items while A-class coverage has dropped to 12 days.

**Decision question:** Is this a demand signal failure (forecast under-estimated A-class demand) or a replenishment priority failure (reorder triggered too late)?

**Who decides:** Supply Chain Controlling Lead + Demand Planner.

**Consequence of inaction:** 4.2% stockout on A-class SKUs that represent 60% of revenue = ~2.5% effective lost sales rate. At €200M revenue = €5M annual lost sales risk.

**Action Code triggered:** S-I1.3 (Safety Stock Adjustment) + SCM-003 forecast review for demand signal correction.

### Scenario C: Obsolete Inventory Build Approaching Write-off Threshold

**Situation:** Obsolete inventory as a % of total has risen from 2.1% to 5.8% over 3 months. The aging analysis shows 80% of the obsolete stock is in 3 discontinued SKUs in the Southern DC.

**Decision question:** At what point does the cost of holding exceed the write-off cost? Is there a liquidation channel available?

**Who decides:** Head of Supply Chain + Finance Controlling.

**Consequence of inaction:** Holding €4M of obsolete inventory at 5% CoC = €200K annual holding cost, plus full write-off risk when the items breach the accounting aging policy.

**Action Code triggered:** S-R2.1 (Obsolescence Management) — activates liquidation or write-off decision protocol.

---







