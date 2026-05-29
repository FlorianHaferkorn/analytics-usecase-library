"""pbi-quality CLI: validate, repair, and diagnose Power BI / PBIP report artifacts.

Commands:
  validate   Detect violations in .Report directories.
  repair     Run the deterministic self-heal loop.
  doctor     Quick overall diagnosis of a PBIP dist root.

Exit codes (validate / repair):
  0  Green -- no critical violations.
  1  One or more CRITICAL violations remain.
  2  No reports found or dist-root missing.
  3  Self-heal stalled (repair command only).
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_report_quality_on_path(repo_root: Path | None = None) -> None:
    """Add the report_quality package to sys.path so it can be imported as a library.

    When installed as pbi-quality-tools, the code is vendored into the package.
    When running from repo root, we resolve relative to this file.
    """
    # Vendored path (inside the installed package)
    vendored = Path(__file__).parent / "vendor" / "report_quality"
    if vendored.is_dir():
        sys.path.insert(0, str(vendored.parent))
        return

    # Repo-relative path (development install)
    candidates = [
        Path(__file__).parents[3] / "tooling",  # packages/pbi_quality_tools/pbi_quality_tools -> tooling
        Path.cwd() / "tooling",
    ]
    if repo_root:
        candidates.insert(0, repo_root / "tooling")

    for candidate in candidates:
        if (candidate / "report_quality").is_dir():
            sys.path.insert(0, str(candidate))
            return

    raise ImportError(
        "report_quality library not found. "
        "Run from repo root or install pbi-quality-tools with vendored modules."
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="pbi-quality",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── validate ──────────────────────────────────────────────────────────────
    val_p = sub.add_parser("validate", help="Detect violations in .Report directories.")
    val_p.add_argument("--dist-root", default="products/fabric/powerbi/dist",
                       help="Path to dist folder containing .Report directories.")
    val_p.add_argument("--include-schema", action="store_true",
                       help="Fetch and validate Microsoft JSON schemas.")
    val_p.add_argument("--json", action="store_true", help="JSON output.")
    val_p.add_argument("--summary", action="store_true",
                       help="Compact output for CI / agent prompts.")

    # ── repair ────────────────────────────────────────────────────────────────
    rep_p = sub.add_parser("repair", help="Run the deterministic self-heal loop.")
    rep_p.add_argument("--dist-root", default="products/fabric/powerbi/dist")
    rep_p.add_argument("--dry-run", action="store_true",
                       help="Report fixes without writing files.")
    rep_p.add_argument("--max-iterations", type=int, default=3, metavar="N")
    rep_p.add_argument("--write-fix-log", metavar="PATH",
                       help="Write JSON fix log to this path.")
    rep_p.add_argument("--summary", action="store_true")

    # ── doctor ────────────────────────────────────────────────────────────────
    doc_p = sub.add_parser("doctor", help="Quick diagnosis of a PBIP dist root.")
    doc_p.add_argument("--pbip-root", default="products/fabric/powerbi/dist",
                       help="Path to the dist folder.")

    args = parser.parse_args(argv)

    try:
        _ensure_report_quality_on_path()
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.command == "validate":
        from tooling.report_quality.cli import main as _validate_main  # type: ignore[import]
        cli_args = ["--dist-root", args.dist_root]
        if args.include_schema:
            cli_args.append("--include-schema")
        if args.json:
            cli_args.append("--json")
        if args.summary:
            cli_args.append("--summary")
        return _validate_main(cli_args)

    if args.command == "repair":
        from tooling.report_quality.cli import main as _repair_main  # type: ignore[import]
        cli_args = [
            "--dist-root", args.dist_root,
            "--self-heal",
            "--max-iterations", str(args.max_iterations),
        ]
        if args.dry_run:
            cli_args.append("--dry-run")
        if args.write_fix_log:
            cli_args += ["--write-fix-log", args.write_fix_log]
        if args.summary:
            cli_args.append("--summary")
        return _repair_main(cli_args)

    if args.command == "doctor":
        return _doctor(Path(args.pbip_root))

    return 0


def _doctor(pbip_root: Path) -> int:
    """Quick diagnosis: count reports, violations, fixable vs manual."""
    if not pbip_root.exists():
        print(f"PBIP root not found: {pbip_root}", file=sys.stderr)
        return 2

    try:
        from tooling.report_quality.cli import validate  # type: ignore[import]
        from tooling.report_quality.pbir import iter_report_dirs  # type: ignore[import]
        from tooling.report_quality.models import violations_summary  # type: ignore[import]
    except ImportError as e:
        print(f"ERROR importing report_quality: {e}", file=sys.stderr)
        return 2

    reports = list(iter_report_dirs(pbip_root))
    if not reports:
        print(f"No .Report directories found under: {pbip_root}")
        return 2

    violations = validate(pbip_root)
    summ = violations_summary(violations)

    print(f"pbi-quality doctor: {pbip_root}")
    print(f"  Reports found : {len(reports)}")
    print(f"  Critical      : {summ['critical']}")
    print(f"  Warning       : {summ['warning']}")
    print(f"  Info          : {summ['info']}")

    if not violations:
        print("  Status        : GREEN")
        return 0

    print("  Status        : RED" if summ["critical"] > 0 else "  Status        : WARN")
    print()
    print("  Top issues:")
    for v in violations[:10]:
        print(f"    [{v.severity.upper()}] {v.check} @ {v.pointer}: {v.message}")
    if len(violations) > 10:
        print(f"    ... and {len(violations) - 10} more. Run 'pbi-quality validate' for full list.")

    return 1 if summ["critical"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
