"""
Proposal Costing – Cost engine.
Loads cost_drivers.yaml and scenarios.yaml, computes monthly/yearly costs from scenario + overrides.
Supports reservation pricing, viewer note (F64 threshold), optional OneLake storage, scope and assumptions.
"""

from __future__ import annotations

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


def _license_prices(drivers: dict[str, Any]) -> tuple[float, float]:
    """Return (pro_usd_per_month, ppu_usd_per_month)."""
    pro_price = ppu_price = 0.0
    for item in drivers.get("power_bi_licenses", []):
        if item.get("id") == "pro":
            pro_price = float(item["price_usd_per_month"])
        elif item.get("id") == "ppu":
            ppu_price = float(item["price_usd_per_month"])
    return pro_price, ppu_price


def _parse_valid_from(valid_from: str | None) -> datetime:
    """Parse valid_from (YYYY-MM-DD) to datetime; default today."""
    if valid_from:
        try:
            return datetime.strptime(valid_from.strip()[:10], "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


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
) -> dict[str, Any]:
    """
    Compute monthly and yearly costs for a scenario.
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
    if package and package.get("implementation_fixed_usd") is None:
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

    capacity_month = 0.0
    capacity_breakdown: list[dict[str, Any]] = []
    for env, sku in capacities.items():
        if not sku:
            continue
        price = _price_by_sku(drivers, sku, use_reservation=use_reservation)
        capacity_month += price
        capacity_breakdown.append({"environment": env, "sku": sku, "usd_per_month": price})

    pro_price, ppu_price = _license_prices(drivers)
    license_month = pro_users * pro_price + ppu_users * ppu_price
    license_breakdown = [
        {"license": "pro", "users": pro_users, "usd_per_month": pro_users * pro_price},
        {"license": "ppu", "users": ppu_users, "usd_per_month": ppu_users * ppu_price},
    ]

    storage_month = 0.0
    storage_breakdown: dict[str, Any] | None = None
    if storage_gb is not None and storage_gb > 0:
        onelake = (drivers.get("onelake_storage") or {}).get("usd_per_gb_month") or 0.023
        storage_month = round(storage_gb * float(onelake), 2)
        storage_breakdown = {"gb": storage_gb, "usd_per_month": storage_month}

    implementation_one_time = 0.0
    maintenance_year = 0.0
    if package and package.get("implementation_fixed_usd") is not None:
        implementation_one_time = round(float(package["implementation_fixed_usd"]), 2)
        maintenance_year = round(float(package.get("maintenance_fixed_usd_per_year", 0)), 2)
    elif impl_fte > 0 or impl_months > 0 or maint_fte > 0:
        services = drivers.get("services_rates")
        if not services:
            raise ValueError("services_rates missing in cost_drivers.yaml; required when implementation_fte, implementation_months, or maintenance_fte are set")
        rate_impl = float(services.get("implementation_usd_per_fte_month", 0))
        rate_maint = float(services.get("maintenance_usd_per_fte_year", 0))
        implementation_one_time = round(impl_fte * impl_months * rate_impl, 2) if (impl_fte and impl_months) else 0.0
        maintenance_year = round(maint_fte * rate_maint, 2) if maint_fte else 0.0

    total_month = capacity_month + license_month + storage_month
    total_year = round(total_month * 12, 2)

    prod_sku = capacities.get("prod") or ""
    if prod_sku and _sku_at_least_f64(prod_sku):
        viewer_note = defaults.get("viewer_note_f64_plus", _INLINE_DEFAULTS["viewer_note_f64_plus"])
    elif prod_sku:
        viewer_note = defaults.get("viewer_note_below_f64", _INLINE_DEFAULTS["viewer_note_below_f64"])
    else:
        viewer_note = ""

    valid_from_val = valid_from or drivers.get("valid_from") or datetime.now().strftime("%Y-%m-%d")
    quote_days = quote_valid_days if quote_valid_days is not None else int(defaults.get("default_quote_valid_days", 30))
    dt = _parse_valid_from(valid_from_val)
    quote_valid_until = (dt + timedelta(days=quote_days)).strftime("%Y-%m-%d")

    scope_in_list = defaults.get("scope_in", _INLINE_DEFAULTS["scope_in"])
    scope_out_list = defaults.get("scope_out", _INLINE_DEFAULTS["scope_out"])
    scope_in = "\n".join(f"- {s}" for s in scope_in_list) if isinstance(scope_in_list, list) else str(scope_in_list)
    scope_out = "\n".join(f"- {s}" for s in scope_out_list) if isinstance(scope_out_list, list) else str(scope_out_list)

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

    sensitivity_note = (defaults.get("sensitivity_note") or "").strip()
    customer_contrib_list = defaults.get("customer_contributions") or []
    customer_contributions = "\n".join(f"- {s}" for s in customer_contrib_list) if isinstance(customer_contrib_list, list) else str(customer_contrib_list) if customer_contrib_list else ""
    implementation_milestones_raw = defaults.get("implementation_milestones") or []
    implementation_milestones_table = format_milestones_table(implementation_milestones_raw)

    return {
        "scenario_id": scenario_id,
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
        "scope_in": scope_in,
        "scope_out": scope_out,
        "valid_from": valid_from_val if isinstance(valid_from_val, str) else str(valid_from_val),
        "quote_valid_until": quote_valid_until,
        "contract_term_months": contract_term_months if contract_term_months is not None else int(defaults.get("default_contract_term_months", 12)),
        "region": region or defaults.get("default_region", _INLINE_DEFAULTS["default_region"]),
        "price_basis": price_basis or defaults.get("price_basis", _INLINE_DEFAULTS["price_basis"]),
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
    lines = ["| Horizon | Years | USD/year (platform) | USD/year (maintenance) |", "|---------|-------|---------------------|------------------------|"]
    for h in horizons:
        label = h.get("label", h.get("id", ""))
        years = h.get("years", 0)
        plat = h.get("total_year", 0)
        maint = h.get("maintenance_year", 0)
        lines.append(f"| {label} | {years} | {plat:.2f} | {maint:.2f} |")
    return "\n".join(lines)


def format_breakdown_capacity(breakdown: list[dict[str, Any]]) -> str:
    """Format capacity_breakdown for template placeholder."""
    if not breakdown:
        return "—"
    return " | ".join(f"{r['environment']}: {r['sku']} {r['usd_per_month']:.2f} USD/mo" for r in breakdown)


def format_breakdown_license(breakdown: list[dict[str, Any]]) -> str:
    """Format license_breakdown for template placeholder."""
    if not breakdown:
        return "—"
    parts = [f"{r['license'].upper()}: {r['users']} users, {r['usd_per_month']:.2f} USD/mo" for r in breakdown if r["users"] > 0]
    return " | ".join(parts) if parts else "—"


def format_storage_breakdown(storage_breakdown: dict[str, Any] | None) -> str:
    """Format storage_breakdown for template placeholder."""
    if not storage_breakdown:
        return "—"
    return f"{storage_breakdown.get('gb', 0)} GB, {storage_breakdown.get('usd_per_month', 0):.2f} USD/mo"


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


def format_building_blocks_table(building_blocks: list[dict[str, Any]]) -> str:
    """Format building_blocks as Markdown table for template placeholder. Optional category column if present."""
    if not building_blocks:
        return "—"
    has_category = any(b.get("category") for b in building_blocks)
    if has_category:
        lines = ["| Baustein | Kategorie | USD/month | USD/year |", "|----------|-----------|-----------|----------|"]
        for b in building_blocks:
            label = b.get("label", b.get("id", ""))
            cat = b.get("category", "") or "—"
            mo = b.get("usd_per_month", 0) or 0
            yr = b.get("usd_per_year", 0) or (mo * 12)
            lines.append(f"| {label} | {cat} | {mo:.2f} | {yr:.2f} |")
    else:
        lines = ["| Baustein | USD/month | USD/year |", "|----------|-----------|----------|"]
        for b in building_blocks:
            label = b.get("label", b.get("id", ""))
            mo = b.get("usd_per_month", 0) or 0
            yr = b.get("usd_per_year", 0) or (mo * 12)
            lines.append(f"| {label} | {mo:.2f} | {yr:.2f} |")
    return "\n".join(lines)


def fill_template(result: dict[str, Any], template_content: str) -> str:
    """Replace {{ key }} placeholders in template_content with result values."""
    cap_m = result.get("capacity_month", 0)
    lic_m = result.get("license_month", 0)
    storage_m = result.get("storage_month", 0) or 0
    replacements = {
        "scenario_id": result.get("scenario_id", ""),
        "capacity_month": f"{cap_m:.2f}",
        "license_month": f"{lic_m:.2f}",
        "capacity_year": f"{cap_m * 12:.2f}",
        "license_year": f"{lic_m * 12:.2f}",
        "total_month": f"{result.get('total_month', 0):.2f}",
        "total_year": f"{result.get('total_year', 0):.2f}",
        "capacity_breakdown": format_breakdown_capacity(result.get("capacity_breakdown", [])),
        "license_breakdown": format_breakdown_license(result.get("license_breakdown", [])),
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
        "storage_breakdown": format_storage_breakdown(result.get("storage_breakdown")),
        "building_blocks_table": format_building_blocks_table(result.get("building_blocks", [])),
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
    }
    out = template_content
    for key, value in replacements.items():
        out = out.replace(f"{{{{ {key} }}}}", str(value))
    return out
