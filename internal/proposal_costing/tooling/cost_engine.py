"""
Proposal Costing – Cost engine.
Loads cost_drivers.yaml and scenarios.yaml, computes monthly/yearly costs from scenario + overrides.
Supports reservation pricing, viewer note (F64 threshold), optional OneLake storage, scope and assumptions.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

# Fabric SKU order for F64 threshold (prod >= F64 => viewers Free).
_FABRIC_SKU_CU = ("F2", "F4", "F8", "F16", "F32", "F64", "F128", "F256", "F512", "F1024", "F2048")

_INLINE_DEFAULTS: dict[str, Any] = {
    "scope_in": ["Fabric Capacity (Pay-as-you-go or reservation)", "Power BI Pro / PPU licenses as specified"],
    "scope_out": ["Implementation / Professional Services", "Training", "OneLake Storage (unless estimated)", "Network egress", "Local taxes"],
    "default_contract_term_months": 12,
    "default_region": "West Europe",
    "price_basis": "Microsoft list price (USD)",
    "viewer_note_below_f64": "With production capacity below F64, report viewers require Power BI Pro.",
    "viewer_note_f64_plus": "With F64+ production capacity, viewers can use the Free license.",
    "default_quote_valid_days": 30,
    "building_block_labels": {
        "fabric_capacity": "Fabric Capacity",
        "power_bi": "Power BI (Pro / PPU)",
        "onelake_storage": "OneLake Storage",
        "implementation": "Implementation (one-time)",
        "maintenance": "Maintenance (per year)",
    },
}


def _product_root() -> Path:
    """Root of proposal_costing product (parent of tooling/)."""
    return Path(__file__).resolve().parent.parent


def _capacity_module():
    """Load tooling/superversion/capacity.py — the single home of the Learn capacity facts.

    Loaded by file path because this product puts its own ``tooling/`` on sys.path, which
    would shadow the repo-level ``tooling`` package. capacity.py has no imports of its own.
    """
    path = Path(__file__).resolve().parents[3] / "tooling" / "superversion" / "capacity.py"
    spec = importlib.util.spec_from_file_location("_aluca_superversion_capacity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_CAPACITY = _capacity_module()
_HOURS_PER_MONTH = 730  # Azure monthly list prices are hourly rate x 730 h.


def payg_usd_per_cu_hour(drivers: dict[str, Any], sku: str) -> float:
    """PAYG price per CU hour, derived from the monthly list price in cost_drivers.yaml.

    Derived, not a second price source: monthly price / (CU x 730 h). Keeps the overage and
    planning lines on the same price basis as the capacity line of the same quote.
    """
    return _price_by_sku(drivers, sku) / (_CAPACITY.CU[sku] * _HOURS_PER_MONTH)


def region_key(region: str | None) -> str:
    """'West Europe', 'west-europe' and 'westeurope' name the same Azure region."""
    return "".join(ch for ch in str(region or "").lower() if ch.isalnum())


def regional_rates(drivers: dict[str, Any], region: str | None, currency: str = "USD") -> dict[str, float] | None:
    """PAYG per CU hour and OneLake hot per GB-month for one region and currency, or None if unknown."""
    row = ((drivers.get("fabric_regions") or {}).get("regions") or {}).get(region_key(region))
    cur = currency.lower()
    if not row or f"payg_{cur}_per_cu_hour" not in row:
        return None
    return {"payg_per_cu_hour": float(row[f"payg_{cur}_per_cu_hour"]),
            "onelake_hot_per_gb_month": float(row[f"onelake_hot_{cur}_per_gb_month"])}


def capacity_price_per_month(drivers: dict[str, Any], sku: str, *, region: str | None = None,
                             currency: str = "USD", use_reservation: bool = False) -> tuple[float, str]:
    """Monthly list price of one capacity and where it came from.

    With a known region: CU x regional PAYG rate x 730 h, reservation discount from the SKU table.
    Without one: the SKU table (US price, USD only). Raises KeyError when neither applies.
    """
    rates = regional_rates(drivers, region, currency) if region else None
    if rates is None:
        if currency.upper() != "USD":
            raise KeyError(f"No {currency.upper()} price for region {region!r}")
        return _price_by_sku(drivers, sku, use_reservation=use_reservation), "sku_table_us"
    price = _CAPACITY.CU[sku] * rates["payg_per_cu_hour"] * _HOURS_PER_MONTH
    if use_reservation:
        row = next((r for r in drivers.get("fabric_capacity", []) if r.get("sku") == sku), None)
        if row is None:
            raise KeyError(f"No reservation discount for {sku}")
        price *= 1 - float(row.get("reservation_discount_pct", 0)) / 100.0
    return price, f"region:{region_key(region)}"


def compute_overage(drivers: dict[str, Any], sku: str, enabled: bool | None = None,
                    threshold_cu_hours: float | None = None,
                    payg_per_cu_hour: float | None = None, currency: str = "USD") -> dict[str, Any]:
    """Capacity-overage line for the production SKU.

    `max_per_day` is in `currency` (the currency of `payg_per_cu_hour`); `max_usd_per_day`
    stays as an alias only for USD so a EUR amount never carries a USD name.

    enabled False: overage is off, no cost line. Otherwise the threshold is either the
    customer's (threshold_cu_hours) or Microsoft's default at capacity creation (25 % of
    the daily CU hours), in which case the decision is an open customer question.
    max_usd_per_day = threshold x 3 x PAYG per CU hour is derived, not measured, and not
    a cap: the threshold is checked every 5 minutes and running operations continue.
    """
    cur = currency.upper()
    if enabled is False:
        off = {"sku": sku, "enabled": False, "max_per_day": 0.0, "currency": cur,
               "threshold_source": "customer"}
        if cur == "USD":
            off["max_usd_per_day"] = 0.0
        return off
    prof = _CAPACITY.overage_profile(sku, threshold_cu_hours,
                                     payg_per_cu_hour if payg_per_cu_hour is not None
                                     else payg_usd_per_cu_hour(drivers, sku))
    line = {
        "sku": sku,
        "enabled": True,  # on by default for new F capacities unless switched off
        "cu_hours_per_day": prof["cu_hours_per_day"],
        "threshold_cu_hours": prof["threshold_cu_hours"],
        "threshold_source": prof["threshold_source"],
        "recommended_max_threshold_cu_hours": prof["recommended_max_threshold_cu_hours"],
        "above_recommended_max": prof["above_recommended_max"],
        "quota_cu_required": prof["quota_cu_required"],
        "max_per_day": prof["max_cost_per_day_usd"],
        "currency": cur,
        "evidence": prof["evidence"],
        "caveat": prof["caveat"],
        "customer_question": prof.get("customer_question"),
    }
    if cur == "USD":
        line["max_usd_per_day"] = line["max_per_day"]
    return line


def compute_planning(drivers: dict[str, Any], sessions: dict[str, int], sku: str,
                     payg_per_cu_hour: float | None = None, currency: str = "USD") -> dict[str, Any]:
    """Fabric Planning sessions as a capacity cost position on the production SKU.

    Sessions consume CU of the capacity they run on, so the USD figure is the share of the
    capacity price they occupy (CU hours x PAYG per CU hour), already inside the capacity
    line — shown for transparency, not added to the total. `payg_per_cu_hour` is the
    regional rate from compute(); without it the US table applies (eastus, 0.18 USD).
    """
    load = _CAPACITY.planning_load(sessions, sku)
    rate = payg_per_cu_hour if payg_per_cu_hour is not None else payg_usd_per_cu_hour(drivers, sku)
    load["equivalent_per_session_window"] = round(load["cu_hours_per_session_window"] * rate, 2)
    load["currency"] = currency.upper()
    if load["currency"] == "USD":
        load["usd_equivalent_per_session_window"] = load["equivalent_per_session_window"]
    load["included_in_capacity_total"] = True
    load["evidence"] = "derived"
    return load


def load_cost_drivers(product_root: Path | None = None) -> dict[str, Any]:
    """Load model/cost_drivers.yaml."""
    root = product_root or _product_root()
    path = root / "model" / "cost_drivers.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Cost drivers not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_scenarios(product_root: Path | None = None) -> dict[str, Any]:
    """Load model/scenarios.yaml."""
    root = product_root or _product_root()
    path = root / "model" / "scenarios.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Scenarios not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_proposal_defaults(product_root: Path | None = None) -> dict[str, Any]:
    """Load model/proposal_defaults.yaml. Falls back to _INLINE_DEFAULTS if missing."""
    root = product_root or _product_root()
    path = root / "model" / "proposal_defaults.yaml"
    if not path.exists():
        return _INLINE_DEFAULTS.copy()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out = _INLINE_DEFAULTS.copy()
    for key in _INLINE_DEFAULTS:
        if key in data:
            out[key] = data[key]
    for key in data:
        if key not in out:
            out[key] = data[key]
    return out


def load_role_allocation(product_root: Path | None = None, path_override: Path | str | None = None) -> dict[str, Any]:
    """Load role allocation YAML. Returns { roles_source, allocations } or empty allocations if file missing."""
    root = product_root or _product_root()
    path = Path(path_override) if path_override else root / "model" / "role_allocation.yaml"
    if not path.is_absolute():
        path = root / path if path_override else root / "model" / "role_allocation.yaml"
    if not path.exists():
        return {"roles_source": "core", "allocations": []}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {"roles_source": data.get("roles_source", "core"), "allocations": data.get("allocations", [])}


def _load_org_roles_for_roles(roles_source: str, product_root: Path) -> dict[str, dict[str, Any]]:
    """Load org_roles.yaml; return dict role_id -> { title, domain }."""
    root = product_root or _product_root()
    if roles_source == "core":
        org_path = root.parent.parent / "core" / "organization" / "org_roles.yaml"
    else:
        org_path = root.parent.parent / roles_source if not Path(roles_source).is_absolute() else Path(roles_source)
    if not org_path.exists():
        return {}
    with open(org_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    by_id: dict[str, dict[str, Any]] = {}
    for r in data.get("roles", []):
        rid = r.get("id")
        if rid:
            by_id[rid] = {"title": r.get("title", rid), "domain": r.get("domain", "")}
    return by_id


def load_projection(product_root: Path | None = None) -> dict[str, Any]:
    """Load model/projection.yaml. Returns { horizons, tco_years }; empty if file missing."""
    root = product_root or _product_root()
    path = root / "model" / "projection.yaml"
    if not path.exists():
        return {"horizons": [], "tco_years": []}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {"horizons": data.get("horizons", []), "tco_years": data.get("tco_years", [])}


def load_product_packages(product_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load model/product_packages.yaml. Returns dict package_id -> package; empty if file missing."""
    root = product_root or _product_root()
    path = root / "model" / "product_packages.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    packages = data.get("packages") or {}
    return dict(packages) if isinstance(packages, dict) else {}


