"""
IR roundtrip parity tests.

Tests: bracket YAML → BracketCompiler → DashboardSpec → PBIPAdapter.render()
       produces structurally valid PBIP output that matches scaffold-writer layout.

These tests use in-memory bracket data so they run without a full repo checkout.
The fixture bracket covers the minimum required structure (Overview + Detail pages,
KPI_Cards visual with at least one measure, Smart_Narrative on detail).
"""
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# ── helpers ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]


def _minimal_bracket(use_case_id: str = "COM-001") -> Dict[str, Any]:
    """Minimal bracket that satisfies BracketCompiler requirements."""
    return {
        "id": use_case_id,
        "title": "Test Use Case",
        "domain": "Commercial",
        "primary_kpi_ids": [],          # no live catalog needed in unit tests
        "influencing_kpi_ids": [],
        "ux_layout_rules": {
            "page_1_summary": {
                "page_type": "T1",
                "component_30s": [
                    {"visual_type": "trend_line", "kpi_id": None, "category": "dim_date.Date"},
                ],
            },
            "page_2_execution": {
                "component_300s": {"action_panel": False},
            },
        },
        "orchestration": {
            "strategic_kpi_id": None,
            "action_code_ids": [],
        },
    }


def _write_bracket(tmp_dir: Path, bracket: Dict) -> Path:
    bracket_path = tmp_dir / "UseCase_Bracket.yaml"
    bracket_path.write_text(yaml.dump(bracket), encoding="utf-8")
    return bracket_path


# ── imports that need sys.path ───────────────────────────────────────────────

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.generator_core.ir.compiler import BracketCompiler
from tooling.generator_core.ir.specs import (
    DashboardSpec,
    PageRole,
    VisualType,
)
from products.fabric.powerbi.tooling.adapters.pbip import (
    PBIPAdapter,
    _build_tmdl_measures,
    _speaking_report_name,
)
from tooling.generator_core.adapters.base import RenderResult


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_bracket_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def minimal_spec(tmp_bracket_dir):
    bracket = _minimal_bracket("COM-001")
    bracket_path = _write_bracket(tmp_bracket_dir, bracket)
    compiler = BracketCompiler(
        kpi_catalog_root=REPO_ROOT / "core/kpi_catalog",
        action_codes_root=REPO_ROOT / "core/action_codes",
    )
    return compiler.compile(bracket_path)


# ── compiler tests ────────────────────────────────────────────────────────────

class TestBracketCompiler:
    def test_compile_produces_dashboard_spec(self, minimal_spec):
        assert isinstance(minimal_spec, DashboardSpec)

    def test_use_case_id_preserved(self, minimal_spec):
        assert minimal_spec.use_case_id == "COM-001"

    def test_domain_preserved(self, minimal_spec):
        assert minimal_spec.domain == "Commercial"

    def test_two_pages(self, minimal_spec):
        assert len(minimal_spec.pages) == 2

    def test_overview_page_exists(self, minimal_spec):
        assert minimal_spec.overview_page() is not None
        assert minimal_spec.overview_page().role == PageRole.OVERVIEW

    def test_detail_page_exists(self, minimal_spec):
        assert minimal_spec.detail_page() is not None
        assert minimal_spec.detail_page().role == PageRole.DETAIL

    def test_kpi_cards_visual_on_overview(self, minimal_spec):
        overview = minimal_spec.overview_page()
        kpi_visual = overview.visual_by_id("KPI_Cards")
        assert kpi_visual is not None
        assert kpi_visual.visual_type == VisualType.KPI_CARD

    def test_smart_narrative_on_detail(self, minimal_spec):
        detail = minimal_spec.detail_page()
        sn = detail.visual_by_id("Smart_Narrative")
        assert sn is not None
        assert sn.visual_type == VisualType.SMART_NARRATIVE

    def test_semantic_model_set(self, minimal_spec):
        assert minimal_spec.semantic_model == "Commercial.SemanticModel"

    def test_source_bracket_set(self, minimal_spec):
        assert minimal_spec.source_bracket.endswith("UseCase_Bracket.yaml")


# ── PBIP adapter render tests ─────────────────────────────────────────────────

def _report_prefix(spec) -> str:
    """Return the report folder prefix used in render() output keys."""
    return f"{_speaking_report_name(spec.use_case_id, spec.title)}.Report"


