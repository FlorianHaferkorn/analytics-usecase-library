"""
Upgrade all 5 SemanticModel _Measures.tmdl files:
  1. Replace static Action_X_Text DAX with conditional threshold-triggered IF logic
  2. Append Narrative Text measure (domain KPI summary string)
  3. Append Active Actions Text measure (aggregates triggered actions)

Run from repo root:
  python3 products/fabric/powerbi/tooling/scripts/upgrade_measures.py
"""
import json
import re
import uuid
from pathlib import Path

DIST = Path("products/fabric/powerbi/dist")
NL = "UNICHAR ( 10 )"

# Pre-computed so they can be used inside f-strings without backslash issues
_RED   = "\U0001f534 L3"   # 🔴
_ORANGE = "\U0001f7e0 L2"  # 🟠
_YELLOW = "\U0001f7e1 L1"  # 🟡
_ARROW = "→"          # →
_CHECK = "✅"          # ✅
_DASH  = "—"          # —


# ── DAX builders ──────────────────────────────────────────────────────────────

def _if3(kpi, comp, l3, l2, l1, code, name, owner, fmt, s1, s2, s3):
    """3-level single-KPI conditional action text (single-expression DAX)."""
    def cmp(v, t):
        if comp == "lt":     return f"{v} < {t}"
        if comp == "gt":     return f"{v} > {t}"
        if comp == "abs_gt": return f"ABS ( {v} ) > {t}"
    ref = f"[{kpi}]"
    def txt(sev):
        return (
            f'"{sev} {_DASH} {code} {_DASH} {name}" & {NL} & '
            f'"Owner: {owner} | " & FORMAT ( {ref}, "{fmt}" ) & {NL} & '
            f'"{_ARROW} {s1} {_DASH} {s2} {_DASH} {s3}"'
        )
    return (
        f"IF ( {cmp(ref, l3)}, {txt(_RED)}, "
        f"IF ( {cmp(ref, l2)}, {txt(_ORANGE)}, "
        f"IF ( {cmp(ref, l1)}, {txt(_YELLOW)}, "
        f"BLANK () ) ) )"
    )


def _if_band(kpi, lo3, lo2, lo1, hi3, hi2, hi1, code, name, owner, fmt, s1, s2, s3):
    """Band trigger (too low OR too high)."""
    ref = f"[{kpi}]"
    def txt(sev):
        return (
            f'"{sev} {_DASH} {code} {_DASH} {name}" & {NL} & '
            f'"Owner: {owner} | " & FORMAT ( {ref}, "{fmt}" ) & {NL} & '
            f'"{_ARROW} {s1} {_DASH} {s2} {_DASH} {s3}"'
        )
    return (
        f"IF ( {ref} < {lo3} || {ref} > {hi3}, {txt(_RED)}, "
        f"IF ( {ref} < {lo2} || {ref} > {hi2}, {txt(_ORANGE)}, "
        f"IF ( {ref} < {lo1} || {ref} > {hi1}, {txt(_YELLOW)}, "
        f"BLANK () ) ) )"
    )


def _if2kpi(k1, c1, l3_1, l1_1, k2, c2, l2_2, f1, code, name, owner, s1, s2, s3):
    """Two-KPI trigger: k1 for L1/L3, k2 for L2."""
    def cmp(v, c, t):
        return f"{v} < {t}" if c == "lt" else f"{v} > {t}"
    r1 = f"[{k1}]"
    r2 = f"[{k2}]"
    def txt(sev, fexpr):
        return (
            f'"{sev} {_DASH} {code} {_DASH} {name}" & {NL} & '
            f'"Owner: {owner} | " & {fexpr} & {NL} & '
            f'"{_ARROW} {s1} {_DASH} {s2} {_DASH} {s3}"'
        )
    f1e = f'FORMAT ( {r1}, "{f1}" )'
    f2e = f'FORMAT ( {r2}, "0.0" ) & "d"'
    return (
        f"IF ( {cmp(r1, c1, l3_1)}, {txt(_RED, f2e)}, "
        f"IF ( {cmp(r2, c2, l2_2)}, {txt(_ORANGE, f2e)}, "
        f"IF ( {cmp(r1, c1, l1_1)}, {txt(_YELLOW, f1e)}, "
        f"BLANK () ) ) )"
    )


