# Aurora gold data generators

A single entry point generates all synthetic gold-layer parquet for the Aurora showcase. Output is written to `showcases/aurora_group/data/gold/` (dimensions and facts). Contract-compliant per framework data contracts; table names match CoreActionReady semantic model (e.g. `dim_case_queue`, `fact_support_cases`, `fact_accounts_payable`, `fact_cash_position`, `fact_cash_flow`).

**Run from repo root:**

```powershell
# All domains (operations, supply_chain, experience, finance, commercial)
py showcases/aurora_group/data/scripts/generate_aurora_gold.py

# Selected domains only
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain supply_chain,experience,finance
```

**Domains:** `commercial`, `operations`, `supply_chain`, `experience`, `finance` (default: all).

**Prerequisites:** Python with `pandas` and `pyarrow` (e.g. `pip install pandas pyarrow`). The script reads existing gold dimensions (dim_org, dim_date, dim_product, dim_customer) when present to align keys.

**Location:** `showcases/aurora_group/data/scripts/` — orchestrator; output in sibling folder `gold/`. Operations and supply_chain are delegated to `gold/generate_operations_gold.py` and `gold/generate_supply_chain_gold.py` (realistic names, seasonality, full 2020–2024). For RLS, run `py showcases/aurora_group/data/gold/generate_security_user_org.py` (generates `security_user_org` from company org chart).
