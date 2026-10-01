"""Run-cost delta of a decision alternative: what the platform costs per month, baseline vs alternative.

WB-008 compares structure, WB-009 the delivery effort and its price. Neither answers the question a
customer asks about an environment or capacity decision: *what does running it cost?* This module
evaluates the same hypothetical selection (`evaluate_alternative`) and prices the Fabric capacities
that the selected environments actually use.

Rules, deliberately narrow:

* **Public list prices only.** Capacity prices come from `internal/proposal_costing` through its own
  `cost_engine` (Microsoft list price, USD). No tenant rate, no margin, nothing from the price canon
  (ADR-0019, ADR-0020): the run cost is the customer's Azure bill, not our offer.
* **The engine prices, this module sums.** SKU price, reservation discount and the overage ceiling
  come from `cost_engine`; the module adds them per side and subtracts.
* **No silent zero.** A workspace whose capacity is not declared in `architecture_input.capacities`,
  or a SKU without a list price, is listed under ``unpriced``; the totals say how many capacities
  they cover.
* **The overage ceiling stays a ceiling.** Overage is billed only when used; its derived maximum
  (threshold x 3 x PAYG) is reported separately and never added to the monthly total.
* **Nothing is written.** The result is a read-only comparison like WB-008.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from .alternative_impact import _fingerprint, evaluate_alternative
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
_COST_ENGINE = Path(__file__).resolve().parents[3] / "internal" / "proposal_costing" / "tooling" / "cost_engine.py"
#: Monthly view of the daily overage ceiling; Azure list prices use 730 h per month.
_DAYS_PER_MONTH = 730 / 24


@lru_cache(maxsize=1)
def _engine():
    """Load cost_engine by path: the product puts its own ``tooling/`` first and would shadow ours."""
    spec = importlib.util.spec_from_file_location("_aluca_proposal_cost_engine", _COST_ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def run_cost_side(architecture: dict, drivers: dict | None = None) -> dict:
    """Monthly run cost of the capacities used by the selected environments. Pure."""
    engine = _engine()
    drivers = drivers if drivers is not None else engine.load_cost_drivers()
    selected = set(architecture["environments"]["recommended"])
    declared: dict[str, dict] = {}
    unpriced: list[dict] = []
    for row in architecture.get("capacities") or []:
        if row["id"] in declared:
            unpriced.append({"capacity_id": row["id"], "reason": "Capacity is declared twice; neither declaration is priced."})
        declared[row["id"]] = row
    duplicate = {row["capacity_id"] for row in unpriced}
    used: dict[str, list[str]] = {}
    for ws in architecture.get("physical_workspaces") or []:
        if ws["environment"] in selected:
            used.setdefault(ws["capacity_id"], [])
            if ws["environment"] not in used[ws["capacity_id"]]:
                used[ws["capacity_id"]].append(ws["environment"])
    rows, total, ceiling = [], 0.0, 0.0
    for capacity_id in sorted(used):
        if capacity_id in duplicate:
            continue
        row = declared.get(capacity_id)
        if row is None:
            unpriced.append({"capacity_id": capacity_id,
                             "reason": "Used by a selected workspace but not declared in architecture_input.capacities."})
            continue
        reservation = row.get("billing") == "reservation"
        try:
            price = engine._price_by_sku(drivers, row["sku"], use_reservation=reservation)
        except KeyError:
            unpriced.append({"capacity_id": capacity_id, "reason": f"No list price for {row['sku']} in cost_drivers.yaml."})
            continue
        overage = row.get("overage") or {}
        enabled = None if not overage else overage["state"] == "enabled"
        line = engine.compute_overage(drivers, row["sku"], enabled, overage.get("threshold_cu_hours"))
        cap = round(float(line["max_usd_per_day"]) * _DAYS_PER_MONTH, 2)
        rows.append({"capacity_id": capacity_id, "sku": row["sku"], "billing": "reservation" if reservation else "payg",
                     "environments": sorted(used[capacity_id]), "usd_per_month": round(price, 2),
                     "overage": {"enabled": line["enabled"], "threshold_source": line["threshold_source"],
                                 "max_usd_per_month": cap}})
        total += price
        ceiling += cap
    licences = _licences(architecture, rows, drivers)
    licence_total = licences["usd_per_month"] if licences else 0.0
    return {"capacities": rows, "capacity_usd_per_month": round(total, 2), "licences": licences,
            "usd_per_month": round(total + licence_total, 2), "overage_ceiling_usd_per_month": round(ceiling, 2),
            "priced_capacities": len(rows), "unpriced": unpriced}


def _licences(architecture: dict, capacity_rows: list[dict], drivers: dict) -> dict | None:
    """Power BI licences for the report audience, coupled to the production SKU.

    Authors always need Pro. Viewers read without a licence when the production capacity is F64
    or larger (Learn ``enterprise/licenses``; same boundary as Meridian OUT-REPORT and
    ``capacity.FREE_VIEWER_MIN_SKU``); below it every viewer needs Pro. Without a declared
    ``report_audience`` no licence cost is evaluated, and without a priced production capacity the
    boundary is unknown, so viewers are counted as Pro and the row says so.
    """
    audience = architecture.get("report_audience")
    if not audience:
        return None
    engine = _engine()
    pro, _ppu = engine._license_prices(drivers)
    prod = [row for row in capacity_rows if "prod" in row["environments"]]
    sku = max((row["sku"] for row in prod), key=lambda s: int(s[1:]), default=None)
    free_viewers = sku is not None and engine._sku_at_least_f64(sku)
    authors, viewers = int(audience.get("authors", 0)), int(audience.get("viewers", 0))
    pro_users = authors + (0 if free_viewers else viewers)
    return {"authors": authors, "viewers": viewers, "production_sku": sku,
            "viewers_need_pro": not free_viewers, "pro_users": pro_users,
            "pro_usd_per_user_month": pro, "usd_per_month": round(pro_users * pro, 2),
            "basis": ("production SKU F64 or larger: viewers without licence" if free_viewers else
                      "production SKU below F64: every viewer needs Pro" if sku else
                      "no priced production capacity: viewers counted as Pro")}


def compare_run_cost(repository: ProjectPackageRevisionRepository, project_ref: str, baseline_revision: str,
                     decision_ref: str, option_ref: str, *, drivers: dict | None = None) -> dict:
    """Run-cost delta of one declared alternative against the released baseline. Read-only."""
    state = evaluate_alternative(repository, project_ref, baseline_revision, decision_ref, option_ref)
    if state["blockers"]:
        raise ValueError("Alternative impact is blocked; resolve it before evaluating a run-cost delta: "
                         + "; ".join(state["blockers"]))
    engine = _engine()
    drivers = drivers if drivers is not None else engine.load_cost_drivers()
    base_arch = state["compiler"]["modules"]["architecture_input"]
    if not base_arch.get("capacities"):
        return {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
                "decision_ref": decision_ref, "alternative_option_ref": option_ref, "status": "not_evaluated",
                "reason": "architecture_input declares no capacities; the run cost is not guessed from workspaces.",
                "persist": False, "approval_granted": False}
    base = run_cost_side(base_arch, drivers)
    alt = run_cost_side(state["projected"]["architecture_input"], drivers)
    if state["before_fingerprint"] != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    return {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
            "decision_ref": decision_ref, "alternative_option_ref": option_ref, "status": "evaluated",
            "currency": "USD", "price_basis": "Microsoft list price", "price_valid_from": str(drivers.get("valid_from")),
            "baseline": base, "alternative": alt,
            "delta": {"usd_per_month": round(alt["usd_per_month"] - base["usd_per_month"], 2),
                      "capacity_usd_per_month": round(alt["capacity_usd_per_month"] - base["capacity_usd_per_month"], 2),
                      "licence_usd_per_month": round((alt["licences"] or {}).get("usd_per_month", 0.0)
                                                     - (base["licences"] or {}).get("usd_per_month", 0.0), 2),
                      "usd_per_year": round(12 * (alt["usd_per_month"] - base["usd_per_month"]), 2),
                      "overage_ceiling_usd_per_month": round(alt["overage_ceiling_usd_per_month"]
                                                             - base["overage_ceiling_usd_per_month"], 2),
                      "capacities_removed": sorted({r["capacity_id"] for r in base["capacities"]}
                                                   - {r["capacity_id"] for r in alt["capacities"]}),
                      "capacities_added": sorted({r["capacity_id"] for r in alt["capacities"]}
                                                 - {r["capacity_id"] for r in base["capacities"]})},
            "comparable": not base["unpriced"] and not alt["unpriced"],
            "persist": False, "approval_granted": False, "tenant_actions_performed": False,
            "limitations": [
                "Capacity list prices in USD from cost_drivers.yaml; regional price differences and currency are not applied.",
                "Paused hours are not modelled: a pay-as-you-go capacity is priced for the full month.",
                "Overage is a ceiling derived from the threshold (threshold x 3 x PAYG), billed only when used; it is not in the monthly total.",
                "Licences only for a declared report_audience: authors always Pro, viewers Pro below an F64 production capacity; PPU is not modelled.",
                "OneLake storage and workspace-monitoring ingestion are not part of this delta.",
                "A capacity shared by several environments costs the same whether one or all of them run on it."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--schemas", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read(100_001))
        if not isinstance(payload, dict) or set(payload) != {"project_ref", "revision_hash", "decision_ref", "option_ref"}:
            raise ValueError("Invalid run-cost request")
        if not re.fullmatch(r"[a-f0-9]{64}", str(payload["revision_hash"])):
            raise ValueError("Invalid request revision")
        value = compare_run_cost(ProjectPackageRevisionRepository(args.repository, args.schemas), payload["project_ref"],
                                 payload["revision_hash"], payload["decision_ref"], payload["option_ref"])
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=True))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1
    except Exception as error:  # noqa: BLE001 - the bridge needs JSON, never a bare traceback
        print(json.dumps({"ok": False, "error": f"Run-cost delta failed: {type(error).__name__}", "status": 500}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
