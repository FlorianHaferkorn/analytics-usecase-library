"""
OSS Report Orchestrator — mirrors products/fabric/powerbi/orchestrator/ structure.

Drives the full OSS report generation pipeline for one or all use cases:
    Step 0  Preflight checks (shared generator_core.preflight)
    Step 1  Compile bracket YAML → DashboardSpec (shared generator_core.ir)
    Step 2  Select OSS adapter (Metabase / Grafana / Superset)
    Step 3  Render DashboardSpec → output files
    Step 4  Write files to dist/
    Step 5  Record telemetry (shared generator_core.intelligence)

Usage (from repo root):
    python products/oss/orchestrator/orchestrate_oss.py \\
        --bracket core/usecases/core/COM-001/UseCase_Bracket.yaml \\
        --adapter metabase \\
        --output products/oss/dist/

    python products/oss/orchestrator/orchestrate_oss.py \\
        --all --adapter grafana

Status: STUB — wire up once adapters are implemented.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="orchestrate_oss",
        description="OSS Report Orchestrator — compile bracket → OSS dashboard",
    )
    parser.add_argument("--bracket",  type=Path, help="Single UseCase_Bracket.yaml")
    parser.add_argument("--all",      action="store_true", help="Process all brackets")
    parser.add_argument(
        "--adapter",
        choices=["metabase", "grafana", "superset"],
        default="metabase",
        help="Target OSS tool (default: metabase)",
    )
    parser.add_argument("--output",   type=Path, default=Path("products/oss/dist"))
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    if not args.bracket and not args.all:
        parser.error("Provide --bracket <path> or --all")

    # Step 0: Preflight
    if not args.skip_preflight and args.bracket:
        from tooling.generator_core.preflight.validator import PreflightValidator
        validator = PreflightValidator(
            kpi_catalog_root=Path("core/kpi_catalog"),
            action_codes_root=Path("core/action_codes"),
        )
        report = validator.run(args.bracket)
        print(report.summary())
        if not report.passed:
            print("Preflight FAILED — generation aborted.", file=sys.stderr)
            return 1

    # Steps 1–4: Compile → Render → Write
    if args.bracket:
        _generate_one(args.bracket, args.adapter, args.output, args.dry_run)
    else:
        brackets = list(Path("core/usecases/core").rglob("UseCase_Bracket.yaml"))
        for bracket in brackets:
            _generate_one(bracket, args.adapter, args.output, args.dry_run)

    return 0


def _generate_one(bracket: Path, adapter_name: str, output: Path, dry_run: bool) -> None:
    from tooling.generator_core.ir.compiler import BracketCompiler
    from tooling.generator_core.ir.specs import AdapterTarget

    # Map adapter name to AdapterTarget
    _TARGET_MAP = {
        "metabase": AdapterTarget.METABASE,
        "grafana":  AdapterTarget.GRAFANA,
        "superset": AdapterTarget.SUPERSET,
    }
    target = _TARGET_MAP[adapter_name]

    compiler = BracketCompiler(
        kpi_catalog_root=Path("core/kpi_catalog"),
        action_codes_root=Path("core/action_codes"),
        target_adapter=target,
    )
    spec = compiler.compile(bracket)

    if dry_run:
        print(f"[dry-run] {spec.use_case_id} → {len(spec.pages)} pages, "
              f"{len(spec.measures)} measures, adapter={adapter_name}")
        return

    # Load concrete adapter
    if adapter_name == "metabase":
        from products.oss.tooling.adapters.metabase import MetabaseAdapter
        adapter = MetabaseAdapter()
    elif adapter_name == "grafana":
        from products.oss.tooling.adapters.grafana import GrafanaAdapter
        adapter = GrafanaAdapter()
    elif adapter_name == "superset":
        from products.oss.tooling.adapters.superset import SupersetAdapter
        adapter = SupersetAdapter()
    else:
        raise ValueError(f"Unknown adapter: {adapter_name}")

    errors = adapter.validate_ir(spec)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return

    result = adapter.render(spec)
    written = result.write_to(output)
    print(f"  {spec.use_case_id}: wrote {len(written)} files → {output}")


if __name__ == "__main__":
    sys.exit(main())
