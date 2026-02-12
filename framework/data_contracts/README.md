# Data Contracts

**Purpose:** Define the **Silver layer** (conformed, validated domain data) for the ActionReady Analytics Framework. Contracts fix schemas, grains, units, and lineage so Gold and semantic models stay consistent.

**Data layers (standard):** We define **Silver** via contracts. Gold (consumption-ready) is derived from Silver. Staging/Bronze are out of scope unless explicitly included. See `framework/strategy_operating_model/operating_model/data_layers_standard.md`.

**Scope:**

- Domain contracts (commercial_sales, operations, supply_chain, finance, experience, executive) — **Silver**
- Source contracts (including synthetic backbone) — map to Silver
- Keys, grains, units, aggregation rules, ownership metadata
- Excludes ETL code and customer-specific storage formats

Structure:

```yaml
framework/data_contracts/
  domains/
    commercial_sales.yaml
    operations.yaml
    supply_chain.yaml
    finance.yaml
    experience.yaml
    executive.yaml
  sources/
    commercial.yaml
    operations.yaml
    supply_chain.yaml
    finance.yaml
    experience.yaml
    synthetic/
      synthetic_data_contract.yaml
      synthetic_config_core_v1.yaml
```

Usage:

- Customers: validate existing systems against these requirements; align IT and business on ownership and data quality.
- Delivery teams: model and ingestion specs start here; keep semantic assumptions identical to these contracts.
- Framework evolution: extend contracts carefully and version changes; preserve conformed dimensions (dim_date, dim_org, dim_product, dim_customer, security_user_org).

Relations:

- WHY: derived from domains and KPIs in `framework/strategy_operating_model/company/`.
- HOW: enforced by `framework/strategy_operating_model/operating_model/semantic_layer.md` and `data_governance.md`.
- WITH WHAT: templates in `framework/templates/data_contract_templates/` guide structure.
- WHAT: framework/semantic_models and framework/usecases depend on these schemas.