def _ftes_from_role_allocation(role_allocation: dict[str, Any], org_roles_by_id: dict[str, dict[str, Any]]) -> tuple[float, float, list[dict[str, Any]]]:
    """Sum FTE by phase; build role_breakdown with title, domain. Returns (impl_fte, maint_fte, role_breakdown)."""
    impl = 0.0
    maint = 0.0
    breakdown: list[dict[str, Any]] = []
    for a in role_allocation.get("allocations", []):
        rid = a.get("role_id", "")
        fte = float(a.get("fte", 0))
        phase = (a.get("phase") or "").strip().lower()
        person = (a.get("person") or a.get("contact") or "").strip()
        info = org_roles_by_id.get(rid, {})
        breakdown.append({"role_id": rid, "title": info.get("title", rid), "domain": info.get("domain", ""), "fte": fte, "phase": phase, "person": person})
        if phase == "implementation":
            impl += fte
        elif phase == "maintenance":
            maint += fte
    return impl, maint, breakdown


def _sku_at_least_f64(sku: str) -> bool:
    """True if SKU is F64 or larger (viewers Free)."""
    if not sku or sku not in _FABRIC_SKU_CU:
        return False
    return _FABRIC_SKU_CU.index(sku) >= _FABRIC_SKU_CU.index("F64")


