# FIN-002 – Cost Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** FIN-002
- **Domain:** Finance / Operations
- **Owner (Business):** CFO / Ops Finance / Plant Controllers
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/finance.yaml
- **Related Semantic Model:** semantic_models/domains/finance/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve operating profit by reducing unit cost and controlling OpEx vs Plan.  
**Business Value:** -2–4 % unit cost, better OpEx discipline, higher GM/EBITDA.  
**Out of Scope:** Strategic sourcing roadmap (handled separately).

---

## 2. Core Questions
- Which plants/lines/products have the highest unit cost and why?
- Where does OpEx deviate vs Plan and LY?
- Which suppliers, materials, or processes drive cost variance?
- Which actions will move GM/EBITDA fastest?

**Example Queries:**  
- “Which top-20 SKUs drive +>3 % unit cost vs Plan?”  
- “Where are material costs up with flat volume?”  

---

## 3. KPI Set (Business View)

| KPI Name             | KPI ID (mandatory)          | Purpose                     | Definition (short)                | Unit / Format | Target / Threshold   | Interpretation               |
|----------------------|-----------------------------|-----------------------------|-----------------------------------|---------------|----------------------|------------------------------|
| Unit Cost            | cost.unit.amount            | Cost efficiency             | Total Cost / Units produced/sold  | €             | ≤ Plan               | Lower = more efficient       |
| COGS % of Sales      | margin.cogs.pct             | Margin quality              | COGS / Net Sales                  | %             | ≤ Plan               | Margin pressure indicator    |
| OpEx vs Plan %       | cost.opex.vs_plan.pct       | Spend control               | (OpEx – Plan) / Plan              | %             | ± band; >0 flag      | Gap to plan                  |
| Material Cost %      | cost.material.pct           | Direct material pressure    | Material Cost / Net Sales         | %             | ≤ Plan               | Procurement lever            |
| Labor Productivity % | ops.labor.productivity.pct  | Workforce efficiency        | Output / Labor hours or cost      | %             | ↑ vs Plan/LY         | Lower = utilization issue    |

> Do: set KPI IDs/targets; no technical fields as KPIs.

---

## 4. Business Logic & Thresholds
- Unit Cost > Plan by >3 % for 2 periods → action required.
- COGS % of Sales up >1 pp with flat volume → pricing or procurement issue.
- OpEx vs Plan % > +5 % → discretionary spend review.
- Material Cost % rise >2 pp → supplier/BOM renegotiation.

**Trigger (formal):**
```
WHEN cost.unit.amount > plan + 3 %
OR   margin.cogs.pct > plan + 1 pp
OR   cost.opex.vs_plan.pct > 5 %
THEN propose PC2/O2/M1/L2
```

---

## 5. Action Codes

| Code | Name                      | Trigger (formal, KPIs)             | Description (business action)             | Expected KPI Impact      |
|------|---------------------------|------------------------------------|-------------------------------------------|--------------------------|
| PC2  | Cost Out / Re-Negotiate   | cost.unit.amount > plan            | Revisit supplier terms/BOM/logistics      | -2–4 % unit cost         |
| O2   | Process Improvement       | margin.cogs.pct rising, low OEE    | Lean/Six Sigma to remove waste            | -1–3 % unit cost         |
| M1   | Make/Buy Optimization     | capacity/cost imbalance            | Shift to optimal sourcing mix             | Lower conversion cost    |
| L2   | Productivity Boost        | labor productivity down vs Plan    | Productivity programs (shifts, training)  | +3–8 % productivity      |

> Do: use ActionCodes_Portfolio; KPI-based triggers.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- Unit Cost | COGS % of Sales | OpEx vs Plan % | Material Cost % | Labor Productivity %

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name         | Type      | X-Axis / Category | Y-Axis / Value                              | Segment / Legend | Filters          |
|---------------------|-----------|-------------------|---------------------------------------------|------------------|------------------|
| Unit Cost Trend     | Line      | dim_date[Month]   | [Unit Cost], [Unit Cost vs Plan %]          | Plant/BU         | Last 12–24M      |
| Cost Variance Bridge| Waterfall | Drivers (Material, Labor, Energy, Overhead, OpEx) | Δ Cost vs Plan | n/a | Period selector |
| Cost by Plant/Line  | Bar       | dim_org[Plant]/[Line] | [Unit Cost], [Material %, Labor %, Overhead %] | Region/BU   | Top/Bottom N     |
| Detail Matrix       | Matrix    | Plant → Line → Product | Unit Cost, Material %, Labor %, Overhead %, OpEx | Region/BU | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Plant → Line → Product; supplier/material contribution.
- Export: action list per plant/owner with variances.

---

## 7. Dependencies, Assumptions & Constraints
- Data: BOM and routing accurate; UoM consistent; plan cost and OpEx available; supplier/material master.
- Assumptions: Plan values frozen post-close; overhead allocation consistent.
- Constraints: Missing plan/target fields reduce insight; high granularity may need aggregation.

---

## 8. Success Criteria
- Leading: >80 % use in monthly cost/performance reviews; action list maintained.
- Lagging: Sustained reduction in Unit Cost/COGS %; OpEx within plan tolerance (<2–3 % variance); productivity improving with stable quality.
- Cadence/Quality: Monthly review; no KPI-definition conflicts.
