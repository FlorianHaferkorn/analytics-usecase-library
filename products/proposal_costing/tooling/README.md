# Tooling

Cost engine and CLI for proposal costing.

## Cost engine (`cost_engine.py`)

- **load_cost_drivers()** / **load_scenarios()** / **load_proposal_defaults()** / **load_role_allocation()** / **load_projection():** Load model YAML files (defaults optional; fallback to inline where defined).
- **compute(scenario_id, overrides=None, use_reservation=False, storage_gb=None, implementation_fte=None, implementation_months=None, maintenance_fte=None, role_allocation_path=None, contract_term_months=None, region=None, price_basis=None, valid_from=None, quote_valid_days=None):** Returns full result dict including `capacity_month`, `license_month`, `total_month`, `total_year`, `capacity_breakdown`, `license_breakdown`, `building_blocks`, `implementation_one_time`, `maintenance_year`, `role_breakdown`, `pricing_mode`, `viewer_note`, `prod_sku`, `scope_in`, `scope_out`, `valid_from`, `quote_valid_until`, and optionally `storage_month`, `storage_breakdown`.
- **compute_projection(scenario_id, product_root=None, projection_config=None, tco_years_list=None, use_reservation=False, storage_gb=None, implementation_fte=None, implementation_months=None, maintenance_fte=None, role_allocation_path=None, **compute_kw):** Runs compute per horizon from projection.yaml; returns `horizons`, `tco_by_year`, `tco_by_years`.
- **fill_template(result, template_content):** Replaces placeholders including `scenario_id`, `total_year`, `capacity_breakdown`, `license_breakdown`, `building_blocks_table`, `role_breakdown_table`, `projection_table`, `implementation_one_time`, `maintenance_year`, `tco_3y`, `tco_5y`, scope/assumptions, storage.

## CLI (`run_costing.py`)

Run from the product root or from `tooling/` (with dependencies installed: `pip install -r ../requirements.txt` or repo-wide). Scenario is required unless provided via `--config`.

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
```

**Options:** `--config` (run-config YAML; all other params can come from here; CLI overrides config), `--scenario` (required if not in config), `--pro-users`, `--ppu-users`, `--capacity-dev`, `--capacity-test`, `--capacity-prod`, `--reservation`, `--storage-gb`, `--implementation-fte`, `--implementation-months`, `--maintenance-fte`, `--role-allocation`, `--projection`, `--tco-years` (comma-separated, e.g. `3,5`), `--contract-months`, `--region`, `--quote-valid-days`, `--json`, `--output` / `-o`.
