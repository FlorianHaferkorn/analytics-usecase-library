"""
tooling.connectors — pluggable data source connector framework.

Each connector translates a source system (SAP, Salesforce, etc.) into
Aurora-schema Parquet files in the Delta Lake bronze zone, ready for
dbt transformations into silver/gold.

Usage:
    from tooling.connectors.sap.adapter import SAPConnectorAdapter, SAPConfig
    from tooling.connectors.base import ParquetSink

    adapter = SAPConnectorAdapter()
    sink = ParquetSink(root=Path("data/bronze/sap"))
    result = adapter.run(SAPConfig(base_url="...", client="100"), sink)
"""

from tooling.connectors.base import ConnectorAdapter, ConnectorResult, ParquetSink

__all__ = ["ConnectorAdapter", "ConnectorResult", "ParquetSink"]
