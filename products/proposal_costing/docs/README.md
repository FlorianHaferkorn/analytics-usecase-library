# Proposal Costing Product

## Purpose

Provide a governed, auditable product for proposal costing and pricing decisions that aligns with the ActionReady framework.

## Scope

- Cost driver catalog (Fabric capacity SKUs, Power BI Pro/PPU)
- Scenario-based allocation and pricing logic
- CLI and optional output templates for pricing proposals and approvals

## License logic

- **Power BI Pro** ($14/user/month): Required for **authors** (publish, edit reports) when using Fabric capacity or Power BI Premium capacity. With **F64 or larger** capacity, **viewers** do not need Pro (Free viewer access). Use Pro only for developer/author count when sizing with F64+.
- **Power BI Premium Per User (PPU)** ($24/user/month): Gives premium features per user **without** a Fabric F capacity. With PPU only, there is **no** Fabric Lakehouse, Warehouse, or full Medallion—only Power BI. For full Fabric (ingestion, pipelines, Warehouse), an **F capacity** is required; then Pro for authors is sufficient (viewers Free with F64+).
- **Enterprise recommendation:** Production on **F64 or larger** for stable performance and Free viewer access; Dev/Test can use smaller SKUs (e.g. F2/F4/F8).

## Scenarios

| Scenario | Strategy | Capacity (default) | Licenses | Use case |
|----------|----------|---------------------|----------|----------|
| **enterprise** | enterprise | F2 / F4 / F64 | Pro for authors | Full Medallion, 9 workspaces, large org |
| **compact** | compact | F2 / F4 / F8 | Pro for authors | Medallion, 3 workspaces, reduced footprint |
| **power_bi_only** | — | none | PPU for all | No Fabric; Power BI only |
| **compact_with_fabric** | compact | F2 per env | Pro for authors | Small team, Fabric + reports |

## Price sources

- **Fabric capacity:** [Microsoft Fabric pricing (Azure)](https://azure.microsoft.com/pricing/details/microsoft-fabric/) — Pay-as-you-go USD/month; ~41% savings with 1- or 3-year reservation.
- **Power BI Pro / PPU:** [Power BI pricing](https://powerbi.microsoft.com/pricing/) — List prices USD (annual commitment); Pro $14, PPU $24 per user/month.
- All amounts in this product are **USD**. Regional and contractual variations apply; treat as reference only.

## Output and proposal readiness

The generated proposal snippet includes: **Scope** (included / not included), **Viewer note** (automatic: F64+ prod = Free viewers; below F64 = viewers need Pro), **Pricing mode** (Pay-as-you-go or 1-year reservation), **Assumptions** (contract term, region, price basis, valid-from, quote-valid-until), and optional **OneLake Storage** when `--storage-gb` is used. Default scope and assumption texts are configurable in `model/proposal_defaults.yaml`.

## Phase 2: Building blocks, FTE, roles, projection, TCO

- **Cost by building block:** Result and template include a fixed list of technical building blocks (Fabric Capacity, Power BI, OneLake Storage, Implementation, Maintenance) with USD/month and USD/year. Labels come from `model/proposal_defaults.yaml` (`building_block_labels`).
- **Implementation and maintenance (FTE):** One-time implementation cost = `implementation_fte × implementation_months × rate`; annual maintenance = `maintenance_fte × rate`. Rates are defined only in `model/cost_drivers.yaml` under `services_rates` (`implementation_usd_per_fte_month`, `maintenance_usd_per_fte_year`). No default rates in code. FTE defaults can be set in `proposal_defaults.yaml`, per scenario, or via CLI/run-config.
- **Data roles and FTE:** Optional `model/role_allocation.yaml` (or path via `--role-allocation`) references `core/organization/org_roles.yaml` (or a showcase `org_roles`) by `role_id`. Each allocation has `role_id`, `fte`, and `phase` (implementation | maintenance). The engine can derive total implementation_fte and maintenance_fte from role allocations; result includes `role_breakdown` for the proposal.
- **Projection horizons:** Optional `model/projection.yaml` defines horizons (e.g. year1, year2_3, year4_5) with overrides for capacities and user counts. The engine runs `compute()` per horizon and returns a cost projection table. No horizon definitions in code; all values in YAML.
- **TCO:** Total cost of ownership over N years (e.g. 3 or 5) = platform costs per year + one-time implementation (year 1) + annual maintenance. N is configurable via `projection.yaml` (`tco_years`) or CLI `--tco-years`. Result includes `tco_by_years` (e.g. `{3: sum_3y, 5: sum_5y}`).
- **Run-config and reproducibility:** Optional run-config YAML (e.g. `model/run_config.yaml.example`) can hold scenario_id, overrides, use_reservation, storage_gb, implementation_fte, maintenance_fte, role_allocation_path, projection, tco_years, output_path. CLI supports `--config <path>`. Same model files + same CLI args (or same run-config) yield the same output. Document version/valid_from when archiving a quote.

## Status

Implemented: cost driver catalog, scenarios, cost engine, CLI, proposal template, reservation, viewer note, scope/assumptions, OneLake; Phase 2: building blocks, FTE/impl/maintenance, role_allocation, projection, TCO, run-config. See [model/README.md](../model/README.md) and [tooling/README.md](../tooling/README.md).
