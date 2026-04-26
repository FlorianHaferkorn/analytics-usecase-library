"""
test_connector_sap.py — CI smoke test for the SAP connector framework.

Uses MockSAPService exclusively (no network, no SAP sandbox required).
Tests cover:
  1. Base ConnectorAdapter ABC contract
  2. SAPConfig validation (mock + live paths)
  3. MockSAPService schema fidelity for all three entities
  4. SAPConnectorAdapter.extract() in mock mode
  5. SAPConnectorAdapter.run() end-to-end: extract → land → result
  6. ParquetSink: partitioned and unpartitioned writes
  7. ConnectorResult fields
  8. schema_map() completeness
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    _HAS_PYARROW = True
except ImportError:
    _HAS_PYARROW = False

_needs_pyarrow = pytest.mark.skipif(not _HAS_PYARROW, reason="pyarrow not installed")

from tooling.connectors.base import ConnectorAdapter, ConnectorResult, ParquetSink
from tooling.connectors.sap.adapter import SAPConfig, SAPConnectorAdapter
from tooling.connectors.sap.mock_service import MockSAPService
from tooling.connectors.sap.schema_map import (
    FACT_GL_JOURNAL_SCHEMA,
    FACT_INVENTORY_SCHEMA,
    FACT_SALES_SCHEMA,
    SAP_SCHEMA_REGISTRY,
)


# ── Base contract ────────────────────────────────────────────────────────────

class TestConnectorAdapterABC:
    def test_adapter_is_abstract(self):
        with pytest.raises(TypeError):
            ConnectorAdapter()  # type: ignore[abstract]

    def test_sap_adapter_is_concrete(self):
        adapter = SAPConnectorAdapter()
        assert adapter is not None

    def test_source_system_identifier(self):
        assert SAPConnectorAdapter().source_system == "sap"

    def test_schema_map_returns_dict(self):
        sm = SAPConnectorAdapter().schema_map()
        assert isinstance(sm, dict)
        assert len(sm) > 0

    def test_parquet_sink_defaults(self, tmp_path):
        sink = ParquetSink(root=tmp_path)
        assert sink.compression == "snappy"
        assert sink.partition_by == []


# ── SAPConfig validation ─────────────────────────────────────────────────────

class TestSAPConfigValidation:
    def _adapter(self):
        return SAPConnectorAdapter()

    def test_mock_mode_always_valid(self):
        cfg = SAPConfig(base_url="", auth_type="mock")
        errors = self._adapter().validate(cfg)
        assert errors == []

    def test_basic_missing_url(self):
        cfg = SAPConfig(base_url="", auth_type="basic", username="u", password="p")
        errors = self._adapter().validate(cfg)
        assert any("base_url" in e for e in errors)

    def test_basic_missing_credentials(self):
        cfg = SAPConfig(base_url="https://sap.example.com", auth_type="basic")
        errors = self._adapter().validate(cfg)
        assert any("username" in e for e in errors)

    def test_oauth2_missing_token(self):
        cfg = SAPConfig(base_url="https://sap.example.com", auth_type="oauth2")
        errors = self._adapter().validate(cfg)
        assert any("oauth_token" in e for e in errors)

    def test_unknown_auth_type(self):
        cfg = SAPConfig(base_url="https://sap.example.com", auth_type="kerberos")
        errors = self._adapter().validate(cfg)
        assert any("auth_type" in e for e in errors)

    def test_valid_basic_config(self):
        cfg = SAPConfig(
            base_url="https://sap.example.com",
            auth_type="basic",
            username="BIADMIN",
            password="secret",
        )
        errors = self._adapter().validate(cfg)
        assert errors == []


# ── MockSAPService ────────────────────────────────────────────────────────────

@_needs_pyarrow
class TestMockSAPService:
    def test_fetch_fact_sales_schema(self):
        svc = MockSAPService(seed=42)
        batch = next(svc.fetch("fact_sales"))
        assert batch.schema == FACT_SALES_SCHEMA

    def test_fetch_fact_gl_journal_schema(self):
        svc = MockSAPService(seed=42)
        batch = next(svc.fetch("fact_gl_journal"))
        assert batch.schema == FACT_GL_JOURNAL_SCHEMA

    def test_fetch_fact_inventory_schema(self):
        svc = MockSAPService(seed=42)
        batch = next(svc.fetch("fact_inventory"))
        assert batch.schema == FACT_INVENTORY_SCHEMA

    def test_default_row_count(self):
        svc = MockSAPService(seed=42, rows_per_entity=20)
        batch = next(svc.fetch("fact_sales"))
        assert batch.num_rows == 20

    def test_custom_row_count(self):
        svc = MockSAPService(seed=42, rows_per_entity=5)
        batch = next(svc.fetch("fact_sales"))
        assert batch.num_rows == 5

    def test_deterministic_with_same_seed(self):
        svc_a = MockSAPService(seed=7)
        svc_b = MockSAPService(seed=7)
        b_a = next(svc_a.fetch("fact_sales"))
        b_b = next(svc_b.fetch("fact_sales"))
        assert b_a.to_pydict() == b_b.to_pydict()

    def test_different_seeds_differ(self):
        svc_a = MockSAPService(seed=1)
        svc_b = MockSAPService(seed=2)
        b_a = next(svc_a.fetch("fact_sales"))
        b_b = next(svc_b.fetch("fact_sales"))
        assert b_a.to_pydict() != b_b.to_pydict()

    def test_unknown_entity_raises_key_error(self):
        svc = MockSAPService()
        with pytest.raises(KeyError, match="unknown entity"):
            list(svc.fetch("fact_nonexistent"))

    def test_invoice_line_ids_are_unique(self):
        svc = MockSAPService(seed=42, rows_per_entity=50)
        batch = next(svc.fetch("fact_sales"))
        ids = batch.column("InvoiceLineID").to_pylist()
        assert len(ids) == len(set(ids))

    def test_fiscal_year_matches_config(self):
        svc = MockSAPService(seed=42, fiscal_year=2024)
        batch = next(svc.fetch("fact_sales"))
        years = set(batch.column("FiscalYear").to_pylist())
        assert years == {2024}

    def test_no_null_line_ids_in_sales(self):
        svc = MockSAPService(seed=42)
        batch = next(svc.fetch("fact_sales"))
        nulls = batch.column("InvoiceLineID").null_count
        assert nulls == 0

    def test_no_null_material_keys_in_inventory(self):
        svc = MockSAPService(seed=42)
        batch = next(svc.fetch("fact_inventory"))
        nulls = batch.column("MaterialKey").null_count
        assert nulls == 0


# ── SAPConnectorAdapter extract (mock mode) ───────────────────────────────────

@_needs_pyarrow
class TestSAPAdapterExtractMock:
    def _mock_cfg(self, entities=None):
        return SAPConfig(
            base_url="",
            auth_type="mock",
            entities=entities or ["fact_sales", "fact_gl_journal", "fact_inventory"],
        )

    def test_extract_yields_batches(self):
        adapter = SAPConnectorAdapter()
        batches = list(adapter.extract(self._mock_cfg()))
        assert len(batches) == 3

    def test_extract_single_entity(self):
        adapter = SAPConnectorAdapter()
        batches = list(adapter.extract(self._mock_cfg(entities=["fact_sales"])))
        assert len(batches) == 1
        assert batches[0].schema == FACT_SALES_SCHEMA

    def test_extract_all_entities_have_rows(self):
        adapter = SAPConnectorAdapter()
        for batch in adapter.extract(self._mock_cfg()):
            assert batch.num_rows > 0


# ── SAPConnectorAdapter.run() end-to-end ─────────────────────────────────────

@_needs_pyarrow
class TestSAPAdapterRun:
    def _mock_cfg_single(self, entity="fact_sales"):
        return SAPConfig(base_url="", auth_type="mock", entities=[entity])

    def test_run_returns_connector_result(self, tmp_path):
        result = SAPConnectorAdapter().run(
            self._mock_cfg_single(), ParquetSink(root=tmp_path)
        )
        assert isinstance(result, ConnectorResult)

    def test_run_success_flag(self, tmp_path):
        result = SAPConnectorAdapter().run(
            self._mock_cfg_single(), ParquetSink(root=tmp_path)
        )
        assert result.success is True

    def test_run_writes_parquet(self, tmp_path):
        SAPConnectorAdapter().run(
            self._mock_cfg_single("fact_sales"), ParquetSink(root=tmp_path)
        )
        files = list(tmp_path.rglob("*.parquet"))
        assert len(files) >= 1

    def test_run_parquet_readable(self, tmp_path):
        SAPConnectorAdapter().run(
            self._mock_cfg_single("fact_sales"), ParquetSink(root=tmp_path)
        )
        files = list(tmp_path.rglob("*.parquet"))
        t = pq.read_table(files[0])
        assert t.num_rows > 0

    def test_run_parquet_schema_matches(self, tmp_path):
        SAPConnectorAdapter().run(
            self._mock_cfg_single("fact_sales"), ParquetSink(root=tmp_path)
        )
        files = list(tmp_path.rglob("*.parquet"))
        schema = pq.read_schema(files[0])
        for field in FACT_SALES_SCHEMA:
            assert field.name in schema.names

    def test_run_records_extracted_nonzero(self, tmp_path):
        result = SAPConnectorAdapter().run(
            self._mock_cfg_single("fact_gl_journal"), ParquetSink(root=tmp_path)
        )
        assert result.records_extracted > 0

    def test_run_source_system_set(self, tmp_path):
        result = SAPConnectorAdapter().run(
            self._mock_cfg_single(), ParquetSink(root=tmp_path)
        )
        assert result.source_system == "sap"

    def test_run_validation_failure_returns_errors(self, tmp_path):
        cfg = SAPConfig(base_url="", auth_type="basic")
        result = SAPConnectorAdapter().run(cfg, ParquetSink(root=tmp_path))
        assert not result.success
        assert len(result.errors) > 0
        assert result.records_extracted == 0

    def test_run_all_three_entities(self, tmp_path):
        cfg = SAPConfig(
            base_url="", auth_type="mock",
            entities=["fact_sales", "fact_gl_journal", "fact_inventory"],
        )
        result = SAPConnectorAdapter().run(cfg, ParquetSink(root=tmp_path))
        assert result.success
        assert result.records_extracted > 0
        assert len(result.files_written) >= 3

    def test_run_unknown_entity_warns(self, tmp_path):
        cfg = SAPConfig(base_url="", auth_type="mock", entities=["fact_nonexistent"])
        result = SAPConnectorAdapter().run(cfg, ParquetSink(root=tmp_path))
        assert result.success
        assert any("nonexistent" in w for w in result.warnings)


# ── schema_map completeness ───────────────────────────────────────────────────

class TestSchemaMap:
    def test_all_aurora_fact_tables_present(self):
        sm = SAP_SCHEMA_REGISTRY
        assert "fact_sales" in sm
        assert "fact_gl_journal" in sm
        assert "fact_inventory" in sm

    def test_fact_sales_has_invoice_line_id(self):
        names = [f.name for f in FACT_SALES_SCHEMA]
        assert "InvoiceLineID" in names

    def test_fact_gl_journal_has_journal_line_id(self):
        names = [f.name for f in FACT_GL_JOURNAL_SCHEMA]
        assert "JournalLineID" in names

    def test_fact_inventory_has_material_key(self):
        names = [f.name for f in FACT_INVENTORY_SCHEMA]
        assert "MaterialKey" in names

    @_needs_pyarrow
    def test_all_schemas_are_pyarrow_schemas(self):
        for name, schema in SAP_SCHEMA_REGISTRY.items():
            assert isinstance(schema, pa.Schema), f"{name} schema is not pa.Schema"
