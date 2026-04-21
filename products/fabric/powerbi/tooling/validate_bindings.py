#!/usr/bin/env python3
"""
validate_bindings.py — Post-generation binding validation for PBIP reports.

Checks that all report visuals have proper field bindings (no empty projections
on chart visuals) and that required slots exist on each page.

Usage:
    python3 validate_bindings.py [--dist-dir <path>] [--strict]

Exit code 0 = all reports pass. Exit code 1 = one or more failures.
Designed for CI integration (Azure Pipelines, GitHub Actions).
"""
import json
import glob
import argparse
import sys
from pathlib import Path

# Visual types that MUST have at least one projection to be useful
BOUND_REQUIRED_TYPES = {"lineChart", "clusteredBarChart", "barChart", "waterfallChart",
                        "stackedBarChart", "hundredPercentStackedBarChart", "clusteredColumnChart",
                        "scatterChart", "funnelChart", "tableEx", "matrixVisual"}

# Visuals that are intentionally unbound (text containers, shapes)
UNBOUND_ALLOWED_TYPES = {"textbox", "image", "shape", "actionButton"}

# Required slot IDs per page type
REQUIRED_OVERVIEW_SLOTS = {"KPI_Cards", "Main_1", "Main_2", "Slicer_Date"}
REQUIRED_DETAIL_SLOTS = {"Detail_Matrix", "Smart_Narrative", "ActionPanel"}


def count_projections(query_state: dict) -> int:
    """Count total field projections across all query buckets."""
    return sum(
        len(bucket.get("projections", []))
        for bucket in query_state.values()
        if isinstance(bucket, dict)
    )


def validate_report(report_dir: Path, strict: bool = False) -> list[str]:
    """Validate a single .Report folder. Returns list of error strings."""
    errors = []
    report_name = report_dir.name.replace(".Report", "")

    page_dirs = sorted((report_dir / "definition" / "pages").glob("Page_*"))
    if not page_dirs:
        errors.append(f"{report_name}: No pages found in definition/pages/")
        return errors

    for page_dir in page_dirs:
        page_id = page_dir.name
        is_overview = "Overview" in page_id
        is_detail = "Detail" in page_id

        # Collect all visual names on this page
        visual_dirs = sorted(page_dir.glob("visuals/*/"))
        visual_names = {vd.name for vd in visual_dirs}

        # Check required slots
        if is_overview:
            missing = REQUIRED_OVERVIEW_SLOTS - visual_names
            if missing:
                errors.append(f"{report_name}/{page_id}: Missing required slots: {sorted(missing)}")
        if is_detail:
            missing = REQUIRED_DETAIL_SLOTS - visual_names
            if missing:
                errors.append(f"{report_name}/{page_id}: Missing required slots: {sorted(missing)}")

        # Check each visual's binding
        for vd in visual_dirs:
            vf = vd / "visual.json"
            if not vf.exists():
                continue
            try:
                visual = json.loads(vf.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{report_name}/{page_id}/{vd.name}: Invalid JSON — {e}")
                continue

            vtype = visual.get("visual", {}).get("visualType", "?")
            qs = visual.get("visual", {}).get("query", {}).get("queryState", {})
            proj_count = count_projections(qs)

            # Binding check: chart/table visuals must have projections
            if vtype in BOUND_REQUIRED_TYPES and proj_count == 0:
                # Slicer on Detail page may have 0 projections if empty (non-blocking in non-strict mode)
                level = "ERROR" if strict else "WARN"
                errors.append(
                    f"[{level}] {report_name}/{page_id}/{vd.name}: "
                    f"visualType={vtype} has 0 projections — visual will render empty"
                )

            # Type sanity: chart slots should not be tableEx (except Detail_Matrix)
            if vd.name in ("Main_1", "Main_2", "Main_3") and vtype == "tableEx":
                errors.append(
                    f"[ERROR] {report_name}/{page_id}/{vd.name}: "
                    f"chart slot has visualType=tableEx — should be lineChart/barChart"
                )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate PBIP report visual bindings")
    parser.add_argument("--dist-dir", default=None,
                        help="Path to dist/ folder containing .Report directories")
    parser.add_argument("--strict", action="store_true",
                        help="Treat WARNINGs as ERRORs (fail on any unbound visual)")
    parser.add_argument("--report", default=None,
                        help="Validate only a specific use case ID (e.g. FIN-001)")
    parser.add_argument("--domain", default=None,
                        help="Filter to reports belonging to a domain prefix (e.g. Commercial → COM-*, Finance → FIN-*)")
    args = parser.parse_args()

    # Resolve dist dir
    if args.dist_dir:
        dist_dir = Path(args.dist_dir)
    else:
        # Auto-detect: walk up from this script to find products/fabric/powerbi/dist
        script_dir = Path(__file__).parent
        candidates = [
            script_dir.parent / "dist",
            script_dir.parent.parent / "dist",
            script_dir / "dist",
        ]
        dist_dir = next((c for c in candidates if c.exists()), None)
        if not dist_dir:
            print("ERROR: Cannot find dist/ directory. Use --dist-dir to specify it.", file=sys.stderr)
            sys.exit(1)

    # Domain → report prefix mapping
    DOMAIN_PREFIXES = {
        "Commercial": "COM-",
        "Experience": ["XD-", "SVC-"],
        "Finance": "FIN-",
        "Operations": "OPS-",
        "SupplyChain": "SCM-",
    }

    report_dirs = sorted(dist_dir.glob("*.Report"))
    if args.domain:
        prefixes = DOMAIN_PREFIXES.get(args.domain)
        if prefixes is None:
            print(f"ERROR: Unknown domain '{args.domain}'. Valid: {list(DOMAIN_PREFIXES)}", file=sys.stderr)
            sys.exit(1)
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        report_dirs = [r for r in report_dirs if any(r.name.startswith(p) for p in prefixes)]
    if args.report:
        report_dirs = [r for r in report_dirs if args.report in r.name]

    if not report_dirs:
        print(f"No .Report directories found in {dist_dir}", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    warn_count = 0
    error_count = 0

    print(f"Validating {len(report_dirs)} report(s) in {dist_dir}\n")

    for report_dir in report_dirs:
        errors = validate_report(report_dir, strict=args.strict)
        name = report_dir.name.replace(".Report", "")
        if not errors:
            print(f"  ✅ {name}")
        else:
            for e in errors:
                is_warn = e.startswith("[WARN]")
                print(f"  {'⚠' if is_warn else '❌'} {e}")
                if is_warn:
                    warn_count += 1
                else:
                    error_count += 1
        all_errors.extend(errors)

    print(f"\n{'='*60}")
    blocking = [e for e in all_errors if not e.startswith("[WARN]")]
    warnings = [e for e in all_errors if e.startswith("[WARN]")]
    print(f"Result: {len(report_dirs)} reports | "
          f"{error_count} errors | {warn_count} warnings")

    if blocking:
        print(f"\n❌ FAILED — {len(blocking)} blocking error(s) found.")
        sys.exit(1)
    elif warnings and args.strict:
        print(f"\n❌ FAILED (strict mode) — {len(warnings)} warning(s) treated as errors.")
        sys.exit(1)
    else:
        print(f"\n✅ PASSED — All reports have valid bindings.")
        sys.exit(0)


if __name__ == "__main__":
    main()
