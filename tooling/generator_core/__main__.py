"""
CLI entry point for generator_core.

Usage
-----
    python -m tooling.generator_core preflight --bracket <path>
    python -m tooling.generator_core compile   --bracket <path> [--dry-run]
    python -m tooling.generator_core score     --bracket <path>
    python -m tooling.generator_core telemetry --stats
    python -m tooling.generator_core kb        --list [--category tmdl_syntax]

Run from the repo root so that default paths resolve correctly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kpi-catalog-root",   type=Path, default=Path("core/kpi_catalog"))
    parser.add_argument("--action-codes-root",  type=Path, default=Path("core/action_codes"))
    parser.add_argument("--data-contracts-root",type=Path, default=Path("core/data_contracts"))
    parser.add_argument("--dist-root",          type=Path, default=Path("products/fabric/powerbi/dist"))
    parser.add_argument("--use-cases-root",     type=Path, default=Path("core/usecases/core"))


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_preflight(args: argparse.Namespace) -> int:
    from .preflight.validator import PreflightValidator
    validator = PreflightValidator(
        kpi_catalog_root=args.kpi_catalog_root,
        action_codes_root=args.action_codes_root,
        data_contracts_root=args.data_contracts_root,
        dist_root=args.dist_root,
        mode=args.mode,
    )
    if args.bracket:
        reports = [validator.run(args.bracket)]
    elif args.domain:
        reports = validator.run_domain(args.use_cases_root, args.domain)
    else:
        brackets = list(args.use_cases_root.rglob("UseCase_Bracket.yaml"))
        reports = validator.run_all(brackets)

    if args.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2))
    else:
        for r in reports:
            print(r.summary())
            print()

    return 0 if all(r.passed for r in reports) else 1


def cmd_compile(args: argparse.Namespace) -> int:
    from .ir.compiler import BracketCompiler
    from .ir.specs import AdapterTarget

    compiler = BracketCompiler(
        kpi_catalog_root=args.kpi_catalog_root,
        action_codes_root=args.action_codes_root,
        target_adapter=AdapterTarget(args.adapter),
    )
    spec = compiler.compile(args.bracket)

    if compiler.warnings:
        for w in compiler.warnings:
            print(f"WARN  {w}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps({
            "use_case_id": spec.use_case_id,
            "domain": spec.domain,
            "pages": [p.id for p in spec.pages],
            "measures": len(spec.measures),
            "compiler_warnings": [str(w) for w in compiler.warnings],
        }, indent=2))
        return 0

    # Load adapter from the appropriate product directory.
    # Concrete adapters are NOT part of generator_core — they live in their
    # product directories and are imported lazily here.
    if args.adapter == "pbip":
        from products.fabric.powerbi.tooling.adapters.pbip import PBIPAdapter
        adapter = PBIPAdapter()
    elif args.adapter == "metabase":
        from products.oss.tooling.adapters.metabase import MetabaseAdapter
        adapter = MetabaseAdapter()
    elif args.adapter == "grafana":
        from products.oss.tooling.adapters.grafana import GrafanaAdapter
        adapter = GrafanaAdapter()
    elif args.adapter == "superset":
        from products.oss.tooling.adapters.superset import SupersetAdapter
        adapter = SupersetAdapter()
    else:
        print(f"ERROR Unknown adapter '{args.adapter}'", file=sys.stderr)
        return 1

    errors = adapter.validate_ir(spec)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 1

    result = adapter.render(spec)
    dest = Path(args.output or args.dist_root)
    written = result.write_to(dest)
    print(f"Rendered {len(written)} files to {dest}")
    for w in result.warnings:
        print(f"WARN  {w}", file=sys.stderr)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    from .intelligence.scorer import QualityScorer
    scorer = QualityScorer()
    score = scorer.score(
        bracket_path=args.bracket,
        report_dir=args.report_dir,
        model_dir=args.model_dir,
    )
    if args.json:
        print(json.dumps(score.to_dict(), indent=2))
    else:
        print(score.summary())
    return 0 if score.overall >= 0.70 else 1


def cmd_telemetry(args: argparse.Namespace) -> int:
    from .intelligence.telemetry import TelemetryCollector
    tc = TelemetryCollector()
    if args.stats:
        stats = tc.summary_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            for k, v in stats.items():
                print(f"  {k}: {v}")
    elif args.recurring:
        recurring = tc.recurring_errors(min_count=args.min_count)
        if args.json:
            print(json.dumps(recurring, indent=2))
        else:
            for err, count in sorted(recurring.items(), key=lambda x: -x[1]):
                print(f"  [{count}x] {err[:100]}")
    return 0


def cmd_kb(args: argparse.Namespace) -> int:
    from .intelligence.kb import KnowledgeBase
    kb = KnowledgeBase()
    entries = kb.lookup_by_category(args.category) if args.category else kb.all_entries()
    if args.json:
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        print(f"Knowledge base: {kb.entry_count()} entries")
        for e in entries:
            print(f"  [{e.id}] ({e.category}) {e.symptom[:60]}")
            print(f"    Fix: {e.fix[:80]}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.generator_core",
        description="Generator Core CLI — compile, preflight, score, telemetry",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # preflight
    p_pre = sub.add_parser("preflight", help="Run pre-generation checks")
    _add_common_args(p_pre)
    p_pre.add_argument("--bracket",  type=Path, help="Single bracket file")
    p_pre.add_argument("--domain",   type=str,  help="Domain prefix (e.g. COM)")
    p_pre.add_argument("--mode",     choices=["quick", "full"], default="full")
    p_pre.add_argument("--json",     action="store_true")

    # compile
    p_comp = sub.add_parser("compile", help="Compile bracket to IR and render")
    _add_common_args(p_comp)
    p_comp.add_argument("--bracket",  type=Path, required=True)
    p_comp.add_argument("--adapter",  choices=["pbip", "metabase", "grafana", "superset"],
                        default="pbip")
    p_comp.add_argument("--output",   type=str, help="Output directory (default: dist-root)")
    p_comp.add_argument("--dry-run",  action="store_true", help="Print spec without writing files")
    p_comp.add_argument("--json",     action="store_true")

    # score
    p_score = sub.add_parser("score", help="Score generated output quality")
    _add_common_args(p_score)
    p_score.add_argument("--bracket",    type=Path, required=True)
    p_score.add_argument("--report-dir", type=Path)
    p_score.add_argument("--model-dir",  type=Path)
    p_score.add_argument("--json",       action="store_true")

    # telemetry
    p_tel = sub.add_parser("telemetry", help="Show run history and stats")
    p_tel.add_argument("--stats",     action="store_true", help="Show aggregate stats")
    p_tel.add_argument("--recurring", action="store_true", help="Show recurring errors")
    p_tel.add_argument("--min-count", type=int, default=2)
    p_tel.add_argument("--json",      action="store_true")

    # kb
    p_kb = sub.add_parser("kb", help="Browse the error knowledge base")
    p_kb.add_argument("--list",     action="store_true")
    p_kb.add_argument("--category", type=str, help="Filter by category")
    p_kb.add_argument("--json",     action="store_true")

    args = parser.parse_args()

    dispatch = {
        "preflight": cmd_preflight,
        "compile":   cmd_compile,
        "score":     cmd_score,
        "telemetry": cmd_telemetry,
        "kb":        cmd_kb,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
