"""comp_gate — COMP*-DSGVO compliance gate on the canonical model (task I-4.4).

Fed from ALUCA's compliance doctrine (`compliance/`) and each UC's
`data_protection` block (the single source for PII classification), this gate
enforces the headline GDPR rule at the model layer:

  **PII without row-level security → FAIL.** A UC that declares
  ``data_protection.personal_data: true`` must ship a model whose roles carry an
  actual RLS filter (``Role.table_permissions[].filter_expression``); otherwise
  personal data would be exposed unfiltered.

Two finding classes (severity-switchable, mirroring `golden_thread`):
  - ``pii_without_rls`` — personal_data=true but the model has no RLS. Default
    **error**.
  - ``data_protection_unclassified`` — no ``personal_data`` flag at all. Default
    **warn** ("unklassifiziert"): missing classification is a gap to flag, not a
    hard block.

Rollback (I-4.4 DoD): ``warn_only=True`` (CLI ``--warn``) downgrades everything to
advisory.

Scope note: the gated universal UCs (`golden_thread.GATED_UCS`) are all
``personal_data: false``, so the CLI stage gate is green on them. The blocking
"PII-UC without RLS → red" behaviour is proven against XD-002 (the one
``personal_data: true`` UC, whose governance roles carry no RLS filter) in
`tests/test_comp_gate.py`.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.golden_thread import GATED_UCS, _KPIS, _UC_DIR

KIND_PII_NO_RLS = "pii_without_rls"
KIND_UNCLASSIFIED = "data_protection_unclassified"

DEFAULT_SEVERITY = {KIND_PII_NO_RLS: "error", KIND_UNCLASSIFIED: "warn"}


class CompGateError(AssertionError):
    """The model breaks a COMP*-DSGVO rule (error-severity findings)."""


@dataclass(frozen=True)
class CompFinding:
    kind: str
    ref: str          # use case id
    detail: str

    def severity(self, *, strict: bool = False, warn_only: bool = False) -> str:
        if warn_only:
            return "warn"
        if strict:
            return "error"
        return DEFAULT_SEVERITY.get(self.kind, "error")


def model_has_rls(model: CanonicalModel) -> bool:
    """True if any role enforces row-level security (a non-empty table filter)."""
    return any(
        (tp.filter_expression or "").strip()
        for role in model.semantic.roles
        for tp in role.table_permissions
    )


def check_compliance(use_case: str, data_protection: Optional[dict],
                     model: CanonicalModel) -> list[CompFinding]:
    """Return COMP findings for a UC given its data_protection block + model (pure)."""
    findings: list[CompFinding] = []
    if not data_protection or "personal_data" not in data_protection:
        findings.append(CompFinding(
            KIND_UNCLASSIFIED, use_case,
            "data_protection.personal_data is missing — PII status unclassified",
        ))
        return findings
    if data_protection.get("personal_data") is True and not model_has_rls(model):
        cats = data_protection.get("personal_data_categories") or []
        cat_str = ", ".join(map(str, cats)) if cats else "unspecified categories"
        findings.append(CompFinding(
            KIND_PII_NO_RLS, use_case,
            f"personal_data=true ({cat_str}) but the model enforces no row-level "
            "security (no role table filter)",
        ))
    return findings


def assert_compliance(use_case: str, data_protection: Optional[dict], model: CanonicalModel,
                      *, strict: bool = False, warn_only: bool = False) -> list[CompFinding]:
    """Raise `CompGateError` on any error-severity finding. Returns all findings."""
    findings = check_compliance(use_case, data_protection, model)
    errors = [f for f in findings if f.severity(strict=strict, warn_only=warn_only) == "error"]
    if errors:
        lines = "\n".join(f"  [{f.kind}] {f.ref} — {f.detail}" for f in errors)
        raise CompGateError(f"COMP-DSGVO violations ({len(errors)}):\n{lines}")
    return findings


def load_data_protection(bracket_path: Path) -> Optional[dict]:
    """Read the `data_protection` block from a UseCase_Bracket.yaml (or None)."""
    bracket = yaml.safe_load(Path(bracket_path).read_text(encoding="utf-8")) or {}
    dp = bracket.get("data_protection")
    return dp if isinstance(dp, dict) else None


# --------------------------------------------------------------------------- #
# Stage gate (CLI)                                                            #
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.eval.comp_gate",
        description="COMP*-DSGVO gate: PII without row-level security → FAIL (I-4.4).",
    )
    parser.add_argument("--strict", action="store_true",
                        help="escalate unclassified warnings to errors")
    parser.add_argument("--warn", action="store_true",
                        help="rollback: downgrade ALL findings to advisory (exit 0)")
    args = parser.parse_args(argv)

    total_errors = 0
    for uc, folder in sorted(GATED_UCS.items()):
        bracket = _UC_DIR / folder / "UseCase_Bracket.yaml"
        if not bracket.exists():
            print(f"[comp-dsgvo] {uc}: bracket missing (skip)")
            continue
        model = from_bracket_file(bracket, _KPIS)
        dp = load_data_protection(bracket)
        findings = check_compliance(uc, dp, model)
        errs = [f for f in findings if f.severity(strict=args.strict, warn_only=args.warn) == "error"]
        warns = [f for f in findings if f.severity(strict=args.strict, warn_only=args.warn) == "warn"]
        total_errors += len(errs)
        status = "FAIL" if errs else ("WARN" if warns else "OK")
        print(f"[comp-dsgvo] {uc}: {status} ({len(errs)} error, {len(warns)} warn)")
        for f in errs + warns:
            sev = f.severity(strict=args.strict, warn_only=args.warn).upper()
            print(f"    {sev} [{f.kind}] {f.ref} — {f.detail}")

    if total_errors:
        print(f"[comp-dsgvo] {total_errors} error-severity finding(s) → exit 1")
        return 1
    print("[comp-dsgvo] no error-severity findings.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
