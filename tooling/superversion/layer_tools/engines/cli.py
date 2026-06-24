"""engines.cli — standalone stage gate for the gov/eng/arch engines (task I-5.3).

    python -m tooling.superversion.layer_tools.engines.cli all <bracket>
    python -m tooling.superversion.layer_tools.engines.cli gov <bracket> --mode greenfield

Beta engines surface warnings/infos, not errors, so the smoke is green (exit 0)
unless an engine hits a hard error. Runs standalone against a bare CanonicalModel.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import engines

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.layer_tools.engines.cli",
        description="Run gov/eng/arch Beta engines against a use case (I-5.3).",
    )
    parser.add_argument("engine", help="engine id (gov|dataarch|dataeng) or 'all'")
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    parser.add_argument("--kpis", type=Path, default=_KPIS)
    parser.add_argument("--mode", choices=["ingest", "greenfield"], default="ingest")
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(f"[engines] bracket not found: {args.bracket}")
        return 1
    model = from_bracket_file(args.bracket, args.kpis)
    ids = engines.available() if args.engine == "all" else [args.engine]

    hard_error = False
    for eid in ids:
        report = engines.run(eid, model, args.mode)
        c = report.counts()
        print(f"[engines] {eid} [{report.status}] mode={report.mode}: "
              f"{c['error']} error, {c['warn']} warn, {c['info']} info — "
              f"{'OK' if report.ok else 'FAIL'}")
        for f in report.findings:
            print(f"    {f.severity.upper()} [{f.code}] {f.detail}")
        hard_error = hard_error or not report.ok
    return 1 if hard_error else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
