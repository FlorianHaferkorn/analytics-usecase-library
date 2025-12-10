# Sample Data Contracts (Aurora)

Purpose:
Minimal references to the synthetic data contracts used for the Aurora Group showcase.

Sources:
- `data_contracts/sources/synthetic/synthetic_data_contract.yaml` – backbone for generated demo data
- Domain overlays: `data_contracts/domains/commercial_sales.yaml`, `operations.yaml`, `supply_chain.yaml`, `finance.yaml`, `experience.yaml`

Usage:
- Use these contracts to generate or validate synthetic datasets before loading into the Aurora semantic model.
- Keep field names identical to the domain contracts to stay OneLake-compatible.
- Preferred grains for demo:
  - `fact_sales` (invoice_line)
  - `fact_ops` (shift/asset/day)
  - `fact_inventory` (product/org/day)
  - `fact_finance` (org/month)
  - `fact_service` (customer/org/day)
