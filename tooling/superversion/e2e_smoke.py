"""e2e_smoke — end-to-end smoke for one use case (task I-3.5).

One command drives the whole Superversion delivery chain for a single bracket and
fails if any stage is red:

    Bracket → from_aluca → CanonicalModel
            → Golden-Thread gate (I-3.4)
            → TMDL emit (I-3.2)  + TMDL hard-rule hook
            → PBIR emit (I-3.3)  + official `powerbi-report-author validate`

Run it:
    python -m tooling.superversion.e2e_smoke                 # default: COM-001
    python -m tooling.superversion.e2e_smoke <bracket.yaml>  # any UC
    python -m tooling.superversion.e2e_smoke --require-cli   # fail (not skip) if
                                                             # the PBIR validator is absent

Design notes:
  - The PBIR gate is the **official** CLI `powerbi-report-author validate`
    (Invariant I3 official-first), not a re-implementation. When the CLI is not
    on PATH the stage is reported SKIP and does not block (so local dev without
    the npm CLI still runs the chain); `--require-cli` (used in CI, where the CLI
    is installed) turns the skip into a hard failure so the gate is enforced.
  - The TMDL gate is the same PostToolUse hook (`validate_tmdl_style.sh`) that
    guards hand-written TMDL, run via `bash`; if the hook script or `bash` itself
    is absent (I-10.1: plain Windows without WSL/Git Bash) a structural fallback
    check runs instead — never a crash.
  - Each stage prints `[e2e] <stage>: PASS|FAIL|SKIP — detail`; the process exit
    code is 0 only when no stage FAILED.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.golden_thread import GoldenThreadError, assert_golden_thread
from tooling.superversion.targets import base
from tooling.superversion.targets import pbir  # noqa: F401 — registers "pbir"
from tooling.superversion.targets import tmdl  # noqa: F401 — registers "tmdl"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)
_TMDL_HOOK = _REPO_ROOT / ".claude" / "hooks" / "validate_tmdl_style.sh"
_PBIR_CLI = "powerbi-report-author"

# Git for Windows' own installer default (not always added to PATH) — checked
# only after PATH itself, so a real PATH-resolved bash (WSL, MSYS2, ...) always
# wins. I-10.1 follow-up: plain shutil.which("bash") missed this common case.
_GIT_BASH_FALLBACK_PATHS = [
    Path(root) / "Git" / "bin" / "bash.exe"
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"))
    if root
]


def resolve_bash() -> Optional[str]:
    """Find a usable `bash` — PATH first, then Git for Windows' default
    install location. Returns None (never raises) if neither exists, so
    callers can degrade honestly instead of crashing with WinError 2."""
    on_path = shutil.which("bash")
    if on_path:
        return on_path
    for candidate in _GIT_BASH_FALLBACK_PATHS:
        if candidate.exists():
            return str(candidate)
    return None


class StageResult:
    """Outcome of one pipeline stage: PASS / WARN / FAIL / SKIP + a one-line detail.

    WARN is visible but does not block (`failed` matches FAIL only) — the same
    advisory-first step L11 took for the fidelity floor: report the gap honestly
    before turning it into a hard gate, so the gate lands on a repo that can pass it.
    """

    def __init__(self, name: str, status: str, detail: str = ""):
        self.name, self.status, self.detail = name, status, detail

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"

    def __str__(self) -> str:
        tail = f" — {self.detail}" if self.detail else ""
        return f"[e2e] {self.name}: {self.status}{tail}"


def _stage_slots(bracket: Path, kpis: Path) -> StageResult:
    """Does the emitted page carry the mandatory slots its variant governs?

    Measured on 2026-08-02, the first time this could be asked at all: **39 of 40
    pages** across the 20 brackets miss at least one mandatory slot — `Slicer_Date`
    (19×), `ActionPanel` (13×), `Slicer_Pane` (7×), `Focus_Area` (3×).

    Nothing had reported this, for three independent reasons, each sufficient on its
    own: `RequiredSlots` was in no production spec; its page-label sniffing matched
    neither `page_1_summary` nor `page_2_execution`; and the visual ids were counters
    (`page_1_summary_3s_1`), so a slot-name comparison could never intersect. Three
    layers of blindness over one gap.

    WARN, not FAIL, until the emission closes the gap — a gate that is red on arrival
    gets switched off rather than satisfied.
    """
    from tooling.superversion.from_aluca import slot_luecken

    try:
        rows = slot_luecken(bracket, kpis)
    except Exception as exc:  # noqa: BLE001 — a broken check must be loud, not absent
        return StageResult("page_slots", "FAIL", f"{type(exc).__name__}: {exc}")

    ungeprueft = [r["page"] for r in rows if r["missing"] is None]
    fehlend = {r["page"]: r["missing"] for r in rows if r["missing"]}
    if not rows:
        return StageResult("page_slots", "SKIP", "bracket declares no pages")
    if fehlend or ungeprueft:
        teile = [f"{p}: {', '.join(m)}" for p, m in sorted(fehlend.items())]
        if ungeprueft:
            teile.append(f"no template_variant on {', '.join(sorted(ungeprueft))}")
        return StageResult("page_slots", "WARN", "; ".join(teile))
    return StageResult("page_slots", "PASS",
                       f"{len(rows)} page(s), all mandatory slots present")


def _stage_tmdl(model: CanonicalModel, dest: Path) -> StageResult:
    files = base.render("tmdl", model, dest)
    bash = resolve_bash()
    if _TMDL_HOOK.exists() and bash:
        for f in files:
            if f.suffix != ".tmdl":
                continue
            payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
            proc = subprocess.run([bash, str(_TMDL_HOOK)], input=payload,
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                return StageResult("tmdl", "FAIL",
                                   f"hook blocked {f.name}: {(proc.stdout + proc.stderr).strip()[:200]}")
        return StageResult("tmdl", "PASS", f"{len(files)} file(s), hard-rule hook green")
    # Fallback structural check when the hook script is absent, or there is no
    # `bash` on PATH to run it (e.g. plain Windows without WSL/Git Bash — I-10.1:
    # a missing `bash` must degrade to this check, not crash with WinError 2).
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("  ") or ":=" in line:
                return StageResult("tmdl", "FAIL", f"{f.name}:{i} violates TMDL hard-rules")
    return StageResult("tmdl", "PASS", f"{len(files)} file(s), structural check (hook or bash absent)")


def _stage_pbir(model: CanonicalModel, dest: Path, *, require_cli: bool) -> StageResult:
    base.render("pbir", model, dest)
    report_dir = dest / f"{model.report.name}.Report"
    if shutil.which(_PBIR_CLI) is None:
        if require_cli:
            return StageResult("pbir", "FAIL", f"required '{_PBIR_CLI}' CLI not on PATH")
        return StageResult("pbir", "SKIP", f"'{_PBIR_CLI}' CLI not installed (official gate not run)")
    proc = subprocess.run(
        [_PBIR_CLI, "validate", str(report_dir), "--no-schema", "--format", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        data = json.loads(proc.stdout)["data"]
    except (json.JSONDecodeError, KeyError):
        return StageResult("pbir", "FAIL", f"validator output unparseable (rc={proc.returncode})")
    errors = data.get("errorCount", -1)
    if errors == 0:
        return StageResult("pbir", "PASS", f"check_pbir 0 errors ({data.get('warningCount', 0)} warn)")
    diags = ", ".join((data.get("diagnostics") or {}).keys())
    return StageResult("pbir", "FAIL", f"check_pbir {errors} error(s): {diags}")


def run(bracket: Path, *, kpis: Path = _KPIS, require_cli: bool = False,
        keep: Optional[Path] = None) -> list[StageResult]:
    """Run the full chain for one bracket; returns the per-stage results."""
    results: list[StageResult] = []

    # Stage 1 — source adapter.
    try:
        model = from_bracket_file(bracket, kpis)
        results.append(StageResult("source", "PASS",
                                   f"{bracket.parent.name} → model "
                                   f"({len(model.semantic.tables)} tables, {len(model.report.pages)} pages)"))
    except Exception as exc:  # noqa: BLE001 — surface any source failure as a red stage
        results.append(StageResult("source", "FAIL", f"{type(exc).__name__}: {exc}"))
        return results

    # Stage 2 — Golden-Thread gate (error-severity blocks; warns are logged).
    try:
        violations = assert_golden_thread(model)
        warns = len(violations)
        results.append(StageResult("golden_thread", "PASS",
                                   f"strategic anchors intact ({warns} advisory)"))
    except GoldenThreadError as exc:
        results.append(StageResult("golden_thread", "FAIL", str(exc).splitlines()[0]))
        return results

    dest = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="e2e_smoke_"))
    dest.mkdir(parents=True, exist_ok=True)

    # Stage 3 — Pflicht-Slots je Seitenvariante (template_manifest.yaml).
    results.append(_stage_slots(bracket, kpis))
    # Stage 4 — TMDL emit + hard-rule gate.
    results.append(_stage_tmdl(model, dest))
    # Stage 4 — PBIR emit + official validator gate.
    results.append(_stage_pbir(model, dest, require_cli=require_cli))
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.e2e_smoke",
        description="E2E smoke: Bracket → model → TMDL+PBIR → validate (one UC).",
    )
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET,
                        help="UseCase_Bracket.yaml (default: COM-001)")
    parser.add_argument("--kpis", type=Path, default=_KPIS, help="KPI catalog dir")
    parser.add_argument("--require-cli", action="store_true",
                        help="fail (not skip) if the powerbi-report-author CLI is absent (CI)")
    parser.add_argument("--keep", type=Path, default=None,
                        help="write emitted artifacts here instead of a temp dir")
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(f"[e2e] source: FAIL — bracket not found: {args.bracket}")
        return 1

    results = run(args.bracket, kpis=args.kpis, require_cli=args.require_cli, keep=args.keep)
    for r in results:
        print(r)
    if any(r.failed for r in results):
        print("[e2e] FAILED — at least one stage is red.")
        return 1
    # „green" only when nothing is warning either. A summary that says green while a
    # stage says WARN teaches readers to skip the stage lines — which is how the slot
    # gap survived unseen in the first place.
    warns = [r for r in results if r.status == "WARN"]
    if warns:
        print(f"[e2e] OK with {len(warns)} advisory warning(s) — "
              f"{', '.join(r.name for r in warns)}. No stage is red.")
        return 0
    print("[e2e] OK — full chain green.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