# ── Per-model configuration ────────────────────────────────────────────────────

CONFIGS = {
    "Commercial.SemanticModel": {
        "replacements": {
            "Action_C-C3.1_Text": _if3("Customer Retention %", "lt", 0.9, 0.94, 0.97,
                "C-C3.1", "Customer Retention Intervention", "commercial_controlling_lead",
                "0.0%", "Identify at-risk segments", "Assign CRM recovery", "Review retention monthly"),
            "Action_C-C3.2_Text": _if3("Net Promoter Score (NPS)", "lt", -5, 5, 20,
                "C-C3.2", "Complaint & Advocacy Recovery", "commercial_bi_lead",
                "#,0.0", "Map complaint patterns", "Execute recovery actions", "Review NPS monthly"),
            "Action_C-M2.1_Text": _if3("Price Realization %", "lt", 0.9, 0.92, 0.95,
                "C-M2.1", "Price Realization Guardrails", "pricing_lead",
                "0.0%", "Freeze discretionary discounts", "Enforce approvals", "Review realization monthly"),
            "Action_C-M2.2_Text": _if3("Mix Effect Amount", "lt", -200000, -75000, 0,
                "C-M2.2", "Mix Optimization (Margin-Driven)", "category_manager",
                "€#,0", "Identify negative-mix entities", "Rank SKUs by margin", "Monitor mix monthly"),
            "Action_C-P4.1_Text": _if3("Promo ROI %", "lt", -0.1, -0.05, 0.0,
                "C-P4.1", "Promo Calendar Discipline", "trade_marketing_lead",
                "0.0%", "Identify negative-ROI promos", "Review and resequence", "Validate ROI next cycle"),
            "Action_C-S1.1_Text": _if3("Gross Margin %", "lt", 0.22, 0.23, 0.25,
                "C-S1.1", "Price Discipline Enforcement", "pricing_manager",
                "0.0%", "Identify GM-breaching entities", "Freeze new discounts", "Review realization weekly"),
            "Action_C-S1.2_Text": _if3("Net Sales % vs Plan", "lt", -0.08, -0.05, -0.02,
                "C-S1.2", "Sales Gap Recovery", "commercial_controlling_lead",
                "+0.0%;-0.0%", "Identify plan-breaching entities", "Apply price/pack adjustments", "Review uplift"),
        },
        "active_actions": [
            "Action_C-C3.1_Text", "Action_C-C3.2_Text",
            "Action_C-M2.1_Text", "Action_C-M2.2_Text",
            "Action_C-P4.1_Text", "Action_C-S1.1_Text", "Action_C-S1.2_Text",
        ],
        "narrative_dax": (
            "VAR _s = [Net Sales Amount] "
            "VAR _g = [Gross Margin %] "
            "VAR _p = [Net Sales % vs Plan] "
            "VAR _pr = [Price Realization %] "
            "VAR _r = [Customer Retention %] "
            "VAR _d = SWITCH ( TRUE (), ABS ( [Price Effect Amount] ) >= ABS ( [Volume Effect Amount] ) && ABS ( [Price Effect Amount] ) >= ABS ( [Mix Effect Amount] ), "
            "\"Price: \" & FORMAT ( [Price Effect Amount], \"+€#,0;-€#,0\" ), "
            "ABS ( [Volume Effect Amount] ) >= ABS ( [Mix Effect Amount] ), "
            "\"Volume: \" & FORMAT ( [Volume Effect Amount], \"+€#,0;-€#,0\" ), "
            "\"Mix: \" & FORMAT ( [Mix Effect Amount], \"+€#,0;-€#,0\" ) ) "
            "RETURN "
            "\"Sales: \" & FORMAT ( _s, \"€#,0\" ) & \"  |  vs Plan: \" & FORMAT ( _p, \"+0.0%;-0.0%\" ) & UNICHAR ( 10 ) & "
            "\"GM: \" & FORMAT ( _g, \"0.0%\" ) & \"  |  Price Realiz.: \" & FORMAT ( _pr, \"0.0%\" ) & \"  |  Retention: \" & FORMAT ( _r, \"0.0%\" ) & UNICHAR ( 10 ) & "
            "\"Top driver: \" & _d"
        ),
    },
    "Finance.SemanticModel": {
        "replacements": {
            "Action_F-C1.1_Text": _if2kpi("Cash vs Plan %", "lt", -0.10, -0.05, "CCC Days", "gt", 5,
                "+0.0%;-0.0%", "F-C1.1", "Working Capital Improvement", "finance_director",
                "Accelerate receivables", "Extend payables discipline", "Review CCC weekly"),
            "Action_F-C1.2_Text": _if3("DSO Days", "gt", 42, 37, 33,
                "F-C1.2", "DSO Reduction Programme", "finance_director",
                "0.0", "Identify overdue accounts", "Accelerate collections", "Review DSO weekly"),
            "Action_F-C1.4_Text": _if3("DPO Days", "lt", 18, 23, 27,
                "F-C1.4", "DPO Extension Discipline", "finance_director",
                "0.0", "Review payment terms", "Negotiate extensions", "Monitor DPO monthly"),
            "Action_F-K2.1_Text": _if3("Material Cost %", "gt", 0.70, 0.65, 0.60,
                "F-K2.1", "Cost Take-Out Orchestration", "finance_director",
                "0.0%", "Identify cost overrun categories", "Initiate take-out actions", "Review unit cost monthly"),
            "Action_F-K2.2_Text": _if3("Material Cost %", "gt", 0.70, 0.65, 0.60,
                "F-K2.2", "Material Cost Containment", "operations_controller",
                "0.0%", "Identify high-cost materials", "Renegotiate supplier terms", "Monitor monthly"),
            "Action_F-K2.3_Text": _if3("Labor Productivity %", "lt", -0.10, -0.06, -0.03,
                "F-K2.3", "Labor Productivity Recovery", "hr_operations_lead",
                "+0.0%;-0.0%", "Identify low-productivity lines", "Review scheduling", "Monitor weekly"),
            "Action_F-K2.4_Text": _if3("OpEx vs Plan %", "gt", 0.08, 0.05, 0.02,
                "F-K2.4", "OpEx Discipline Enforcement", "finance_director",
                "+0.0%;-0.0%", "Identify opex overruns", "Apply cost freeze", "Review vs plan monthly"),
            "Action_F-S-I1.2_Text": _if3("DIO Days", "gt", 60, 40, 20,
                "F-S-I1.2", "Inventory Working Capital", "supply_chain_finance_lead",
                "0.0", "Identify high-DIO locations", "Initiate destocking", "Monitor DIO monthly"),
        },
        "active_actions": [
            "Action_F-C1.1_Text", "Action_F-C1.2_Text", "Action_F-C1.4_Text",
            "Action_F-K2.1_Text", "Action_F-K2.2_Text", "Action_F-K2.3_Text", "Action_F-K2.4_Text",
        ],
        "narrative_dax": (
            "VAR _cf = [Operating Cash Flow] "
            "VAR _ccc = [CCC Days] "
            "VAR _dso = [DSO Days] "
            "VAR _dpo = [DPO Days] "
            "VAR _opex = [OpEx vs Plan %] "
            "VAR _mat = [Material Cost %] "
            "RETURN "
            "\"Cash Flow: \" & FORMAT ( _cf, \"€#,0\" ) & \"  |  CCC: \" & FORMAT ( _ccc, \"0.0\" ) & \"d\" & UNICHAR ( 10 ) & "
            "\"DSO: \" & FORMAT ( _dso, \"0.0\" ) & \"d  |  DPO: \" & FORMAT ( _dpo, \"0.0\" ) & \"d\" & UNICHAR ( 10 ) & "
            "\"OpEx vs Plan: \" & FORMAT ( _opex, \"+0.0%;-0.0%\" ) & \"  |  Material Cost: \" & FORMAT ( _mat, \"0.0%\" )"
        ),
    },
    "Operations.SemanticModel": {
        "replacements": {
            "Action_O-A2.1_Text": _if3("Availability %", "lt", 0.84, 0.88, 0.92,
                "O-A2.1", "Reliability Orchestration", "maintenance_manager",
                "0.0%", "Identify chronic failure modes", "Execute corrective maintenance", "Monitor weekly"),
            "Action_O-A2.2_Text": _if3("MTBF (hours)", "lt", 60, 72, 90,
                "O-A2.2", "MTBF Improvement", "maintenance_manager",
                "0.0", "Analyse recurring failures", "Implement reliability fixes", "Review MTBF monthly"),
            "Action_O-A2.3_Text": _if3("MTTR (hours)", "gt", 15, 10, 8,
                "O-A2.3", "MTTR Reduction", "maintenance_manager",
                "0.0", "Identify slow repair categories", "Standardise procedures", "Review MTTR monthly"),
            "Action_O-A2.4_Text": _if3("PM Compliance %", "lt", 0.85, 0.90, 0.95,
                "O-A2.4", "PM Compliance Enforcement", "maintenance_manager",
                "0.0%", "Identify overdue PM tasks", "Reschedule and prioritise", "Monitor compliance weekly"),
            "Action_O-A2.5_Text": _if3("Spare Parts Stockout %", "gt", 0.20, 0.10, 0.05,
                "O-A2.5", "Spare Parts Availability", "maintenance_manager",
                "0.0%", "Identify critical stockouts", "Emergency replenishment", "Review coverage monthly"),
            "Action_O-O1.1_Text": _if3("Availability %", "lt", 0.80, 0.85, 0.90,
                "O-O1.1", "Operations Stabilisation", "maintenance_manager",
                "0.0%", "Identify recurring downtime", "Execute corrective actions", "Monitor availability weekly"),
            "Action_O-O1.2_Text": _if3("Performance %", "lt", 0.85, 0.90, 0.95,
                "O-O1.2", "Performance Recovery", "production_manager",
                "0.0%", "Identify speed-loss causes", "Eliminate micro-stoppages", "Monitor performance weekly"),
            "Action_O-O1.3_Text": _if3("Quality %", "lt", 0.94, 0.96, 0.98,
                "O-O1.3", "Quality Stabilisation", "quality_manager",
                "0.0%", "Identify top defect categories", "Implement quality controls", "Monitor daily"),
            "Action_O-O1.4_Text": _if3("OEE %", "lt", 0.65, 0.70, 0.75,
                "O-O1.4", "OEE Improvement", "plant_manager",
                "0.0%", "Identify OEE constraint factor", "Execute targeted improvement", "Review weekly"),
            "Action_O-Q3.1_Text": _if3("First Pass Yield %", "lt", 0.94, 0.96, 0.98,
                "O-Q3.1", "Quality & Yield Orchestration", "head_of_quality",
                "0.0%", "Identify yield loss sources", "Implement process controls", "Review FPY daily"),
            "Action_O-Q3.2_Text": _if3("Defect Density", "gt", 0.004, 0.0025, 0.001,
                "O-Q3.2", "Defect Density Reduction", "quality_manager",
                "0.0000", "Identify defect-dense processes", "Apply statistical controls", "Monitor weekly"),
            "Action_O-Q3.3_Text": _if3("Scrap Rate %", "gt", 0.06, 0.04, 0.02,
                "O-Q3.3", "Scrap Rate Reduction", "quality_manager",
                "0.0%", "Identify high-scrap lines", "Root cause and correct", "Review monthly"),
            "Action_O-Q3.4_Text": _if3("Cost of Poor Quality", "gt", 200000, 100000, 50000,
                "O-Q3.4", "CoPQ Reduction", "head_of_quality",
                "€#,0", "Quantify CoPQ by category", "Prioritise reduction projects", "Review monthly"),
            "Action_O-Q3.5_Text": _if3("Complaint Rate %", "gt", 0.010, 0.006, 0.003,
                "O-Q3.5", "Complaint Rate Reduction", "head_of_quality",
                "0.00%", "Identify complaint root causes", "Implement corrective actions", "Review monthly"),
        },
        "active_actions": [
            "Action_O-O1.1_Text", "Action_O-O1.2_Text", "Action_O-O1.3_Text", "Action_O-O1.4_Text",
            "Action_O-A2.1_Text", "Action_O-A2.4_Text", "Action_O-A2.5_Text",
            "Action_O-Q3.1_Text", "Action_O-Q3.3_Text", "Action_O-Q3.4_Text",
        ],
        "narrative_dax": (
            "VAR _oee = [OEE %] "
            "VAR _a = [Availability %] "
            "VAR _p = [Performance %] "
            "VAR _q = [Quality %] "
            "VAR _fpy = [First Pass Yield %] "
            "VAR _copq = [Cost of Poor Quality] "
            "RETURN "
            "\"OEE: \" & FORMAT ( _oee, \"0.0%\" ) & \"  =  Avail: \" & FORMAT ( _a, \"0.0%\" ) & \"  x  Perf: \" & FORMAT ( _p, \"0.0%\" ) & \"  x  Qual: \" & FORMAT ( _q, \"0.0%\" ) & UNICHAR ( 10 ) & "
            "\"FPY: \" & FORMAT ( _fpy, \"0.0%\" ) & \"  |  CoPQ: \" & FORMAT ( _copq, \"€#,0\" )"
        ),
    },
    "SupplyChain.SemanticModel": {
        "replacements": {
            "Action_S-F3.1_Text": _if3("Forecast Accuracy %", "lt", 0.55, 0.65, 0.75,
                "S-F3.1", "Forecast Quality Orchestration", "s_and_op_lead",
                "0.0%", "Identify forecast error sources", "Recalibrate models", "Review accuracy monthly"),
            "Action_S-F3.2_Text": _if3("Forecast Bias %", "abs_gt", 0.30, 0.20, 0.10,
                "S-F3.2", "Forecast Bias Correction", "s_and_op_lead",
                "+0.0%;-0.0%", "Quantify systematic bias", "Adjust demand signals", "Review bias monthly"),
            "Action_S-F3.3_Text": _if3("Service Impact %", "gt", 0.08, 0.05, 0.02,
                "S-F3.3", "Forecast-Driven Service Impact", "s_and_op_lead",
                "0.0%", "Identify impacted SKUs", "Emergency stock deployment", "Review monthly"),
            "Action_S-F3.4_Text": _if3("Plans Count", "gt", 10, 6, 3,
                "S-F3.4", "Re-Planning Discipline", "s_and_op_lead",
                "#,0", "Identify re-plan root causes", "Stabilise demand signals", "Monitor weekly"),
            "Action_S-I1.1_Text": _if3("Days in Inventory", "gt", 70, 62, 55,
                "S-I1.1", "Inventory Orchestration", "head_of_supply_chain",
                "0.0", "Identify excess inventory locations", "Initiate destocking", "Review DIO monthly"),
            "Action_S-I1.2_Text": _if3("Days in Inventory", "gt", 60, 40, 20,
                "S-I1.2", "Inventory Working Capital", "head_of_supply_chain",
                "0.0", "Identify high-DIO SKUs", "Reduce safety stock", "Monitor DIO monthly"),
            "Action_S-I1.3_Text": _if3("Stockout Rate %", "gt", 0.10, 0.05, 0.02,
                "S-I1.3", "Stockout Reduction", "head_of_supply_chain",
                "0.0%", "Identify stockout-prone SKUs", "Emergency replenishment", "Review weekly"),
            "Action_S-I1.4_Text": _if3("Obsolete Inventory %", "gt", 0.20, 0.10, 0.05,
                "S-I1.4", "Obsolete Inventory Disposal", "head_of_supply_chain",
                "0.0%", "Identify obsolescence categories", "Execute disposal or markdown", "Review monthly"),
            "Action_S-I1.5_Text": _if3("Forecast Accuracy %", "lt", 0.50, 0.60, 0.70,
                "S-I1.5", "Forecast-Driven Inventory Risk", "s_and_op_lead",
                "0.0%", "Identify accuracy-risk SKUs", "Increase safety stock", "Review accuracy monthly"),
            "Action_S-R2.1_Text": _if3("OTIF %", "lt", 0.90, 0.93, 0.96,
                "S-R2.1", "OTIF Orchestration", "head_of_supply_chain",
                "0.0%", "Identify OTIF-failing suppliers", "Escalate and correct", "Review OTIF weekly"),
            "Action_S-R2.2_Text": _if3("On-Time %", "lt", 0.90, 0.94, 0.97,
                "S-R2.2", "On-Time Delivery Recovery", "head_of_supply_chain",
                "0.0%", "Identify late delivery causes", "Expedite priority orders", "Review weekly"),
            "Action_S-R2.3_Text": _if3("Stockout Impact %", "gt", 0.10, 0.06, 0.03,
                "S-R2.3", "Stockout Impact Containment", "head_of_supply_chain",
                "0.0%", "Identify impacted customers", "Alternative sourcing", "Review weekly"),
            "Action_S-R2.4_Text": _if3("Penalty Amount", "gt", 50000, 25000, 10000,
                "S-R2.4", "Supplier Penalty Reduction", "head_of_supply_chain",
                "€#,0", "Identify penalty-triggering suppliers", "Negotiate SLA terms", "Review monthly"),
            "Action_S-R2.5_Text": _if3("Expedite Cost Amount", "gt", 100000, 50000, 25000,
                "S-R2.5", "Expedite Cost Reduction", "head_of_supply_chain",
                "€#,0", "Identify expedite drivers", "Reduce last-minute orders", "Monitor monthly"),
        },
        "active_actions": [
            "Action_S-I1.1_Text", "Action_S-I1.2_Text", "Action_S-I1.3_Text", "Action_S-I1.4_Text",
            "Action_S-R2.1_Text", "Action_S-R2.2_Text", "Action_S-R2.3_Text",
            "Action_S-F3.1_Text", "Action_S-F3.2_Text", "Action_S-F3.4_Text",
        ],
        "narrative_dax": (
            "VAR _otif = [OTIF %] "
            "VAR _ot = [On-Time %] "
            "VAR _inf = [In-Full %] "
            "VAR _dio = [Days in Inventory] "
            "VAR _acc = [Forecast Accuracy %] "
            "VAR _stk = [Stockout Rate %] "
            "RETURN "
            "\"OTIF: \" & FORMAT ( _otif, \"0.0%\" ) & \"  =  On-Time: \" & FORMAT ( _ot, \"0.0%\" ) & \"  x  In-Full: \" & FORMAT ( _inf, \"0.0%\" ) & UNICHAR ( 10 ) & "
            "\"DIO: \" & FORMAT ( _dio, \"0.0\" ) & \"d  |  Forecast Acc.: \" & FORMAT ( _acc, \"0.0%\" ) & \"  |  Stockout: \" & FORMAT ( _stk, \"0.0%\" )"
        ),
    },
    "Experience.SemanticModel": {
        "replacements": {
            "Action_X-E3.2_Text": _if3("Enterprise Value-at-Risk Index", "gt", 0.7, 0.5, 0.3,
                "X-E3.2", "Cross-Domain Risk Prioritisation", "head_of_enterprise_controlling",
                "0.000", "Identify highest-risk KPIs", "Escalate to steering", "Review risk index monthly"),
            "Action_X-E3.3_Text": _if3("Action Effectiveness Delta (XD)", "lt", -0.3, -0.2, -0.1,
                "X-E3.3", "Strategy Execution Monitoring", "head_of_enterprise_controlling",
                "+0.000;-0.000", "Identify underperforming actions", "Review execution quality", "Escalate failures"),
            "Action_X-R2.1_Text": _if_band("Utilization %", 0.55, 0.60, 0.65, 0.95, 0.92, 0.90,
                "X-R2.1", "Resource Utilization Rebalancing", "head_of_workforce_management",
                "0.0%", "Identify over/under-utilized teams", "Rebalance scheduling", "Review weekly"),
            "Action_X-R2.2_Text": _if_band("Occupancy %", 0.55, 0.60, 0.65, 0.95, 0.92, 0.90,
                "X-R2.2", "Occupancy Optimisation", "head_of_workforce_management",
                "0.0%", "Identify occupancy outliers", "Adjust staffing plan", "Monitor daily"),
            "Action_X-R2.3_Text": _if3("Shrinkage %", "gt", 0.35, 0.30, 0.25,
                "X-R2.3", "Shrinkage Reduction", "head_of_workforce_management",
                "0.0%", "Identify shrinkage categories", "Address scheduling and absence", "Review monthly"),
            "Action_X-R2.4_Text": _if3("Overtime %", "gt", 0.18, 0.12, 0.08,
                "X-R2.4", "Overtime Containment", "head_of_workforce_management",
                "0.0%", "Identify overtime drivers", "Adjust headcount or schedule", "Review weekly"),
        },
        "new_measures": [
            {
                "name": "Action_X-S1.1_Text",
                "comment": "/// ActionReady Logic: X-S1.1 - Service Level Orchestration",
                "dax": _if3("SLA Attainment %", "lt", 0.88, 0.92, 0.95,
                    "X-S1.1", "Service Level Orchestration", "head_of_service_operations",
                    "0.0%", "Identify SLA-breaching queues", "Redeploy to breaching teams", "Review SLA daily"),
                "format": "@",
                "folder": "9_ActionReady_Logic",
                "ac_id": "X-S1.1",
            },
            {
                "name": "Action_X-S1.3_Text",
                "comment": "/// ActionReady Logic: X-S1.3 - FCR Improvement Programme",
                "dax": _if3("First Contact Resolution %", "lt", 0.55, 0.65, 0.75,
                    "X-S1.3", "FCR Improvement Programme", "head_of_service_operations",
                    "0.0%", "Analyse repeat-contact causes", "Implement agent coaching", "Review FCR weekly"),
                "format": "@",
                "folder": "9_ActionReady_Logic",
                "ac_id": "X-S1.3",
            },
        ],
        "active_actions": [
            "Action_X-S1.1_Text", "Action_X-S1.3_Text",
            "Action_X-R2.1_Text", "Action_X-R2.2_Text", "Action_X-R2.3_Text", "Action_X-R2.4_Text",
            "Action_X-E3.2_Text", "Action_X-E3.3_Text",
        ],
        "narrative_dax": (
            "VAR _sla = [SLA Attainment %] "
            "VAR _fcr = [First Contact Resolution %] "
            "VAR _aht = [Average Handling Time (minutes)] "
            "VAR _util = [Utilization %] "
            "VAR _shrink = [Shrinkage %] "
            "VAR _clv = [CLV (Customer Lifetime Value)] "
            "RETURN "
            "\"SLA: \" & FORMAT ( _sla, \"0.0%\" ) & \"  |  FCR: \" & FORMAT ( _fcr, \"0.0%\" ) & \"  |  AHT: \" & FORMAT ( _aht, \"0.0\" ) & \"min\" & UNICHAR ( 10 ) & "
            "\"Utilization: \" & FORMAT ( _util, \"0.0%\" ) & \"  |  Shrinkage: \" & FORMAT ( _shrink, \"0.0%\" ) & \"  |  CLV: €\" & FORMAT ( _clv, \"#,0\" )"
        ),
    },
}


