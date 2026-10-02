# Run-cost delta of a draft alternative

Status: implemented in the decision engine (`tooling/superversion/project_package/run_cost_delta.py`) and in Studio (panel "Run cost" in the alternative comparison, route `GET /api/projects/{id}/architecture/run-cost`). No tenant execution, no approval, no release.

## Purpose

WB-008 shows what an alternative changes in structure, WB-009 what it changes in delivery effort and price. Neither answers the customer's question about an environment or capacity decision: what does running the platform cost afterwards? This module prices the Fabric capacities that the selected environments actually use, for the baseline and for the alternative, and subtracts.

## Input

`architecture_input.capacities[]` (optional, additive in schema 2.0.0): `id` (the UUID that `physical_workspaces[].capacity_id` refers to), `sku` (F2 to F8192), `billing` (`payg` default, `reservation`) and `overage` (`state`, `threshold_cu_hours`). Without the list the comparison returns `not_evaluated`: a capacity is never guessed from a workspace.

`architecture_input.report_audience` (optional): `authors`, `viewers`. With it the run cost includes Power BI Pro licences, coupled to the production SKU: authors always need Pro, viewers only below F64 (Learn `enterprise/licenses`; same boundary as Meridian OUT-REPORT). An alternative that moves production across F64 therefore shows its licence effect next to the capacity price.

Region and currency: `architecture_input.region` selects the regional PAYG rate per CU hour from `cost_drivers.yaml` `fabric_regions` (Azure Retail Prices API, fetched 2026-10-01; westeurope and germanywestcentral 0.22 USD, eastus 0.18 USD). `cost_currency` (`USD` default, `EUR`) selects Microsoft's own EUR list, which is not a converted USD value (germanywestcentral 0.1936 EUR vs westeurope 0.1889 EUR at the same USD price). A region without a rate falls back to the US SKU table, in USD only. Power BI licences use Microsoft's list price in the chosen currency (Pro 14 USD / 12.10 EUR per user and month, annual billing, excl. VAT; EUR read 02.10.2026 from microsoft.com/de-de). A currency without a recorded licence price is counted but listed as unpriced (since 1.3.0).

`architecture_input.monitoring` (optional): `capacity_id` of the capacity hosting the central monitoring Eventhouse (priced even if no workload workspace uses it) and `retained_gb` (monitoring data at the chosen retention, OneLake hot rate). Monitoring compute is CU on that capacity and already inside its price (Learn `real-time-intelligence-consumption`).

Without `monitoring.capacity_id` the first capacity with `purpose: monitoring` hosts the monitoring Eventhouse, the convention of the Meridian blueprint (`kapazitaet_stufen.monitoring_kapazitaet`, D-615). The explicit id wins; if it names a different capacity than the tagged one, `monitoring_capacity.note` says so. Each side reports `monitoring_capacity` with `capacity_id` and `source` (`monitoring.capacity_id` or `capacities[].purpose`). Since `run_cost_delta.py` 1.2.0.

## Behavior

`compare_run_cost(repository, project_ref, baseline_revision, decision_ref, option_ref)`:

1. Evaluates the same hypothetical selection as WB-008 (`evaluate_alternative`) and refuses a blocked alternative.
2. Per side: the capacities used by workspaces in the selected environments, priced with `internal/proposal_costing` `cost_engine` (Microsoft list price, USD, reservation discount from `cost_drivers.yaml`).
3. Overage: the derived ceiling (threshold x 3 x PAYG per CU hour, per month) is reported per capacity and summed separately, never into the monthly total. Without a declared overage the Microsoft default (enabled, 25 %) applies and is marked as such.
4. Unpriced capacities (not declared, duplicate, SKU without list price) are listed, and `comparable` is false. They are never counted as zero.
5. Repository fingerprint before and after; nothing is written.

## What the reference shows

`build_reference_baseline(..., capacity_layout=...)`:

| Layout | Capacities | Dropping the test stage (`dev_prod`) |
|---|---|---|
| `prod_non_prod` (Meridian D-596) | F64 reserved for prod, F8 for dev and test | no saving: dev keeps the shared capacity |
| `per_stage` (full Microsoft recommendation) | F64 prod, F8 dev, F16 test | the test capacity goes |

## Limits

- List prices only; no negotiated or enterprise-agreement discount. Regional rates are a snapshot (`fetched` in `cost_drivers.yaml`) and must be refreshed.
- Paused hours are not modelled.
- Licences only for a declared `report_audience`; PPU is not modelled.
- OneLake storage of workload data is outside this delta; only monitoring storage is priced.
- Studio: the route needs the **viewer** role, unlike WB-009 (editor, price: admin). The result carries list prices only, which is what the customer's own Azure bill shows; no rate, margin or staffing. Fetched on explicit request, `private, no-store`, rejected unless `persist: false`.
