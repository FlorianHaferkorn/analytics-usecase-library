"""Loader for the vendored Meridian canonical-core (ADR-0005, task I-2.2).

Loads Meridian's **real** contract dataclasses from the pinned vendor subtree
(`tooling/superversion/vendor/meridian`) WITHOUT importing them as
`core.pbi_engine`: ALUCA already uses `core` as a namespace package
(`core.brand.*`), so registering a `core` package here would shadow it and break
ALUCA. Meridian's parser modules are pure-stdlib with no internal cross-imports,
so we load each file directly by path under a private module name — `core` is
never touched in `sys.modules`.

`model.py` itself uses absolute `from core.pbi_engine.parsers… import …` imports
that we deliberately do NOT honour (they would pollute `core`); its
`CanonicalModel` is a trivial two-field dataclass we reconstruct identically here
from the loaded `SemanticModel` / `ReportModel`.

`load_contract()` raises `VendorUnavailable` when the subtree is missing or its
integrity manifest (`PIN.json` sha256) does not match — callers soft-fallback to
the mirror (`_canonical_mirror`). This is the seam ADR-0005 rule 4 describes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "meridian"
PIN_PATH = VENDOR_DIR / "PIN.json"

# The dataclass names the contract exposes (must match _canonical_mirror + Meridian).
CONTRACT_NAMES = (
    "Column", "Measure", "RoleTablePermission", "RoleColumnPermission", "Role",
    "Table", "Relationship", "ModelFunction", "SemanticModel",
    "VisualCalculation", "Visual", "ReportPage", "ExtensionMeasure", "Bookmark",
    "ReportModel", "CanonicalModel",
)


class VendorUnavailable(RuntimeError):
    """The vendored Meridian subtree is absent or fails its integrity manifest."""


def _read_pin() -> dict:
    if not PIN_PATH.exists():
        raise VendorUnavailable(f"no vendor pin at {PIN_PATH}")
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


def _verify_manifest(pin: dict) -> None:
    """Detect local divergence of the vendored files (ADR-0005 rule 6 / SA review):
    every file in PIN.json must exist and match its recorded sha256."""
    for entry in pin.get("files", []):
        f = VENDOR_DIR / entry["path"]
        if not f.exists():
            raise VendorUnavailable(f"vendored file missing: {entry['path']}")
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        if got != entry["sha256"]:
            raise VendorUnavailable(
                f"vendored file diverged locally: {entry['path']} "
                f"(sha256 {got[:12]}… != pinned {entry['sha256'][:12]}…)"
            )


def _load_module(mod_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise VendorUnavailable(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Register under its private name BEFORE exec so dataclasses' annotation
    # resolution (sys.modules[cls.__module__]) works. The name is namespaced
    # away from `core`, so ALUCA's `core.*` namespace package is untouched.
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)  # parsers are pure-stdlib, no `core` imports
    return module


def load_contract() -> dict:
    """Return Meridian's real contract dataclasses, keyed by `CONTRACT_NAMES`.

    Reconstructs `CanonicalModel` from the loaded parser dataclasses (model.py's
    own absolute imports are intentionally not honoured). Raises
    `VendorUnavailable` if the subtree is absent or its manifest fails.
    """
    pin = _read_pin()
    _verify_manifest(pin)

    tmdl = _load_module(
        "_meridian_vendor_tmdl_parser",
        VENDOR_DIR / "core" / "pbi_engine" / "parsers" / "tmdl_parser.py",
    )
    pbir = _load_module(
        "_meridian_vendor_pbir_parser",
        VENDOR_DIR / "core" / "pbi_engine" / "parsers" / "pbir_parser.py",
    )

    semantic_model = tmdl.SemanticModel
    report_model = pbir.ReportModel

    @dataclass
    class CanonicalModel:
        """Reconstruction of Meridian's `core.pbi_engine.model.CanonicalModel`
        (a two-field dataclass) — structurally identical, no `core` import."""
        semantic: semantic_model
        report: report_model

    contract = {
        "Column": tmdl.Column,
        "Measure": tmdl.Measure,
        "RoleTablePermission": tmdl.RoleTablePermission,
        "RoleColumnPermission": tmdl.RoleColumnPermission,
        "Role": tmdl.Role,
        "Table": tmdl.Table,
        "Relationship": tmdl.Relationship,
        "ModelFunction": tmdl.ModelFunction,
        "SemanticModel": tmdl.SemanticModel,
        "VisualCalculation": pbir.VisualCalculation,
        "Visual": pbir.Visual,
        "ReportPage": pbir.ReportPage,
        "ExtensionMeasure": pbir.ExtensionMeasure,
        "Bookmark": pbir.Bookmark,
        "ReportModel": pbir.ReportModel,
        "CanonicalModel": CanonicalModel,
    }
    missing = [n for n in CONTRACT_NAMES if n not in contract]
    if missing:  # pragma: no cover - guards a vendor/contract-name skew
        raise VendorUnavailable(f"vendored contract missing names: {missing}")
    return contract


def is_available() -> bool:
    try:
        load_contract()
        return True
    except VendorUnavailable:
        return False
