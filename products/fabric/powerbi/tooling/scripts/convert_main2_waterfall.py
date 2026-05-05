"""Convert Main_2 clusteredBarChart → waterfallChart in 14 PBIR reports.

Run from repo root:
  python3 products/fabric/powerbi/tooling/scripts/convert_main2_waterfall.py
"""

import json
import sys
from pathlib import Path

DIST = Path("products/fabric/powerbi/dist")

# (entity, property) tuple for column projections
# ("_Measures", name) tuple for measure projections
CONVERSIONS: dict[str, dict] = {
    "COM-002_Margin_Price_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Price Effect Amount"),
            ("_Measures", "Volume Effect Amount"),
            ("_Measures", "Mix Effect Amount"),
        ],
    },
    "COM-003_Customer_Value": {
        "category": ("dim_org", "Entity"),
        "y_measures": [
            ("_Measures", "CLV (Customer Lifetime Value)"),
        ],
    },
    "COM-004_Promotion_Effectiveness": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Incremental Gross Margin Amount"),
            ("_Measures", "Promo Cost"),
            ("_Measures", "Cannibalized Sales Amount"),
        ],
    },
    "FIN-001_Cash_Liquidity_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Operating Cash Flow"),
        ],
    },
    "FIN-002_Cost_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "OpEx vs Plan %"),
            ("_Measures", "Material Cost %"),
            ("_Measures", "Labor Productivity %"),
        ],
    },
    "OPS-001_Operations_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "OEE %"),
            ("_Measures", "Availability %"),
            ("_Measures", "Performance %"),
            ("_Measures", "Quality %"),
        ],
    },
    "OPS-002_Asset_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Downtime %"),
            ("_Measures", "Unplanned Downtime %"),
            ("_Measures", "PM Compliance %"),
        ],
    },
    "OPS-003_Quality_Yield": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Rework Rate %"),
            ("_Measures", "Scrap Rate %"),
            ("_Measures", "Complaint Rate %"),
        ],
    },
    "SCM-001_Inventory_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Stockout Rate %"),
            ("_Measures", "Obsolete Inventory %"),
        ],
    },
    "SCM-002_Supply_Reliability_OTIF": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "OTIF %"),
            ("_Measures", "On-Time %"),
            ("_Measures", "In-Full %"),
        ],
    },
    "SCM-003_Forecast_vs_Actual": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Forecast Bias %"),
            ("_Measures", "Forecast MAPE %"),
        ],
    },
    "XD-001_Service_Level_Performance": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "SLA Attainment %"),
            ("_Measures", "First Contact Resolution %"),
            ("_Measures", "Escalation %"),
        ],
    },
    "XD-002_Resource_Utilization": {
        "category": ("dim_date", "CalendarYearMonth"),
        "y_measures": [
            ("_Measures", "Utilization %"),
            ("_Measures", "Occupancy %"),
            ("_Measures", "Shrinkage %"),
        ],
    },
    "XD-003_Executive_KPI_Overview": {
        "category": ("dim_org", "Entity"),
        "y_measures": [
            ("_Measures", "CLV (Customer Lifetime Value)"),
        ],
    },
}


def _col_projection(entity: str, prop: str) -> dict:
    qref = f"{entity}.{prop}"
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop,
            }
        },
        "queryRef": qref,
        "nativeQueryRef": prop,
    }


def _meas_projection(entity: str, name: str) -> dict:
    qref = f"{entity}.{name}"
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": name,
            }
        },
        "queryRef": qref,
        "nativeQueryRef": name,
    }


def convert(report_stem: str, cfg: dict) -> bool:
    report_dir = DIST / f"{report_stem}.Report"
    pages_dir = report_dir / "definition" / "pages"

    # Find the page that contains a Main_2 directory
    main2_dirs = list(pages_dir.glob("*/visuals/Main_2"))
    if not main2_dirs:
        print(f"  SKIP {report_stem}: no Main_2 directory found")
        return False

    path = main2_dirs[0] / "visual.json"
    data = json.loads(path.read_text())

    cat_entity, cat_prop = cfg["category"]
    cat_proj = _col_projection(cat_entity, cat_prop)

    y_projs = [_meas_projection(ent, name) for ent, name in cfg["y_measures"]]

    data["visual"]["visualType"] = "waterfallChart"
    data["visual"]["query"]["queryState"]["Category"]["projections"] = [cat_proj]
    data["visual"]["query"]["queryState"]["Y"]["projections"] = y_projs

    # Keep only categoryAxis (remove clusteredBarChart-specific layout/dataLabels)
    objects = data["visual"].get("objects", {})
    waterfall_objects = {}
    if "categoryAxis" in objects:
        waterfall_objects["categoryAxis"] = objects["categoryAxis"]
    data["visual"]["objects"] = waterfall_objects

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    measures_str = ", ".join(m for _, m in cfg["y_measures"])
    print(f"  OK  {report_stem}: {cat_entity}.{cat_prop} | {measures_str}")
    return True


def main() -> None:
    if not DIST.exists():
        sys.exit(f"ERROR: dist directory not found at {DIST}. Run from repo root.")

    print(f"Converting {len(CONVERSIONS)} reports …")
    ok = 0
    for stem, cfg in CONVERSIONS.items():
        if convert(stem, cfg):
            ok += 1
    print(f"\n{ok}/{len(CONVERSIONS)} reports converted.")


if __name__ == "__main__":
    main()
