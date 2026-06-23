"""canonical_contract — the single contract seam (ADR-0005).

Exposes the canonical model dataclasses ALUCA's source adapter builds against.
Per ADR-0005 rule 4 this module is the ONLY import point for the contract — no
call site imports `core.pbi_engine` directly:

- When the **vendored Meridian core** is present and intact (`PIN.json` sha256
  matches), this re-exports Meridian's **real** dataclasses (`_meridian_vendor`).
- Otherwise it falls back to the **structure-identical mirror** (`_canonical_mirror`),
  keeping ALUCA standalone-runnable (PRODUCT_PLAN F4).

Because the mirror is verbatim, `from_aluca` + `model_to_json` produce byte-identical
output in either mode (Invariant I2). Equivalence is guarded field-for-field, both
directions, by `tests/test_from_aluca.py::test_contract_parity_with_meridian`,
enforced in CI where the vendored core is present (ADR-0005 rule 3).

`USING_MERIDIAN_ORIGINALS` records which path is active (introspection/tests only).
"""
from __future__ import annotations

_NAMES = (
    "Column", "Measure", "RoleTablePermission", "RoleColumnPermission", "Role",
    "Table", "Relationship", "ModelFunction", "SemanticModel",
    "VisualCalculation", "Visual", "ReportPage", "ExtensionMeasure", "Bookmark",
    "ReportModel", "CanonicalModel",
)

try:
    from tooling.superversion._meridian_vendor import load_contract as _load_contract

    _contract = _load_contract()
    globals().update(_contract)
    USING_MERIDIAN_ORIGINALS = True
except Exception:
    # Soft-fallback to the standalone mirror — never a hard error (ADR-0005 rule 4).
    from tooling.superversion import _canonical_mirror as _m

    globals().update({name: getattr(_m, name) for name in _NAMES})
    USING_MERIDIAN_ORIGINALS = False

__all__ = [*_NAMES, "USING_MERIDIAN_ORIGINALS"]
