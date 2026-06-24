"""bridge — the Studio→Superversion seam (ADR-0007, subprocess/CLI transport).

The Studio cockpit docks onto the governed Python core by **spawning** this module
and reading JSON from stdout (decision E-1 / ADR-0007, transport ratified
2026-06-24). No second server process — local-first, BYO-key (I-6.5).

I-6.2 ("Vor dem Core") ships the ``precore`` command: build the canonical model
(`from_aluca`) and run the gov/eng/arch engines (I-5.3) as a pre-core reality
check, emitting deterministic JSON. I-6.3 ("Nach dem Core") adds the ``generate``
command: emit a chosen target (`targets.render`, ADR-0006) and surface the
**Gate-Report** — the Golden-Thread gate (I-3.4) + the E2E smoke (I-3.5) — so the
customer sees *why* a deliverable is green/red.

    python -m tooling.superversion.bridge precore  <bracket> [--kpis <dir>]
    python -m tooling.superversion.bridge generate <bracket> [--target tmdl]

Contract: JSON to stdout. Success → exit 0; failure → ``{"ok": false, "error": ...}``,
exit 1. Pure/deterministic (Invariant I2): same bracket → same JSON.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Optional

from tooling.superversion import e2e_smoke  # registers tmdl+pbir targets on import
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import engines
from tooling.superversion.targets import base as targets

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)


def precore(bracket_path: Path, kpis_dir: Path) -> dict:
    """Pre-core reality: canonical model + gov/eng/arch engine findings as a dict."""
    model = from_bracket_file(bracket_path, kpis_dir)
    engine_reports = []
    for eid in engines.available():
        report = engines.run(eid, model, "ingest")
        engine_reports.append({
            "id": report.engine_id,
            "label": engines.get(eid).label,
            "status": report.status,
            "ok": report.ok,
            "counts": report.counts(),
            "findings": [
                {"severity": f.severity, "code": f.code, "detail": f.detail}
                for f in report.findings
            ],
        })
    return {"ok": True, "bracket": bracket_path.parent.name, "engines": engine_reports}


def generate(bracket_path: Path, kpis_dir: Path, target: str) -> dict:
    """Post-core: emit one target + the Gate-Report (Golden-Thread + E2E smoke).

    ``ok`` is true only when the chosen target emits AND no gate stage FAILED —
    the gate is a first-class output of generation (ADR-0007), not a hidden step.
    """
    if target not in targets.available():
        raise ValueError(f"unknown target '{target}'; available: {targets.available()}")

    # Artifact manifest — emit the chosen target from the canonical model (no disk write).
    model = from_bracket_file(bracket_path, kpis_dir)
    emitted = targets.get(target).emit(model)
    artifacts = [
        {"path": path, "bytes": len(content.encode("utf-8"))}
        for path, content in emitted.items()
    ]

    # Gate-Report — reuse the governed E2E chain (I-3.4 Golden-Thread + I-3.5 smoke).
    with tempfile.TemporaryDirectory(prefix="bridge_gen_") as tmp:
        stages = e2e_smoke.run(bracket_path, kpis=kpis_dir, keep=Path(tmp))
    gate = {
        "ok": not any(s.failed for s in stages),
        "stages": [{"name": s.name, "status": s.status, "detail": s.detail} for s in stages],
    }
    adapter = targets.get(target)
    return {
        "ok": gate["ok"],
        "bracket": bracket_path.parent.name,
        "target": target,
        "target_label": adapter.label,
        "target_status": adapter.status,
        "targets_available": targets.available(),
        "artifacts": artifacts,
        "gate": gate,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.bridge",
        description="Studio→Superversion bridge (ADR-0007).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping", help="cheap readiness probe — JSON {ok,targets_available} (I-6.5)")
    p_pre = sub.add_parser("precore", help="run gov/eng/arch engines against a bracket (JSON out)")
    p_pre.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    p_pre.add_argument("--kpis", type=Path, default=_KPIS)
    p_gen = sub.add_parser("generate", help="emit a target + Gate-Report for a bracket (JSON out)")
    p_gen.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    p_gen.add_argument("--kpis", type=Path, default=_KPIS)
    p_gen.add_argument("--target", default="tmdl", help="target stack id (default: tmdl)")
    args = parser.parse_args(argv)

    try:
        if args.command == "ping":
            # No model work — proves the Python seam + registry import (engines/targets) are live.
            result = {"ok": True, "engines_available": engines.available(),
                      "targets_available": targets.available()}
        elif not args.bracket.exists():
            raise FileNotFoundError(f"bracket not found: {args.bracket}")
        elif args.command == "precore":
            result = precore(args.bracket, args.kpis)
        elif args.command == "generate":
            result = generate(args.bracket, args.kpis, args.target)
        else:  # pragma: no cover — argparse enforces a valid subcommand
            return 2
    except Exception as exc:  # noqa: BLE001 — bridge reports errors as JSON, never a stack trace
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
