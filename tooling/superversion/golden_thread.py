"""golden_thread — Golden-Thread gate on the canonical model (task I-3.4).

ALUCA's Golden Thread: every measure traces to a governed KPI (its strategic
anchor), and every visual binds only measures that actually exist in the model.
Mirrors `tooling/ontology/registry_builder.py`'s referential-integrity doctrine,
but at the canonical-model layer (post `from_aluca`), so it guards the Superversion
output the same way ALUCA guards its catalog.

Two violation classes:
  - ``unresolved_measure`` — a measure with no governed KPI anchor (it landed in
    the `_Unresolved` display folder). Default severity **error** ("jede Measure
    hat strategischen Anker, sonst FAIL").
  - ``dangling_visual_bind`` — a visual binds a measure name absent from the
    semantic model (a broken reference). Default severity **warn**: real shipped
    UCs (COM-001/COM-002) currently bind comparison measures (Plan/LY) the adapter
    does not yet materialize — the gate surfaces this drift honestly without
    reddening main. ``--strict`` escalates it to error.

Rollback (I-3.4 DoD): ``warn_only=True`` (CLI ``--warn``) downgrades everything to
advisory.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import UNRESOLVED_DISPLAY_FOLDER, from_bracket_file

KIND_UNRESOLVED = "unresolved_measure"
KIND_DANGLING = "dangling_visual_bind"

# Default severity per violation kind. `dangling` is advisory by default because
# it reflects pre-existing bracket drift (see module docstring); `--strict` lifts it.
DEFAULT_SEVERITY = {KIND_UNRESOLVED: "error", KIND_DANGLING: "warn"}


class GoldenThreadError(AssertionError):
    """The canonical model breaks the Golden Thread (error-severity violations)."""


@dataclass(frozen=True)
class Violation:
    kind: str
    ref: str          # measure name or "visual:measure"
    detail: str

    def severity(self, *, strict: bool = False, warn_only: bool = False) -> str:
        if warn_only:
            return "warn"
        if strict:
            return "error"
        return DEFAULT_SEVERITY.get(self.kind, "error")


def validate_golden_thread(model: CanonicalModel) -> list[Violation]:
    """Return all Golden-Thread violations in the canonical model (pure)."""
    violations: list[Violation] = []

    measure_names: set[str] = set()
    for table in model.semantic.tables:
        for m in table.measures:
            measure_names.add(m.name)
            if m.display_folder == UNRESOLVED_DISPLAY_FOLDER:
                violations.append(Violation(
                    KIND_UNRESOLVED, m.name,
                    "measure has no governed KPI anchor (unresolved)",
                ))

    for page in model.report.pages:
        for v in page.visuals:
            for bm in v.bound_measures:
                if bm not in measure_names:
                    violations.append(Violation(
                        KIND_DANGLING, f"{v.visual_id}:{bm}",
                        f"visual '{v.visual_id}' binds measure '{bm}' "
                        "not present in the semantic model",
                    ))
    return violations


def assert_golden_thread(model: CanonicalModel, *, strict: bool = False,
                         warn_only: bool = False) -> list[Violation]:
    """Raise `GoldenThreadError` if any error-severity violation exists.

    Returns the full violation list (incl. warnings) for the caller to log.
    `strict` escalates all violations to error; `warn_only` downgrades all
    (rollback). Default: per `DEFAULT_SEVERITY`.
    """
    violations = validate_golden_thread(model)
    errors = [v for v in violations if v.severity(strict=strict, warn_only=warn_only) == "error"]
    if errors:
        lines = "\n".join(f"  [{v.kind}] {v.ref} — {v.detail}" for v in errors)
        raise GoldenThreadError(f"Golden-Thread violations ({len(errors)}):\n{lines}")
    return violations


# --------------------------------------------------------------------------- #
# Stage gate (CLI)                                                            #
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_UC_DIR = _REPO_ROOT / "core" / "usecases" / "core"
# The universal UCs the Superversion adapter is hardened against (I-1).
GATED_UCS = {
    "COM-001": "COM-001_Sales_Performance",
    "COM-002": "COM-002_Margin_Price_Performance",
    "COM-003": "COM-003_Customer_Value",
    "FIN-002": "FIN-002_Cost_Performance",
    "SCM-002": "SCM-002_Supply_Reliability_OTIF",
}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.golden_thread",
        description="Golden-Thread gate over the hardened universal use cases.",
    )
    parser.add_argument("--strict", action="store_true",
                        help="escalate dangling-visual-bind warnings to errors")
    parser.add_argument("--warn", action="store_true",
                        help="rollback: downgrade ALL violations to advisory (exit 0)")
    args = parser.parse_args(argv)

    total_errors = 0
    for uc, folder in sorted(GATED_UCS.items()):
        bracket = _UC_DIR / folder / "UseCase_Bracket.yaml"
        if not bracket.exists():
            print(f"[golden-thread] {uc}: bracket missing (skip)")
            continue
        model = from_bracket_file(bracket, _KPIS)
        violations = validate_golden_thread(model)
        errs = [v for v in violations if v.severity(strict=args.strict, warn_only=args.warn) == "error"]
        warns = [v for v in violations if v.severity(strict=args.strict, warn_only=args.warn) == "warn"]
        total_errors += len(errs)
        status = "FAIL" if errs else ("WARN" if warns else "OK")
        print(f"[golden-thread] {uc}: {status} ({len(errs)} error, {len(warns)} warn)")
        for v in errs + warns:
            sev = v.severity(strict=args.strict, warn_only=args.warn).upper()
            print(f"    {sev} [{v.kind}] {v.ref} — {v.detail}")

    if total_errors:
        print(f"[golden-thread] {total_errors} error-severity violation(s) → exit 1")
        return 1
    print("[golden-thread] no error-severity violations.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
