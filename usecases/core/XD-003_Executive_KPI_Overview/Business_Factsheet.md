# XD-003 — Executive KPI Overview  
## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Use Case ID:** XD-003
- **Domain:** Executive / Cross-Functional
- **Business Owner:** CEO / CFO / COO
- **KPI Owner:** Finance / Strategy / Ops Controlling
- **Decision Owner:** Executive Committee
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/executive.yaml
- **Related Semantic Model:** semantic_models/domains/executive/model_definition.yaml

---

## 1. Business Summary
**Purpose:** Provide a unified, board-ready overview of top enterprise KPIs and their drivers.  
**Business Value:** Faster, aligned executive decisions on growth, profitability, liquidity, service, people, and operations.  
**Out of Scope:** Deep dives handled in domain-specific UCs (COM/FIN/SCM/OPS/XD).

---

## 2. Core Business Questions
- What is the current performance vs plan and LY across growth, margin, liquidity, service, and people?
- Which domains/regions drive variance?
- Which actions across domains should be prioritised to close gaps?
- How are leading KPIs trending and impacting lagging financials?

**Example Query Patterns (optional):**
- “Where are growth and GM % off plan, and which regions are driving it?”  
- “How do CCC and OTIF trends link to margin and service performance?”

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: sales.revenue.growth_pct
    name: Revenue Growth %
    purpose: Topline growth
    definition_short: (Revenue – prior period) / prior period
    unit: %
    grain: month
    agg: avg
    target: ≥ plan
    interpretation: Negative growth signals topline risk
    lineage: fact_revenue[Revenue], prior period
  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Profitability quality
    definition_short: Gross Margin / Net Sales
    unit: %
    grain: month
    agg: avg
    target: ≥ target
    interpretation: Compression shows price/mix/cost pressure
    lineage: fact_finance[GM], fact_finance[Net Sales]
  - id: profit.ebitda_margin
    name: EBITDA Margin
    purpose: Profitability
    definition_short: EBITDA / Net Sales
    unit: %
    grain: month
    agg: avg
    target: ≥ target
    interpretation: Low margin signals cost/price/mix issues
    lineage: fact_finance[EBITDA], fact_finance[Net Sales]
  - id: ops.working_capital.ccc.days
    name: Cash Conversion Cycle (days)
    purpose: Liquidity/efficiency
    definition_short: DSO + DIO – DPO
    unit: days
    grain: month
    agg: avg
    target: Reduce to target
    interpretation: Higher CCC slows cash
    lineage: DSO/DIO/DPO measures
  - id: supply.otif.pct
    name: OTIF %
    purpose: Service level
    definition_short: On-Time In-Full orders / total orders
    unit: %
    grain: order
    agg: avg
    target: ≥ 97–99%
    interpretation: Low OTIF reflects fulfillment issues
    lineage: fact_fulfillment[OTIF Flag]
  - id: hr.turnover.pct
    name: Employee Turnover %
    purpose: People stability
    definition_short: Leavers / Avg headcount
    unit: %
    grain: month
    agg: avg
    target: ≤ target
    interpretation: High turnover signals retention/engagement issues
    lineage: fact_hr[Leavers], fact_hr[Headcount]
```

---

## 4. Business Logic & Thresholds
Formal rules that define performance and action triggers.

### 4.1 Logic Description
- Flag deviations vs plan/targets on growth, margin, CCC, OTIF, turnover.
- Highlight regions/entities with multiple KPI misses.
- Prioritize actions by impact on EBITDA margin and CCC.

### 4.2 Formal Trigger Rules (Machine-Readable)
```yaml
triggers:
  - kpi: sales.revenue.growth_pct
    condition: <
    threshold: plan_target
    scope: region_entity
    exclusion: none
    action_code: SP1
  - kpi: margin.gm.pct
    condition: <
    threshold: gm_target
    scope: region_entity
    exclusion: none
    action_code: SP2
  - kpi: ops.working_capital.ccc.days
    condition: >
    threshold: ccc_target
    scope: region_entity
    exclusion: none
    action_code: W1
  - kpi: supply.otif.pct
    condition: <
    threshold: otif_target
    scope: region_entity
    exclusion: force_majeure
    action_code: O2
  - kpi: hr.turnover.pct
    condition: >
    threshold: turnover_target
    scope: region_entity
    exclusion: restructuring
    action_code: C1
