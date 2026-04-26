# SAP ECC / S/4HANA Connector

Extracts billing, GL journal, and inventory data from SAP ECC or S/4HANA via
OData v2 and lands it into the Aurora Delta Lake bronze zone as partitioned
Parquet files.

## Source → Target mapping

| SAP Tables | OData EntitySet | Aurora Target |
|---|---|---|
| VBAK + VBAP | `BillingDocumentItemSet` | `fact_sales` |
| BKPF + BSEG | `JournalEntryItemSet` | `fact_gl_journal` |
| MARA + MBEW | `InventoryStockSet` | `fact_inventory` |

## Quick start

```python
from tooling.connectors.sap.adapter import SAPConnectorAdapter, SAPConfig
from tooling.connectors.base import ParquetSink
from pathlib import Path

adapter = SAPConnectorAdapter()

# CI / local dev — no SAP sandbox required
config = SAPConfig(base_url="", auth_type="mock")
sink = ParquetSink(root=Path("data/bronze/sap"), partition_by=["FiscalYear"])

result = adapter.run(config, sink)
print(f"Extracted {result.records_extracted} rows → {len(result.files_written)} files")
```

## Authentication

### Basic auth (SAP ECC)

```python
config = SAPConfig(
    base_url="https://my-sap-system.example.com",
    client="100",
    auth_type="basic",
    username="BIADMIN",
    password="<password>",
)
```

### OAuth2 bearer (S/4HANA Cloud)

```python
config = SAPConfig(
    base_url="https://my-s4.example.com",
    auth_type="oauth2",
    oauth_token="<bearer_token>",
)
```

## OData service setup (SAP basis)

The connector expects an OData v2 service named `ZBI_AURORA_SRV` registered
in SICF.  Three EntitySets must be exposed:

| EntitySet | SAP Transaction | CDS View |
|---|---|---|
| `BillingDocumentItemSet` | VF03/VF05 | `ZBI_C_BILLINGITEM` |
| `JournalEntryItemSet` | FB03/FAGLL03 | `ZBI_C_JOURNALITEM` |
| `InventoryStockSet` | MB52/MB53 | `ZBI_C_INVENTORYSTOCK` |

Activation steps:
1. `/n/IWFND/MAINT_SERVICE` → Add service → search `ZBI_AURORA`
2. Assign authorization object `S_SERVICE` to the BI user
3. Test with `$format=json&$top=1` in a browser before running the connector

## Studio plugin

The connector ships a Studio plugin at `studio/plugins/sap-connector/`.
Install it via **Studio → Plugins → Install from local** and configure the
connection settings in the plugin settings panel.

Hook events emitted:
- `onConnectorExtract` — fires before extraction starts
- `onConnectorLand` — fires after each entity lands (with row count)
- `onConnectorPromote` — fires when bronze Parquet is ready for dbt

## CI smoke test

```bash
python3 -m pytest tooling/tests/test_connector_sap.py -q
# 41 passed
```

All tests use `MockSAPService` — no SAP sandbox or network access required.

## Bronze zone layout

```
data/bronze/sap/
  fact_sales/
    FiscalYear=2021/fact_sales.parquet
    FiscalYear=2022/fact_sales.parquet
    ...
  fact_gl_journal/
    FiscalYear=2021/fact_gl_journal.parquet
    ...
  fact_inventory/
    FiscalYear=2021/fact_inventory.parquet
    ...
```

After landing, run `dbt run --select aurora_silver+` to promote bronze → silver → gold.