def _price_by_sku(drivers: dict[str, Any], sku: str, use_reservation: bool = False) -> float:
    """Return USD/month for a Fabric SKU. If use_reservation, apply reservation_discount_pct."""
    for item in drivers.get("fabric_capacity", []):
        if item.get("sku") == sku:
            price = float(item["price_usd_per_month"])
            if use_reservation:
                discount = float(item.get("reservation_discount_pct", 0)) / 100.0
                price = price * (1 - discount)
            return price
    raise KeyError(f"Unknown Fabric SKU: {sku}")


def _license_prices(drivers: dict[str, Any], currency: str = "USD") -> tuple[float | None, float | None]:
    """Return (pro_per_month, ppu_per_month) in `currency`.

    USD keeps the old behaviour (0.0 for a missing row). Any other currency reads
    `price_<cur>_per_month` and returns None where Microsoft's list price in that currency is not
    recorded: a USD price is never converted.
    """
    key = f"price_{currency.lower()}_per_month"
    usd = currency.upper() == "USD"
    pro_price = ppu_price = 0.0 if usd else None
    for item in drivers.get("power_bi_licenses", []):
        value = item.get(key)
        if value is None:
            continue
        if item.get("id") == "pro":
            pro_price = float(value)
        elif item.get("id") == "ppu":
            ppu_price = float(value)
    return pro_price, ppu_price


