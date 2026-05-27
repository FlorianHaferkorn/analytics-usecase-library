"""Command line entry point for report quality checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .content_validator import validate_report_content
from .dax_reference_validator import validate_report_measure_references
from .models import Violation, violations_summary
from .pbir import iter_report_dirs
from .schema_validator import validate_report_directory
from .structural_validator import check_report


def _print_violations(violations: list[Violation], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps([v.__dict__ for v in violations], indent=2, ensure_ascii=False))
        return
    summary = violations_summary(violations)
    print(
        "Report quality: "
        f"{summary['critical']} critical, {summary['warning']} warning, {summary['info']} info"
    )
    for violation in violations:
        print(f"  {violation}")


def validate(dist_root: Path, *, include_schema: bool = False) -> list[Violation]:
    violations: list[Violation] = []
    for report_dir in iter_report_dirs(dist_root):
        if include_schema:
            violations.extend(validate_report_directory(report_dir))
        violations.extend(check_report(report_dir))
        violations.extend(validate_report_content(report_dir))
    violations.extend(validate_report_measure_references(dist_root))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-root", default="products/fabric/powerbi/dist")
    parser.add_argument("--include-schema", action="store_true", help="Fetch and validate Microsoft JSON schemas.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args(argv)

    dist_root = Path(args.dist_root)
    if not dist_root.exists():
        print(f"Report root not found: {dist_root}", file=sys.stderr)
        return 1
    violations = validate(dist_root, include_schema=args.include_schema)
    _print_violations(violations, json_output=args.json)
    return 1 if any(v.severity == "critical" for v in violations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
