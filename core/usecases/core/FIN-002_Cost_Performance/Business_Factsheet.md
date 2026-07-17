---
id: FIN-002
factsheet_type: business
---

# FIN-002 - Cost Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** FIN-002
- **Domain:** Finance / Operations
- **Business Owner:** CFO / Ops Finance Lead
- **KPI Owner:** Plant/Ops Controllers
- **Decision Owner:** Finance & Operations Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/data_contracts/domains/finance.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Finance.SemanticModel (domain model for FIN-*).

---

## 1. Business Summary

**Purpose:** Reduce unit cost and improve margin by controlling material, labor, and OpEx vs plan.  
**Business Value:** Better cost competitiveness, margin protection, and more efficient operations without sacrificing throughput/quality.  
**Out of Scope:** Detailed OEE/performance tuning (OPS-001); supplier PPV specifics (OPS-002); logistics cost ratio (OPS-009).

---

## 2. Core Business Questions

- What is unit cost vs plan/LY by plant/line/product?
- Which cost buckets (material, labor, overhead/OpEx) drive variance?
- Where is COGS % rising and margin eroding?
- Which actions reduce cost fastest without harming service/quality?

**Example Query Patterns (optional):**

- "Which plants have unit cost above plan and margin below target in the last quarter?"
- "Which products show highest material cost % variance?"

---

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| cost.unit.amount | Strategic |
| margin.cogs.pct | Influencing |
| cost.opex.vs_plan.pct | Influencing |
| cost.material.pct | Influencing |
| ops.labor.productivity.pct | Influencing |
| ops.throughput.units | Influencing |
| ops.quality.defect_rate.pct | Influencing |
| ops.yield.pct | Influencing |
| sales.net_sales.amount | Supporting |
| cost.base_volume.amount | Supporting |
| cost.opex.base.amount | Supporting |
| supply.otif.pct | Supporting |

**Action Codes:** F-K2.1, F-K2.2, F-K2.3, F-K2.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Unit Cost Amount** (`cost.unit.amount`) → **IFRS IAS 2** (none): Internal cost-accounting metric (total cost / units); no external financial-reporting standard.
- **COGS % of Sales** (`margin.cogs.pct`) → **ESMA-APM** (partial): Inverse of the gross-margin ratio; same APM treatment.
- **OpEx vs Plan %** (`cost.opex.vs_plan.pct`) → **IFRS IAS 1** (none): Internal budget-variance management metric; no external financial-reporting standard defines it.
- **Material Cost %** (`cost.material.pct`) → **IFRS IAS 2** (none): Management cost-structure ratio (material cost share of sales); not an IFRS-defined figure.
- **Labor Productivity %** (`ops.labor.productivity.pct`) → **ISO 22400-2 WE** (partial): ISO 22400-2 Worker efficiency WE = actual personnel work time / actual personnel attendance time.
- **Throughput Units** (`ops.throughput.units`) → **ISO 22400-2** (partial): Produced-quantity sum is the ISO 22400-2 PQ element feeding Effectiveness, Quality ratio and Throughput rate; not a ratio KPI (governed throughput; consolidated from the former `ops.production.volume`).
- **Quality Defect Rate %** (`ops.quality.defect_rate.pct`) → **ISO 22400-2 QR** (partial): Defect rate = 1 − Quality ratio; it is the quality-loss complement of ISO 22400-2 QR, decomposed by the standard into scrap ratio (SR) and rework ratio (RR).
- **Yield %** (`ops.yield.pct`) → **ISO 22400-2 QR** (partial): 'Good units / total produced' duplicates ISO 22400-2 Quality ratio and overlaps First Pass Yield (FPY).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Unit Cost Amount  
- COGS % of Sales  
- OpEx vs Plan %  
- Material Cost %  
- Labor Productivity %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Unit Cost vs Plan by Plant/Line | Column | dim_org[Plant/Line] | [Unit Cost], [Plan] | Product | Current quarter | Core ranking |
| COGS % vs Target | Column | dim_org[Entity] | [COGS %], [Target] | Region | Current quarter | Margin driver |
| Material Cost % Trend | Line | dim_date[Month] | [Material Cost %] | Plant/Category | L12M | Efficiency trend |
| OpEx vs Plan | Column | dim_org[Entity] | [OpEx vs Plan %] | Region | Current quarter | Overhead control |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Entity / Plant / Line  
- Product / Category  
- Cost bucket (Material/Labor/OpEx)