def _parse_valid_from(valid_from: str | None) -> datetime:
    """Parse valid_from (YYYY-MM-DD) to datetime; default today."""
    if valid_from:
        try:
            return datetime.strptime(valid_from.strip()[:10], "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _amounts(per_month: float, currency: str, per_year: float | None = None) -> dict[str, float]:
    """Neutral amount keys, plus the historic usd_* aliases when the currency is USD."""
    out = {"per_month": per_month}
    if per_year is not None:
        out["per_year"] = per_year
    if currency == "USD":
        out.update({f"usd_{k}": v for k, v in list(out.items())})
    return out


def _compute_capacity_costs(capacities: dict[str, Any], drivers: dict[str, Any], use_reservation: bool,
                            region: str | None = None, currency: str = "USD") -> tuple[float, list]:
    """Return (total_cost, building_blocks_list) for capacity.

    Priced at the regional PAYG rate when the region is in ``fabric_regions`` (01.10.2026: until
    then every region was priced at the US table, about 22 % below West Europe); otherwise the
    US SKU table, and the row says so.
    """
    capacity_month = 0.0
    capacity_breakdown: list[dict[str, Any]] = []
    for env, sku in capacities.items():
        if not sku:
            continue
        price, basis = capacity_price_per_month(drivers, sku, region=region, currency=currency,
                                                use_reservation=use_reservation)
        price = round(price, 2)
        capacity_month += price
        capacity_breakdown.append({"environment": env, "sku": sku, **_amounts(price, currency),
                                   "price_basis": basis})
    return capacity_month, capacity_breakdown


def _compute_license_costs(pro_users: int | float, ppu_users: int | float, drivers: dict[str, Any],
                           currency: str = "USD") -> tuple[float, list]:
    """Return (total_cost, building_blocks_list) for licenses. Raises ValueError for a currency
    without a recorded list price instead of converting the USD price."""
    pro_price, ppu_price = _license_prices(drivers, currency)
    if (pro_users and pro_price is None) or (ppu_users and ppu_price is None):
        raise ValueError(f"No {currency} list price for Power BI Pro/PPU in cost_drivers.yaml")
    pro_price, ppu_price = pro_price or 0.0, ppu_price or 0.0
    license_month = pro_users * pro_price + ppu_users * ppu_price
    license_breakdown = [
        {"license": "pro", "users": pro_users, **_amounts(pro_users * pro_price, currency)},
        {"license": "ppu", "users": ppu_users, **_amounts(ppu_users * ppu_price, currency)},
    ]
    return license_month, license_breakdown


def _package_has_fixed_price(package: dict[str, Any] | None) -> bool:
    """True when the package carries a fixed implementation price in any currency."""
    return bool(package) and any(k.startswith("implementation_fixed_") and v is not None
                                 for k, v in package.items())


def _compute_service_costs(impl_fte: float, impl_months: float, maint_fte: float, drivers: dict[str, Any],
                           package: dict[str, Any] | None, currency: str = "USD") -> tuple[float, float]:
    """Return (impl_cost, maint_annual_cost) in `currency`.

    Fixed package prices and FTE rates are read under the currency's own key
    (`implementation_fixed_eur`, `implementation_eur_per_fte_month`, ...). A missing key in a
    non-USD currency raises ValueError: our service price is never converted from USD.
    """
    cur = currency.lower()
    implementation_one_time = 0.0
    maintenance_year = 0.0
    if _package_has_fixed_price(package):
        fixed = package.get(f"implementation_fixed_{cur}")
        if fixed is None:
            raise ValueError(f"Package has no implementation_fixed_{cur}; a {currency} offer needs the "
                             f"package price in {currency}, the USD price is not converted")
        implementation_one_time = round(float(fixed), 2)
        maintenance_year = round(float(package.get(f"maintenance_fixed_{cur}_per_year", 0)), 2)
    elif impl_fte > 0 or impl_months > 0 or maint_fte > 0:
        services = drivers.get("services_rates")
        if not services:
            raise ValueError("services_rates missing in cost_drivers.yaml; required when implementation_fte, implementation_months, or maintenance_fte are set")
        if cur != "usd" and f"implementation_{cur}_per_fte_month" not in services:
            raise ValueError(f"services_rates has no implementation_{cur}_per_fte_month; a {currency} offer "
                             "needs the service rates in that currency, the USD rate is not converted")
        rate_impl = float(services.get(f"implementation_{cur}_per_fte_month", 0))
        rate_maint = float(services.get(f"maintenance_{cur}_per_fte_year", 0))
        implementation_one_time = round(impl_fte * impl_months * rate_impl, 2) if (impl_fte and impl_months) else 0.0
        maintenance_year = round(maint_fte * rate_maint, 2) if maint_fte else 0.0
    return implementation_one_time, maintenance_year


def _resolve_assumptions(defaults: dict[str, Any], drivers: dict[str, Any], valid_from: str | None, quote_days: int, region: str | None) -> dict[str, Any]:
    """Normalize valid_from, quote_valid_until, scope strings. Return assumptions dict."""
    valid_from_val = valid_from or drivers.get("valid_from") or datetime.now().strftime("%Y-%m-%d")
    dt = _parse_valid_from(valid_from_val)
    quote_valid_until = (dt + timedelta(days=quote_days)).strftime("%Y-%m-%d")

    scope_in_list = defaults.get("scope_in", _INLINE_DEFAULTS["scope_in"])
    scope_out_list = defaults.get("scope_out", _INLINE_DEFAULTS["scope_out"])
    scope_in = "\n".join(f"- {s}" for s in scope_in_list) if isinstance(scope_in_list, list) else str(scope_in_list)
    scope_out = "\n".join(f"- {s}" for s in scope_out_list) if isinstance(scope_out_list, list) else str(scope_out_list)

    return {
        "valid_from_val": valid_from_val if isinstance(valid_from_val, str) else str(valid_from_val),
        "quote_valid_until": quote_valid_until,
        "scope_in": scope_in,
        "scope_out": scope_out,
        "region": region or defaults.get("default_region", _INLINE_DEFAULTS["default_region"]),
    }


def compute(
    scenario_id: str,
    overrides: dict[str, Any] | None = None,
    product_root: Path | None = None,
    package_id: str | None = None,
    use_reservation: bool = False,
    storage_gb: float | None = None,
    implementation_fte: float | None = None,
    implementation_months: float | None = None,
    maintenance_fte: float | None = None,
    role_allocation_path: Path | str | None = None,
    contract_term_months: int | None = None,
    region: str | None = None,
    price_basis: str | None = None,
    valid_from: str | None = None,
    quote_valid_days: int | None = None,
    currency: str = "USD",
) -> dict[str, Any]:
    """
    Compute monthly and yearly costs for a scenario.
    currency: USD (default) or EUR. Every Microsoft amount comes from Microsoft's own list in that
    currency (fabric_regions, price_eur_per_month); service prices need their own EUR keys. Nothing
    is converted: a missing price raises ValueError. Amount keys are neutral (per_month, per_year,
    max_per_day); the usd_* aliases exist only for USD.
    If package_id is set, scenario_id and implementation/maintenance come from the package (fixed USD or FTE profile).
    overrides can include: capacities (dev/test/prod -> SKU), pro_users, ppu_users.
    use_reservation: use reservation pricing for capacity (~41% savings).
    storage_gb: optional OneLake storage estimate (adds storage_month to total).
    contract_term_months, region, price_basis, valid_from, quote_valid_days: for assumptions; defaults from proposal_defaults.yaml.
    Returns dict with capacity_month, license_month, total_month, total_year, capacity_breakdown, license_breakdown,
    scenario_id, pro_users, ppu_users, pricing_mode, viewer_note, prod_sku, scope_in, scope_out,
    valid_from, quote_valid_until, contract_term_months, region, price_basis, package_id, package_name, and optionally storage_month, storage_breakdown.
    """
    overrides = overrides or {}
    root = product_root or _product_root()
    package: dict[str, Any] | None = None
    package_id_out = ""
    package_name_out = ""
    if package_id:
        packages = load_product_packages(root)
        if package_id not in packages:
            raise ValueError(f"Unknown package: {package_id}. Valid: {list(packages)}")
        package = packages[package_id]
        scenario_id = package.get("scenario_id", scenario_id)
        role_allocation_path = package.get("role_allocation_path") or role_allocation_path
        package_id_out = package_id
        package_name_out = package.get("name", package_id) or package_id

    drivers = load_cost_drivers(root)
    defaults = load_proposal_defaults(root)
    scenarios_data = load_scenarios(root)
    scenarios = scenarios_data.get("scenarios", {})
    if scenario_id not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario_id}. Valid: {list(scenarios)}")

    scenario = scenarios[scenario_id].copy()
    capacities = dict(scenario.get("capacities") or {})
    for env, sku in (overrides.get("capacities") or {}).items():
        capacities[env] = sku
    pro_users = overrides.get("pro_users") if "pro_users" in overrides else scenario.get("default_pro_users", 0)
    ppu_users = overrides.get("ppu_users") if "ppu_users" in overrides else scenario.get("default_ppu_users", 0)

    impl_fte = implementation_fte if implementation_fte is not None else overrides.get("implementation_fte")
    impl_months = implementation_months if implementation_months is not None else overrides.get("implementation_months")
    maint_fte = maintenance_fte if maintenance_fte is not None else overrides.get("maintenance_fte")
    if package and not _package_has_fixed_price(package):
        if impl_fte is None and package.get("implementation_fte") is not None:
            impl_fte = package.get("implementation_fte")
        if impl_months is None and package.get("implementation_months") is not None:
            impl_months = package.get("implementation_months")
        if maint_fte is None and package.get("maintenance_fte") is not None:
            maint_fte = package.get("maintenance_fte")

    role_breakdown: list[dict[str, Any]] = []
    if role_allocation_path is not None or overrides.get("role_allocation_path") is not None:
        ra_path = overrides.get("role_allocation_path") or role_allocation_path
        role_alloc = load_role_allocation(root, ra_path)
        if role_alloc.get("allocations"):
            org_by_id = _load_org_roles_for_roles(role_alloc.get("roles_source", "core"), root)
            ra_impl, ra_maint, role_breakdown = _ftes_from_role_allocation(role_alloc, org_by_id)
            if impl_fte is None:
                impl_fte = ra_impl
            if maint_fte is None:
                maint_fte = ra_maint

    if impl_fte is None:
        impl_fte = scenario.get("default_implementation_fte") or defaults.get("default_implementation_fte")
    if impl_months is None:
        impl_months = scenario.get("default_implementation_months") or defaults.get("default_implementation_months")
    if maint_fte is None:
        maint_fte = scenario.get("default_maintenance_fte") or defaults.get("default_maintenance_fte")

    impl_fte = float(impl_fte) if impl_fte is not None else 0.0
    impl_months = float(impl_months) if impl_months is not None else 0.0
    maint_fte = float(maint_fte) if maint_fte is not None else 0.0

    cur = (currency or "USD").upper()
    if cur not in ("USD", "EUR"):
        raise ValueError(f"Unsupported currency {currency!r}: USD or EUR")
    effective_region = region or defaults.get("default_region", _INLINE_DEFAULTS["default_region"])
    regional = regional_rates(drivers, effective_region, cur)
    if regional is None and cur != "USD":
        raise ValueError(f"No {cur} rates for region {effective_region!r} in fabric_regions; "
                         "the USD table is not converted")
    capacity_month, capacity_breakdown = _compute_capacity_costs(capacities, drivers, use_reservation,
                                                                 effective_region, cur)

    license_month, license_breakdown = _compute_license_costs(pro_users, ppu_users, drivers, cur)

    storage_month = 0.0
    storage_breakdown: dict[str, Any] | None = None
    if storage_gb is not None and storage_gb > 0:
        onelake = (regional["onelake_hot_per_gb_month"] if regional else
                   (drivers.get("onelake_storage") or {}).get("usd_per_gb_month") or 0.023)
        storage_month = round(storage_gb * float(onelake), 2)
        storage_breakdown = {"gb": storage_gb, **_amounts(storage_month, cur)}

    implementation_one_time, maintenance_year = _compute_service_costs(impl_fte, impl_months, maint_fte, drivers,
                                                                       package, cur)

    total_month = capacity_month + license_month + storage_month
    total_year = round(total_month * 12, 2)

    prod_sku = capacities.get("prod") or ""
    overage: dict[str, Any] | None = None
    planning: dict[str, Any] | None = None
    customer_questions: list[str] = []
    if prod_sku:
        overage = compute_overage(drivers, prod_sku, overrides.get("overage_enabled"),
                                  overrides.get("overage_threshold_cu_hours"),
                                  regional["payg_per_cu_hour"] if regional else None, cur)
        if overage.get("customer_question"):
            customer_questions.append(overage["customer_question"])
        if overrides.get("planning_sessions"):
            planning = compute_planning(drivers, overrides["planning_sessions"], prod_sku,
                                        regional["payg_per_cu_hour"] if regional else None, cur)
    if prod_sku and _sku_at_least_f64(prod_sku):
        viewer_note = defaults.get("viewer_note_f64_plus", _INLINE_DEFAULTS["viewer_note_f64_plus"])
    elif prod_sku:
        viewer_note = defaults.get("viewer_note_below_f64", _INLINE_DEFAULTS["viewer_note_below_f64"])
    else:
        viewer_note = ""

    quote_days = quote_valid_days if quote_valid_days is not None else int(defaults.get("default_quote_valid_days", 30))
    assumptions = _resolve_assumptions(defaults, drivers, valid_from, quote_days, region)

    block_labels = defaults.get("building_block_labels") or _INLINE_DEFAULTS.get("building_block_labels") or {}
    block_categories = defaults.get("building_block_categories") or {}

    def _block_label(block_id: str) -> str:
        return block_labels.get(block_id, block_id) if isinstance(block_labels, dict) else block_id

    def _block_category(block_id: str) -> str:
        return (block_categories.get(block_id) or "") if isinstance(block_categories, dict) else ""

    building_blocks = [
        {"id": "fabric_capacity", "label": _block_label("fabric_capacity"), "category": _block_category("fabric_capacity"), "usd_per_month": round(capacity_month, 2), "usd_per_year": round(capacity_month * 12, 2)},
        {"id": "power_bi", "label": _block_label("power_bi"), "category": _block_category("power_bi"), "usd_per_month": round(license_month, 2), "usd_per_year": round(license_month * 12, 2)},
        {"id": "onelake_storage", "label": _block_label("onelake_storage"), "category": _block_category("onelake_storage"), "usd_per_month": round(storage_month, 2), "usd_per_year": round(storage_month * 12, 2)},
    ]
    building_blocks.append({"id": "implementation", "label": _block_label("implementation"), "category": _block_category("implementation"), "usd_per_month": 0.0, "usd_per_year": implementation_one_time})
    building_blocks.append({"id": "maintenance", "label": _block_label("maintenance"), "category": _block_category("maintenance"), "usd_per_month": round(maintenance_year / 12, 2) if maintenance_year else 0.0, "usd_per_year": maintenance_year})

    # Neutral keys for every block; usd_* aliases only for USD (see _amounts).
    building_blocks = [{**{k: v for k, v in b.items() if not k.startswith("usd_")},
                        **_amounts(b["usd_per_month"], cur, b["usd_per_year"])} for b in building_blocks]

    sensitivity_note = (defaults.get("sensitivity_note") or "").strip()
    customer_contrib_list = defaults.get("customer_contributions") or []
    customer_contributions = "\n".join(f"- {s}" for s in customer_contrib_list) if isinstance(customer_contrib_list, list) else str(customer_contrib_list) if customer_contrib_list else ""
    implementation_milestones_raw = defaults.get("implementation_milestones") or []
    implementation_milestones_table = format_milestones_table(implementation_milestones_raw)

    return {
        "scenario_id": scenario_id,
        "currency": cur,
        "capacity_month": round(capacity_month, 2),
        "license_month": round(license_month, 2),
        "total_month": round(total_month, 2),
        "total_year": total_year,
        "capacity_breakdown": capacity_breakdown,
        "license_breakdown": license_breakdown,
        "pro_users": pro_users,
        "ppu_users": ppu_users,
        "pricing_mode": "1-year reservation (~41% savings)" if use_reservation else "Pay-as-you-go",
        "viewer_note": viewer_note,
        "prod_sku": prod_sku,
        "scope_in": assumptions["scope_in"],
        "scope_out": assumptions["scope_out"],
        "valid_from": assumptions["valid_from_val"],
        "quote_valid_until": assumptions["quote_valid_until"],
        "contract_term_months": contract_term_months if contract_term_months is not None else int(defaults.get("default_contract_term_months", 12)),
        "region": assumptions["region"],
        "price_basis": price_basis or str(defaults.get("price_basis", _INLINE_DEFAULTS["price_basis"])).replace(
            "(USD)", f"({cur})"),
        "storage_month": round(storage_month, 2),
        "storage_breakdown": storage_breakdown,
        "building_blocks": building_blocks,
        "implementation_one_time": implementation_one_time,
        "maintenance_year": maintenance_year,
        "implementation_fte": impl_fte,
        "implementation_months": impl_months,
        "maintenance_fte": maint_fte,
        "role_breakdown": role_breakdown,
        "sensitivity_note": sensitivity_note,
        "customer_contributions": customer_contributions,
        "implementation_milestones_table": implementation_milestones_table,
        "package_id": package_id_out,
        "package_name": package_name_out,
        "overage": overage,
        "planning": planning,
        "customer_questions": customer_questions,
    }


