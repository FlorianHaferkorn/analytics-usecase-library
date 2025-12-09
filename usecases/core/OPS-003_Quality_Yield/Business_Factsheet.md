# OPS-003 – Quality & Yield (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** OPS-003
- **Domain:** Operations / Quality
- **Owner (Business):** COO / Head of Quality / Production Lead
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve first-pass yield and reduce scrap/rework to lower cost and protect service levels.  
**Business Value:** Lower cost of poor quality, fewer complaints, higher throughput and stability.  
**Out of Scope:** Supplier audit program (handled in procurement/quality sourcing).

---

## 2. Core Questions
- Where do scrap and rework concentrate (lines, products, shifts)?
- Which defect categories drive the largest losses and cost?
- How do quality issues impact unit cost, service levels, and customer complaints?
- Which corrective actions are most effective and repeatable?
- Where can best-practice settings be replicated?

**Example Queries:**
- “Which top 5 lines caused 80% of scrap last month and why?”
- “What is the FPY and scrap trend by shift for Product Family A?”

---

## 3. KPI Set (Business View)

| KPI Name             | KPI ID (mandatory)       | Purpose                     | Definition (short)                              | Unit / Format | Target / Threshold      | Interpretation                   |
|----------------------|--------------------------|-----------------------------|-------------------------------------------------|---------------|-------------------------|----------------------------------|
| First Pass Yield %   | quality.fpy.pct          | Process quality             | Good Units / (Good + Rework + Scrap)            | %             | ≥ 95–98 %               | Core quality indicator           |
| Scrap Rate %         | quality.scrap.pct        | Waste level                 | Scrap Units / Total Units                       | %             | ≤ 2 % (critical lines)  | Waste/leakage                    |
| Rework Rate %        | quality.rework.pct       | Stability/efficiency        | Rework Units / Total Units                      | %             | ≤ 3 %                   | Hidden cost of poor quality      |
| Cost of Poor Quality | quality.copq.amount      | Financial impact            | Scrap Cost + Rework Cost                        | currency      | ↓ vs prior period       | Financial leakage                |
| Complaint Rate %     | quality.complaint.pct    | Customer impact             | Complaints / Shipments                          | %             | ≤ 0.5–1.0 %             | External quality perception      |
| Defect Density       | quality.defect_density   | Defect intensity            | Defects / 1k units                              | count/1k      | ↓ trend                 | Process health                   |

> Use KPI IDs from the catalog; targets vary by line/product criticality.

---

## 4. Business Logic & Thresholds
- FPY % < target or downward trend for 2 periods → containment and RCA.
- Scrap Rate % > 2 % for priority products → root cause deep-dive and CAPA.
- Rework Rate % > 3 % with rising labor cost → standardise process and training.
- Complaint Rate % uptrend → supplier/process audit and customer containment.
- COPQ rising while volume flat → immediate corrective actions.

**Trigger Logic (formal, for automation):**
```
WHEN quality.fpy.pct < target_line
OR   quality.scrap.pct > 2
OR   quality.rework.pct > 3
OR   quality.complaint.pct > 1
THEN propose O2 (process improvement), M2 (maintenance fix), PC2 (supplier quality), L2 (training/SOP)
```

---

## 5. Action Codes

| Code | Name                         | Trigger (formal, KPIs)                                 | Description (business action)                    | Expected KPI Impact             |
|------|------------------------------|--------------------------------------------------------|--------------------------------------------------|---------------------------------|
| O2   | Process Improvement          | scrap.pct > 2 % OR rework.pct > 3 %                    | Poka-Yoke, parameter tuning, standard work       | -10–20 % scrap/rework           |
| M2   | Maintenance Optimisation     | defects linked to equipment failures                   | Maintenance/Calibration to stabilise equipment   | Higher FPY, lower scrap         |
| PC2  | Supplier Quality Fix         | defect reasons tied to incoming material               | Tighten specs, incoming inspection, supplier CAPA| Fewer incoming defects          |
| L2   | Training / Work Standards    | human-error defects, shift-specific scrap spikes       | Training, SOP reinforcement, certification       | Higher FPY, lower rework        |

> Use ActionCodes_Portfolio; ensure triggers reference KPIs.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- FPY %, Scrap %, Rework %, COPQ, Complaint Rate %, Defect Density.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name           | Type   | X-Axis / Category                | Y-Axis / Value                             | Segment / Legend | Filters / Defaults |
|-----------------------|--------|----------------------------------|--------------------------------------------|------------------|--------------------|
| FPY & Scrap Trend     | Line   | dim_date[Month]                  | [FPY %], [Scrap %], [Rework %]             | Product/Line     | Last 12–18 months  |
| Scrap Pareto          | Bar    | dim_defect[DefectReason]         | [Scrap Units], [Scrap %]                   | DefectCategory   | Current period     |
| FPY by Line/Shift     | Column | dim_org[Line] or dim_date[Shift] | [FPY %], [Scrap %]                         | ProductCategory  | Last 30–90 days    |
| COPQ by Driver        | Column | Driver (Scrap, Rework, Complaints)| [COPQ Amount]                              | Product/Line     | Current period     |
| Complaints Trend      | Line   | dim_date[Month]                  | [Complaint Rate %]                         | Region/Channel   | Last 12 months     |
| Quality Detail Matrix | Matrix | Region > Plant > Line > Product  | FPY %, Scrap %, Rework %, COPQ, Defect Density | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Plant → Line → Shift → Defect Reason; link to asset and supplier where captured.
- Export: action list with owner, due date, KPI impact; defect log with cost and responsible function.

---

## 7. Dependencies, Assumptions & Constraints
- Data: good/rework/scrap units, cost of scrap/rework, defect codes with category/reason, complaint records linked to shipments, org/product hierarchies, shift calendar.
- Assumptions: Targets per line/product maintained; defect coding standardised; COPQ mapping includes material + labor + overhead.
- Constraints: Missing defect codes reduce insight; incomplete cost mapping understates COPQ; late complaint capture hides issues.

---

## 8. Success Criteria
- Leading: >80 % usage in daily/weekly quality reviews; action log maintained; defect coding completeness ≥95 %.
- Lagging: FPY rising toward target; Scrap/Rework % declining; COPQ down while volume flat; complaints stable or declining.
- Cadence/Quality: Daily ops view, weekly quality review; consistent KPI definitions across plants.
