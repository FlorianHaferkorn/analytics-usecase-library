#!/usr/bin/env python3
"""Dataarch contract-surface mirror-drift sensor (ADR-0051 / I-20 · Tier-3 #8).

ALUCA mirrors Meridian's neutral-IR **contract surface** (concept/gov registries + ODCS) by hand —
`dataarch_engine` is NOT vendored, so unlike the pbi_engine mirror there is no vendored-file hash to
diff. This sensor closes that gap: when a Meridian checkout is reachable it compares the **public
contract** of both sides and reports drift, so a Meridian-side change can no longer silently desync
ALUCA's mirror.

DOCTRINE (same as `check_superversion_pins.py`): **reports drift, never bumps.** Advisory (exit 0) by
default; `--strict` turns drift into an error (exit 1) for a release gate. Meridian unreachable →
soft-skip (exit 0) — the sibling checkout is a dev convenience, not a CI guarantee.

Compared contract (the mirror's guarantees):
  * architecture: DEFAULT_CONCEPT + the registered concept ids;
  * governance: DEFAULT_GOVERNANCE_CONCEPT + concept ids + each id's contract_standard;
  * ODCS: ODCS_API_VERSION + the public API function names.

Meridian root resolution: ``$MERIDIAN_ROOT`` env, else the sibling ``../Freelancing`` of this repo.
Modules are loaded **by path** (concepts/governance are self-contained) or **read as source** (odcs
imports a sibling), never via ``import core`` — ALUCA owns its own ``core`` package.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MER_REL = "core/dataarch_engine/blueprint"
_ALU_REL = "tooling/superversion"
_ODCS_PUBLIC = ("to_odcs", "emit_odcs", "to_odcs_ingestion", "emit_odcs_ingestion",
                "from_odcs", "import_sql_table", "odcs_to_catalog", "validate_odcs")

# Zweite, stärkere Hälfte des Sensors (SHARED_SUBSTANCE.md Klasse A): die offiziell
# belegten Emitter werden nicht per Hand nachgezogen, sondern **byte-identisch**
# gespiegelt. Dafür genügt kein Vertragsflächen-Vergleich — hier wird Datei-sha256
# gediffed, gegen Meridian *und* gegen das lokale PIN.
_VENDOR_REL = "tooling/superversion/vendor/meridian_dataarch"


def _meridian_root() -> Path | None:
    env = os.environ.get("MERIDIAN_ROOT")
    if env:
        p = Path(env).expanduser()
        return p if (p / _MER_REL / "concepts.py").is_file() else None
    sibling = REPO_ROOT.parent / "Freelancing"
    return sibling if (sibling / _MER_REL / "concepts.py").is_file() else None


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _odcs_facts(source: Path) -> dict:
    text = source.read_text(encoding="utf-8")
    version = re.search(r'ODCS_API_VERSION\s*=\s*"([^"]+)"', text)
    defs = set(re.findall(r'^def (\w+)\(', text, re.M))
    return {"api_version": version.group(1) if version else None,
            "public_api": sorted(d for d in defs if d in _ODCS_PUBLIC)}


def _extract(concepts_py: Path, gov_py: Path, odcs_py: Path, tag: str) -> dict:
    c = _load(f"_{tag}_concepts", concepts_py)
    g = _load(f"_{tag}_gov", gov_py)
    gov_standards = {i: g.get_governance_concept(i).profile().get("contract_standard")
                     for i in g.available_governance_concepts()}
    return {
        "arch_default": c.DEFAULT_CONCEPT,
        "arch_concepts": sorted(c.available_concepts()),
        "gov_default": g.DEFAULT_GOVERNANCE_CONCEPT,
        "gov_concepts": sorted(g.available_governance_concepts()),
        "gov_standards": gov_standards,
        "odcs": _odcs_facts(odcs_py),
    }


_CONTRACT_KEYS = ("arch_default", "arch_concepts", "gov_default", "gov_concepts", "gov_standards", "odcs")


def _diff(meridian: dict, aluca: dict) -> list[str]:
    """Return one line per drifted contract field (empty = in sync). Pure, unit-testable."""
    return [f"  {k}: Meridian={meridian.get(k)!r}  vs  ALUCA={aluca.get(k)!r}"
            for k in _CONTRACT_KEYS if meridian.get(k) != aluca.get(k)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vendor_pin() -> dict | None:
    """The vendored subtree's PIN manifest, or None when nothing is vendored yet."""
    pin = REPO_ROOT / _VENDOR_REL / "PIN.json"
    return json.loads(pin.read_text(encoding="utf-8")) if pin.is_file() else None