def compute_projection(
    scenario_id: str,
    product_root: Path | None = None,
    projection_config: dict[str, Any] | None = None,
    tco_years_list: list[int] | None = None,
    package_id: str | None = None,
    use_reservation: bool = False,
    storage_gb: float | None = None,
    implementation_fte: float | None = None,
    implementation_months: float | None = None,
    maintenance_fte: float | None = None,
    role_allocation_path: Path | str | None = None,
    **compute_kw: Any,
) -> dict[str, Any]:
    """
    Run compute() per horizon from projection.yaml; return horizons and TCO.
    tco_years_list: optional override for which TCO year sums to compute (e.g. [3, 5]); from projection_config if not set.
    """
    root = product_root or _product_root()
    proj = projection_config or load_projection(root)
    horizons_config = proj.get("horizons") or []
    if not horizons_config:
        return {"horizons": [], "tco_by_years": {}, "tco_by_year": []}

    horizons_out: list[dict[str, Any]] = []
    for h in horizons_config:
        overrides: dict[str, Any] = {}
        if h.get("capacities"):
            overrides["capacities"] = h["capacities"]
        if "pro_users" in h:
            overrides["pro_users"] = h["pro_users"]
        if "ppu_users" in h:
            overrides["ppu_users"] = h["ppu_users"]
        single = compute(
            scenario_id,
            overrides=overrides if overrides else None,
            product_root=root,
            package_id=package_id,
            use_reservation=use_reservation,
            storage_gb=storage_gb,
            implementation_fte=implementation_fte,
            implementation_months=implementation_months,
            maintenance_fte=maintenance_fte,
            role_allocation_path=role_allocation_path,
            **compute_kw,
        )
        horizons_out.append({
            "id": h.get("id", ""),
            "label": h.get("label", ""),
            "years": int(h.get("years", 1)),
            "total_year": single.get("total_year", 0),
            "total_month": single.get("total_month", 0),
            "implementation_one_time": single.get("implementation_one_time", 0),
            "maintenance_year": single.get("maintenance_year", 0),
            "breakdown": single,
        })

    tco_year_list = tco_years_list if tco_years_list is not None else proj.get("tco_years") or []
    tco_by_year: list[dict[str, Any]] = []
    cum = 0
    for i, h in enumerate(horizons_out):
        n = h["years"]
        platform_yr = h["total_year"]
        maint_yr = h["maintenance_year"]
        impl_once = h["implementation_one_time"] if i == 0 else 0.0
        for y in range(1, n + 1):
            year_num = cum + y
            row = {
                "year": year_num,
                "platform": platform_yr,
                "maintenance": maint_yr,
                "implementation": impl_once if year_num == 1 else 0.0,
                "total": platform_yr + maint_yr + (impl_once if year_num == 1 else 0.0),
            }
            tco_by_year.append(row)
        cum += n

    tco_by_years: dict[int, float] = {}
    for n in tco_year_list:
        tco_by_years[int(n)] = round(sum(r["total"] for r in tco_by_year if r["year"] <= n), 2)

    return {"horizons": horizons_out, "tco_by_years": tco_by_years, "tco_by_year": tco_by_year}


