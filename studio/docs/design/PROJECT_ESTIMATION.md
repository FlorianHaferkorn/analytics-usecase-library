# Project estimation preview

Status: implemented preview, not an approved offer or automated scheduling system.

## Boundary and decision

The existing Project Package commercial schema explicitly requires `price_values_embedded: false` when that flag is present. Its estimate stores a total and basis references, not a private rate card. The plan records effort and role references, not named people and availability. The calculator therefore does not silently expand those modules or overwrite commercial approval. It calculates a private, unsaved scenario against an exact package revision, with an explicit JSON download. The download includes entered rates and names and must not be treated as a customer-facing deliverable.

`ProjectEstimation({projectId, revisionHash})` can be mounted in the automation workspace. The form uses the shared Studio panel/button components and design tokens. Project or revision changes clear inputs. Editing any input invalidates the result. Late responses cannot restore a result for stale inputs. No rate or capacity value is prefilled. Private JSON downloads can be restored only into the same project and exact revision (1 MB maximum). Restore validates safe form structure and resource references; it restores inputs only, never trusts saved totals, and requires a fresh Python calculation. A scenario is not implicitly transferred to a newer revision or another customer.

## Calculation

- Enter one currency, planning horizon in working days and an explicit effort contingency percentage, including zero where intended.
- Enter named people, hours per working day and availability percentage.
- Assign effort hours and explicit hourly cost/sell rates to a person and role.
- Buffered effort = effort × (1 + contingency / 100). Cost and rate-based revenue use buffered effort. This revenue is a scenario, not a fixed-price quote.
- Each line amount is rounded half-up to two decimals; person, role and project totals sum those rounded line amounts.
- Capacity = planning working days × hours/day × availability/100. Repeated assignments to the same person are summed before checking overload.
- Minimum working days = maximum, across people, of buffered effort / daily available hours. Assigned effort with zero capacity is infeasible.
- Margin is undefined when revenue is zero. Zero rates/effort are permitted only when explicitly entered; empty/missing values are rejected.

This is a resource-capacity lower bound, not a dependency/calendar-aware schedule. Taxes, travel, software charges, exchange rates, leave and acceptance commitments are not inferred. Mixed currencies are rejected. Two-decimal amounts are a documented calculation convention, not currency-specific accounting precision.

## Authority and testing

Python `tooling.superversion.project_package.estimation` owns validation and Decimal arithmetic. POST `/api/projects/[projectId]/estimation` requires project editor access, an exact revision and explicit scenario. The engine checks the revision belongs to the selected project. Responses are private/no-store. There is no Package write, approval side effect or shared rate cache.

Tests cover decimal arithmetic, line rounding, zero and missing values, nonfinite values, currency mismatches, resource overload, impossible capacity, duplicate/foreign resources, deterministic output, project/revision binding, API authorization, stale UI results and private input reset.

Next integration requires an explicitly designed private commercial repository and an approved mapping from a scenario reference to the Package aggregate estimate. Do not embed private rates in shared Package outputs to claim that the workflow is complete.
