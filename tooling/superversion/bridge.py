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
    python -m tooling.superversion.bridge attribute <use_case> <action_code_id> --t1 <json>

Contract: JSON to stdout. Success → exit 0; failure → ``{"ok": false, "error": ...}``,
exit 1. Pure/deterministic (Invariant I2): same bracket → same JSON.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from tooling.superversion import e2e_smoke  # registers tmdl+pbir targets on import
from tooling.superversion.eval import refinement, wirkung
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.layer_tools import engines
from tooling.superversion.targets import base as targets
from tooling.superversion.targets import osi  # noqa: F401 — registers "osi"
from tooling.superversion.targets import databricks  # noqa: F401 — registers "databricks"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_ACTION_CODES = _REPO_ROOT / "core" / "action_codes"
_USE_CASES = _REPO_ROOT / "core" / "usecases" / "core"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)


def resolve_bracket(reference: Path) -> Path:
    """Resolve either an explicit bracket path or a governed use-case ID."""
    if reference.is_absolute() or reference.suffix:
        if reference.exists():
            return reference.resolve()
        raise FileNotFoundError(f"bracket not found: {reference}")

    bracket_id = reference.name
    matches = sorted(_USE_CASES.glob(f"{bracket_id}_*/UseCase_Bracket.yaml"))
    if not matches:
        raise FileNotFoundError(f"bracket not found: {bracket_id}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous bracket id '{bracket_id}': {len(matches)} matches")
    return matches[0].resolve()


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


def generate(
    bracket_path: Path,
    kpis_dir: Path,
    target: str,
    *,
    include_content: bool = False,
) -> dict:
    """Post-core: emit one target + the Gate-Report (Golden-Thread + E2E smoke).

    ``ok`` is true only when the chosen target emits AND no gate stage FAILED —
    the gate is a first-class output of generation (ADR-0007), not a hidden step.
    """
    if target not in targets.available():
        raise ValueError(f"unknown target '{target}'; available: {targets.available()}")

    # Artifact manifest — emit the chosen target from the canonical model (no disk write).
    model = from_bracket_file(bracket_path, kpis_dir)
    emitted = targets.get(target).emit(model)
    artifacts = []
    for path, content in emitted.items():
        artifact = {"path": path, "bytes": len(content.encode("utf-8"))}
        if include_content:
            artifact["content"] = content
        artifacts.append(artifact)

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


def _load_outcome_kpis(action_code_id: str) -> list[str]:
    """Resolve a governed action-code's ``kpis.outcome_kpis`` by id.

    The bridge never accepts outcome-KPIs as caller input (Studio would then be
    able to attribute an action against KPIs it was never governed for) — always
    resolved from the checked-in action-code YAML, same as every other Golden
    Thread reference in this repo.
    """
    for path in sorted(_ACTION_CODES.rglob("*.yaml")):
        if path.name.endswith("_business_case.yaml"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if doc.get("id") == action_code_id:
            return list(doc.get("kpis", {}).get("outcome_kpis", []))
    raise ValueError(f"unknown action_code_id '{action_code_id}'")


def attribute(
    use_case: str,
    action_code_id: str,
    t1: dict,
    *,
    method: wirkung.Method = "before_after",
    control_t0: Optional[dict] = None,
    control_t1: Optional[dict] = None,
) -> dict:
    """Attribute an action's KPI effect: governed refcalc baseline (t0) + caller-
    supplied after-values (t1) — the DoD shape from test_wirkung.py, wired for
    Studio. Also derives reviewable RefinementProposals (never auto-applied,
    ADR-0009 §5); the caller (Studio's approval gate) decides their fate.
    """
    outcome_kpis = _load_outcome_kpis(action_code_id)
    if not outcome_kpis:
        raise ValueError(f"action_code '{action_code_id}' has no outcome_kpis")

    t0 = wirkung.snapshot_via_refcalc(use_case)
    action = wirkung.ActionEvent(action_code_id, outcome_kpis, scope=use_case)
    records = wirkung.attribute(
        action, t0, t1, method=method, control_t0=control_t0, control_t1=control_t1,
    )
    proposals = refinement.derive_refinements(records)
    return {
        "ok": True,
        "use_case": use_case,
        "action_code_id": action_code_id,
        "method": method,
        "outcome_kpis": outcome_kpis,
        "attribution": [r.to_dict() for r in records],
        "refinements": [p.to_dict() for p in proposals],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.bridge",
        description="Studio→Superversion bridge (ADR-0007).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping", help="cheap readiness probe — JSON {ok,targets_available} (I-6.5)")
    p_resolve = sub.add_parser("resolve", help="resolve a governed use-case id to its bracket")
    p_resolve.add_argument("bracket", type=Path)
    p_pre = sub.add_parser("precore", help="run gov/eng/arch engines against a bracket (JSON out)")
    p_pre.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    p_pre.add_argument("--kpis", type=Path, default=_KPIS)
    p_gen = sub.add_parser("generate", help="emit a target + Gate-Report for a bracket (JSON out)")
    p_gen.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET)
    p_gen.add_argument("--kpis", type=Path, default=_KPIS)
    p_gen.add_argument("--target", default="tmdl", help="target stack id (default: tmdl)")
    p_gen.add_argument(
        "--include-content",
        action="store_true",
        help="include deterministic artifact text in the JSON response (Studio download path)",
    )
    p_attr = sub.add_parser(
        "attribute",
        help="attribute an action's KPI effect: governed refcalc baseline + supplied "
             "after-values, and derive reviewable refinement proposals (JSON out, ADR-0009)",
    )
    p_attr.add_argument("use_case", help="use case id whose reference data supplies the t0 baseline (e.g. COM-001)")
    p_attr.add_argument("action_code_id", help="governed action-code id (outcome_kpis resolved from its YAML)")
    p_attr.add_argument("--t1", required=True, help="JSON object of after-snapshot KPI values")
    p_attr.add_argument("--method", default="before_after", choices=["before_after", "diff_in_diff", "holdout"])
    p_attr.add_argument("--control-t0", default=None, help="JSON object, required for diff_in_diff")
    p_attr.add_argument("--control-t1", default=None, help="JSON object, required for diff_in_diff/holdout")
    args = parser.parse_args(argv)

    try:
        if args.command == "ping":
            # No model work — proves the Python seam + registry import (engines/targets) are live.
            result = {"ok": True, "engines_available": engines.available(),
                      "targets_available": targets.available()}
        elif args.command == "resolve":
            bracket = resolve_bracket(args.bracket)
            result = {"ok": True, "bracket": bracket.parent.name}
        elif args.command == "attribute":
            result = attribute(
                args.use_case, args.action_code_id, json.loads(args.t1),
                method=args.method,
                control_t0=json.loads(args.control_t0) if args.control_t0 else None,
                control_t1=json.loads(args.control_t1) if args.control_t1 else None,
            )
        elif args.command == "precore":
            result = precore(resolve_bracket(args.bracket), args.kpis)
        elif args.command == "generate":
            result = generate(
                resolve_bracket(args.bracket),
                args.kpis,
                args.target,
                include_content=args.include_content,
            )
        else:  # pragma: no cover — argparse enforces a valid subcommand
            return 2
    except Exception as exc:  # noqa: BLE001 — bridge reports errors as JSON, never a stack trace
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
