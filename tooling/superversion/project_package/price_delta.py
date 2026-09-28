"""WB-009: private price delta of a decision alternative, returned to an authorised caller only.

The rate-free comparison (`commercial_impact.py`) stays the persistable view. This module is
its counterpart for the one question the rate-free view cannot answer: what does the
alternative change in cost and price? It evaluates the same hypothetical selection, runs every
linked canon package through `kalkulation()` of the mirrored core, and returns money.

Three rules keep that money where it belongs (ADR-0019 §2.3, ADR-0020):

* **Nothing is written.** No file, no package module, no generated output, no audit payload
  carries a value from here. The result is marked ``persist: false``; the Studio route answers
  ``no-store`` to an admin and logs only that a delta was viewed, with hashes.
* **The core computes, this module sums.** Cost, calculated price, rounded price and list
  price per package come from `kalkulation()`; the module adds them per side and subtracts.
* **No silent zero.** A package the core cannot price is listed under ``unpriced`` with its
  reason, and the totals say how many packages they cover.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from tooling.superversion import preis_kanon_mandant as pkm

from .alternative_impact import _fingerprint, evaluate_alternative
from .commercial_impact import _quantities
from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
_MONEY = ("cost", "price_calculated", "price_rounded", "list_price")


def _side(tenant: dict, plan: dict, architecture: dict) -> dict:
    core = pkm.rechenkern()
    rows, unpriced = [], []
    totals = {key: 0.0 for key in _MONEY}
    for wp in plan.get("work_packages", []):
        canon = wp.get("canon")
        if canon is None:
            continue
        try:
            package = core.paket(tenant, canon["package_ref"])
        except (KeyError, ValueError, SystemExit):
            unpriced.append({"work_package_ref": wp["id"], "reason": f"Canon package {canon['package_ref']} is not in the tenant file."})
            continue
        if core.ist_tm(package):
            # Gemessen 28.09.2026: der gespiegelte Kern rechnet T&M ueber die Meridian-Klassen
            # `delivery`/`architektur` und bricht beim Team-Mandanten ab.
            unpriced.append({"work_package_ref": wp["id"], "reason": "Time-and-material packages are not priced by the mirrored core for the team tenant yet."})
            continue
        quantities, _provenance = _quantities(canon, architecture)
        sheet = core.kalkulation(tenant, package, quantities)
        row = {"work_package_ref": wp["id"], "package_ref": canon["package_ref"], "quantities": quantities,
               "hours": sheet["stunden_gesamt"], "cost": sheet["selbstkosten"],
               "price_calculated": sheet["preis_kalkuliert"], "price_rounded": sheet["preis_gerundet"],
               "list_price": sheet["festpreis"], "below_calculation": bool(sheet.get("unter_kalkulation")),
               "status": sheet["status"]}
        rows.append(row)
        for key in _MONEY:
            totals[key] += float(row[key] or 0.0)
    return {"packages": rows, "totals": {key: round(value, 2) for key, value in totals.items()},
            "priced_packages": len(rows), "unpriced": unpriced}


def compare_price(repository: ProjectPackageRevisionRepository, project_ref: str, baseline_revision: str,
                  decision_ref: str, option_ref: str, *, tenant: dict | None = None) -> dict:
    """Money delta of an alternative. For an authorised caller; never persisted."""
    state = evaluate_alternative(repository, project_ref, baseline_revision, decision_ref, option_ref)
    common = {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
              "decision_ref": decision_ref, "alternative_option_ref": option_ref,
              "price_values_embedded": True, "persist": False, "approval_granted": False}
    if state["blockers"]:
        raise ValueError("Alternative impact is blocked; resolve it before evaluating a price delta: " + "; ".join(state["blockers"]))
    try:
        tenant = tenant if tenant is not None else pkm.lade_mandant()
    except pkm.MandantenwerteFehlen as error:
        return {**common, "price_values_embedded": False, "status": "not_checked", "reason": str(error)}
    findings = pkm.pruefe_mandant(tenant)
    if findings:
        return {**common, "price_values_embedded": False, "status": "tenant_findings", "findings": findings}
    modules = state["compiler"]["modules"]
    base = _side(tenant, modules.get("plan") or {}, modules["architecture_input"])
    alt = _side(tenant, state["projected"]["plan"] or {}, state["projected"]["architecture_input"])
    if state["before_fingerprint"] != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    comparable = {row["package_ref"] for row in base["packages"]} == {row["package_ref"] for row in alt["packages"]} \
        and not base["unpriced"] and not alt["unpriced"]
    return {**common, "status": "evaluated", "currency": tenant.get("waehrung", "EUR"),
            "tenant_fingerprint_sha256": canonical_sha256(tenant),
            "baseline": base, "alternative": alt,
            "delta": {key: round(alt["totals"][key] - base["totals"][key], 2) for key in _MONEY},
            "comparable": comparable,
            "limitations": ["Money comes from the tenant price canon through the mirrored core; values are assumptions until the tenant file is confirmed.",
                            "Not written anywhere: not in the package, not in generated outputs, not in the audit trail.",
                            "Only fixed-price packages are priced; unpriced packages are listed, not counted as zero."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--schemas", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read(100_001))
        if not isinstance(payload, dict) or set(payload) != {"project_ref", "revision_hash", "decision_ref", "option_ref"}:
            raise ValueError("Invalid price delta request")
        if not re.fullmatch(r"[a-f0-9]{64}", str(payload["revision_hash"])):
            raise ValueError("Invalid request revision")
        value = compare_price(ProjectPackageRevisionRepository(args.repository, args.schemas), payload["project_ref"],
                              payload["revision_hash"], payload["decision_ref"], payload["option_ref"])
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=True))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1
    except Exception as error:  # noqa: BLE001 - the bridge needs JSON, never a bare traceback
        print(json.dumps({"ok": False, "error": f"Price delta failed: {type(error).__name__}", "status": 500}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