def vendor_integrity(pin: dict) -> list[str]:
    """Local edits inside the byte-identical mirror. Pure; runs without Meridian."""
    root = REPO_ROOT / _VENDOR_REL
    out: list[str] = []
    for entry in pin.get("files", []):
        f = root / entry["path"]
        if not f.is_file():
            out.append(f"  {entry['path']}: missing from the mirror")
            continue
        got = _sha256(f)
        if got != entry["sha256"]:
            out.append(f"  {entry['path']}: edited locally "
                       f"(sha256 {got[:12]}… != pinned {entry['sha256'][:12]}…)")
    return out


def vendor_upstream_drift(pin: dict, meridian_blueprint: Path) -> list[str]:
    """Meridian-side changes the mirror has not picked up yet. Pure."""
    out: list[str] = []
    for entry in pin.get("files", []):
        src = meridian_blueprint / entry["path"]
        if not src.is_file():
            out.append(f"  {entry['path']}: removed in Meridian, still mirrored here")
            continue
        if _sha256(src) != entry["sha256"]:
            out.append(f"  {entry['path']}: Meridian moved on — re-mirror (--write)")
    return out


def write_vendor(meridian_blueprint: Path, pin: dict) -> dict:
    """Re-copy the mirrored files and rewrite PIN.json. Deliberately manual, never in CI."""
    root = REPO_ROOT / _VENDOR_REL
    root.mkdir(parents=True, exist_ok=True)
    names = [e["path"] for e in pin.get("files", [])]
    for name in names:
        shutil.copyfile(meridian_blueprint / name, root / name)
    fresh = {
        "source_repo": pin.get("source_repo", "Freelancing"),
        "source_path": pin.get("source_path", _MER_REL),
        "doctrine": pin.get("doctrine",
                            "SHARED_SUBSTANCE.md class A — home is Meridian, ALUCA mirrors."),
        "files": [{"path": n, "sha256": _sha256(root / n)} for n in names],
    }
    (root / "PIN.json").write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    return fresh


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    strict = "--strict" in argv
    write = "--write" in argv

    pin = vendor_pin()

    # The vendored subtree's integrity does not need Meridian — check it first, always.
    # A local edit is not drift, it is a doctrine breach: the mirror is changed in
    # Meridian and re-mirrored, never patched here.
    if pin is not None:
        local = vendor_integrity(pin)
        if local:
            print("[check-dataarch-mirror] vendored emitters edited locally — change them in "
                  "Meridian and re-mirror instead:")
            for line in local:
                print(line)
            return 1

    mer = _meridian_root()
    if mer is None:
        if pin is not None:
            print(f"[check-dataarch-mirror] vendored emitters OK ({len(pin['files'])} file(s), "
                  f"local integrity)")
        print("[check-dataarch-mirror] Meridian checkout not reachable "
              "($MERIDIAN_ROOT or ../Freelancing) — SKIP (dev-only cross-repo diff)")
        return 0

    if write:
        if pin is None:
            print(f"[check-dataarch-mirror] --write needs an existing "
                  f"{_VENDOR_REL}/PIN.json listing what to mirror")
            return 1
        fresh = write_vendor(mer / _MER_REL, pin)
        print(f"[check-dataarch-mirror] re-mirrored {len(fresh['files'])} file(s) from {mer}")
        return 0

    meridian = _extract(mer / _MER_REL / "concepts.py",
                        mer / _MER_REL / "governance_concepts.py",
                        mer / _MER_REL / "odcs.py", "mer")
    aluca = _extract(REPO_ROOT / _ALU_REL / "architecture_concepts.py",
                     REPO_ROOT / _ALU_REL / "governance_concepts.py",
                     REPO_ROOT / _ALU_REL / "odcs.py", "alu")

    drift = _diff(meridian, aluca)
    if pin is not None:
        drift += vendor_upstream_drift(pin, mer / _MER_REL)

    if not drift:
        vendored = len(pin["files"]) if pin else 0
        print(f"[check-dataarch-mirror] OK — mirror in sync with Meridian ({mer}); "
              f"contract surface + {vendored} vendored file(s)")
        return 0

    print(f"[check-dataarch-mirror] DRIFT vs Meridian ({mer}) — re-mirror:")
    for line in drift:
        print(line)
    if strict:
        print("[check-dataarch-mirror] --strict: drift is a hard failure")
        return 1
    print("[check-dataarch-mirror] advisory (reports drift, never bumps) — Exit 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
