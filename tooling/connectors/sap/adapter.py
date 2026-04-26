"""
SAPConnectorAdapter — OData-based extraction from SAP ECC / S/4HANA.

Supports two extraction modes:
  - live:  real SAP Gateway OData calls (requires base_url + auth)
  - mock:  uses MockSAPService for CI and local development

The adapter maps SAP source tables to three Aurora fact entities:
  - fact_sales       (VBAK + VBAP billing documents)
  - fact_gl_journal  (BKPF + BSEG accounting documents)
  - fact_inventory   (MARA + MBEW material master + valuation)

Auth options (set via SAPConfig.auth_type):
  - "basic"    — username / password (ECC classic)
  - "oauth2"   — client_credentials flow (S/4HANA Cloud)
  - "mock"     — no network calls, returns MockSAPService data

OData paging:
  $top / $skip are used automatically when the source EntitySet returns
  more rows than page_size (default 5,000).  All pages are yielded as
  separate RecordBatches so memory stays bounded.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

import pyarrow as pa

from tooling.connectors.base import ConnectorAdapter, ConnectorResult, ParquetSink
from tooling.connectors.sap.schema_map import (
    FACT_GL_JOURNAL_SCHEMA,
    FACT_INVENTORY_SCHEMA,
    FACT_SALES_SCHEMA,
    SAP_SCHEMA_REGISTRY,
)

# OData EntitySet names exposed by SAP Gateway
_SAP_ENTITY_SETS = {
    "fact_sales":      "BillingDocumentItemSet",
    "fact_gl_journal": "JournalEntryItemSet",
    "fact_inventory":  "InventoryStockSet",
}


@dataclass
class SAPConfig:
    """Connection config for a SAP ECC or S/4HANA system."""

    base_url: str
    client: str = "100"
    auth_type: str = "basic"         # "basic" | "oauth2" | "mock"
    username: str = ""
    password: str = ""
    oauth_token: str = ""
    page_size: int = 5_000
    timeout_seconds: int = 60
    fiscal_year_filter: Optional[int] = None
    entities: List[str] = field(default_factory=lambda: list(_SAP_ENTITY_SETS))


class SAPConnectorAdapter(ConnectorAdapter[SAPConfig]):
    """
    Connector for SAP ECC / S/4HANA via OData v2.

    In mock mode (config.auth_type == "mock") no HTTP calls are made —
    MockSAPService generates deterministic in-memory data.  Use this mode
    for all CI runs and local development without a SAP sandbox.
    """

    @property
    def source_system(self) -> str:
        return "sap"

    def schema_map(self) -> Dict[str, pa.Schema]:
        return SAP_SCHEMA_REGISTRY

    def validate(self, config: SAPConfig) -> List[str]:
        errors: List[str] = []
        if config.auth_type == "mock":
            return errors
        if not config.base_url:
            errors.append("SAPConfig.base_url is required")
        if config.auth_type == "basic" and not (config.username and config.password):
            errors.append("SAPConfig.username and .password are required for auth_type='basic'")
        if config.auth_type == "oauth2" and not config.oauth_token:
            errors.append("SAPConfig.oauth_token is required for auth_type='oauth2'")
        if config.auth_type not in ("basic", "oauth2", "mock"):
            errors.append(f"Unknown auth_type '{config.auth_type}'. Use 'basic', 'oauth2', or 'mock'.")
        return errors

    def extract(self, config: SAPConfig) -> Iterator[pa.RecordBatch]:
        """Yield RecordBatches for every entity in config.entities."""
        if config.auth_type == "mock":
            yield from self._extract_mock(config)
        else:
            yield from self._extract_live(config)

    def run(self, config: SAPConfig, sink: ParquetSink) -> ConnectorResult:
        """Full pipeline: validate → extract each entity → land → return result."""
        errors = self.validate(config)
        if errors:
            return ConnectorResult(
                source_system=self.source_system,
                records_extracted=0,
                files_written=[],
                errors=errors,
            )

        all_written: List[Any] = []
        total_rows = 0
        warnings: List[str] = []

        for entity in config.entities:
            if entity not in SAP_SCHEMA_REGISTRY:
                warnings.append(f"Unknown entity '{entity}' — skipping")
                continue

            batches = self._batches_for_entity(config, entity)
            written = self.land(batches, sink, entity=entity)
            import pyarrow.parquet as pq_mod
            rows = sum(pq_mod.read_metadata(str(f)).num_rows for f in written if f.exists())
            total_rows += rows
            all_written.extend(written)

        return ConnectorResult(
            source_system=self.source_system,
            records_extracted=total_rows,
            files_written=all_written,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _batches_for_entity(
        self, config: SAPConfig, entity: str
    ) -> Iterator[pa.RecordBatch]:
        if config.auth_type == "mock":
            from tooling.connectors.sap.mock_service import MockSAPService
            svc = MockSAPService()
            yield from svc.fetch(entity)
        else:
            yield from self._odata_pages(config, entity)

    def _extract_mock(self, config: SAPConfig) -> Iterator[pa.RecordBatch]:
        from tooling.connectors.sap.mock_service import MockSAPService
        svc = MockSAPService()
        for entity in config.entities:
            yield from svc.fetch(entity)

    def _extract_live(self, config: SAPConfig) -> Iterator[pa.RecordBatch]:
        for entity in config.entities:
            yield from self._odata_pages(config, entity)

    def _odata_pages(
        self, config: SAPConfig, entity: str
    ) -> Iterator[pa.RecordBatch]:
        entity_set = _SAP_ENTITY_SETS.get(entity)
        if entity_set is None:
            return

        schema = SAP_SCHEMA_REGISTRY[entity]
        skip = 0
        while True:
            params = {
                "$format": "json",
                "$top":    str(config.page_size),
                "$skip":   str(skip),
                "sap-client": config.client,
            }
            if config.fiscal_year_filter:
                params["$filter"] = f"FiscalYear eq {config.fiscal_year_filter}"

            url = (
                config.base_url.rstrip("/")
                + f"/sap/opu/odata/sap/ZBI_AURORA_SRV/{entity_set}"
                + "?" + urllib.parse.urlencode(params)
            )
            headers = self._build_headers(config)
            req = urllib.request.Request(url, headers=headers)

            try:
                with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.URLError as exc:
                raise RuntimeError(f"SAP OData request failed for {entity_set}: {exc}") from exc

            results = data.get("d", {}).get("results", [])
            if not results:
                break

            batch = self._odata_results_to_batch(results, entity, schema)
            yield batch

            if len(results) < config.page_size:
                break
            skip += config.page_size

    def _build_headers(self, config: SAPConfig) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if config.auth_type == "basic":
            creds = base64.b64encode(
                f"{config.username}:{config.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {creds}"
        elif config.auth_type == "oauth2":
            headers["Authorization"] = f"Bearer {config.oauth_token}"
        return headers

    def _odata_results_to_batch(
        self,
        results: List[Dict[str, Any]],
        entity: str,
        schema: pa.Schema,
    ) -> pa.RecordBatch:
        """Convert OData JSON result rows to an Arrow RecordBatch."""
        columns: Dict[str, List] = {field.name: [] for field in schema}

        for row in results:
            for f in schema:
                raw = row.get(f.name)
                if pa.types.is_integer(f.type) and raw is not None:
                    raw = int(raw)
                elif pa.types.is_floating(f.type) and raw is not None:
                    raw = float(raw)
                columns[f.name].append(raw)

        arrays = [pa.array(columns[f.name], type=f.type) for f in schema]
        return pa.record_batch(arrays, schema=schema)
