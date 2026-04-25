"""Unit tests for check_catalog_tmdl_drift.py (legacy suite — uses new API names)."""
import sys
import textwrap
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "validation"))
from check_catalog_tmdl_drift import parse_catalog, parse_tmdl_measures, check_catalog_coverage


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

TMDL_ONLY_OTIF = (
    f"{TAB}/// Ops OTIF % - ops.otif.pct\n"
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
    return p


class TestParseCatalog:
    def test_loads_measure_names(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        result = parse_catalog(str(catalog))
        assert result["fin.revenue.net.amount"] == "Net Revenue Amount"
        assert result["ops.otif.pct"] == "Ops OTIF %"

    def test_skips_entry_without_measure_name(self, tmp_path):
        sample = textwrap.dedent("""\
        - kpi_id: no.measure.here
          kpi_key: No Measure
          technical:
            measure_name: ""
        """)
        catalog = write_catalog(tmp_path, sample)
        result = parse_catalog(str(catalog))
        assert "no.measure.here" not in result


class TestParseTmdlMeasures:
    def test_loads_measures(self, tmp_path):
        tmdl = write_tmdl(tmp_path, TMDL_MATCHING)
        result = parse_tmdl_measures([str(tmdl)])
        names = result[str(tmdl)]
        assert "Net Revenue Amount" in names
        assert "Ops OTIF %" in names

    def test_excludes_action_measures(self, tmp_path):
        content = (
            f"{TAB}measure 'Action_C-C3.1_Text' = \"action\"\n"
            f"{TAB}measure 'Net Sales Amount' = SUM ( fact[val] )\n"
        )
        tmdl = write_tmdl(tmp_path, content)
        result = parse_tmdl_measures([str(tmdl)])
        names = result[str(tmdl)]
        assert "Net Sales Amount" in names
        assert "Action_C-C3.1_Text" not in names


class TestCheckCatalogCoverage:
    def test_no_errors_when_measures_present(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        tmdl = write_tmdl(tmp_path, TMDL_MATCHING)
        cat = parse_catalog(str(catalog))
        by_file = parse_tmdl_measures([str(tmdl)])
        errors, warnings = check_catalog_coverage(cat, by_file, {}, strict=True)
        assert not errors

    def test_detects_missing_measure(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        tmdl = write_tmdl(tmp_path, TMDL_ONLY_OTIF)
        cat = parse_catalog(str(catalog))
        by_file = parse_tmdl_measures([str(tmdl)])
        errors, warnings = check_catalog_coverage(cat, by_file, {}, strict=True)
        assert any("Net Revenue Amount" in e for e in errors)

    def test_missing_is_warning_when_not_strict(self, tmp_path):
        catalog = write_catalog(tmp_path, CATALOG_SAMPLE)
        tmdl = write_tmdl(tmp_path, TMDL_ONLY_OTIF)
        cat = parse_catalog(str(catalog))
        by_file = parse_tmdl_measures([str(tmdl)])
        errors, warnings = check_catalog_coverage(cat, by_file, {}, strict=False)
        assert not errors
        assert any("Net Revenue Amount" in w for w in warnings)
