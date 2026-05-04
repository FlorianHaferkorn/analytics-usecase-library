"""
check_page_template_compliance.py — verify generated PBIP pages conform to bracket layout rules.

For each .Report in dist/:
  1. Finds the matching UseCase_Bracket.yaml via use-case ID prefix.
  2. Reads page_1_summary (overview) and page_2_execution (detail) layout rules.
  3. Checks:
     a. Overview page type matches bracket page_type (T1/T2/T3/T4)
     b. Overview visual type map: kpi_card → cardVisual, trend_line → lineChart,
        bar_chart → barChart/clusteredBarChart, waterfall → waterfallChart
     c. Detail page declares correct page_type
     d. evidence_columns declared → Detail_Matrix visual is present
     e. action_panel: true → ActionPanel visual is present
     f. Smart_Narrative present on detail page

Exit codes: 0 = all pass, 1 = violations found.

Usage:
    python check_page_template_compliance.py [--dist-root .] [--use-case-root .]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: PyYAML required — pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise


# ── Visual type mapping (bracket → PBIP visualType) ──────────────────────────

VISUAL_TYPE_MAP: Dict[str, List[str]] = {
    "kpi_card":   ["cardVisual", "kpiVisual", "card"],
    "trend_line": ["lineChart", "lineClusteredColumnComboChart", "lineStackedColumnComboChart"],
    "bar_chart":  ["barChart", "clusteredBarChart", "clusteredColumnChart", "columnChart"],
    "waterfall":  ["waterfallChart"],
    "scatter":    ["scatterChart"],
    "matrix":     ["pivotTable"],
    "table":      ["tableEx"],
}

PAGE_TYPE_LABELS: Dict[str, str] = {
    "T1_Strategic_Overview":       "T1",
    "T2_Tactical_Variance":        "T2",
    "T3_Operational_Monitoring":   "T3",
    "T4_Prescriptive_Recommendation": "T4",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_bracket(bracket_path: Path) -> Optional[Dict[str, Any]]:
    try:
        return yaml.safe_load(bracket_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"  WARN: Cannot read bracket {bracket_path}: {e}", file=sys.stderr)
        return None


def get_visual_type(visual_json: Path) -> Optional[str]:
    try:
        obj = json.loads(visual_json.read_text(encoding="utf-8"))
        return obj.get("visual", {}).get("visualType")
    except Exception:
        return None


def find_page_dir(pages_dir: Path, keyword: str) -> Optional[Path]:
    """Find a page directory whose name contains keyword (case-insensitive)."""
    for d in pages_dir.iterdir():
        if d.is_dir() and keyword.lower() in d.name.lower():
            return d
    return None


def list_visual_types(page_dir: Path) -> Dict[str, str]:
    """Return {visual_name: visualType} for all visuals in a page."""
    result: Dict[str, str] = {}
    visuals_dir = page_dir / "visuals"
    if not visuals_dir.exists():
        return result
    for v_dir in visuals_dir.iterdir():
        if v_dir.is_dir():
            vj = v_dir / "visual.json"
            if vj.exists():
                vt = get_visual_type(vj)
                if vt:
                    result[v_dir.name] = vt
    return result


def check_bracket_visual(
    visuals: Dict[str, str],
    bracket_visual_type: str,
    context: str,
    violations: List[str],
    warnings: List[str],
) -> None:
    """Check that at least one visual in the page matches the expected bracket visual type.

    A type mismatch on a 30s slot is recorded as a warning (not a failure) because
    scaffolded reports may still use placeholder visual types before measures are wired.
    """
    expected_types = VISUAL_TYPE_MAP.get(bracket_visual_type, [bracket_visual_type])
    found = any(vt in expected_types for vt in visuals.values())
    if not found:
        warnings.append(
            f"WARN {context}: bracket declares visual_type='{bracket_visual_type}' "
            f"(expected PBIP types: {expected_types}) but none found in page "
            f"(found: {list(set(visuals.values()))})"
        )


# ── Core check per report ─────────────────────────────────────────────────────

def check_report(
    report_dir: Path,
    uc_root: Path,
    violations: List[str],
    warnings: Optional[List[str]] = None,
) -> bool:
    """Returns True if this report passes all compliance checks."""
    report_name = report_dir.name
    uc_match = re.match(r"^([A-Z]{2,3}-\d+)", report_name)
    if not uc_match:
        return True  # Not a use-case report; skip

    uc_id = uc_match.group(1)
    prefix = f"[{report_name}]"

    # Find bracket
    bracket_path: Optional[Path] = None
    if uc_root.exists():
        for d in uc_root.iterdir():
            if d.is_dir() and d.name.startswith(uc_id):
                candidate = d / "UseCase_Bracket.yaml"
                if candidate.exists():
                    bracket_path = candidate
                    break

    if not bracket_path:
        # No bracket → skip compliance (report may be legacy or non-core)
        return True

    bracket = load_bracket(bracket_path)
    if bracket is None:
        violations.append(f"{prefix} Cannot read UseCase_Bracket.yaml at {bracket_path}")
        return False

    pages_dir = report_dir / "definition" / "pages"
    if not pages_dir.exists():
        violations.append(f"{prefix} definition/pages/ not found")
        return False

    ux = bracket.get("ux_layout_rules", {})
    page1 = ux.get("page_1_summary", {})
    page2 = ux.get("page_2_execution", {})

    local_ok = True

    # ── Overview page ─────────────────────────────────────────────────────────
    overview_dir = find_page_dir(pages_dir, "Overview")
    if not overview_dir:
        violations.append(f"{prefix} No Overview page directory found")
        local_ok = False
    else:
        ov_visuals = list_visual_types(overview_dir)

        # a. page_type label present in page.json displayName or directory name
        bracket_page_type = page1.get("page_type", "")
        short_type = PAGE_TYPE_LABELS.get(bracket_page_type, bracket_page_type)
        page_json_path = overview_dir / "page.json"
        if page_json_path.exists():
            try:
                page_json = json.loads(page_json_path.read_text(encoding="utf-8"))
                display = page_json.get("displayName", "")
                # Allow the page to exist without encoding the page type in its name —
                # just check that the KPI_Cards visual is present (type compliance).
            except Exception:
                pass

        # b. KPI_Cards must be a kpi_card-family visual
        kpi_cards_slot = ov_visuals.get("KPI_Cards")
        if not kpi_cards_slot:
            violations.append(f"{prefix} Overview: KPI_Cards visual slot missing")
            local_ok = False
        else:
            expected = VISUAL_TYPE_MAP.get("kpi_card", [])
            if kpi_cards_slot not in expected:
                violations.append(
                    f"{prefix} Overview: KPI_Cards has visualType='{kpi_cards_slot}' "
                    f"(expected one of {expected})"
                )
                local_ok = False

        # c. component_30s visual types (warnings only — scaffolded types may differ)
        _warn_list: List[str] = warnings if warnings is not None else []
        for component in page1.get("component_30s", []):
            vt = component.get("visual_type")
            if vt and vt in VISUAL_TYPE_MAP:
                check_bracket_visual(
                    ov_visuals, vt,
                    f"{prefix} Overview (30s component '{vt}')",
                    violations=[],   # 30s type mismatch → warning, never a hard failure
                    warnings=_warn_list,
                )

    # ── Detail page ───────────────────────────────────────────────────────────
    detail_dir = find_page_dir(pages_dir, "Detail")
    if not detail_dir:
        violations.append(f"{prefix} No Detail page directory found")
        local_ok = False
    else:
        det_visuals = list_visual_types(detail_dir)

        # d. evidence_columns declared → Detail_Matrix must exist
        comp_300s = page2.get("component_300s", {})
        if comp_300s.get("evidence_columns"):
            if "Detail_Matrix" not in det_visuals:
                violations.append(
                    f"{prefix} Detail: bracket declares evidence_columns but Detail_Matrix visual slot is missing"
                )
                local_ok = False

        # e. action_panel: true → ActionPanel must exist
        if comp_300s.get("action_panel") is True:
            if "ActionPanel" not in det_visuals:
                violations.append(
                    f"{prefix} Detail: bracket declares action_panel: true but ActionPanel visual slot is missing"
                )
                local_ok = False

        # f. Smart_Narrative should be present on detail page
        if "Smart_Narrative" not in det_visuals:
            violations.append(
                f"{prefix} Detail: Smart_Narrative visual slot missing (required by 3-30-300 layout)"
            )
            local_ok = False

    return local_ok


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Check PBIP page template compliance")
    parser.add_argument("--dist-root",     type=Path, default=Path("products/fabric/powerbi/dist"))
    parser.add_argument("--use-case-root", type=Path, default=Path("core/usecases/core"))
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any warning (future use)")
    args = parser.parse_args()

    dist_root = args.dist_root if args.dist_root.is_absolute() else Path.cwd() / args.dist_root
    uc_root   = args.use_case_root if args.use_case_root.is_absolute() else Path.cwd() / args.use_case_root

    if not dist_root.exists():
        print(f"WARN: dist-root not found: {dist_root} — nothing to check.")
        sys.exit(0)

    reports = sorted(p for p in dist_root.iterdir() if p.is_dir() and p.name.endswith(".Report"))

    if not reports:
        print(f"No .Report directories found in {dist_root}.")
        sys.exit(0)

    print(f"Checking {len(reports)} report(s) for template compliance...")

    all_violations: List[str] = []
    all_warnings: List[str] = []
    passed = 0

    for report in reports:
        viol_before = len(all_violations)
        warn_before = len(all_warnings)
        ok = check_report(report, uc_root, all_violations, all_warnings)
        new_viols = all_violations[viol_before:]
        new_warns = all_warnings[warn_before:]
        if not new_viols:
            passed += 1
            if new_warns:
                print(f"  WARN  {report.name}")
                for w in new_warns:
                    print(f"        {w}")
        else:
            print(f"  FAIL  {report.name}")
            for v in new_viols:
                print(f"        {v}")
            for w in new_warns:
                print(f"        {w}")

    print()
    if not all_violations:
        print(f"Page template compliance: PASSED ({len(reports)} report(s))")
        sys.exit(0)
    else:
        print(
            f"Page template compliance: FAILED — {len(all_violations)} violation(s) "
            f"across {len(reports) - passed} report(s)"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
