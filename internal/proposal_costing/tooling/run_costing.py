#!/usr/bin/env python3
"""
Proposal Costing – CLI.
Usage: python run_costing.py --scenario compact [--pro-users 5] [--capacity-prod F64] [--json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root or from tooling/
if __name__ == "__main__" and str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    typer = None
    Console = None
    Table = None

import yaml
from cost_engine import compute, compute_projection, fill_template, load_product_packages

app = typer.Typer(help="Proposal Costing – compute scenario costs.")


def _product_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_config(config_path: str) -> dict:
    root = _product_root()
    p = Path(config_path)
    if not p.is_absolute():
        p = root / p
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _run(
    scenario: str = typer.Option(None, "--scenario", "-s", help="Scenario: enterprise, compact, power_bi_only, compact_with_fabric (or use --package)"),
    config: str | None = typer.Option(None, "--config", help="Run config YAML (params; CLI overrides config)"),
    package: str | None = typer.Option(None, "--package", help="Product package ID (overrides scenario; scenario from package)"),
    template: str | None = typer.Option(None, "--template", help="Template path (e.g. templates/offer_snippet.md); default proposal_snippet.md"),
    customer_name: str | None = typer.Option(None, "--customer-name", help="Customer name for offer output"),
    offer_date: str | None = typer.Option(None, "--offer-date", help="Offer date for offer output"),
    pro_users: int | None = typer.Option(None, "--pro-users", help="Override Pro user count"),
    ppu_users: int | None = typer.Option(None, "--ppu-users", help="Override PPU user count"),
    capacity_dev: str | None = typer.Option(None, "--capacity-dev", help="Override dev capacity SKU (e.g. F2)"),
    capacity_test: str | None = typer.Option(None, "--capacity-test", help="Override test capacity SKU"),
    capacity_prod: str | None = typer.Option(None, "--capacity-prod", help="Override prod capacity SKU"),
    reservation: bool = typer.Option(False, "--reservation", help="Use 1-year reservation pricing for capacity"),
    storage_gb: float | None = typer.Option(None, "--storage-gb", help="OneLake storage estimate (GB); adds storage cost"),
    implementation_fte: float | None = typer.Option(None, "--implementation-fte", help="Implementation FTE (ignored if package has fixed price)"),
    implementation_months: float | None = typer.Option(None, "--implementation-months", help="Implementation months"),
    maintenance_fte: float | None = typer.Option(None, "--maintenance-fte", help="Maintenance FTE (ongoing)"),
    role_allocation: str | None = typer.Option(None, "--role-allocation", help="Path to role_allocation.yaml"),
    projection: bool = typer.Option(False, "--projection", help="Use projection horizons and output TCO"),
    tco_years: str | None = typer.Option(None, "--tco-years", help="TCO year sums (comma-separated, e.g. 3,5)"),
    contract_months: int | None = typer.Option(None, "--contract-months", help="Contract term in months (for assumptions)"),
    region: str | None = typer.Option(None, "--region", help="Region (e.g. West Europe) for assumptions"),
    quote_valid_days: int | None = typer.Option(None, "--quote-valid-days", help="Days until quote expires (from valid_from)"),
    overage_off: bool = typer.Option(False, "--overage-off", help="Customer switched capacity overage off"),
    overage_threshold: float | None = typer.Option(
        None, "--overage-threshold-cu-hours", help="Customer's rolling 24-h overage threshold in CU hours"),
    json_out: bool = typer.Option(False, "--json", help="Output result as JSON only"),
    output: str | None = typer.Option(None, "--output", "-o", help="Fill template and write to file (e.g. dist/last_calculation.md)"),
) -> None:
    cfg: dict = {}
    if config:
        try:
            cfg = _load_config(config)
        except FileNotFoundError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)

    package = package or cfg.get("package_id") or cfg.get("package")
    scenario = scenario or cfg.get("scenario_id") or cfg.get("scenario")
    if package:
        root = _product_root()
        packages = load_product_packages(root)
        if package not in packages:
            typer.echo(f"Unknown package: {package}. Valid: {list(packages)}", err=True)
            raise typer.Exit(1)
        scenario = packages[package].get("scenario_id", scenario)
    if not scenario:
        typer.echo("Scenario required (--scenario or config.scenario_id, or use --package)", err=True)
        raise typer.Exit(1)

    template = template or cfg.get("template_path") or cfg.get("template")
    customer_name = customer_name if customer_name is not None else cfg.get("customer_name")
    offer_date = offer_date if offer_date is not None else cfg.get("offer_date")

    overrides: dict = {}
    pro_users = pro_users if pro_users is not None else cfg.get("pro_users")
    ppu_users = ppu_users if ppu_users is not None else cfg.get("ppu_users")
    capacity_dev = capacity_dev or cfg.get("capacity_dev")
    capacity_test = capacity_test or cfg.get("capacity_test")
    capacity_prod = capacity_prod or cfg.get("capacity_prod")
    reservation = reservation or cfg.get("use_reservation", False)
    storage_gb = storage_gb if storage_gb is not None else cfg.get("storage_gb")
    implementation_fte = implementation_fte if implementation_fte is not None else cfg.get("implementation_fte")
    implementation_months = implementation_months if implementation_months is not None else cfg.get("implementation_months")
    maintenance_fte = maintenance_fte if maintenance_fte is not None else cfg.get("maintenance_fte")
    role_allocation = role_allocation or cfg.get("role_allocation_path")
    projection = projection or cfg.get("projection", False)
    tco_years_list: list[int] | None = None
    if tco_years:
        tco_years_list = [int(x.strip()) for x in tco_years.split(",") if x.strip()]
    elif cfg.get("tco_years"):
        tco_years_list = [int(x) for x in cfg["tco_years"]]
    contract_months = contract_months or cfg.get("contract_term_months")
    region = region or cfg.get("region")
    quote_valid_days = quote_valid_days if quote_valid_days is not None else cfg.get("quote_valid_days")
    output = output or cfg.get("output_path")

    if pro_users is not None:
        overrides["pro_users"] = pro_users
    if ppu_users is not None:
        overrides["ppu_users"] = ppu_users
    caps = {}
    if capacity_dev is not None:
        caps["dev"] = capacity_dev
    if capacity_test is not None:
        caps["test"] = capacity_test
    if capacity_prod is not None:
        caps["prod"] = capacity_prod
    if caps:
        overrides["capacities"] = caps
    # Overage decision (customer question) and Fabric Planning sessions; config keys
    # overage_enabled, overage_threshold_cu_hours, planning_sessions {planner, stakeholder, viewer}.
    if overage_off or cfg.get("overage_enabled") is False:
        overrides["overage_enabled"] = False
    threshold = overage_threshold if overage_threshold is not None else cfg.get("overage_threshold_cu_hours")
    if threshold is not None:
        overrides["overage_threshold_cu_hours"] = threshold
    if cfg.get("planning_sessions"):
        overrides["planning_sessions"] = cfg["planning_sessions"]

    root = _product_root()
    try:
        if projection:
            proj_result = compute_projection(
                scenario,
                product_root=root,
                tco_years_list=tco_years_list,
                package_id=package,
                use_reservation=reservation,
                storage_gb=storage_gb,
                implementation_fte=implementation_fte,
                implementation_months=implementation_months,
                maintenance_fte=maintenance_fte,
                role_allocation_path=role_allocation,
                contract_term_months=contract_months,
                region=region,
                quote_valid_days=quote_valid_days,
            )
            first = (proj_result.get("horizons") or [{}])[0]
            result = first.get("breakdown", {}) if isinstance(first, dict) else {}
            result = dict(result)
            result["horizons"] = proj_result.get("horizons", [])
            result["tco_by_years"] = proj_result.get("tco_by_years", {})
        else:
            result = compute(
                scenario,
                overrides if overrides else None,
                product_root=root,
                package_id=package,
                use_reservation=reservation,
                storage_gb=storage_gb,
                implementation_fte=implementation_fte,
                implementation_months=implementation_months,
                maintenance_fte=maintenance_fte,
                role_allocation_path=role_allocation,
                contract_term_months=contract_months,
                region=region,
                quote_valid_days=quote_valid_days,
            )
    except (FileNotFoundError, KeyError, ValueError) as e:
        if json_out:
            print(json.dumps({"error": str(e)}))
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if json_out:
        print(json.dumps(result, indent=2))
        if output:
            _write_template_output(result, output, template_path=template, customer_name=customer_name, offer_date=offer_date)
        return

    if output:
        _write_template_output(result, output, template_path=template, customer_name=customer_name, offer_date=offer_date)

    console = Console()
    console.print(f"\n[bold]Scenario:[/bold] {result['scenario_id']}  [dim]Pricing: {result.get('pricing_mode', 'Pay-as-you-go')}[/dim]\n")
    table = Table(title="Cost summary (USD)")
    table.add_column("Item", style="cyan")
    table.add_column("Per month", justify="right")
    table.add_column("Per year", justify="right")
    table.add_row("Capacity", f"{result['capacity_month']:.2f}", f"{result['capacity_month'] * 12:.2f}")
    table.add_row("Licenses (Pro + PPU)", f"{result['license_month']:.2f}", f"{result['license_month'] * 12:.2f}")
    if result.get("storage_month"):
        table.add_row("OneLake Storage", f"{result['storage_month']:.2f}", f"{result['storage_month'] * 12:.2f}")
    if result.get("implementation_one_time") or result.get("maintenance_year"):
        table.add_row("Implementation (one-time)", "—", f"{result.get('implementation_one_time', 0):.2f}")
        table.add_row("Maintenance (per year)", f"{result.get('maintenance_year', 0) / 12:.2f}", f"{result.get('maintenance_year', 0):.2f}")
    table.add_row("[bold]Total[/bold]", f"[bold]{result['total_month']:.2f}[/bold]", f"[bold]{result['total_year']:.2f}[/bold]")
    console.print(table)
    if result.get("tco_by_years"):
        console.print("\n[bold]TCO[/bold]")
        for years, val in sorted(result["tco_by_years"].items()):
            console.print(f"  {years} years: {val:.2f} USD")
    if result.get("viewer_note"):
        console.print(f"\n[dim]Viewer:[/dim] {result['viewer_note']}")

    if result["capacity_breakdown"]:
        console.print("\n[bold]Capacity breakdown[/bold]")
        ct = Table()
        ct.add_column("Environment")
        ct.add_column("SKU")
        ct.add_column("USD/month", justify="right")
        for row in result["capacity_breakdown"]:
            ct.add_row(row["environment"], row["sku"], f"{row['usd_per_month']:.2f}")
        console.print(ct)

    if result["license_breakdown"]:
        console.print("\n[bold]License breakdown[/bold]")
        lt = Table()
        lt.add_column("License")
        lt.add_column("Users", justify="right")
        lt.add_column("USD/month", justify="right")
        for row in result["license_breakdown"]:
            if row["users"] > 0:
                lt.add_row(row["license"].upper(), str(row["users"]), f"{row['usd_per_month']:.2f}")
        console.print(lt)
    console.print()


def _write_template_output(result: dict, output_path: str, template_path: str | None = None, customer_name: str | None = None, offer_date: str | None = None) -> None:
    root = _product_root()
    if template_path:
        tp = Path(template_path)
        if not tp.is_absolute():
            tp = root / tp
    else:
        tp = root / "templates" / "proposal_snippet.md"
    if not tp.exists():
        typer.echo(f"Template not found: {tp}", err=True)
        return
    res = dict(result)
    if customer_name is not None:
        res["customer_name"] = customer_name
    if offer_date is not None:
        res["offer_date"] = offer_date
    with open(tp, encoding="utf-8") as f:
        content = fill_template(res, f.read())
    out = Path(output_path)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    typer.echo(f"Written: {out}")


@app.command()
def main(
    scenario: str = typer.Option(None, "--scenario", "-s", help="Scenario (or set in --config or use --package)"),
    config: str | None = typer.Option(None, "--config", help="Run config YAML for reproducibility"),
    package: str | None = typer.Option(None, "--package", help="Product package ID"),
    template: str | None = typer.Option(None, "--template", help="Template path (e.g. templates/offer_snippet.md)"),
    customer_name: str | None = typer.Option(None, "--customer-name", help="Customer name for offer"),
    offer_date: str | None = typer.Option(None, "--offer-date", help="Offer date for offer"),
    pro_users: int | None = typer.Option(None, "--pro-users", help="Override Pro user count"),
    ppu_users: int | None = typer.Option(None, "--ppu-users", help="Override PPU user count"),
    capacity_dev: str | None = typer.Option(None, "--capacity-dev", help="Override dev capacity SKU"),
    capacity_test: str | None = typer.Option(None, "--capacity-test", help="Override test capacity SKU"),
    capacity_prod: str | None = typer.Option(None, "--capacity-prod", help="Override prod capacity SKU"),
    reservation: bool = typer.Option(False, "--reservation", help="Use 1-year reservation pricing"),
    storage_gb: float | None = typer.Option(None, "--storage-gb", help="OneLake storage estimate (GB)"),
    implementation_fte: float | None = typer.Option(None, "--implementation-fte", help="Implementation FTE"),
    implementation_months: float | None = typer.Option(None, "--implementation-months", help="Implementation months"),
    maintenance_fte: float | None = typer.Option(None, "--maintenance-fte", help="Maintenance FTE"),
    role_allocation: str | None = typer.Option(None, "--role-allocation", help="Path to role_allocation.yaml"),
    projection: bool = typer.Option(False, "--projection", help="Use projection horizons and TCO"),
    tco_years: str | None = typer.Option(None, "--tco-years", help="TCO years (e.g. 3,5)"),
    contract_months: int | None = typer.Option(None, "--contract-months", help="Contract term in months"),
    region: str | None = typer.Option(None, "--region", help="Region for assumptions"),
    quote_valid_days: int | None = typer.Option(None, "--quote-valid-days", help="Days until quote expires"),
    overage_off: bool = typer.Option(False, "--overage-off", help="Customer switched capacity overage off"),
    overage_threshold: float | None = typer.Option(
        None, "--overage-threshold-cu-hours", help="Customer's rolling 24-h overage threshold in CU hours"),
    json_out: bool = typer.Option(False, "--json", help="Output result as JSON only"),
    output: str | None = typer.Option(None, "--output", "-o", help="Fill template and write to file"),
) -> None:
    _run(
        scenario=scenario or "",
        config=config,
        package=package,
        template=template,
        customer_name=customer_name,
        offer_date=offer_date,
        pro_users=pro_users,
        ppu_users=ppu_users,
        capacity_dev=capacity_dev,
        capacity_test=capacity_test,
        capacity_prod=capacity_prod,
        reservation=reservation,
        storage_gb=storage_gb,
        implementation_fte=implementation_fte,
        implementation_months=implementation_months,
        maintenance_fte=maintenance_fte,
        role_allocation=role_allocation,
        projection=projection,
        tco_years=tco_years,
        contract_months=contract_months,
        region=region,
        quote_valid_days=quote_valid_days,
        overage_off=overage_off,
        overage_threshold=overage_threshold,
        json_out=json_out,
        output=output,
    )


if __name__ == "__main__":
    app()
