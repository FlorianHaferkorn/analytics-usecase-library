"""Run-cost delta of a decision alternative: what the platform costs per month, baseline vs alternative.

WB-008 compares structure, WB-009 the delivery effort and its price. Neither answers the question a
customer asks about an environment or capacity decision: *what does running it cost?* This module
evaluates the same hypothetical selection (`evaluate_alternative`) and prices the Fabric capacities
that the selected environments actually use, the Power BI licences of the report audience and the
workspace-monitoring storage.

Rules, deliberately narrow:

* **Public list prices only.** Prices come from `internal/proposal_costing` through its own
  `cost_engine` (Microsoft list price; regional rates from the Azure Retail Prices API). No tenant
  rate, no margin, nothing from the price canon (ADR-0019, ADR-0020): the run cost is the customer's
  Azure bill, not our offer.
* **Region and currency from the package.** `architecture_input.region` selects the regional rate;
  `cost_currency` (USD default, EUR) selects Microsoft's own price list in that currency. A region
  without a rate falls back to the US table, in USD only; the result says which basis it used.
* **The engine prices, this module sums.** Capacity price, reservation discount, overage ceiling and
  storage rate come from `cost_engine`; the module adds them per side and subtracts.
* **No silent zero.** Undeclared capacities, SKUs or currencies without a price are listed under
  ``unpriced``, and ``comparable`` is false.
* **The overage ceiling stays a ceiling.** Overage is billed only when used; its derived maximum
  (threshold x 3 x PAYG) is reported separately and never added to the monthly total.
* **Nothing is written.** The result is a read-only comparison like WB-008.
* **The monitoring capacity follows the blueprint.** `monitoring.capacity_id` names it explicitly;
  without it the first capacity with `purpose: monitoring` hosts the workspace-monitoring
  Eventhouse, the same convention as Meridian's `kapazitaet_stufen.monitoring_kapazitaet` (D-615).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

from .alternative_impact import _fingerprint, evaluate_alternative
from .repository import ProjectPackageRevisionRepository

VERSION = "1.3.0"
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


def _price_capacity(engine, drivers: dict, row: dict, region: str | None, currency: str) -> dict:
    """One declared capacity at list price, with its overage ceiling. Raises KeyError if unpriced."""
    reservation = row.get("billing") == "reservation"
    price, basis = engine.capacity_price_per_month(drivers, row["sku"], region=region, currency=currency,
                                                   use_reservation=reservation)
    rates = engine.regional_rates(drivers, region, currency) if region else None
    overage = row.get("overage") or {}
    enabled = None if not overage else overage["state"] == "enabled"
    line = engine.compute_overage(drivers, row["sku"], enabled, overage.get("threshold_cu_hours"),
                                  rates["payg_per_cu_hour"] if rates else None)
    return {"capacity_id": row["id"], "sku": row["sku"], "billing": "reservation" if reservation else "payg",
            "price_basis": basis, "per_month": round(price, 2),
            "overage": {"enabled": line["enabled"], "threshold_source": line["threshold_source"],
                        "max_per_month": round(float(line["max_usd_per_day"]) * _DAYS_PER_MONTH, 2)}}


def monitoring_capacity(architecture: dict) -> dict | None:
    """Which capacity hosts workspace monitoring, and where that came from. Pure.

    The explicit ``monitoring.capacity_id`` wins; otherwise the first declared capacity with
    ``purpose: monitoring``. A disagreement between the two is reported, not resolved silently.
    """
    explicit = (architecture.get("monitoring") or {}).get("capacity_id")
    tagged = [row["id"] for row in architecture.get("capacities") or []
              if str(row.get("purpose") or "").strip().lower() == "monitoring"]
    if explicit:
        found = {"capacity_id": explicit, "source": "monitoring.capacity_id"}
        if tagged and explicit not in tagged:
            found["note"] = (f"monitoring.capacity_id names {explicit!r}, the blueprint tags "
                             f"{tagged[0]!r} with purpose: monitoring; the explicit id is priced.")
        return found
    if tagged:
        return {"capacity_id": tagged[0], "source": "capacities[].purpose"}
    return None


def run_cost_side(architecture: dict, drivers: dict | None = None) -> dict:
    """Monthly run cost of one package state. Pure."""
    engine = _engine()
    drivers = drivers if drivers is not None else engine.load_cost_drivers()
    currency = architecture.get("cost_currency", "USD")
    region = architecture.get("region")
    selected = set(architecture["environments"]["recommended"])
    declared: dict[str, dict] = {}
    unpriced: list[dict] = []
    for row in architecture.get("capacities") or []:
        if row["id"] in declared:
            unpriced.append({"item": row["id"], "reason": "Capacity is declared twice; neither declaration is priced."})
        declared[row["id"]] = row
    duplicate = {row["item"] for row in unpriced}
    used: dict[str, list[str]] = {}
    for ws in architecture.get("physical_workspaces") or []:
        if ws["environment"] in selected:
            envs = used.setdefault(ws["capacity_id"], [])
            if ws["environment"] not in envs:
                envs.append(ws["environment"])
    monitoring = architecture.get("monitoring") or {}
    host = monitoring_capacity(architecture)
    if host:
        used.setdefault(host["capacity_id"], []).append("monitoring")
    rows, total, ceiling = [], 0.0, 0.0
    for capacity_id in sorted(used):
        if capacity_id in duplicate:
            continue
        row = declared.get(capacity_id)
        if row is None:
            unpriced.append({"item": capacity_id,
                             "reason": "Used by a selected workspace or by monitoring but not declared in architecture_input.capacities."})
            continue
        try:
            priced = _price_capacity(engine, drivers, row, region, currency)
        except KeyError as error:
            unpriced.append({"item": capacity_id, "reason": f"{row['sku']}: {error.args[0] if error.args else 'no list price'}."})
            continue
        priced["environments"] = sorted(used[capacity_id])
        rows.append(priced)
        total += priced["per_month"]
        ceiling += priced["overage"]["max_per_month"]
    licences = _licences(architecture, rows, drivers, currency, unpriced)
    storage = _monitoring_storage(monitoring, drivers, region, currency, unpriced)
    extra = (licences or {}).get("per_month") or 0.0
    extra += (storage or {}).get("per_month") or 0.0
    return {"currency": currency, "capacities": rows, "capacity_per_month": round(total, 2), "licences": licences,
            "monitoring_storage": storage, "monitoring_capacity": host, "per_month": round(total + extra, 2),
            "overage_ceiling_per_month": round(ceiling, 2), "priced_capacities": len(rows), "unpriced": unpriced}


def _licences(architecture: dict, capacity_rows: list[dict], drivers: dict, currency: str,
              unpriced: list[dict]) -> dict | None:
    """Power BI licences for the report audience, coupled to the production SKU.

    Authors always need Pro. Viewers read without a licence when the production capacity is F64
    or larger (Learn ``enterprise/licenses``; same boundary as Meridian OUT-REPORT and
    ``capacity.FREE_VIEWER_MIN_SKU``); below it every viewer needs Pro. Without a declared
    ``report_audience`` no licence cost is evaluated. USD and EUR come from Microsoft's own price
    list in that currency (``price_<cur>_per_month``); a currency without a recorded list price
    is counted but not priced, never converted.
    """
    audience = architecture.get("report_audience")
    if not audience:
        return None
    engine = _engine()
    prod = [row for row in capacity_rows if "prod" in row["environments"]]
    sku = max((row["sku"] for row in prod), key=lambda s: int(s[1:]), default=None)
    free_viewers = sku is not None and engine._sku_at_least_f64(sku)
    authors, viewers = int(audience.get("authors", 0)), int(audience.get("viewers", 0))
    pro_users = authors + (0 if free_viewers else viewers)
    result = {"authors": authors, "viewers": viewers, "production_sku": sku, "viewers_need_pro": not free_viewers,
              "pro_users": pro_users,
              "basis": ("production SKU F64 or larger: viewers without licence" if free_viewers else
                        "production SKU below F64: every viewer needs Pro" if sku else
                        "no priced production capacity: viewers counted as Pro")}
    pro, _ppu = engine._license_prices(drivers, currency)
    if pro is None:
        unpriced.append({"item": "power_bi_licences", "reason": f"No {currency} list price for Power BI Pro in cost_drivers.yaml."})
        return {**result, "pro_per_user_month": None, "per_month": None}
    return {**result, "pro_per_user_month": pro, "per_month": round(pro_users * pro, 2)}


def _monitoring_storage(monitoring: dict, drivers: dict, region: str | None, currency: str,
                        unpriced: list[dict]) -> dict | None:
    """OneLake storage of the workspace-monitoring Eventhouse (retained GB x hot storage rate).

    Monitoring compute is CU on the capacity that hosts the Eventhouse and is already inside that
    capacity's price; only storage is billed on its own (Learn ``real-time-intelligence-consumption``).
    """
    if monitoring.get("retained_gb") is None:
        return None
    engine = _engine()
    rates = engine.regional_rates(drivers, region, currency) if region else None
    if rates is None:
        if currency != "USD":
            unpriced.append({"item": "monitoring_storage", "reason": f"No {currency} storage price for region {region!r}."})
            return {"retained_gb": monitoring["retained_gb"], "per_gb_month": None, "per_month": None}
        rate = float(drivers["onelake_storage"]["usd_per_gb_month"])
    else:
        rate = rates["onelake_hot_per_gb_month"]
    return {"retained_gb": monitoring["retained_gb"], "per_gb_month": rate,
            "per_month": round(float(monitoring["retained_gb"]) * rate, 2)}


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
    common = {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
              "decision_ref": decision_ref, "alternative_option_ref": option_ref,
              "persist": False, "approval_granted": False}
    if not base_arch.get("capacities"):
        return {**common, "status": "not_evaluated",
                "reason": "architecture_input declares no capacities; the run cost is not guessed from workspaces."}
    base = run_cost_side(base_arch, drivers)
    alt = run_cost_side(state["projected"]["architecture_input"], drivers)
    if state["before_fingerprint"] != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    part = lambda side, key: ((side.get(key) or {}).get("per_month") or 0.0)  # noqa: E731
    region = base_arch.get("region")
    regional = engine.regional_rates(drivers, region, base["currency"]) is not None
    fetched = (drivers.get("fabric_regions") or {}).get("fetched")
    return {**common, "status": "evaluated", "currency": base["currency"], "region": region,
            "price_basis": ("Microsoft list price, regional rate (Azure Retail Prices API)" if regional
                            else "Microsoft list price, US table (region not in cost_drivers.yaml)"),
            "price_valid_from": str(fetched if regional else drivers.get("valid_from")),
            "baseline": base, "alternative": alt,
            "delta": {"per_month": round(alt["per_month"] - base["per_month"], 2),
                      "per_year": round(12 * (alt["per_month"] - base["per_month"]), 2),
                      "capacity_per_month": round(alt["capacity_per_month"] - base["capacity_per_month"], 2),
                      "licence_per_month": round(part(alt, "licences") - part(base, "licences"), 2),
                      "monitoring_storage_per_month": round(part(alt, "monitoring_storage") - part(base, "monitoring_storage"), 2),
                      "overage_ceiling_per_month": round(alt["overage_ceiling_per_month"] - base["overage_ceiling_per_month"], 2),
                      "capacities_removed": sorted({r["capacity_id"] for r in base["capacities"]}
                                                   - {r["capacity_id"] for r in alt["capacities"]}),
                      "capacities_added": sorted({r["capacity_id"] for r in alt["capacities"]}
                                                 - {r["capacity_id"] for r in base["capacities"]})},
            "comparable": not base["unpriced"] and not alt["unpriced"],
            "tenant_actions_performed": False,
            "limitations": [
                "List prices from cost_drivers.yaml: regional PAYG rates fetched from the Azure Retail Prices API, reservation discount from the SKU table; no negotiated discount.",
                "Paused hours are not modelled: a pay-as-you-go capacity is priced for the full month.",
                "Overage is a ceiling derived from the threshold (threshold x 3 x PAYG), billed only when used; it is not in the monthly total.",
                "Licences only for a declared report_audience, in USD or EUR (Microsoft list price per currency, annual billing, excl. VAT): authors always Pro, viewers Pro below an F64 production capacity; PPU is not modelled.",
                "Workspace monitoring: compute runs on the hosting capacity (priced there), storage only for a declared retained_gb at the OneLake hot rate.",
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
