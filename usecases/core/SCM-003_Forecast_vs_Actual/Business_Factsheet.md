# SCM-003 – Forecast vs Actual (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** SCM-003
- **Domain:** Supply Chain / Planning
- **Owner (Business):** Head of Demand Planning / S&OP Lead
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/supply_chain.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve forecast accuracy and bias to stabilize supply, inventory, and service.  
**Business Value:** Higher forecast accuracy, fewer re-plans, lower safety stock and expedites, better service.  
**Out of Scope:** Long-term product portfolio strategy; advanced ML model design (handled separately).

---

## 2. Core Questions
- Where do forecasts deviate most vs actuals (by SKU/channel/region)?
- Is bias persistent (over- or under-forecasting) and where?
- How does forecast error drive stockouts, excess inventory, and expedites?
- Which items need segmentation, collaborative planning, or model upgrade?

**Example Queries:**
- “Which A-SKUs have Accuracy <80% and bias >+5% for two periods?”
- “Which channels drive the highest service impact due to forecast error?”

---

## 3. KPI Set (Business View)

| KPI Name             | KPI ID (mandatory)           | Purpose                        | Definition (short)                              | Unit / Format | Target / Threshold        | Interpretation                  |
|----------------------|------------------------------|--------------------------------|-------------------------------------------------|---------------|---------------------------|---------------------------------|
| Forecast Accuracy %  | plan.forecast.accuracy.pct   | Overall forecast quality       | 1 - \|Actual - Forecast\| / Actual              | %             | ≥ 80–90% by class         | Quality of plan                 |
| MAPE %               | plan.forecast.mape.pct       | Error magnitude                | Mean Absolute Percentage Error                  | %             | ↓ vs baseline             | Variability of error            |
| Bias %               | plan.forecast.bias.pct       | Systematic over/under          | (Forecast - Actual) / Actual                    | %             | Between -5% and +5%       | Direction of error              |
| Service Impact %     | plan.forecast.service_impact.pct | Service exposure            | Lines with stockout/expedite due to error / total | %           | ≤ 3%                      | Customer/service risk           |
| Re-plan Frequency    | plan.replan.count            | Process stability              | Plan versions per period                        | count         | ↓ with governance         | Planning discipline             |

> KPI IDs must align to the catalog; targets vary by ABC/XYZ class.

---

## 4. Business Logic & Thresholds
- Forecast Accuracy % < 80% for A-items → immediate review and segmentation.
- Bias % outside ±5% for 2 periods → adjust inputs or collaboration.
- Service Impact % > 3% → safety stock or supply response; revisit forecast horizon.
- High Re-plan Frequency with stable demand → governance and lock windows.

**Trigger Logic (formal, for automation):**
```
WHEN plan.forecast.accuracy.pct < 80
OR   plan.forecast.bias.pct > 5 OR plan.forecast.bias.pct < -5
OR   plan.forecast.service_impact.pct > 3
THEN propose SP1 (forecast discipline), O2 (process improvement), I2 (policy tuning), D1 (demand signal integration)
```

---

## 5. Action Codes

| Code | Name                           | Trigger (formal, KPIs)                             | Description (business action)                   | Expected KPI Impact                |
|------|--------------------------------|----------------------------------------------------|-------------------------------------------------|------------------------------------|
| SP1  | Forecast Discipline            | accuracy < target OR replan count high             | Governance, lock windows, consensus checkpoints | Higher stability, fewer re-plans   |
| O2   | Process Improvement            | persistent bias or low accuracy for segments       | Segmentation, better inputs, cleanse anomalies  | Higher accuracy, lower bias        |
| I2   | Policy Tuning                  | service_impact.pct > 3%                            | Adjust safety stock for volatile SKUs           | Higher service, stable WC          |
| D1   | Demand Signal Integration      | low accuracy for demand-driven SKUs                | Add POS/market signals, shorten horizon         | Lower error/bias                   |

> Use ActionCodes_Portfolio; keep triggers KPI-based.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- Forecast Accuracy %, MAPE %, Bias %, Service Impact %, Re-plan Frequency.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name             | Type   | X-Axis / Category              | Y-Axis / Value                                  | Segment / Legend | Filters / Defaults |
|-------------------------|--------|--------------------------------|-------------------------------------------------|------------------|--------------------|
| Accuracy & Bias Trend   | Line   | dim_date[Month]                | [Forecast Accuracy %], [Bias %]                 | Channel/Region   | Last 12–18 months  |
| Accuracy by SKU/Channel | Column | dim_product[SKU] or dim_org[Channel] | [Forecast Accuracy %], [MAPE %]            | Class (ABC/XYZ)  | A/B items          |
| Bias Distribution       | Column | dim_product[SKU]               | [Bias %]                                        | Category         | Current period     |
| Service Impact Pareto   | Bar    | dim_product[SKU]               | [Service Impact %] or impacted Qty              | Region/Channel   | Current period     |
| Detail Matrix           | Matrix | Region > Channel > SKU         | Accuracy %, MAPE %, Bias %, Service Impact %, Re-plan Count | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Channel → SKU → Forecast Version; view version deltas and re-plan events.
- Export: list of SKUs for model upgrade or collaboration with owner/target action.

---

## 7. Dependencies, Assumptions & Constraints
- Data: versioned forecasts with timestamps and horizon, actuals at matching grain, stockout/expedite flags, ABC/XYZ segmentation, planning calendar.
- Assumptions: Latest forecast version identified; plan freeze/lock periods defined; class targets maintained.
- Constraints: Missing versioning undermines accuracy/bias; misaligned actuals/forecasts cause noisy KPIs.

---

## 8. Success Criteria
- Leading: >80% usage in weekly S&OP; action log maintained; versioning completeness ≥95%.
- Lagging: Accuracy/Bias within targets; service impact from forecast error ≤3%; fewer re-plans with stable demand.
- Cadence/Quality: Weekly S&OP, monthly IBP; consistent KPI definitions across channels/regions.