---

### 5.4 300-Second Layer (Diagnostics)

- Plant-line-product variance bridge tying unit cost, material share, labor productivity, and production volume into one reconciled cost story.
- Quality and yield drill showing whether scrap, rework, or defect deterioration is the real cause of cost pressure rather than pure price or overhead variance.
- OpEx and overhead control view by entity and plant to separate structural overspend from temporary ramp-up or approved transformation effects.

## 6. Data Requirements Summary

- Required facts: fact_cost, fact_output, fact_finance, fact_labor, plus fact_ops and fact_quality where productivity, yield, and defect drivers are used to explain cost pressure.
- Required dimensions: dim_date, dim_org, dim_product, and security_user_org.
- Required grain: plant_line_product_month for unit-cost diagnostics, with entity_month finance views for OpEx control.
- Required time range: 12-24 months history plus current plan and baseline comparatives.
- Required slicers: Date, Entity/Plant/Line, Product/Category, Cost bucket.

---

## 7. Dependencies, Assumptions & Constraints

- Plan vs actual available for unit cost and OpEx; cost buckets aligned to same period.
- Allocation rules for overhead clear; labor hours available; material costs separated.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; currency EUR.

---

## 8. Success Criteria

- **Benchmark Targets (world-class reference):** SG&A cost at or below the APQC Open Standards Benchmarking industry median (APQC); favourable net cost variance vs standard with material price and usage variances both controlled (CIMA Official Terminology; Horngren's Cost Accounting 17e); stable-to-declining COGS % with input inflation fully recovered in pricing; OPEX within plan via zero-based justify-from-zero discipline (McKinsey/Deloitte ZBB).  
- Impact: Reduced unit cost vs plan; improved COGS %; material cost % lowered; productivity improved.  
- Adoption: Used in monthly ops/finance reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across finance/ops; reconciled to source totals.  
- Decision Frequency: Monthly and weekly cost reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misallocation of overhead distorting unit cost.  
- Material cost % misread if price/volume/mix effects not separated.  
- Productivity dips during planned training/ramp-up misinterpreted.  






## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: Unit Cost Spike Driven by Volume Drop

**Situation:** Cost per unit has increased 15% vs plan in Q2. COGS % is stable, but production volume dropped 20% due to demand shortfall, spreading fixed costs over fewer units.

**Decision question:** Is the volume shortfall temporary (seasonal, order timing) or structural (demand erosion)? Should production be consolidated?

**Who decides:** Operations Controller + Plant Manager.

**Consequence of inaction:** Fixed cost absorption worsens each month of underutilization; unit cost gap compounds into margin erosion.

**Action Code triggered:** F-K2.1 (Cost Variance Investigation) — activates fixed/variable cost split analysis by plant and product line.

### Scenario B: OPEX Overrun Despite Revenue on Track

**Situation:** OPEX is 8% above plan while revenue tracks at +1%. Labor productivity has declined 5% and defect rate increased, driving rework costs.

**Decision question:** Is the OPEX overrun driven by quality issues (rework), headcount creep, or input cost inflation?

**Who decides:** Finance Controller + Operations Lead.

**Consequence of inaction:** OPEX overrun flows directly to EBIT; annualized gap equals €2M if unaddressed.

**Action Code triggered:** F-K2.3 (OPEX Containment) — activates cost driver decomposition and variance bridge.
