# Evidence-Grain Normalization Log

**Date:** 2026-02-14
**Purpose:** Record normalizations applied when mapping audit-recommended grains to governed data-contract grains.

## Normalization Rules Applied

| UseCase_ID | Audit Grain | Contract Grain (applied) | Reason |
|------------|-------------|--------------------------|--------|
| SCM-003 | `sku_location_month` | `location_sku_month` | Audit used reversed entity order; contract defines `location_sku_month` in `supply_chain.yaml` (`fact_inventory`, `fact_inventory_plan`). Normalized to contract naming for tooling compatibility. |

## Use Cases with Exact Match (no normalization needed)

| UseCase_ID | Grain | Contract Source |
|------------|-------|-----------------|
| COM-001 | `invoice_line` | `commercial_sales.yaml` / `fact_sales` |
| COM-002 | `invoice_line` | `commercial_sales.yaml` / `fact_sales` |
| COM-003 | `customer_month` | `commercial_sales.yaml` / `fact_customer_events`, `fact_customer_value` |
| COM-004 | `promotion` | `commercial_sales.yaml` / `fact_promo` |
| FIN-001 | `entity_month` | `finance.yaml` / `fact_fin` |
| FIN-002 | `plant_line_product_month` | `finance.yaml` / `fact_cost` |
| OPS-001 | `line_day` | `operations.yaml` / `fact_ops` |
| OPS-002 | `failure_event` | `operations.yaml` / `fact_ops_failures` |
| OPS-003 | `line_day` | `operations.yaml` / `fact_ops` |
| SCM-001 | `location_sku_month` | `supply_chain.yaml` / `fact_inventory` |
| SCM-002 | `shipment_line` | `supply_chain.yaml` / `fact_shipments` |
| XD-001 | `case` | `experience.yaml` / `fact_support_cases` |
| XD-002 | `agent_day` | `experience.yaml` / `fact_workforce_management` |
| XD-003 | `entity_month` | `executive.yaml` / `fact_exec` |

## Governance Gaps Identified

None. All 15 grains now match a governed fact-table grain in `core/data_contracts/domains/*.yaml`.