# ── TMDL patching ─────────────────────────────────────────────────────────────

# Matches: `\tmeasure 'Name' = <any non-newline chars>\n`
_MEASURE_LINE = re.compile(r"(\tmeasure '([^']+)' = )([^\n]+)(\n)")


def _build_active_actions_dax(names: list) -> str:
    refs = ", ".join(f"[{n}]" for n in names)
    ok_msg = f"{_CHECK} All KPIs within tolerance {_DASH} no actions triggered."
    return (
        f"VAR _rows = FILTER ( {{ {refs} }}, NOT ISBLANK ( [Value] ) ) "
        f"VAR _result = CONCATENATEX ( _rows, [Value], UNICHAR ( 10 ) & UNICHAR ( 10 ) ) "
        f"RETURN IF ( ISBLANK ( _result ), \"{ok_msg}\", _result )"
    )


def _new_measure_block(name, dax, fmt, folder, comment="", annotations=None):
    tag = str(uuid.uuid4())
    lines = []
    if comment:
        lines.append(f"\t{comment}")
    lines.append(f"\tmeasure '{name}' = {dax}")
    lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tisHidden")
    lines.append(f"\t\tdisplayFolder: {folder}")
    lines.append(f"\t\tlineageTag: {tag}")
    if annotations:
        for k, v in annotations.items():
            lines.append(f"")
            lines.append(f"\t\tannotation {k} = \"{v}\"")
    lines.append("")
    return "\n".join(lines) + "\n"


