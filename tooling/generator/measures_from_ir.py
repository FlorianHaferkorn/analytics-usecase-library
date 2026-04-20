"""
measures_from_ir.py — Phase 2 IR entry point.

Compiles a UseCase_Bracket.yaml to a DashboardSpec via BracketCompiler and
emits a TMDL _Measures.tmdl file via the PBIPAdapter.  Replaces direct YAML
parsing in Phase 2 of the orchestrator pipeline.

Usage (from repo root):
    python3 tooling/generator/measures_from_ir.py \\
        --bracket core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml \\
        --out products/fabric/powerbi/dist/Commercial.SemanticModel/definition/tables/_Measures.tmdl

    # Multiple brackets → shared domain model (measures deduplicated)
    python3 tooling/generator/measures_from_ir.py \\
        --bracket core/usecases/core/COM-001.../UseCase_Bracket.yaml \\
        --bracket core/usecases/core/COM-002.../UseCase_Bracket.yaml \\
        --out products/fabric/powerbi/dist/Commercial.SemanticModel/definition/tables/_Measures.tmdl

Exit codes:
    0  success
    1  missing bracket or catalog
    2  compiler warnings (soft errors); output still written
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional


def _repo_root_from_script() -> Path:
    """Derive repo root: tooling/generator/measures_from_ir.py → 2 levels up."""
    return Path(__file__).resolve().parents[2]


def _ensure_sys_path(repo_root: Path) -> None:
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _build_tmdl(measures, table_name: str = "_Measures") -> str:
    """Emit TMDL for a list of MeasureSpec objects."""
    from products.fabric.powerbi.tooling.adapters.pbip import _build_tmdl_measures
    raw = _build_tmdl_measures(measures)
    # _build_tmdl_measures emits "table _Measures" header; re-label if needed
    if table_name != "_Measures":
        raw = raw.replace("table _Measures", f"table {table_name}", 1)
        raw = raw.replace("partition _Measures", f"partition {table_name}", 1)
        raw = raw.replace("isHidden _Measures", f"isHidden {table_name}", 1)
    return raw


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 2: compile bracket(s) to DashboardSpec and emit _Measures.tmdl.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--bracket",
        dest="brackets",
        action="append",
        required=True,
        metavar="PATH",
        help="Path to UseCase_Bracket.yaml (repeatable for shared model)",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Destination _Measures.tmdl path",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-detected from script location)",
    )
    parser.add_argument(
        "--kpi-catalog",
        type=Path,
        default=None,
        help="KPI catalog root (default: <repo-root>/core/kpi_catalog)",
    )
    parser.add_argument(
        "--action-codes",
        type=Path,
        default=None,
        help="Action codes root (default: <repo-root>/core/action_codes)",
    )
    parser.add_argument(
        "--table-name",
        default="_Measures",
        help="TMDL table name (default: _Measures)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root) if args.repo_root else _repo_root_from_script()
    _ensure_sys_path(repo_root)

    kpi_catalog_root = Path(args.kpi_catalog) if args.kpi_catalog else repo_root / "core/kpi_catalog"
    action_codes_root = Path(args.action_codes) if args.action_codes else repo_root / "core/action_codes"

    if not kpi_catalog_root.is_dir():
        print(f"ERROR: KPI catalog root not found: {kpi_catalog_root}", file=sys.stderr)
        return 1

    from tooling.generator_core.ir.compiler import BracketCompiler

    compiler = BracketCompiler(
        kpi_catalog_root=kpi_catalog_root,
        action_codes_root=action_codes_root,
    )

    # Compile all brackets and collect measures (deduplicated by kpi_id)
    seen_kpi_ids: set = set()
    all_measures = []
    exit_code = 0

    for bracket_path_str in args.brackets:
        bracket_path = Path(bracket_path_str)
        if not bracket_path.exists():
            print(f"ERROR: bracket not found: {bracket_path}", file=sys.stderr)
            return 1

        spec = compiler.compile(bracket_path)

        if compiler.warnings:
            exit_code = 2
            for w in compiler.warnings:
                print(f"WARNING [{bracket_path.parent.name}]: {w}", file=sys.stderr)

        for m in spec.measures:
            if m.kpi_id not in seen_kpi_ids:
                seen_kpi_ids.add(m.kpi_id)
                all_measures.append(m)

        print(
            f"  Compiled {bracket_path.parent.name}: "
            f"{len(spec.measures)} measures "
            f"({len(compiler.warnings)} warning(s))",
            file=sys.stderr,
        )

    if not all_measures:
        print("WARNING: no measures collected from bracket(s)", file=sys.stderr)
        return exit_code

    tmdl_text = _build_tmdl(all_measures, table_name=args.table_name)

    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tmdl_text, encoding="utf-8")

    print(
        f"Generated {out_path} — {len(all_measures)} measure(s) "
        f"from {len(args.brackets)} bracket(s)"
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
