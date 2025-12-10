# Sample Data (Aurora)

Purpose:
Store small synthetic extracts aligned to the Aurora data contracts for demos and PBIP mockups.

Generation:
- Use `_internal/tools/scripts` together with `data_contracts/sources/synthetic/synthetic_config_core_v1.yaml`.
- Target file set (minimum for demo): `fact_sales.csv`, `fact_ops.csv`, `fact_inventory.csv`, `fact_finance.csv`, `dim_date.csv`, `dim_org.csv`, `dim_product.csv`, `dim_customer.csv`, `dim_asset.csv`, `security_user_org.csv`.
- Keep column names exactly as in the domain data contracts.

Notes:
- If no samples are present, regenerate before demos. Do not place client data here.
- Use UTF-8, comma-separated, headers included.