def upgrade_model(model_name: str, cfg: dict) -> None:
    path = DIST / model_name / "definition" / "tables" / "_Measures.tmdl"
    if not path.exists():
        print(f"  SKIP {model_name}: file not found")
        return

    text = path.read_text(encoding="utf-8")
    replacements = cfg.get("replacements", {})
    replaced = 0

    for name, new_dax in replacements.items():
        # Match the measure line: \tmeasure 'Name' = <old dax>\n
        pat = re.compile(
            r"(\tmeasure '" + re.escape(name) + r"' = )([^\n]+)(\n)",
        )
        m = pat.search(text)
        if not m:
            print(f"    WARN: measure '{name}' not found in {model_name}")
            continue
        text = pat.sub(r"\g<1>" + new_dax.replace("\\", "\\\\") + r"\g<3>", text, count=1)
        replaced += 1

    # Insert new measures (e.g. XD model missing X-S1.x)
    for nm in cfg.get("new_measures", []):
        block = _new_measure_block(
            nm["name"], nm["dax"], nm["format"], nm["folder"],
            comment=nm.get("comment", ""),
            annotations={"ActionReady_ActionCodeId": nm["ac_id"]},
        )
        # Insert just before the column Column1 section
        text = text.replace("\tcolumn Column1\n", block + "\tcolumn Column1\n", 1)

    # Append Narrative Text measure
    narr_block = _new_measure_block(
        "Narrative Text",
        cfg["narrative_dax"],
        "@",
        "0_Summary",
        comment="/// Purpose: Dynamic KPI summary string for the Detail page narrative header.",
    )

    # Append Active Actions Text measure
    active_dax = _build_active_actions_dax(cfg["active_actions"])
    active_block = _new_measure_block(
        "Active Actions Text",
        active_dax,
        "@",
        "0_Summary",
        comment="/// Purpose: Concatenates all currently triggered action recommendations.",
    )

    # Insert both before \tcolumn Column1
    insert = narr_block + active_block
    text = text.replace("\tcolumn Column1\n", insert + "\tcolumn Column1\n", 1)

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  OK  {model_name}: {replaced} measures replaced, +Narrative Text, +Active Actions Text")