def format_projection_table(horizons: list[dict[str, Any]]) -> str:
    """Format horizons as Markdown table for template placeholder."""
    if not horizons:
        return "—"
    cur = (horizons[0].get("breakdown") or {}).get("currency", "USD")
    lines = [f"| Horizon | Years | {cur}/year (platform) | {cur}/year (maintenance) |", "|---------|-------|---------------------|------------------------|"]
    for h in horizons:
        label = h.get("label", h.get("id", ""))
        years = h.get("years", 0)
        plat = h.get("total_year", 0)
        maint = h.get("maintenance_year", 0)
        lines.append(f"| {label} | {years} | {plat:.2f} | {maint:.2f} |")
    return "\n".join(lines)


def _pm(row: dict[str, Any]) -> float:
    """Monthly amount of a row; neutral key first, historic usd_per_month as fallback."""
    return row.get("per_month", row.get("usd_per_month", 0)) or 0


def format_breakdown_capacity(breakdown: list[dict[str, Any]], currency: str = "USD") -> str:
    """Format capacity_breakdown for template placeholder."""
    if not breakdown:
        return "—"
    return " | ".join(f"{r['environment']}: {r['sku']} {_pm(r):.2f} {currency}/mo" for r in breakdown)


def format_breakdown_license(breakdown: list[dict[str, Any]], currency: str = "USD") -> str:
    """Format license_breakdown for template placeholder."""
    if not breakdown:
        return "—"
    parts = [f"{r['license'].upper()}: {r['users']} users, {_pm(r):.2f} {currency}/mo" for r in breakdown if r["users"] > 0]
    return " | ".join(parts) if parts else "—"


