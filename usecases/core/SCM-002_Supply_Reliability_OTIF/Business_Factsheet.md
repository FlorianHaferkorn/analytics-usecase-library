# SCM-002 – Supply Reliability & OTIF (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** SCM-002
- **Domain:** Supply Chain
- **Owner (Business):** Head of Supply Chain / Logistics / Procurement
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve supply reliability and OTIF to protect service and reduce penalties/expedites.  
**Business Value:** OTIF ≥97%, fewer chargebacks and expedites, lower buffer stock, stable service.  
**Out of Scope:** Long-term vendor sourcing decisions (procurement strategy).

---

## 2. Core Questions
- Which suppliers/lanes/DCs drive OTIF misses and why?
- Are misses driven by On-Time, In-Full, or both?
- How do OTIF issues translate into stockouts, lost sales, or penalties?
- Which corrective actions and SLAs fix OTIF fastest?

**Example Queries:**
- “Top 10 suppliers by OTIF gap and related penalties last month?”
- “Which lanes show On-Time <95% while In-Full is ok (transport issue)?”

---

## 3. KPI Set (Business View)

| KPI Name          | KPI ID (mandatory)      | Purpose                      | Definition (short)                              | Unit / Format | Target / Threshold        | Interpretation                    |
|-------------------|-------------------------|------------------------------|-------------------------------------------------|---------------|---------------------------|-----------------------------------|
| OTIF %            | supply.otif.pct         | Supply reliability           | On-Time AND In-Full lines / total lines         | %             | ≥ 97%                     | Core reliability indicator        |
| On-Time %         | supply.on_time.pct      | Punctuality                  | On-time lines / total lines                     | %             | ≥ 95%                     | Transport/schedule adherence      |
| In-Full %         | supply.in_full.pct      | Completeness                 | Complete lines / total lines                    | %             | ≥ 97%                     | Picking/inventory reliability     |
| Stockout Impact % | supply.stockout_impact.pct | Service risk              | Lines with stockout due to supply / total lines | %             | ≤ 3%                      | Service exposure                  |
| Penalties Amount  | supply.penalty.amount   | Financial leakage            | Chargebacks/penalties linked to OTIF            | currency      | ↓ vs prior period         | Cost of misses                    |
| Expedite Cost     | supply.expedite.amount  | Cost of mitigation           | Expedite cost to fix misses                     | currency      | ↓ vs prior period         | Cost to protect service           |

> KPI IDs must match the catalog; targets per lane/supplier class where needed.

---

## 4. Business Logic & Thresholds
- OTIF % < 97% or downward trend → supplier/logistics escalation.
- On-Time % < 95% but In-Full high → transport/scheduling issue.
- In-Full % < 97% → picking/inventory accuracy issue.
- Stockout Impact % > 3% → immediate mitigation (buffer/replan).
- Penalties/Expedites rising → enforce SLA and root-cause actions.

**Trigger Logic (formal, for automation):**
```
WHEN supply.otif.pct < 97
OR   supply.on_time.pct < 95
OR   supply.in_full.pct < 97
OR   supply.stockout_impact.pct > 3
THEN propose PC4 (supplier/logistics fix), O2 (process improvement), I1 (buffering/rebalance), SP1 (plan alignment)
```

---

## 5. Action Codes

| Code | Name                          | Trigger (formal, KPIs)                       | Description (business action)                     | Expected KPI Impact        |
|------|-------------------------------|----------------------------------------------|---------------------------------------------------|----------------------------|
| PC4  | Supplier/Logistics Fix        | otif.pct < 97 OR on_time.pct < 95            | Enforce SLA, stabilize lead times, route redesign | +1–3 pp OTIF               |
| O2   | Process Improvement           | in_full.pct < 97 or picking errors           | Improve ASN/picking/pack accuracy                 | Higher In-Full %           |
| I1   | Inventory Rebalance / Buffer  | stockout_impact.pct > 3                      | Temporary buffer on critical SKUs/locations       | Lower stockout impact      |
| SP1  | Forecast/Plan Alignment       | recurring misses from plan mismatch          | Align plan/capacity; lock windows                 | Fewer re-plans, higher OTIF|

> Use ActionCodes_Portfolio; keep triggers KPI-based and formal.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- OTIF %, On-Time %, In-Full %, Stockout Impact %, Penalties, Expedite Cost.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name              | Type   | X-Axis / Category            | Y-Axis / Value                         | Segment / Legend | Filters / Defaults |
|--------------------------|--------|------------------------------|----------------------------------------|------------------|--------------------|
| OTIF Trend               | Line   | dim_date[Week/Month]         | [OTIF %], Targets                      | Supplier/Lane    | Last 12–18 months  |
| On-Time vs In-Full Split | Column | dim_supplier[SupplierName]   | [On-Time %], [In-Full %]               | Region           | Top/Bottom N       |
| Root Cause Pareto        | Bar    | fact_shipments[RootCause]    | [Shipment Lines], [OTIF % variance]    | CauseCategory    | Current period     |
| Cost of Misses           | Column | dim_supplier[SupplierName]   | [Penalties Amount], [Expedite Cost]    | Region           | Current period     |
| Detail Matrix            | Matrix | Supplier > Lane > DC > SKU   | OTIF %, On-Time %, In-Full %, Stockout Impact %, Penalties | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Supplier → Lane → DC → SKU → shipment lines with timestamps and ASN status.
- Export: action list per supplier/lane with owner, due date, SLA target.

---

## 7. Dependencies, Assumptions & Constraints
- Data: shipment lines with promised vs actual timestamps, quantities, OTIF flags, root cause coding; mapping to supplier, lane, DC, SKU; penalties/expedite costs; stockout linkage to orders.
- Assumptions: SLA targets per lane/supplier maintained; ASN quality captured; lead times stable.
- Constraints: Missing root cause coding reduces diagnostics; poor linkage to stockouts understates impact.

---

## 8. Success Criteria
- Leading: >80% usage in weekly supplier/logistics reviews; action log maintained; root cause coding ≥90%.
- Lagging: OTIF ≥ target; penalties/expedites trending down; Stockout Impact % ≤ 3%.
- Cadence/Quality: Weekly review; consistent KPI definitions; SLA master kept current.