```

---

## 5. Action Codes (Mandatory)
Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| SP1 | Growth Acceleration | sales.revenue.growth_pct < plan | Drive growth levers (price/volume/mix, channel) | Improve revenue growth, margin | L2 | Commercial |
| SP2 | Margin Stabilisation | margin.gm.pct < target | Price/mix/cost actions to lift margin | Improve GM %, EBITDA margin | L2 | Commercial/Finance |
| W1 | Working Capital Improvement | ops.working_capital.ccc.days > target | Address DSO/DIO/DPO levers | Improve CCC, liquidity | L2 | Finance/Ops |
| O2 | Operations Stabilisation | supply.otif.pct < target | Fix fulfillment drivers | Improve OTIF, protect revenue | L2 | Supply/Logistics |
| C1 | Retention Playbook | hr.turnover.pct > target | Retention actions | Reduce turnover, stabilise capability | L2 | HR |

---

## 6. 3–30–300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Revenue Growth %  
- Gross Margin %  
- EBITDA Margin %  
- CCC (days)  
- OTIF %  
- Employee Turnover %  

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| KPI vs Plan/Target by Region/Entity | Column | dim_org[Entity] | [KPI], [Target] | Region | Current quarter | Core ranking |
| Margin & Growth Trend | Line | dim_date[Month] | [Revenue Growth %], [GM %], [EBITDA Margin] | Region | L12M | Financial trajectory |
| CCC vs OTIF | Scatter | [CCC Days] | [OTIF %] | Region/Entity | Current quarter | Liquidity/service linkage |
| Turnover vs Margin | Scatter | [Turnover %] | [EBITDA Margin] | Region/Entity | Current quarter | People-performance linkage |

### 6.3 Required Slicers (Mandatory)
- Date (Month/Quarter)  
- Region / Entity / Segment  
- Domain drill (Commercial / Ops / Supply / HR)  

---

## 7. Data Requirements Summary
```yaml
required_facts:
  - fact_revenue (for growth)
  - fact_finance (GM, EBITDA)
  - fact_wc (DSO/DIO/DPO/CCC) or derived from AR/AP/Inventory
  - fact_fulfillment (OTIF)
  - fact_hr (turnover)
required_dimensions:
  - dim_date
  - dim_org (entity/region/segment)
  - security_user_org
required_grain: month for finance/CCC/hr; order for OTIF
required_time_range: 12–24 months history + plan/targets
required_slicers: Date, Region/Entity/Segment, Domain drill
```

---

## 8. Dependencies, Assumptions & Constraints
- Plan/targets available for KPIs; mappings across domains consistent.
- CCC derived from DSO/DIO/DPO in finance/supply chain models.
- OTIF from supply chain; turnover from HR; growth/margin from finance/commercial.
- OneLake canonical dims used (dim_date, dim_org, security_user_org).
- Data latency ≤24h; currency EUR.

---

## 9. Success Criteria
- Impact: Executives see unified KPI view; gaps prioritized and actions aligned; improved GM/EBITDA, CCC, OTIF, and turnover.  
- Adoption: Used in monthly executive reviews; action codes triggered with <5% false positives.  
- Quality: Consistent KPI definitions across domains; reconciled to source totals.  
- Decision Frequency: Monthly and quarterly executive reviews.

---

## 10. Risks & Wrong Interpretations (Short)
- Misalignment of targets across domains leading to false signals.  
- Over-aggregation hiding critical regional issues.  
- CCC misread if DSO/DIO/DPO not aligned to same periods/entities.  
