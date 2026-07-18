---
id: COM-001
factsheet_type: business
---
# COM-001 - Sales Performance vs Plan & LY  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-001
- **Domain:** Commercial
- **Business Owner:** CCO / Head of Sales
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Commercial.SemanticModel (domain model for COM-*).

---

## 1. Business Summary

**Purpose:** Explain Net Sales performance vs Plan and vs Last Year by price,
volume, mix, and channel/region to protect revenue and margin.  
**Business Value:** Faster detection of revenue gaps; targeted pricing and mix
actions to stabilise gross margin; focus resources on the most material
regions/channels.  
**Out of Scope:** Promotion ROI deep dives (COM-004); detailed margin leakage
diagnostics (COM-002); pipeline/win-loss (COM-010).

---

## 2. Core Business Questions

- Where do Net Sales deviate most vs Plan and vs LY by region, channel, and
  product hierarchy?
- What is the contribution of price, volume, and mix to the Net Sales gap?
- Which customer or product segments drive negative gross margin %?
- Which actions (pricing, mix, volume activation) close the largest gaps
  fastest?
- How persistent are the gaps over the last 3 months and current quarter?

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |
| cost.cogs.amount | Influencing |
| sales.net_sales.amount | Influencing |
| sales.net_sales.delta_pct.plan | Influencing |
| sales.net_sales.delta_pct.ly | Influencing |
| sales.pvm.price_effect.amount | Influencing |
| sales.pvm.volume_effect.amount | Influencing |
| sales.pvm.mix_effect.amount | Influencing |
| sales.price.list.amount | Supporting |
| sales.price.net.amount | Supporting |

**Action Codes:** C-M2.1, C-S1.1, C-S1.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Gross Margin %** (`margin.gm.pct`) → **ESMA-APM** (partial): A ratio of two IFRS figures (IFRS 15 revenue, IAS 2 cost of sales); the percentage itself is a non-GAAP APM.
- **Net Sales % vs Plan** (`sales.net_sales.delta_pct.plan`) → **IFRS 15** (none): Net-sales-vs-plan is an internal budget-variance metric.
- **Delta% Net Sales** (`sales.net_sales.delta_pct.ly`) → **IFRS 15** (none): Year-over-year growth is a management trend metric.
- **Net Sales Amount** (`sales.net_sales.amount`) → **IFRS 15** (partial): Net sales is a presentation of IFRS 15 revenue: net of VAT (correctly excluded — amounts collected on behalf of third parties are not revenue) and net of returns (IFRS 15 variable consideration — recognise a refund liability, not revenue).
- **Price Effect Amount** (`sales.pvm.price_effect.amount`) → **Management accounting (CIMA/IMA)** (partial): Price effect follows the managerial-accounting sales-price-variance convention (CIMA Official Terminology; IMA Statements on Management Accounting) — not a governed ISO/IFRS standard.
- **Volume Effect Amount** (`sales.pvm.volume_effect.amount`) → **Management accounting (CIMA/IMA)** (partial): Volume effect follows the sales-volume-variance convention.
- **Mix Effect Amount** (`sales.pvm.mix_effect.amount`) → **Management accounting (CIMA/IMA)** (partial): Mix effect is the residual (total − price − volume) in the standard three-way variance decomposition.
- **Cost of Goods Sold Amount** (`cost.cogs.amount`) → **IFRS IAS 2** (exact): COGS is the IAS 2 carrying amount of inventories recognised as an expense when the related revenue is recognised (IAS 2.34), presented as 'cost of sales' under the IAS 1 function-of-expense method.

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Net Sales Amount  
- Net Sales % vs Plan  
- Net Sales % vs LY  
- Gross Margin %  
- Price/Volume/Mix Effects (cards or mini-tiles)  

### 5.2 30-Second Layer (Main Visuals)

- **Net Sales vs Plan/LY**
  - Visual Type: Line + area band
  - X-Axis: Date[Month]
  - Y-Axis: Net Sales, Plan, LY
  - Segment: Region/Channel
  - Default Filter: L12M
  - Notes: Show gaps

- **PVM Bridge**
  - Visual Type: Waterfall
  - X-Axis: Drivers
  - Y-Axis: P, V, M impact
  - Segment: Region/Channel
  - Default Filter: Current Q
  - Notes: Link to COM-002

- **GM % by Region/Channel**
  - Visual Type: Column
  - X-Axis: Region/Channel
  - Y-Axis: GM %
  - Segment: Product Tier
  - Default Filter: Current Q
  - Notes: Guardrails

