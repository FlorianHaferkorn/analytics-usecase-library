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

**Prerequisites:** Python with `pandas`, `pyarrow`, and `deltalake` (e.g. `pip install pandas pyarrow deltalake`). Delta Lake format is optional but recommended for date-partitioned facts. The script reads existing gold dimensions (dim_org, dim_date, dim_product, dim_customer) when present to align keys.

**Location:** `showcases/aurora_group/data/scripts/` — orchestrator; output in sibling folder `gold/`. Operations and supply_chain are delegated to `gold/generate_operations_gold.py` and `gold/generate_supply_chain_gold.py` (realistic names, seasonality, full 2020–2024). For RLS, run `py showcases/aurora_group/data/gold/generate_security_user_org.py` (generates `security_user_org` from company org chart).

**Verifying fact coverage:** From repo root run `py showcases/aurora_group/data/gold/check_fact_coverage.py` to report row counts, date ranges (2020–2024), parquet file counts, and format (Delta/Parquet) per fact. Facts marked SPARSE (e.g. supply_chain with only 60 month-ends) can be refreshed by re-running the orchestrator or `--domain supply_chain`. Facts with multiple parquet files (MULTI) must use `Table.Combine` in the semantic model M partition (e.g. fact_sales, fact_experience).

## Data Format

**Delta Lake format:** Date-partitioned facts (fact_sales, fact_accounts_payable, fact_accounts_receivable, fact_cash_position, fact_cash_flow, fact_inventory, fact_cogs, fact_fulfillment, fact_stockout, fact_forecast, fact_ops, fact_ops_failures, fact_maintenance, fact_quality, fact_experience) are written as Delta Lake when `deltalake` package is available. This enables partition pruning and better query performance.

**Fiscal Year partitioning:** All date-partitioned facts use `partition_by=["Fiscal Year"]`, creating folder structure `Fiscal Year=2020/`, `Fiscal Year=2021/`, etc. The `Fiscal Year` column is derived from `DateKey` (first 4 characters) automatically by `write_fact_delta()`.

**TMDL pattern:** Semantic model uses `Table.Combine` pattern for all Delta-partitioned facts to read all parquet files under the fact folder (including subfolders like `Fiscal Year=YYYY/`). Example pattern:

```m
ParquetTables = Table.AddColumn(FilteredFiles, "Parquet", each Parquet.Document([Content])),
Combined = Table.Combine(ParquetTables[Parquet])
```

**Plain parquet facts:** fact_promo (no date dimension) and dimensions remain as single parquet files. These do not benefit from partitioning due to small size or lack of date dimension.

## Quick Reference

### Regenerate specific fact(s)

```powershell
# Single domain
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain experience

# Multiple domains
py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain operations,supply_chain

# All domains
py showcases/aurora_group/data/scripts/generate_aurora_gold.py
```

### Verify fact format and coverage

```powershell
# Check all facts (rows, dates, format)
py showcases/aurora_group/data/gold/check_fact_coverage.py

# Full validation: coverage + optional regeneration + Stage 1 (run from repo root)
.\showcases\aurora_group\data\validate_delta_migration.ps1
.\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -Domain experience
.\showcases\aurora_group\data\validate_delta_migration.ps1 -Regenerate -SkipStage1
```

### Verify Delta format manually

```powershell
# Check if fact is Delta (has _delta_log folder)
Test-Path "showcases/aurora_group/data/gold/facts/fact_experience/_delta_log"

# List all Delta facts
Get-ChildItem "showcases/aurora_group/data/gold/facts" -Directory | 
    Where-Object { Test-Path (Join-Path $_.FullName "_delta_log") } | 
    Select-Object Name
```

### Troubleshooting

**Issue:** Fact shows as "Parquet" but should be Delta

- **Solution:** Ensure `deltalake` package is installed: `pip install deltalake`
- Regenerate the fact: `py showcases/aurora_group/data/scripts/generate_aurora_gold.py --domain <domain>`

**Issue:** TMDL partition fails to load fact data

- **Solution:** Verify fact uses `Table.Combine` pattern (check fact_*.tmdl partition source)
- Ensure fact folder contains parquet files (check `Fiscal Year=YYYY/` subfolders for Delta)

**Issue:** Relationship missing in semantic model

- **Solution:** Check relationships.tmdl for the relationship
- Verify corresponding Technical Factsheet documents the relationship (section 4.2)