def format_storage_breakdown(storage_breakdown: dict[str, Any] | None, currency: str = "USD") -> str:
    """Format storage_breakdown for template placeholder."""
    if not storage_breakdown:
        return "—"
    return f"{storage_breakdown.get('gb', 0)} GB, {_pm(storage_breakdown):.2f} {currency}/mo"


def format_role_breakdown_table(role_breakdown: list[dict[str, Any]]) -> str:
    """Format role_breakdown as Markdown table for template placeholder. Includes optional person/contact."""
    if not role_breakdown:
        return "—"
    has_person = any(r.get("person") for r in role_breakdown)
    if has_person:
        lines = ["| Role | Domain | FTE | Phase | Person / Ansprechpartner |", "|------|--------|-----|-------|---------------------------|"]
        for r in role_breakdown:
            title = r.get("title", r.get("role_id", ""))
            domain = r.get("domain", "")
            fte = r.get("fte", 0)
            phase = r.get("phase", "")
            person = r.get("person", "") or "—"
            lines.append(f"| {title} | {domain} | {fte} | {phase} | {person} |")
    else:
        lines = ["| Role | Domain | FTE | Phase | Person / Ansprechpartner |", "|------|--------|-----|-------|---------------------------|"]
        for r in role_breakdown:
            title = r.get("title", r.get("role_id", ""))
            domain = r.get("domain", "")
            fte = r.get("fte", 0)
            phase = r.get("phase", "")
            lines.append(f"| {title} | {domain} | {fte} | {phase} | — |")
    return "\n".join(lines)


def format_milestones_table(milestones: list[dict[str, Any]]) -> str:
    """Format implementation_milestones as Markdown table (Phase | Deliverable | Dauer)."""
    if not milestones or not isinstance(milestones, list):
        return "—"
    lines = ["| Phase | Deliverable | Dauer |", "|-------|-------------|-------|"]
    for m in milestones:
        if not isinstance(m, dict):
            continue
        phase = m.get("phase", "")
        deliverable = m.get("deliverable", "")
        duration = m.get("duration", "")
        lines.append(f"| {phase} | {deliverable} | {duration} |")
    return "\n".join(lines) if len(lines) > 2 else "—"


def format_building_blocks_table(building_blocks: list[dict[str, Any]], currency: str = "USD") -> str:
    """Format building_blocks as Markdown table for template placeholder. Optional category column if present."""
    if not building_blocks:
        return "—"
    has_category = any(b.get("category") for b in building_blocks)
    if has_category:
        lines = [f"| Baustein | Kategorie | {currency}/month | {currency}/year |", "|----------|-----------|-----------|----------|"]
        for b in building_blocks:
            label = b.get("label", b.get("id", ""))
            cat = b.get("category", "") or "—"
            mo = b.get("per_month", b.get("usd_per_month", 0)) or 0
            yr = b.get("per_year", b.get("usd_per_year", 0)) or (mo * 12)
            lines.append(f"| {label} | {cat} | {mo:.2f} | {yr:.2f} |")
    else:
        lines = [f"| Baustein | {currency}/month | {currency}/year |", "|----------|-----------|----------|"]
        for b in building_blocks:
            label = b.get("label", b.get("id", ""))
            mo = b.get("per_month", b.get("usd_per_month", 0)) or 0
            yr = b.get("per_year", b.get("usd_per_year", 0)) or (mo * 12)
            lines.append(f"| {label} | {mo:.2f} | {yr:.2f} |")
    return "\n".join(lines)


