# Model

Product-specific data for proposal costing: cost drivers (prices), scenario definitions, optional role allocation, projection, and run-config.

## cost_drivers.yaml

- **Purpose:** Single source of reference prices (USD) for Fabric capacity SKUs (F2–F2048), optional OneLake storage ($/GB/month), Power BI licenses (Pro, PPU), and **services_rates** for implementation and maintenance.
- **Fields:** `schema_version`, `valid_from`, `source_urls`, `fabric_capacity[]`, `onelake_storage`, `power_bi_licenses[]`, **`fabric_regions`** (PAYG per CU hour and OneLake per GB/month per Azure region, USD and EUR; takes precedence over `fabric_capacity[]` whenever the region is listed), **`services_rates`** (optional but required when FTE are used): `implementation_usd_per_fte_month`, `maintenance_usd_per_fte_year`; optional `source`/`note` for audit. All numeric rates live only here; no fallback in code.
- **Maintenance:** Update `valid_from` when refreshing prices; keep `source_urls` for audit. OneLake is used only when `storage_gb` is passed to `compute()`.

## scenarios.yaml

- **Purpose:** Repeatable scenario definitions: strategy (enterprise | compact | null), default capacities per environment (dev/test/prod), license model (pro_for_authors | ppu_all), and default user counts (default_pro_users, default_ppu_users).
- **Scenarios:** enterprise, compact, power_bi_only, compact_with_fabric. CLI overrides (e.g. --capacity-prod F128, --pro-users 8) override these defaults per run.
- **Maintenance:** Add or adjust scenarios here; ensure every referenced SKU exists in `cost_drivers.yaml`.

## product_packages.yaml (optional)

- **Purpose:** Product packages bundle a scenario with implementation pricing for automated offers. When `package_id` is used, scenario comes from the package; implementation is either fixed USD or FTE-based (rates from cost_drivers).
- **Fields:** `packages`: dict of package_id → `{ name, scenario_id, implementation_fixed_usd?, maintenance_fixed_usd_per_year? }` for fixed-price packages, or `{ name, scenario_id, implementation_fte?, implementation_months?, maintenance_fte? }` for FTE-based (uses cost_drivers.services_rates). Optional per package: `role_allocation_path`, `description`.
- **Maintenance:** Add or adjust packages; ensure scenario_id exists in scenarios.yaml. Fixed-price packages do not require services_rates.

## proposal_defaults.yaml (optional)

- **Purpose:** Default texts for proposal output: `scope_in`, `scope_out` (bullet lists), `default_contract_term_months`, `default_region`, `price_basis`, `viewer_note_below_f64`, `viewer_note_f64_plus`, `default_quote_valid_days`. Optional **`building_block_labels`**: map block id to display label. Optional **`building_block_categories`**: map block id to TCO category (`Acquisition` | `Operating`) for the "Kosten nach Bausteinen" table. Optional **`sensitivity_note`**: one line or short paragraph on how changes (users, capacity, region) affect the TCO. Optional **`customer_contributions`**: list of strings (RFP-style) describing what the customer must provide for implementation. Optional **`implementation_milestones`**: list of `{ phase, deliverable, duration }` (RFP-style) for the implementation timeline table. Optional FTE defaults: `default_implementation_fte`, `default_implementation_months`, `default_maintenance_fte` (overridable by scenario or CLI). If the file is missing, the engine uses inline fallbacks.
- **Maintenance:** Adjust scope, viewer messages, customer contributions, and milestones per organisation; region and quote validity as needed.

## role_allocation.yaml (optional)

- **Purpose:** Allocate FTE to data roles (reference to `core/organization/org_roles.yaml` or a path in `roles_source`) for implementation and maintenance. Used when you want to derive implementation_fte/maintenance_fte from roles or to show a role/FTE table in the proposal.
- **Fields:** `roles_source`: `"core"` or path to org_roles YAML. `allocations`: list of `{ role_id, fte, phase, person? }` with `phase` one of `implementation` | `maintenance`. Optional `person` (or `contact`): name of the person/contact who will fill the role (shown in the proposal; empty/omitted → "—" and "beim Kick-off benennen"). `role_id` must exist in the referenced org_roles. See `role_allocation.yaml.example`.
- **Maintenance:** Per customer/project you can override by passing a different path via CLI `--role-allocation` or run-config.

## projection.yaml (optional)

- **Purpose:** Define cost-projection horizons (e.g. year1, year2_3, year4_5) with overrides for capacities and user counts; and optional `tco_years` (e.g. `[3, 5]`) for TCO sums.
- **Fields:** `horizons`: list of `{ id, label, years, capacities?, pro_users?, ppu_users? }`. Only overrides vs base scenario; missing envs/SKUs come from the scenario. `tco_years`: list of integers for which to compute TCO (e.g. `[3, 5]`). All values in YAML; no horizon definitions in code.
- **Maintenance:** Add or adjust horizons and TCO years; ensure SKUs exist in cost_drivers.

## run_config.yaml.example

- **Purpose:** Example run-config for reproducible calculations. Copy to `run_config.yaml` (or a customer-specific file) and set scenario_id or package_id, overrides, use_reservation, storage_gb, implementation_fte, maintenance_fte, role_allocation_path, projection, tco_years, output_path. Optional for offers: package_id, template_path (e.g. templates/offer_snippet.md), customer_name, offer_date. Run with `--config model/run_config.yaml`. Same config + same model files = same output.
