"""Loader for the mirrored Meridian Copilot-Readiness kernel (I-21 W3.2, Meridian D-579).

The kernel lives in Meridian (``products/meridian_copilot_readiness/generator``) and is mirrored
here byte-identically under ``vendor/meridian_copilot_readiness`` with a ``PIN.json`` (sha256 per
file). ``scripts/check_dataarch_mirror.py`` measures both directions: a local edit is a hard
failure, a Meridian change is reported as drift (``--write-copilot`` re-mirrors from a commit).

**Import bridge.** The mirrored modules import each other absolutely as
``products.meridian_copilot_readiness.generator.<name>`` (Meridian idiom). Rewriting those imports
would end byte identity and make the hash check worthless. ALUCA's ``products`` is a namespace
package, so a ``sys.meta_path`` finder answers **exactly two** names:
``products.meridian_copilot_readiness`` (empty synthetic package) and
``products.meridian_copilot_readiness.generator`` (synthetic package whose ``__path__`` is the
vendor folder). Every other name falls through to the regular resolution — ALUCA's own
``products`` namespace is never touched. Same pattern as ``tooling/superversion/_dataarch_vendor.py``.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import sys
from pathlib import Path
from types import ModuleType

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "meridian_copilot_readiness"
PIN_PATH = VENDOR_DIR / "PIN.json"

_PKG_PARENT = "products.meridian_copilot_readiness"
_PKG = "products.meridian_copilot_readiness.generator"

# The kernel modules ALUCA calls. `loader` carries the intermediate form (`CopilotCore`),
# the next three render the three "Prep data for AI" contents, `zugangswege` holds the
# Microsoft 365 Copilot Chat/Cowork access paths as fields (Meridian D-681, ALUCA D-686).
KERNEL_MODULES = ("loader", "instructions", "verified_answers", "data_schema", "zugangswege")


class VendorUnavailable(RuntimeError):
    """The mirrored kernel is missing or violates its integrity manifest."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pin() -> dict:
    if not PIN_PATH.is_file():
        raise VendorUnavailable(f"no vendor PIN at {PIN_PATH}")
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


def integrity_findings(vendor_dir: Path, pin: dict) -> list[str]:
    """Local deviations from the PIN. Pure, no import side effect."""
    out: list[str] = []
    for entry in pin.get("files", []):
        f = vendor_dir / entry["path"]
        if not f.is_file():
            out.append(f"{entry['path']}: missing from the mirror")
            continue
        got = _sha256(f)
        if got != entry["sha256"]:
            out.append(f"{entry['path']}: edited locally "
                       f"(sha256 {got[:12]}… != pinned {entry['sha256'][:12]}…)")
    return out


def verify() -> dict:
    """Read the PIN and enforce integrity. Raises VendorUnavailable on any deviation."""
    pin = read_pin()
    findings = integrity_findings(VENDOR_DIR, pin)
    if findings:
        raise VendorUnavailable(
            "mirror deviates from its PIN (a mirror is not edited here; change it in Meridian "
            "and re-mirror with scripts/check_dataarch_mirror.py --write-copilot): "
            + "; ".join(findings)
        )
    return pin


class _VendorFinder(importlib.abc.MetaPathFinder):
    """Answers only ``products.meridian_copilot_readiness`` and ``….generator``."""

    def find_spec(self, fullname, path=None, target=None):  # noqa: D102 - MetaPathFinder
        if fullname == _PKG_PARENT:
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = []
            return spec
        if fullname == _PKG:
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = [str(VENDOR_DIR)]
            return spec
        return None


def _install_finder() -> None:
    if not any(isinstance(f, _VendorFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _VendorFinder())


def load_kernel() -> dict[str, ModuleType]:
    """The four kernel modules under their Meridian names, after the integrity check."""
    verify()
    _install_finder()
    return {name: importlib.import_module(f"{_PKG}.{name}") for name in KERNEL_MODULES}
