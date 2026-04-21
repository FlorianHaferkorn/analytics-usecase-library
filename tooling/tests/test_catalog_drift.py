"""Unit tests for check_catalog_tmdl_drift.py."""
import json
import sys
import textwrap
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "validation"))
from check_catalog_tmdl_drift import load_catalog_measures, load_tmdl_measures, check_drift


CATALOG_SAMPLE = textwrap.dedent("""\
- kpi_id: fin.revenue.net.amount
  kpi_key: Net Revenue Amount
  kpi_type: result
  kpi_role: strategic
  impact_dimension: Financial
  domain_tag: [Finance]
  technical:
    measure_name: "Net Revenue Amount"
    depends_on_measures: []
    lineage:
    - fact_sales.Net Sales Amount

- kpi_id: ops.otif.pct
  kpi_key: OTIF %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag: [Operations]
  technical:
    measure_name: "Ops OTIF %"
    depends_on_measures: []
    lineage:
    - fact_fulfillment.OTIF Flag
""")

TAB = "\t"
TMDL_MATCHING = (
    f"{TAB}/// Net Revenue Amount - fin.revenue.net.amount\n"
    f"{TAB}measure 'Net Revenue Amount' =\n"
    f"{TAB}{TAB}SUM ( fact_sales[Net Sales Amount] )\n"
    f"{TAB}{TAB}formatString: \"#,0.00\"\n"
    f"\n"
    f"{TAB}/// Ops OTIF % - ops.otif.pct\n"
    f"{TAB}measure 'Ops OTIF %' =\n"
    f"{TAB}{TAB}DIVIDE ( COUNTROWS ( FILTER ( fact_fulfillment, fact_fulfillment[OTIF Flag] = 1 ) ), COUNTROWS ( fact_fulfillment ) )\n"
    f"{TAB}{TAB}formatString: \"0.0%\"\n"
)

TMDL_DRIFTED = (
    f"{TAB}/// Ops OTIF % - wrong.kpi.id\n"
    f"{TAB}measure 'Ops OTIF %' =\n"
    f"{TAB}{TAB}DIVIDE ( 1, 1 )\n"
    f"{TAB}{TAB}formatString: \"0.0%\"\n"
)


def write_catalog(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "KPI_Catalog.md"
    p.write_text(content)
    return p


def write_tmdl(tmp_path: Path, content: str) -> Path:
    model_dir = tmp_path / "Finance.SemanticModel" / "definition" / "tables"
    model_dir.mkdir(parents=True)
    p = model_dir / "_Measures.tmdl"
    p.write_text(content)
    return tmp_path


class TestLoadCatalogMeasures:
    def test_loads_measure_names(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        entries = load_catalog_measures(catalog)
        names = {e["measure_name"] for e in entries}
        assert "Net Revenue Amount" in names
        assert "Ops OTIF %" in names

    def test_loads_lineage(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        entries = load_catalog_measures(catalog)
        otif = next(e for e in entries if e["kpi_id"] == "ops.otif.pct")
        assert "fact_fulfillment.OTIF Flag" in otif["lineage"]


class TestLoadTmdlMeasures:
    def test_loads_measures(self, tmp_path):
        dist_dir = write_tmdl(tmp_path, TMDL_MATCHING)
        measures = load_tmdl_measures(dist_dir)
        assert "Net Revenue Amount" in measures
        assert "Ops OTIF %" in measures

    def test_extracts_kpi_id_from_comment(self, tmp_path):
        dist_dir = write_tmdl(tmp_path, TMDL_MATCHING)
        measures = load_tmdl_measures(dist_dir)
        assert measures["Ops OTIF %"]["kpi_id"] == "ops.otif.pct"


class TestCheckDrift:
    def test_no_drift_when_matching(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        dist_dir = write_tmdl(tmp_path / "dist", TMDL_MATCHING)
        entries = load_catalog_measures(catalog)
        tmdl_measures = load_tmdl_measures(dist_dir)
        rows = check_drift(entries, tmdl_measures)
        # Should detect missing Net Revenue Amount in drifted TMDL (only Ops OTIF % present)
        missing = [r for r in rows if r["drift_type"] == "missing_in_tmdl"]
        drift = [r for r in rows if r["drift_type"] == "kpi_id_mismatch"]
        assert len(drift) == 0

    def test_detects_kpi_id_mismatch(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        dist_dir = write_tmdl(tmp_path / "dist", TMDL_DRIFTED)
        entries = load_catalog_measures(catalog)
        tmdl_measures = load_tmdl_measures(dist_dir)
        rows = check_drift(entries, tmdl_measures)
        mismatch = [r for r in rows if r["drift_type"] == "kpi_id_mismatch"]
        assert len(mismatch) == 1
        assert mismatch[0]["kpi_id"] == "ops.otif.pct"

    def test_detects_missing_measure(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        dist_dir = write_tmdl(tmp_path / "dist", TMDL_DRIFTED)
        entries = load_catalog_measures(catalog)
        tmdl_measures = load_tmdl_measures(dist_dir)
        rows = check_drift(entries, tmdl_measures)
        missing = [r for r in rows if r["drift_type"] == "missing_in_tmdl"]
        assert any(r["measure_name"] == "Net Revenue Amount" for r in missing)