# ── Visual upgrades ───────────────────────────────────────────────────────────

# Maps report prefix → SemanticModel name (for Active Actions Text binding)
REPORT_MODEL = {
    "COM": "Commercial.SemanticModel",
    "FIN": "Finance.SemanticModel",
    "OPS": "Operations.SemanticModel",
    "SCM": "SupplyChain.SemanticModel",
    "XD":  "Experience.SemanticModel",
}


def _card_visual(base: dict, entity: str, measure_name: str) -> dict:
    """Return a cardVisual visual.json dict bound to a single measure."""
    base["visual"]["visualType"] = "cardVisual"
    base["visual"].pop("objects", None)
    base["visual"]["query"] = {
        "queryState": {
            "Data": {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {"SourceRef": {"Entity": entity}},
                                "Property": measure_name,
                            }
                        },
                        "queryRef": f"{entity}.{measure_name}",
                        "nativeQueryRef": measure_name,
                    }
                ]
            }
        }
    }
    return base


def upgrade_visuals() -> None:
    reports = list(DIST.glob("*.Report"))
    sn_ok = ap_ok = 0

    for report in sorted(reports):
        prefix = report.stem.split("-")[0].split("_")[0]
        # Smart_Narrative: textbox → smartNarrativeVisual
        for sn_path in report.rglob("Smart_Narrative/visual.json"):
            data = json.loads(sn_path.read_text(encoding="utf-8"))
            v = data["visual"]
            if v.get("visualType") == "textbox":
                v["visualType"] = "smartNarrativeVisual"
                v.pop("objects", None)
                # smartNarrativeVisual auto-reads page data; no query needed
                v.pop("query", None)
                sn_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
                sn_ok += 1

        # ActionPanel: textbox → cardVisual bound to Active Actions Text
        for ap_path in report.rglob("ActionPanel/visual.json"):
            data = json.loads(ap_path.read_text(encoding="utf-8"))
            v = data["visual"]
            if v.get("visualType") == "textbox":
                data = _card_visual(data, "_Measures", "Active Actions Text")
                ap_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
                ap_ok += 1

    print(f"  Smart_Narrative upgraded: {sn_ok}")
    print(f"  ActionPanel upgraded:     {ap_ok}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== Upgrading SemanticModel measures ===")
    for model_name, cfg in CONFIGS.items():
        upgrade_model(model_name, cfg)

    print("\n=== Upgrading report visuals ===")
    upgrade_visuals()
    print("\nDone.")


if __name__ == "__main__":
    main()