class TestPBIPAdapterRender:
    def test_render_returns_render_result(self, minimal_spec):
        result = PBIPAdapter().render(minimal_spec)
        assert isinstance(result, RenderResult)

    def test_definition_pbir_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition.pbir" in result.files

    def test_pbip_root_file_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        base = _speaking_report_name(minimal_spec.use_case_id, minimal_spec.title)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/{base}.pbip" in result.files

    def test_version_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition/version.json" in result.files

    def test_report_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition/report.json" in result.files

    def test_pages_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition/pages/pages.json" in result.files

    def test_overview_page_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition/pages/Overview/page.json" in result.files

    def test_detail_page_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        assert f"{prefix}/definition/pages/Detail/page.json" in result.files

    def test_definition_pbir_valid_json(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        content = result.files[f"{prefix}/definition.pbir"]
        data = json.loads(content.decode("utf-8"))
        assert "datasetReference" in data

    def test_definition_pbir_uses_registry_schema(self, minimal_spec):
        from products.fabric.powerbi.tooling.schema_registry import DEFINITION_PBIR_SCHEMA
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        data = json.loads(result.files[f"{prefix}/definition.pbir"].decode())
        assert data["$schema"] == DEFINITION_PBIR_SCHEMA

    def test_report_json_uses_registry_schema(self, minimal_spec):
        from products.fabric.powerbi.tooling.schema_registry import REPORT_SCHEMA
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        data = json.loads(result.files[f"{prefix}/definition/report.json"].decode())
        assert data["$schema"] == REPORT_SCHEMA

    def test_version_json_uses_registry_schema(self, minimal_spec):
        from products.fabric.powerbi.tooling.schema_registry import VERSION_METADATA_SCHEMA
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        data = json.loads(result.files[f"{prefix}/definition/version.json"].decode())
        assert data["$schema"] == VERSION_METADATA_SCHEMA

    def test_pages_json_contains_both_pages(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        pages = json.loads(result.files[f"{prefix}/definition/pages/pages.json"].decode())
        assert "Overview" in pages["pageOrder"]
        assert "Detail" in pages["pageOrder"]

    def test_kpi_cards_visual_json_present(self, minimal_spec):
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        key = f"{prefix}/definition/pages/Overview/visuals/KPI_Cards/visual.json"
        assert key in result.files

    def test_visual_json_uses_registry_schema(self, minimal_spec):
        from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA
        prefix = _report_prefix(minimal_spec)
        result = PBIPAdapter().render(minimal_spec)
        key = f"{prefix}/definition/pages/Overview/visuals/KPI_Cards/visual.json"
        data = json.loads(result.files[key].decode())
        assert data["$schema"] == VISUAL_SCHEMA

    def test_write_to_filesystem(self, minimal_spec, tmp_path):
        result = PBIPAdapter().render(minimal_spec)
        written = result.write_to(tmp_path)
        assert len(written) > 0
        for path in written:
            assert path.exists()

    def test_adapter_name(self):
        assert PBIPAdapter().name == "pbip"


class TestSpeakingReportName:
    def test_simple_title(self):
        assert _speaking_report_name("COM-001", "Sales Performance") == "COM-001_Sales_Performance"

    def test_special_chars_sanitized(self):
        name = _speaking_report_name("FIN-002", "Revenue/Cost: Analysis")
        assert "/" not in name
        assert ":" not in name

    def test_empty_title_uses_id_only(self):
        assert _speaking_report_name("OPS-003", "") == "OPS-003"


# ── benchmark reference-label caption tests ───────────────────────────────────

class TestBenchmarkCaptionEmit:
    """The benchmark reference-label renders via the corpus-verified textbox shape
    (paragraphs/textRuns) — never an unverified card reference-line object."""

    def _caption(self, config):
        from tooling.generator_core.ir.specs import VisualSpec, Position, Binding
        from products.fabric.powerbi.tooling.adapters.pbip import _build_visual_json
        v = VisualSpec(
            id="Benchmark_Caption", visual_type=VisualType.TEXT_BOX,
            page_role=PageRole.OVERVIEW, position=Position(0.0167, 0.152, 0.9666, 0.030),
            binding=Binding(), config=config,
        )
        return _build_visual_json(v)

    def test_caption_emits_textbox_with_label_text(self):
        j = self._caption({"text": "vs. Retail peer 45", "align": "right"})
        assert j["visual"]["visualType"] == "textbox"
        para = j["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]
        assert para["textRuns"][0]["value"] == "vs. Retail peer 45"
        assert para["horizontalTextAlignment"] == "right"

    def test_caption_without_align_omits_alignment(self):
        j = self._caption({"text": "vs. world-class 85%"})
        para = j["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]
        assert "horizontalTextAlignment" not in para


# ── TMDL generation tests ─────────────────────────────────────────────────────

class TestTMDLGeneration:
    def test_empty_measures_produces_table_header(self):
        tmdl = _build_tmdl_measures([])
        assert "table _Measures" in tmdl

    def test_single_measure_block(self):
        from tooling.generator_core.ir.specs import MeasureSpec
        m = MeasureSpec(
            kpi_id="sales.net_sales.amount",
            name="Net Sales Amount",
            dax="SUM ( fact_sales[net_sales] )",
            format_string="#,0.00",
        )
        tmdl = _build_tmdl_measures([m])
        assert "measure 'Net Sales Amount'" in tmdl
        assert "SUM ( fact_sales[net_sales] )" in tmdl
        assert 'formatString: "#,0.00"' in tmdl

    def test_measure_uses_tab_indentation(self):
        from tooling.generator_core.ir.specs import MeasureSpec
        m = MeasureSpec(
            kpi_id="x.y.z",
            name="Test Measure",
            dax="1",
            format_string="#,0",
        )
        tmdl = _build_tmdl_measures([m])
        measure_line = next(l for l in tmdl.splitlines() if "measure 'Test Measure'" in l)
        assert measure_line.startswith("\t"), "TMDL measure must be indented with a tab"

    def test_no_spaces_only_indentation(self):
        from tooling.generator_core.ir.specs import MeasureSpec
        m = MeasureSpec(kpi_id="a.b.c", name="M", dax="0", format_string="#,0")
        tmdl = _build_tmdl_measures([m])
        for line in tmdl.splitlines():
            if line:
                leading = len(line) - len(line.lstrip())
                if leading > 0:
                    assert line[:leading] == "\t" * leading, \
                        f"Line uses spaces for indentation: {repr(line)}"

    def test_purpose_comment_emitted(self):
        from tooling.generator_core.ir.specs import MeasureSpec
        m = MeasureSpec(
            kpi_id="x.y.z",
            name="Alpha",
            dax="0",
            format_string="#,0",
            description="Tracks alpha metric",
        )
        tmdl = _build_tmdl_measures([m])
        assert "/// Purpose: Tracks alpha metric" in tmdl


# ── validate_ir tests ─────────────────────────────────────────────────────────

def _spec_with_kpi_cards() -> DashboardSpec:
    """Build a DashboardSpec that passes validate_ir() — KPI_Cards has ≥1 measure."""
    from tooling.generator_core.ir.specs import (
        Binding, MeasureSpec, PageSpec, Position, VisualSpec,
    )
    overview = PageSpec(
        id="Overview",
        display_name="Overview",
        role=PageRole.OVERVIEW,
        visuals=[
            VisualSpec(
                id="KPI_Cards",
                visual_type=VisualType.KPI_CARD,
                page_role=PageRole.OVERVIEW,
                position=Position(0.0, 0.0, 0.8, 0.18),
                binding=Binding(measures=["Net Sales Amount"]),
            ),
        ],
    )
    detail = PageSpec(
        id="Detail",
        display_name="Detail",
        role=PageRole.DETAIL,
        visuals=[
            VisualSpec(
                id="Smart_Narrative",
                visual_type=VisualType.SMART_NARRATIVE,
                page_role=PageRole.DETAIL,
                position=Position(0.165, 0.0, 0.55, 0.18),
                binding=Binding(),
            ),
        ],
    )
    return DashboardSpec(
        use_case_id="COM-001",
        domain="Commercial",
        title="Valid Spec",
        pages=[overview, detail],
        measures=[
            MeasureSpec(
                kpi_id="sales.net_sales.amount",
                name="Net Sales Amount",
                dax="SUM ( fact_sales[net_sales] )",
                format_string="#,0.00",
            )
        ],
        semantic_model="Commercial.SemanticModel",
    )


class TestValidateIR:
    def test_minimal_spec_valid(self):
        spec = _spec_with_kpi_cards()
        errors = PBIPAdapter().validate_ir(spec)
        assert errors == []

    def test_missing_overview_raises_error(self, tmp_bracket_dir):
        from tooling.generator_core.ir.specs import DashboardSpec
        spec = DashboardSpec(
            use_case_id="COM-999",
            domain="Commercial",
            title="No Overview",
            pages=[],
            semantic_model="Commercial.SemanticModel",
        )
        errors = PBIPAdapter().validate_ir(spec)
        assert any("Overview" in e for e in errors)

    def test_missing_semantic_model_raises_error(self):
        spec = _spec_with_kpi_cards()
        spec.semantic_model = ""
        errors = PBIPAdapter().validate_ir(spec)
        assert any("semantic_model" in e.lower() for e in errors)


# ── diff tests ────────────────────────────────────────────────────────────────

class TestAdapterDiff:
    def test_diff_identical_specs_empty(self, minimal_spec):
        changes = PBIPAdapter().diff(minimal_spec, minimal_spec)
        assert changes == []

    def test_diff_detects_added_measure(self, minimal_spec):
        from tooling.generator_core.ir.specs import MeasureSpec
        import copy
        spec_b = copy.deepcopy(minimal_spec)
        spec_b.measures.append(
            MeasureSpec(kpi_id="x.y.z", name="New KPI", dax="0", format_string="#,0")
        )
        changes = PBIPAdapter().diff(minimal_spec, spec_b)
        assert any("New KPI" in c for c in changes)

    def test_diff_detects_removed_measure(self, minimal_spec):
        from tooling.generator_core.ir.specs import MeasureSpec
        import copy
        spec_a = copy.deepcopy(minimal_spec)
        spec_a.measures.append(
            MeasureSpec(kpi_id="x.y.z", name="Gone KPI", dax="0", format_string="#,0")
        )
        changes = PBIPAdapter().diff(spec_a, minimal_spec)
        assert any("Gone KPI" in c for c in changes)
