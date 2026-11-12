# Tooling

Cost engine and CLI for proposal costing.

## Cost engine (`cost_engine.py`)

- **load_cost_drivers()** / **load_scenarios()** / **load_proposal_defaults()** / **load_role_allocation()** / **load_projection()** / **load_product_packages():** Load model YAML files (defaults optional; fallback to inline where defined).
- **compute(scenario_id, overrides=None, product_root=None, package_id=None, use_reservation=False, storage_gb=None, implementation_fte=None, implementation_months=None, maintenance_fte=None, role_allocation_path=None, ...):** Returns full result dict. If `package_id` is set, scenario and implementation/maintenance come from the package (fixed USD or FTE profile). Result includes `package_id`, `package_name` when a package is used.
  - **currency** (`USD` default, `EUR`): amounts in that currency; rows carry neutral `per_month` / `per_year` (overage `max_per_day`, Planning `equivalent_per_session_window`), the `usd_*` aliases only for USD. Missing EUR prices raise `ValueError`, never a conversion.
- **compute_projection(..., package_id=None, ...):** Runs compute per horizon; passes through `package_id`.
- **fill_template(result, template_content):** Replaces placeholders including `scenario_id`, `total_year`, `capacity_breakdown`, `license_breakdown`, `building_blocks_table`, `role_breakdown_table`, `projection_table`, `implementation_one_time`, `maintenance_year`, `tco_3y`, `tco_5y`, `package_name`, `customer_name`, `offer_date`, `overage`, `planning`, `customer_questions`, scope/assumptions, storage.
- **compute_overage() / compute_planning() / payg_usd_per_cu_hour():** Overage and Fabric Planning lines on the prod SKU, built on `tooling/superversion/capacity.py` (see `docs/README.md`).

## CLI (`run_costing.py`)

Run from the product root or from `tooling/` (with dependencies installed: `pip install -r ../requirements.txt` or repo-wide). Scenario is required unless provided via `--config` or `--package` (package defines scenario).

**Reproducibility:** Same model files (cost_drivers, scenarios, proposal_defaults, optional role_allocation, projection) plus same CLI arguments (or same `--config` file) produce the same output. Use a run-config file per customer/project and document cost_drivers version/valid_from when archiving a quote.

**Examples:**

```bash
# Default compact scenario
python tooling/run_costing.py --scenario compact

# Run from a config file (overrides via CLI still apply)
python tooling/run_costing.py --config model/run_config.yaml

# Override capacity and Pro users
python tooling/run_costing.py --scenario enterprise --capacity-prod F128 --pro-users 8

# Implementation and maintenance FTE (rates from cost_drivers.yaml)
python tooling/run_costing.py --scenario compact --implementation-fte 4 --implementation-months 6 --maintenance-fte 0.5

# Role allocation and projection + TCO
python tooling/run_costing.py --scenario compact --role-allocation model/role_allocation.yaml --projection --tco-years 3,5

# Power BI only (PPU)
python tooling/run_costing.py --scenario power_bi_only --ppu-users 15

# Customer decided the overage question (off, or a threshold in CU hours per rolling 24 h)
python tooling/run_costing.py --scenario compact --overage-off
python tooling/run_costing.py --scenario compact --overage-threshold-cu-hours 40

# JSON output
python tooling/run_costing.py --scenario compact --json

# Fill template and write to dist
python tooling/run_costing.py --scenario compact --output dist/last_calculation.md

# 1-year reservation pricing
python tooling/run_costing.py --scenario compact --reservation

# OneLake storage estimate (e.g. 500 GB)
python tooling/run_costing.py --scenario compact --storage-gb 500

# Assumptions: quote valid 14 days, region
python tooling/run_costing.py --scenario compact --quote-valid-days 14 --region "North Europe"

# Product package (scenario + implementation from package; fixed or FTE)
python tooling/run_costing.py --package starter --projection --output dist/starter_calc.md

# Generate offer with package, custom template, customer and date
python tooling/run_costing.py --package starter --template templates/offer_snippet.md --customer-name "Aurora Group" --offer-date 2025-02-15 --projection --output dist/angebot_aurora.md
```

**Options:** `--config` (run-config YAML; all other params can come from here; CLI overrides config), `--scenario` (required if not using `--package`), `--package` (product package ID; overrides scenario), `--template` (template path, e.g. `templates/offer_snippet.md` for offers), `--customer-name`, `--offer-date` (for offer output), `--pro-users`, `--ppu-users`, `--capacity-dev`, `--capacity-test`, `--capacity-prod`, `--reservation`, `--storage-gb`, `--implementation-fte`, `--implementation-months`, `--maintenance-fte`, `--role-allocation`, `--projection`, `--tco-years` (comma-separated, e.g. `3,5`), `--contract-months`, `--region`, `--quote-valid-days`, `--json`, `--output` / `-o`.