- **Top/Bottom Segments**
  - Visual Type: Bar (rank)
  - X-Axis: Region/Channel/Segment
  - Y-Axis: Net Sales Gap
  - Segment: Product
  - Default Filter: Current Q
  - Notes: Focus list

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Product Category  
- Customer Segment (optional)

### 5.4 300-Second Layer (Diagnostics)

- Gap decomposition by region, channel, product category, and customer segment with absolute and relative contribution to the plan and LY variance.
- Margin guardrail table linking GM%, price realization, and mix deterioration to the specific invoice-line clusters that trigger C-S1.1 or C-S1.2.
- Top-N accounts, SKUs, and channels with adverse price, volume, or mix effects, including the last 3 monthly observations to separate one-off noise from persistent execution gaps.

---

## 6. Data Requirements Summary

- Required facts: fact_sales with plan, LY, list price, net price, quantity, and COGS at invoice-line level.
- Required dimensions: dim_date, dim_org, dim_product, dim_customer where available, and security_user_org.
- Required grain: invoice_line, aggregated to month for KPI tracking and retained at invoice-line level for execution diagnostics.
- Required time range: 24 months history with current plan and prior-year comparatives.
- Required slicers: Date, Region/Channel, Product Category, Customer Segment.

---

## 7. Dependencies, Assumptions & Constraints

- Plan and LY fields must be populated in fact_sales (Plan Sales Amount,
  Last Year Sales Amount).
- PVM requires Net Price Amount, Plan Sales Amount, Quantity and residual logic
  alignment with COM-002.
- Gross Margin uses COGS; returns/credit notes handled upstream.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 8. Success Criteria

- **Benchmark Targets (world-class reference):** Net Sales actuals within ±3% of plan (Gartner Sales Benchmark 2024); Gross Margin 25–45% for B2B manufacturing (APQC Open Standards Benchmarking); 5–10% YoY net-sales growth as a B2B-manufacturing sector reference (Gartner).
- Impact: Net Sales vs Plan/LY gaps reduced; GM % at or above target.
- Adoption: Used in monthly sales performance reviews; actions tracked via
  Action Codes.
- Quality: PVM residual within tolerance; reconciled to source totals;
  definitions consistent with COM-002/004.
- Decision Frequency: Monthly/Quarterly.

---

## 9. Risks & Wrong Interpretations (Short)

- Misstated Plan/LY leading to false gaps.
- PVM residual too high due to inconsistent plan price or quantity.
- Over-reacting on price without GM guardrails can erode margin.

---

## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: Revenue Gap Triggered by Volume Loss in Key Channel

**Situation:** Net Sales are 8% below plan in Month 3 of Q2. The PVM bridge shows a volume effect of −€2.4M with a flat price effect, concentrated in the North Europe channel. The mix effect is slightly positive.

**Decision question:** Is this a structural demand issue, a execution/distribution gap, or a one-time event?

**Who decides:** Commercial Controlling Lead + Regional Sales Director.

**Consequence of inaction:** Gap compounds into Q2 miss; plan credibility with board deteriorates.

**Action Code triggered:** C-S1.1 (Volume Recovery) — activates root-cause split by customer/product in the affected channel.

### Scenario B: Gross Margin Erosion Despite Revenue on Track

**Situation:** Net Sales is +1% vs plan, but GM % has dropped 2.5pp vs plan and 3pp vs LY. The PVM bridge shows a strong negative mix effect (shift from high-margin premium products to volume SKUs).

**Decision question:** Is the mix shift a strategic choice or an unmanaged drift? Is it driven by customer purchasing behavior or by promotional depth?

**Who decides:** Commercial Controlling Lead + Product/Category Manager.

**Consequence of inaction:** A 3pp GM drop on annual revenue of €200M equals €6M unplanned margin erosion. Below the guardrail defined in the Margin-First strategy pattern.

**Action Code triggered:** C-M2.1 (Mix Recovery) — activates segment-level mix analysis and pricing review.

### Scenario C: Regional Outperformance Masks Systemic Under-Delivery

**Situation:** Company-level Net Sales is +2% vs plan, but drilling by region reveals that 70% of the upside is concentrated in one region while 3 other regions are all −5% to −8% below plan.

**Decision question:** Is the regional concentration a risk (single-region dependency) or an opportunity (replicate what's working)?

**Who decides:** Sales Leadership Team.

**Consequence of inaction:** Company-level reporting gives false confidence; under-performing regions are not addressed.

**Action Code triggered:** No single AC fires — management judgment required. The use case flags the concentration risk via the ranking visual.

---

---



