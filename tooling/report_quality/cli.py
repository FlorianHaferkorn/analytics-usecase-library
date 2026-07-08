"""Command line entry point for report quality checks.

Exit codes:
  0  All checks passed; or --dry-run --self-heal with no remaining criticals.
  1  CRITICAL violations remain (detect-only, apply after heal, or dry-run would leave criticals).
  2  dist-root not found or no reports discovered.
  3  Apply-mode self-heal stalled (no progress). Never returned for --dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import MicrosoftReportAuthorBackend
from .content_validator import validate_report_content
from .dax_reference_validator import validate_report_measure_references
from .models import Violation, violations_summary
from .pbir import iter_report_dirs
from .schema_validator import validate_report_directory
from .self_heal import self_heal_all, write_fix_log
from .structural_validator import check_report


def _critical_violations(violations: list[Violation]) -> list[Violation]:
    return [v for v in violations if v.severity == "critical"]


def _print_violations(violations: list[Violation], *, json_output: bool, summary: bool) -> None:
    if json_output:
        print(json.dumps([v.__dict__ for v in violations], indent=2, ensure_ascii=False))
        return
    summ = violations_summary(violations)
    header = (
        f"Report quality: {summ['critical']} critical, {summ['warning']} warning, {summ['info']} info"
    )
    print(header)
    if not summary:
        for violation in violations:
            print(f"  {violation}")
    elif summ["critical"] > 0:
        for violation in violations:
            if violation.severity == "critical":
                print(f"  {violation}")


def validate(dist_root: Path, *, include_schema: bool = False) -> list[Violation]:
    violations: list[Violation] = []
    for report_dir in iter_report_dirs(dist_root):
        if include_schema:
            violations.extend(validate_report_directory(report_dir))
        violations.extend(check_report(report_dir))
        violations.extend(validate_report_content(report_dir))
    violations.extend(validate_report_measure_references(dist_root))
    # Tier 1 oracle (ADR-0001): opt-in via PBI_QUALITY_ALLOW_EXTERNAL, never touches
    # an external process otherwise -- augments, never replaces, the Tier 0 floor.
    violations.extend(MicrosoftReportAuthorBackend().validate(dist_root))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dist-root",
        default="products/fabric/powerbi/dist",
        help="Root directory containing .Report folders.",
    )
    parser.add_argument(
        "--include-schema",
        action="store_true",
        help="Fetch and validate Microsoft JSON schemas.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Compact output: header + criticals only. Suitable for CI/agent prompts.",
    )
    parser.add_argument(
        "--self-heal",
        action="store_true",
        help="Run deterministic fix loop after validation failures.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --self-heal: report fixes without writing files.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        metavar="N",
        help="Max fix iterations per report (default: 3).",
    )
    parser.add_argument(
        "--write-fix-log",
        metavar="PATH",
        help="Write JSON fix log to this path after self-heal.",
    )
    parser.add_argument(
        "--write-results",
        metavar="PATH",
        help="Write structured violation results as JSON to this path.",
    )
    args = parser.parse_args(argv)

    dist_root = Path(args.dist_root)
    if not dist_root.exists():
        print(f"Report root not found: {dist_root}", file=sys.stderr)
        return 2

    report_dirs = list(iter_report_dirs(dist_root))
    if not report_dirs:
        print(f"No .Report directories found under: {dist_root}", file=sys.stderr)
        return 2

    violations = validate(dist_root, include_schema=args.include_schema)
    _print_violations(violations, json_output=args.json, summary=args.summary)

    if args.write_results:
        results_path = Path(args.write_results)
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(
            json.dumps([v.__dict__ for v in violations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if not any(v.severity == "critical" for v in violations):
        return 0

    if not args.self_heal:
        return 1

    print()
    mode = "[DRY-RUN]" if args.dry_run else "[APPLY]"
    print(f"Self-heal {mode}: max {args.max_iterations} iterations per report ...")

    results = self_heal_all(
        dist_root,
        max_iterations=args.max_iterations,
        dry_run=args.dry_run,
    )

    if args.write_fix_log:
        write_fix_log(results, Path(args.write_fix_log))
        print(f"Fix log written: {args.write_fix_log}")

    stalled = False
    for name, result in results.items():
        status = "OK" if result.success else ("DRY-RUN" if args.dry_run else "STALLED")
        print(
            f"  {name}: {status} -- "
            f"{result.fixed_count} fixed, {len(result.remaining)} remaining "
            f"({result.iterations} iterations)"
        )
        if not result.success and not args.dry_run:
            stalled = True

    if stalled:
        return 3

    if args.dry_run:
        would_remain = [
            v for result in results.values() for v in _critical_violations(result.remaining)
        ]
        if would_remain:
            print("Dry-run: critical violations would remain after self-heal:")
            _print_violations(would_remain, json_output=args.json, summary=args.summary)
            return 1
        return 0

    final_violations = validate(dist_root, include_schema=args.include_schema)
    _print_violations(final_violations, json_output=args.json, summary=args.summary)
    return 1 if _critical_violations(final_violations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
