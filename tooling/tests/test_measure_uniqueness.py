"""Unit tests for preflight_measure_names.py."""
import sys
import textwrap
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "generator"))
from preflight_measure_names import load_kpi_measure_map, load_brackets, check_uniqueness


CATALOG_SAMPLE = textwrap.dedent("""\
- kpi_id: fin.revenue.net.amount
  kpi_key: Net Revenue Amount
  technical:
    measure_name: "Net Revenue Amount"

- kpi_id: fin.margin.gross.pct
  kpi_key: Gross Margin %
  technical:
    measure_name: "Gross Margin %"

- kpi_id: ops.otif.pct
  kpi_key: OTIF %
  technical:
    measure_name: "Ops OTIF %"
""")

BRACKET_FIN001 = textwrap.dedent("""\
use_case_id: FIN-001
domain: Finance
kpi_ids:
  - fin.revenue.net.amount
  - fin.margin.gross.pct
""")

BRACKET_FIN002 = textwrap.dedent("""\
use_case_id: FIN-002
domain: Finance
kpi_ids:
  - fin.revenue.net.amount
  - ops.otif.pct
""")

BRACKET_OPS001 = textwrap.dedent("""\
use_case_id: OPS-001
domain: Operations
kpi_ids:
  - ops.otif.pct
""")


def write_catalog(tmp_path: Path) -> Path:
    p = tmp_path / "KPI_Catalog.md"
    p.write_text(CATALOG_SAMPLE, encoding="utf-8")
    return p


def write_bracket(tmp_path: Path, uc_dir: str, content: str) -> Path:
    d = tmp_path / "usecases" / uc_dir
    d.mkdir(parents=True)
    p = d / "UseCase_Bracket.yaml"
    p.write_text(content, encoding="utf-8")
    return tmp_path / "usecases"


class TestLoadKpiMeasureMap:
    def test_loads_all_mappings(self, tmp_path):
        catalog = write_catalog(tmp_path)
        m = load_kpi_measure_map(catalog)
        assert m["fin.revenue.net.amount"] == "Net Revenue Amount"
        assert m["ops.otif.pct"] == "Ops OTIF %"


class TestCheckUniqueness:
    def test_no_conflict_different_domains(self, tmp_path):
        catalog = write_catalog(tmp_path)
        measure_map = load_kpi_measure_map(catalog)
        uc_root = write_bracket(tmp_path, "FIN-001", BRACKET_FIN001)
        write_bracket(tmp_path, "OPS-001", BRACKET_OPS001)
        brackets = load_brackets(uc_root)
        errors = check_uniqueness(brackets, measure_map)
        assert errors == []

    def test_detects_same_domain_overlap(self, tmp_path):
        catalog = write_catalog(tmp_path)
        measure_map = load_kpi_measure_map(catalog)
        uc_root = write_bracket(tmp_path, "FIN-001", BRACKET_FIN001)
        write_bracket(tmp_path, "FIN-002", BRACKET_FIN002)
        brackets = load_brackets(uc_root)
        errors = check_uniqueness(brackets, measure_map)
        # fin.revenue.net.amount appears in both FIN-001 and FIN-002 (Finance domain)
        assert any("Net Revenue Amount" in e for e in errors)

    def test_no_error_for_single_bracket_per_domain(self, tmp_path):
        catalog = write_catalog(tmp_path)
        measure_map = load_kpi_measure_map(catalog)
        uc_root = write_bracket(tmp_path, "FIN-001", BRACKET_FIN001)
        brackets = load_brackets(uc_root)
        errors = check_uniqueness(brackets, measure_map)
        assert errors == []