def format_overage(overage: dict[str, Any] | None) -> str:
    """Overage line for the proposal: derived daily maximum, never presented as a cap."""
    if not overage:
        return "—"
    if overage.get("enabled") is False:
        return f"Capacity overage on {overage['sku']} is switched off: throttling applies, no overage charges."
    source = ("Microsoft default at capacity creation (25 %), not yet confirmed by the customer"
              if overage.get("threshold_source") == "microsoft_default" else "set by the customer")
    lines = [
        f"- SKU {overage['sku']}: {overage['cu_hours_per_day']} CU hours per day",
        f"- Rolling 24-hour threshold: {overage['threshold_cu_hours']:g} CU hours ({source}); "
        f"Microsoft recommends staying below {overage['recommended_max_threshold_cu_hours']:g} "
        "(one third of the daily CU hours)",
        f"- Maximum overage cost per day ≈ threshold × 3 × PAYG price per CU hour ≈ "
        f"{overage.get('max_per_day', overage.get('max_usd_per_day', 0)):.2f} {overage.get('currency', 'USD')} "
        "(derived, not measured; can be exceeded because "
        "the threshold is checked every 5 minutes and running operations continue)",
        f"- Additional Fabric quota required: {overage['quota_cu_required']:g} CU",
    ]
    return "\n".join(lines)


def format_planning(planning: dict[str, Any] | None) -> str:
    """Fabric Planning sessions as capacity share; not added to the total."""
    if not planning:
        return "—"
    roles = ", ".join(f"{n} {r}" for r, n in planning["sessions"].items())
    fit = "fits" if planning.get("fits_with_buffer") else "does NOT fit"
    return "\n".join([
        f"- Sessions per 30-day window: {roles}",
        f"- Consumption: {planning['cu_hours_per_session_window']} CU hours per 730 h "
        f"(average {planning['average_cu']:g} CU) = {planning['share_of_capacity_pct']:g} % of "
        f"{planning['sku']}; {fit} within the recommended 30 % buffer for other workloads",
        f"- Capacity share ≈ {planning.get('equivalent_per_session_window', planning.get('usd_equivalent_per_session_window', 0)):.2f} "
        f"{planning.get('currency', 'USD')} per 30 days "
        "(derived; already contained in the capacity price, not added to the total)",
        f"- Not included: {planning['not_included']}",
    ])


def format_customer_questions(questions: list[str] | None) -> str:
    if not questions:
        return "—"
    return "\n".join(f"- {q}" for q in questions)


def fill_template(result: dict[str, Any], template_content: str) -> str:
    """Replace {{ key }} placeholders in template_content with result values."""
    cap_m = result.get("capacity_month", 0)
    lic_m = result.get("license_month", 0)
    storage_m = result.get("storage_month", 0) or 0
    cur = result.get("currency", "USD")
    replacements = {
        "scenario_id": result.get("scenario_id", ""),
        "currency": cur,
        "capacity_month": f"{cap_m:.2f}",
        "license_month": f"{lic_m:.2f}",
        "capacity_year": f"{cap_m * 12:.2f}",
        "license_year": f"{lic_m * 12:.2f}",
        "total_month": f"{result.get('total_month', 0):.2f}",
        "total_year": f"{result.get('total_year', 0):.2f}",
        "capacity_breakdown": format_breakdown_capacity(result.get("capacity_breakdown", []), cur),
        "license_breakdown": format_breakdown_license(result.get("license_breakdown", []), cur),
        "pricing_mode": result.get("pricing_mode", "—"),
        "viewer_note": result.get("viewer_note", "—"),
        "prod_sku": result.get("prod_sku", "—"),
        "scope_in": result.get("scope_in", "—"),
        "scope_out": result.get("scope_out", "—"),
        "valid_from": result.get("valid_from", "—"),
        "quote_valid_until": result.get("quote_valid_until", "—"),
        "contract_term_months": str(result.get("contract_term_months", "—")),
        "region": result.get("region", "—"),
        "price_basis": result.get("price_basis", "—"),
        "storage_month": f"{storage_m:.2f}" if storage_m else "—",
        "storage_year": f"{storage_m * 12:.2f}" if storage_m else "—",
        "storage_breakdown": format_storage_breakdown(result.get("storage_breakdown"), cur),
        "building_blocks_table": format_building_blocks_table(result.get("building_blocks", []), cur),
        "implementation_one_time": f"{result.get('implementation_one_time', 0):.2f}",
        "maintenance_year": f"{result.get('maintenance_year', 0):.2f}",
        "role_breakdown_table": format_role_breakdown_table(result.get("role_breakdown", [])),
        "projection_table": format_projection_table(result.get("horizons", [])),
        "tco_3y": f"{result.get('tco_by_years', {}).get(3, 0):.2f}" if result.get("tco_by_years") else "—",
        "tco_5y": f"{result.get('tco_by_years', {}).get(5, 0):.2f}" if result.get("tco_by_years") else "—",
        "sensitivity_note": result.get("sensitivity_note", "") or "—",
        "customer_contributions": result.get("customer_contributions", "") or "—",
        "implementation_milestones_table": result.get("implementation_milestones_table", "") or "—",
        "package_name": result.get("package_name", "") or "—",
        "customer_name": result.get("customer_name", "") or "—",
        "offer_date": result.get("offer_date", "") or "—",
        "overage": format_overage(result.get("overage")),
        "planning": format_planning(result.get("planning")),
        "customer_questions": format_customer_questions(result.get("customer_questions")),
    }
    out = template_content
    for key, value in replacements.items():
        out = out.replace(f"{{{{ {key} }}}}", str(value))
    return out
