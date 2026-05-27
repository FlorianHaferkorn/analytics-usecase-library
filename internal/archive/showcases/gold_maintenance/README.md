# Archive: showcases/gold_maintenance

One-time gold-layer data scripts that have served their purpose.

| Script | Archived | Reason |
|---|---|---|
| `generate_missing_facts.py` | 2026-05-27 | One-time backfill script for `fact_quality_costs`, `fact_complaints`, `fact_supplier_risk`. Parquet partitions (2020–2024) are committed under `showcases/aurora_group/data/gold/facts/`. No orchestrator calls this script. Retained for reference when regenerating Aurora showcase from scratch. |
