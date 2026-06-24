"""packs.cli — standalone stage gate for the tool-specific domain packs (I-5.4).

    python -m tooling.superversion.layer_tools.packs.cli all <bracket>
    python -m tooling.superversion.layer_tools.packs.cli unity_catalog <bracket>

Packs surface warn/info, not errors, so the smoke is green (exit 0) unless a pack
hits a hard error. Planned (API-dependent) checks are printed, never dropped.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import packs

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.layer_tools.packs.cli",
        description="Run tool-specific domain packs against a use case (I-5.4).",
    )
    parser.add_argument("pack", help="pack id (unity_catalog|purview|dbt) or 'all'")
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    parser.add_argument("--kpis", type=Path, default=_KPIS)
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(f"[packs] bracket not found: {args.bracket}")
        return 1
    model = from_bracket_file(args.bracket, args.kpis)
    ids = packs.available() if args.pack == "all" else [args.pack]

    hard_error = False
    for pid in ids:
        report = packs.evaluate(pid, model)
        c = report.counts()
        print(f"[packs] {pid} ({report.platform}) [{report.status}]: "
              f"{c['error']} error, {c['warn']} warn, {c['info']} info — "
              f"{'OK' if report.ok else 'FAIL'}")
        for f in report.findings:
            print(f"    {f.severity.upper()} [{f.code}] {f.detail}")
        hard_error = hard_error or not report.ok
    return 1 if hard_error else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
