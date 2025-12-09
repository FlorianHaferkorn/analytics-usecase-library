# XD-003 – Executive KPI Overview (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** XD-003
- **Domain:** Executive / Cross-Domain
- **Owner (Business):** CEO / CFO / COO
- **Reporting Level:** Strategic
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/executive.yaml
- **Related Semantic Model:** semantic_models/domains/executive/model_definition.yaml

---

## 1. Summary
**Purpose:** Provide a concise, trusted executive cockpit across revenue, margin, cash, service, and people.  
**Business Value:** Faster decisions, single source of truth for board/EXCO, early risk detection.  
**Out of Scope:** Deep drill-down diagnostics (handled in domain dashboards).

---

## 2. Core Questions
- Are we on track vs plan across Revenue, Margin, Cash, Service, People?
- Where are the biggest variances vs Plan/LY and trends vs target?
- Which risks require immediate action, and who owns them?
- How do strategic KPIs link to execution (Action Codes, owners, next steps)?

**Example Queries:**
- “Which top 5 KPI variances need decision this week?”
- “Is cash conversion off track due to inventory or receivables?”

---

## 3. KPI Set (Business View)

| KPI Name                 | KPI ID (mandatory)          | Purpose                     | Definition (short)                                  | Unit / Format | Target / Threshold        | Interpretation                 |
|--------------------------|-----------------------------|-----------------------------|-----------------------------------------------------|---------------|---------------------------|--------------------------------|
| Revenue Growth %         | sales.revenue.growth_pct    | Growth                      | (Net Sales vs LY)/LY                                | %             | ≥ plan/forecast           | Growth health                 |
| Gross Margin %           | margin.gm.pct               | Profitability               | (Net Sales - COGS) / Net Sales                      | %             | ≥ plan                    | Profit quality                |
| EBITDA Margin %          | profit.ebitda_margin        | Profitability               | EBITDA / Revenue                                    | %             | ≥ plan                    | Profitability resilience      |
| Cash Conversion Cycle    | ops.working_capital.ccc.days| Liquidity                   | DSO + DIO - DPO                                     | days          | ↓ vs plan/LY              | Cash efficiency               |
| OTIF %                   | supply.otif.pct             | Service reliability         | On-Time In-Full lines / total                       | %             | ≥ 97%                     | Service and supply health     |
| Employee Turnover %      | hr.turnover.pct             | People health               | Leavers / Avg headcount                             | %             | ≤ target                  | Engagement/retention          |
| NPS / CSAT               | svc.nps.index               | Customer experience         | NPS or CSAT index                                   | index         | ↑ vs prior                | Experience sentiment          |

> Use KPI IDs from catalog; display per plan/LY and trend. Keep the set minimal and stable.

---

## 4. Business Logic & Thresholds
- Any KPI below target band triggers escalation; show variance vs Plan and vs LY.
- Alert rules per KPI (e.g., Cash Conversion > target days; OTIF < 97%; Turnover > target).
- Owners must be defined per KPI; actions logged with due dates.

**Trigger Logic (formal, for automation):**
```
WHEN any core KPI outside target band
THEN surface in Exec cockpit and propose action code from respective domain (e.g., P2, M2, I2, PC4, L2)
```

---

## 5. Action Codes

| Code | Name (Domain)                | Trigger (formal, KPIs)                    | Description (business action)                 | Expected KPI Impact             |
|------|------------------------------|-------------------------------------------|-----------------------------------------------|---------------------------------|
| P2   | Price Adjustment (Commercial)| margin.gm.pct < target or price leakage   | Adjust pricing/discounts                      | Improve GM%                     |
| I2   | Inventory Policy Tuning (SCM)| ops.working_capital.ccc.days > target     | Reduce DIO/DSO, improve DPO                   | Faster cash conversion          |
| PC4  | Supplier/Process Fix (SCM)   | supply.otif.pct < 97                      | Stabilise supply, OTIF recovery               | Higher OTIF                     |
| L2   | People Retention (HR)        | hr.turnover.pct > target                  | Retention actions/training                    | Lower turnover                  |

> Keep mapping to domain-specific actions; cockpit only orchestrates.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- Revenue Growth %, Gross Margin %, EBITDA Margin %, Cash Conversion Cycle, OTIF %, Employee Turnover %, NPS/CSAT.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name              | Type   | X-Axis / Category      | Y-Axis / Value                        | Segment / Legend | Filters / Defaults |
|--------------------------|--------|------------------------|---------------------------------------|------------------|--------------------|
| KPI Variance vs Plan/LY  | Column | KPI                    | Variance to Plan, Variance to LY      | n/a              | Current period     |
| Trend Lines              | Line   | dim_date[Month]        | Each KPI vs Plan/Target               | KPI              | Last 12–24 months  |
| Cash Conversion Drivers  | Waterfall | Drivers (DSO, DIO, DPO)| Δ CCC vs Plan/LY                    | n/a              | Current period     |
| Service & People View    | Column | KPI subset (OTIF, Turnover, NPS) | Actual vs Target               | Region/Segment    | Current period     |
| Risk/Action Table        | Table  | KPI list               | Owner, Issue, Action Code, Due date   | Status           | Export enabled     |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill to domain dashboards (Commercial, SCM, Finance, HR, CX) for root cause.
- Export: action log with owners and due dates.

---

## 7. Dependencies, Assumptions & Constraints
- Data: consolidated KPI feeds from domain semantic models; plan/forecast/LY; targets per KPI; owner mapping.
- Assumptions: Domain KPIs already validated; plan versions consistent; targets maintained.
- Constraints: If domain feeds stale, cockpit accuracy degrades; must flag data freshness.

---

## 8. Success Criteria
- Leading: Exec cockpit used in weekly EXCO/steerco; owner/action log maintained; data freshness visible.
- Lagging: KPI variances reduced; fewer surprises; clear ownership and follow-up.
- Cadence/Quality: Weekly and monthly cadence; KPI definitions locked and aligned to catalog.
