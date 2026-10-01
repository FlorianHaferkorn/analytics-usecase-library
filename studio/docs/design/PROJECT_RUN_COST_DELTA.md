# Run-cost delta of a draft alternative

Status: implemented in the decision engine (`tooling/superversion/project_package/run_cost_delta.py`). Not yet in Studio. No tenant execution, no approval, no release.

## Purpose

WB-008 shows what an alternative changes in structure, WB-009 what it changes in delivery effort and price. Neither answers the customer's question about an environment or capacity decision: what does running the platform cost afterwards? This module prices the Fabric capacities that the selected environments actually use, for the baseline and for the alternative, and subtracts.

## Input

`architecture_input.capacities[]` (optional, additive in schema 2.0.0): `id` (the UUID that `physical_workspaces[].capacity_id` refers to), `sku` (F2 to F8192), `billing` (`payg` default, `reservation`) and `overage` (`state`, `threshold_cu_hours`). Without the list the comparison returns `not_evaluated`: a capacity is never guessed from a workspace.

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

- USD list prices; region and currency are not applied.
- Paused hours are not modelled.
- Licences, OneLake storage and workspace-monitoring ingestion are outside this delta.
- Not in Studio yet: the route and the view follow the WB-008/WB-009 pattern.
