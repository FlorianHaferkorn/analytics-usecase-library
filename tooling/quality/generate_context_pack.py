"""Generate a compact agent context pack from the latest quality run artefacts.

The context pack is a minimal Markdown file designed to be loaded into an agent
prompt instead of full logs, dist JSON files, or terminal dumps.

It contains:
  - Gate status (GREEN / RED) and step-level summary
  - Failure signatures with check IDs and pointers (not full messages)
  - Known-error YAML matches for deterministic fixes
  - File references the agent should read next (max 3)
  - Explicit "do NOT load" guard list

Usage:
    python tooling/quality/generate_context_pack.py [--run-dir PATH] [--output PATH]

If --run-dir is omitted, the latest directory under internal/metrics/runs/ is used.

Exit codes:
  0  Context pack written.
  1  No run directory found or quality_results.json missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

RUNS_DIR = Path("internal/metrics/runs")
KNOWN_ERRORS = Path("tooling/quality/known_errors.yaml")
MAX_FAILURES_SHOWN = 10
MAX_NEXT_FILES = 3


def _latest_run_dir() -> Path | None:
    if not RUNS_DIR.exists():
        return None
    dirs = sorted(
        (d for d in RUNS_DIR.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs[0] if dirs else None


def _load_known_errors() -> list[dict]:
    if yaml is None or not KNOWN_ERRORS.exists():
        return []
    with open(KNOWN_ERRORS, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("errors", [])


def _match_error(check: str, message: str, known: list[dict]) -> dict | None:
    """Find the first known_errors entry that matches by check ID prefix."""
    for entry in known:
        if entry.get("check") and check.startswith(entry["check"].split(".")[0]):
            return entry
    return None


def _generate_pack(run_dir: Path) -> str:
    summary_path = run_dir / "quality_summary.md"
    results_path = run_dir / "quality_results.json"
    fix_log_path = run_dir / "self_heal_log.json"

    known_errors = _load_known_errors()

    lines: list[str] = [
        "# Agent Context Pack",
        "",
        f"Run directory: `{run_dir}`",
        "",
    ]

    # ── Summary ──────────────────────────────────────────────────────────────
    if summary_path.exists():
        summary = summary_path.read_text(encoding="utf-8")
        # Extract just the first 30 lines (gate status + step results)
        summary_lines = summary.splitlines()[:30]
        lines.append("## Gate Summary (from quality_summary.md)")
        lines.append("")
        lines.extend(summary_lines)
        lines.append("")
    else:
        lines.append("## Gate Summary")
        lines.append("")
        lines.append("No quality_summary.md found in run directory.")
        lines.append("")

    # ── Failures ─────────────────────────────────────────────────────────────
    failures: list[dict] = []
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
            if isinstance(results, list):
                failures = [r for r in results if r.get("severity") == "critical"]
            elif isinstance(results, dict):
                for report_results in results.values():
                    if isinstance(report_results, list):
                        failures.extend(r for r in report_results if r.get("severity") == "critical")
        except json.JSONDecodeError:
            pass

    if failures:
        lines.append("## Critical Failures (signatures only)")
        lines.append("")
        next_files: list[str] = []
        for f in failures[:MAX_FAILURES_SHOWN]:
            check = f.get("check", "unknown")
            pointer = f.get("pointer", "")
            msg = f.get("message", "")
            lines.append(f"- `{check}` @ `{pointer}`: {msg[:80]}")

            # Extract file path from pointer
            if pointer and pointer not in next_files and len(next_files) < MAX_NEXT_FILES:
                file_part = pointer.split("#")[0]
                next_files.append(file_part)

            # Look up known fix
            match = _match_error(check, msg, known_errors)
            if match:
                fix = match.get("manual_fix") or "see known_errors.yaml"
                det = match.get("deterministic_fix", False)
                tag = "AUTO-FIX" if det else "MANUAL"
                lines.append(f"  - {tag}: {fix}")

        if len(failures) > MAX_FAILURES_SHOWN:
            lines.append(f"  - ... and {len(failures) - MAX_FAILURES_SHOWN} more. Read quality_results.json.")
        lines.append("")

        if next_files:
            lines.append("## Files to Read Next (targeted)")
            lines.append("")
            for nf in next_files:
                lines.append(f"- `{nf}`")
            lines.append("")
    else:
        lines.append("## Failures")
        lines.append("")
        lines.append("No critical failures found in quality_results.json (or file missing).")
        lines.append("")

    # ── Fix log summary ───────────────────────────────────────────────────────
    if fix_log_path.exists():
        try:
            fix_data = json.loads(fix_log_path.read_text(encoding="utf-8"))
            total_fixed = sum(
                r.get("fixed_count", 0) for r in fix_data.values()
            ) if isinstance(fix_data, dict) else 0
            lines.append("## Self-Heal Log")
            lines.append("")
            lines.append(f"Total fixed: {total_fixed}. Full log: `{fix_log_path}`")
            lines.append("")
        except json.JSONDecodeError:
            pass

    # ── Do NOT load guard ────────────────────────────────────────────────────
    lines.append("## Do NOT Load Into Prompt")
    lines.append("")
    lines.append("- `dist/**/*.json` (full PBIR report JSON -- too large)")
    lines.append("- `tooling/schemas/pbir/**` (schema files -- load only specific $ref if needed)")
    lines.append(f"- `{results_path}` (full results -- use targeted queries)")
    lines.append("- Terminal logs > 100 lines (use quality_summary.md instead)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `generate_context_pack.py`. For full details read the artefacts listed above.*")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", metavar="PATH",
                        help="Run directory. Defaults to latest under internal/metrics/runs/.")
    parser.add_argument("--output", metavar="PATH",
                        help="Output path. Defaults to <run-dir>/context_pack.md.")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir) if args.run_dir else _latest_run_dir()
    if not run_dir or not run_dir.is_dir():
        print("No run directory found. Run the quality gate first.", file=sys.stderr)
        return 1

    pack = _generate_pack(run_dir)

    out = Path(args.output) if args.output else (run_dir / "context_pack.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(pack, encoding="utf-8")
    print(f"Context pack written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
