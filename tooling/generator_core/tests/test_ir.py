"""Tests for the IR layer (specs + compiler)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from ..ir.specs import (
    AdapterTarget,
    Binding,
    DashboardSpec,
    MeasureSpec,
    PageRole,
    PageSpec,
    PageType,
    Position,
    VisualSpec,
    VisualType,
)
from ..ir.compiler import BracketCompiler, _card_kpi_ids


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dirs(tmp_path: Path):
    """Create minimal KPI catalog and action codes directories."""
    kpi_root = tmp_path / "kpi_catalog"
    kpi_root.mkdir()
    ac_root = tmp_path / "action_codes" / "commercial"
    ac_root.mkdir(parents=True)

    # KPI
    kpi = {
        "id": "com.sales.net_sales_amount",
        "name": "Net Sales Amount",
        "dax_expression": "SUM ( fact_sales[Net Sales Amount] )",
        "format_string": "#,0",
        "display_folder": "COM-001",
    }
    (kpi_root / "com.sales.net_sales_amount.yaml").write_text(
        yaml.dump(kpi), encoding="utf-8"
    )

    # Action code
    ac = {
        "id": "C-S1.1",
        "name": "Accelerate Top Account Penetration",
        "owner": "Sales VP",
        "trigger": {
            "levels": {
                "L1": {"condition": "Net Sales Amount < Plan × 0.95"}
            }
        },
        "impact": {"category": "Revenue"},
        "operational_execution": {
            "steps": ["Review top 10 accounts", "Schedule calls", "Offer incentives"]
        },
    }
    (ac_root / "C-S1.1.yaml").write_text(yaml.dump(ac), encoding="utf-8")

    return tmp_path, kpi_root, ac_root


@pytest.fixture
def bracket_file(tmp_path: Path):
    """Write a minimal UseCase_Bracket.yaml."""
    bracket = {
        "id": "COM-001",
        "title": "Sales Performance",
        "primary_kpi_ids": ["com.sales.net_sales_amount"],
        "influencing_kpi_ids": [],
        "orchestration": {"action_code_ids": ["C-S1.1"]},
        "ux_layout_rules": {
            "page_1_summary": {
                "page_type": "T1",
                "component_30s": [
                    {"visual_type": "trend_line", "kpi_id": "com.sales.net_sales_amount", "category": "dim_date.Date"},
                    {"visual_type": "bar_chart",  "kpi_id": "com.sales.net_sales_amount", "category": "dim_org.OrgName"},
                ],
            },
            "page_2_execution": {
                "component_300s": {
                    "action_panel": True,
                    "payload_mode": "summary",
                }
            },
        },
        "evidence_grain": {
            "grain": "customer_invoice_line",
            "columns": ["dim_customer.CustomerName", "dim_product.ProductName"],
        },
    }
    p = tmp_path / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
    p.parent.mkdir(parents=True)
    p.write_text(yaml.dump(bracket), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests: IR specs
# ---------------------------------------------------------------------------

class TestVisualSpec:
    def test_basic_construction(self):
        vs = VisualSpec(
            id="KPI_Cards",
            visual_type=VisualType.KPI_CARD,
            page_role=PageRole.OVERVIEW,
            position=Position(0.0, 0.0, 0.8, 0.18),
            binding=Binding(measures=["Net Sales Amount"]),
        )
        assert vs.id == "KPI_Cards"
        assert vs.visual_type == VisualType.KPI_CARD
        assert vs.binding.measures == ["Net Sales Amount"]

    def test_position_to_pixels(self):
        pos = Position(x=0.0, y=0.0, width=0.5, height=0.25)
        px = pos.to_pixels(1280, 720)
        assert px["width"] == 640
        assert px["height"] == 180

    def test_visual_type_values(self):
        assert VisualType.KPI_CARD.value == "kpi_card"
        assert VisualType.TREND_LINE.value == "trend_line"
        assert VisualType.SMART_NARRATIVE.value == "smart_narrative"


class TestPageSpec:
    def test_visual_by_id(self):
        vs1 = VisualSpec("KPI_Cards", VisualType.KPI_CARD, PageRole.OVERVIEW,
                         Position(), Binding())
        vs2 = VisualSpec("Main_1", VisualType.TREND_LINE, PageRole.OVERVIEW,
                         Position(), Binding())
        page = PageSpec("Overview", "Overview", PageRole.OVERVIEW, visuals=[vs1, vs2])
        assert page.visual_by_id("KPI_Cards") is vs1
        assert page.visual_by_id("MISSING") is None

    def test_visuals_by_type(self):
        vs1 = VisualSpec("KPI_Cards", VisualType.KPI_CARD, PageRole.OVERVIEW,
                         Position(), Binding())
        vs2 = VisualSpec("Main_1", VisualType.TREND_LINE, PageRole.OVERVIEW,
                         Position(), Binding())
        page = PageSpec("Overview", "Overview", PageRole.OVERVIEW, visuals=[vs1, vs2])
        kpi_cards = page.visuals_by_type(VisualType.KPI_CARD)
        assert len(kpi_cards) == 1
        assert kpi_cards[0].id == "KPI_Cards"


class TestDashboardSpec:
    def test_overview_and_detail_access(self):
        ov = PageSpec("Overview", "Overview", PageRole.OVERVIEW)
        dt = PageSpec("Detail", "Detail", PageRole.DETAIL)
        spec = DashboardSpec(
            use_case_id="COM-001", domain="Commercial", title="Sales",
            pages=[ov, dt], semantic_model="Commercial.SemanticModel",
        )
        assert spec.overview_page() is ov
        assert spec.detail_page() is dt

    def test_measure_by_kpi(self):
        m = MeasureSpec(kpi_id="com.sales.net_sales", name="Net Sales", dax="SUM(x)")
        spec = DashboardSpec(
            use_case_id="COM-001", domain="Commercial", title="Sales",
            measures=[m], semantic_model="Commercial.SemanticModel",
        )
        assert spec.measure_by_kpi("com.sales.net_sales") is m
        assert spec.measure_by_kpi("nonexistent") is None


# ---------------------------------------------------------------------------
# Tests: BracketCompiler
# ---------------------------------------------------------------------------

class TestBracketCompiler:
    def test_compile_returns_dashboard_spec(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        assert spec.use_case_id == "COM-001"
        assert spec.domain == "Commercial"
        assert spec.semantic_model == "Commercial.SemanticModel"

    def test_compile_has_two_pages(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        assert len(spec.pages) == 2
        assert spec.overview_page() is not None
        assert spec.detail_page() is not None

    def test_overview_has_kpi_cards(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        overview = spec.overview_page()
        kpi_cards = overview.visual_by_id("KPI_Cards")
        assert kpi_cards is not None
        assert kpi_cards.visual_type == VisualType.KPI_CARD

    def test_overview_has_main_visuals(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        overview = spec.overview_page()
        main1 = overview.visual_by_id("Main_1")
        main2 = overview.visual_by_id("Main_2")
        assert main1 is not None
        assert main2 is not None
        assert main1.visual_type == VisualType.TREND_LINE
        assert main2.visual_type == VisualType.BAR_CHART

    def test_detail_has_smart_narrative(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        detail = spec.detail_page()
        sn = detail.visual_by_id("Smart_Narrative")
        assert sn is not None
        assert sn.visual_type == VisualType.SMART_NARRATIVE

    def test_detail_has_action_panel_when_enabled(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        detail = spec.detail_page()
        ap = detail.visual_by_id("ActionPanel")
        assert ap is not None
        assert spec.action_panel is not None
        assert spec.action_panel.enabled is True
        assert "not found" not in (spec.action_panel.rendered_text or "").lower()
        assert "C-S1.1" in spec.action_panel.rendered_text
        assert "Accelerate Top Account Penetration" in spec.action_panel.rendered_text

    def test_detail_has_evidence_matrix(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        detail = spec.detail_page()
        matrix = detail.visual_by_id("Detail_Matrix")
        assert matrix is not None
        assert spec.evidence_table is not None
        assert spec.evidence_table.grain == "customer_invoice_line"

    def test_card_kpi_ids_deduplicates_lead_and_influencing(self):
        bracket = {
            "orchestration": {
                "strategic_kpi_id": "margin.gm.pct",
                "influencing_kpi_ids": [
                    "sales.net_sales.delta_pct.plan",
                    "sales.net_sales.delta_pct.ly",
                    "margin.gm.pct",
                    "sales.net_sales.amount",
                ],
            },
            "ux_layout_rules": {
                "page_1_summary": {
                    "component_3s": {"kpi_id": "sales.net_sales.amount"},
                }
            },
        }
        ids = _card_kpi_ids(bracket)
        assert ids == [
            "sales.net_sales.amount",
            "sales.net_sales.delta_pct.plan",
            "sales.net_sales.delta_pct.ly",
            "margin.gm.pct",
        ]

    def test_measures_compiled_from_catalog(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        assert len(spec.measures) == 1
        m = spec.measures[0]
        assert m.name == "Net Sales Amount"
        assert "SUM" in m.dax

    def test_missing_kpi_produces_warning(self, tmp_dirs, bracket_file):
        tmp_path, kpi_root, ac_root = tmp_dirs
        # Bracket references a KPI that doesn't exist
        bracket = yaml.safe_load(bracket_file.read_text())
        bracket["primary_kpi_ids"].append("nonexistent.kpi")
        bracket_file.write_text(yaml.dump(bracket))

        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)

        warning_codes = [w.code for w in compiler.warnings]
        assert "MISSING_KPI" in warning_codes

    def test_domain_inference(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)

        # Test FIN prefix
        bracket = yaml.safe_load(bracket_file.read_text())
        bracket["id"] = "FIN-001"
        fin_bracket = bracket_file.parent.parent / "FIN-001_test" / "UseCase_Bracket.yaml"
        fin_bracket.parent.mkdir(parents=True, exist_ok=True)
        fin_bracket.write_text(yaml.dump(bracket))
        spec = compiler.compile(fin_bracket)
        assert spec.domain == "Finance"


class TestTriggerFormatting:
    def test_format_trigger_skips_redundant_amount_unit(self):
        from ..ir.compiler import _format_trigger

        ac = {
            "trigger": {
                "levels": {
                    "L2": {
                        "condition": {
                            "metric_kpi_id": "sales.pvm.price_effect.amount",
                            "comparator": "lt",
                            "threshold": {"value": 0, "unit": "amount"},
                        }
                    }
                }
            }
        }
        assert _format_trigger(ac) == "sales.pvm.price_effect.amount < 0"


class TestMeasureNameResolution:
    def test_component_binding_resolves_kpi_id_to_measure_name(self, tmp_dirs, bracket_file):
        _, kpi_root, ac_root = tmp_dirs
        compiler = BracketCompiler(kpi_root, ac_root)
        spec = compiler.compile(bracket_file)
        main1 = spec.overview_page().visual_by_id("Main_1")
        assert main1.binding.measure == "Net Sales Amount"


class TestRealCatalogResolution:
    """A2 (durable IR fix): the compiler resolves real KPIs to display-name
    measures with real DAX from KPI_Catalog.md + the measure dictionaries --
    never the dotted-id BLANK() stubs that produced 96 missing-measure criticals.
    Proven against Aurora COM-001.
    """

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def test_com001_resolves_named_measures_with_dax(self):
        repo_root = self._repo_root()
        bracket = repo_root / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
        if not bracket.exists():
            pytest.skip("real repo layout not present")

        compiler = BracketCompiler(repo_root / "core" / "kpi_catalog", repo_root / "core" / "action_codes")
        spec = compiler.compile(bracket)
        names = {m.name for m in spec.measures}

        assert len(spec.measures) >= 10
        assert not [w for w in compiler.warnings if w.code == "MISSING_KPI"]
        # Names match report bindings (display names), never dotted kpi ids.
        assert "Gross Margin %" in names
        assert "Net Sales Amount" in names
        assert not any("." in n and " " not in n for n in names), f"dotted-id measure name leaked: {names}"
        # The north-star measure carries real DAX, not a BLANK() placeholder.
        gm = next(m for m in spec.measures if m.name == "Gross Margin %")
        assert gm.dax and "BLANK" not in gm.dax


class TestBenchmarkReferenceLabel:
    """The third comparison axis is *visible*: a hero card opting into the benchmark
    axis compiles to a peer-relative reference-label (K4 → render wiring)."""

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def test_format_label_normative_empirical_and_fallback(self):
        from ..ir.compiler import _format_benchmark_label
        norm = {"unit": "pct", "metric": "world_class"}
        assert _format_benchmark_label(norm, 85.0, "universal") == "vs. world-class 85%"
        nps = {"unit": "index", "metric": "median"}
        assert _format_benchmark_label(nps, 45.0, "segment:Retail") == "vs. Retail peer 45"
        assert _format_benchmark_label(nps, 44.0, "cross_industry_fallback") == \
            "vs. cross-industry 44 (no sector match)"

    def test_ops001_hero_compiles_a_benchmark_reference_and_caption(self):
        repo_root = self._repo_root()
        bracket = repo_root / "core/usecases/core/OPS-001_Operations_Performance/UseCase_Bracket.yaml"
        if not bracket.exists():
            pytest.skip("real repo layout not present")
        compiler = BracketCompiler(repo_root / "core/kpi_catalog", repo_root / "core/action_codes")
        spec = compiler.compile(bracket)
        overview = next(p for p in spec.pages if p.role == PageRole.OVERVIEW)

        card = overview.visual_by_id("KPI_Cards")
        ref = card.config.get("benchmark_reference")
        assert ref and ref["kpi_id"] == "ops.oee.pct"
        assert ref["basis"] == "universal" and ref["label"] == "vs. world-class 85%"
        # the primary comparison is preserved — the benchmark is additive
        caption = overview.visual_by_id("Benchmark_Caption")
        assert caption is not None and caption.visual_type == VisualType.TEXT_BOX
        assert caption.config["text"] == "vs. world-class 85%"

    def test_empirical_benchmark_resolves_to_deployment_industry(self):
        repo_root = self._repo_root()
        registry = repo_root / "core/kpi_catalog/benchmarks.yaml"
        if not registry.exists():
            pytest.skip("real repo layout not present")
        # A retail deployment sees the peer segment; an unmatched one sees an honest fallback.
        retail = BracketCompiler(repo_root / "core/kpi_catalog", repo_root / "core/action_codes",
                                 deployment_industry="Omnichannel Retail & Consumer Goods")
        assert retail._benchmark_reference("crm.nps.index")["label"] == "vs. Retail peer 45"
        mining = BracketCompiler(repo_root / "core/kpi_catalog", repo_root / "core/action_codes",
                                 deployment_industry="Mining")
        assert "cross-industry" in mining._benchmark_reference("crm.nps.index")["label"]

    def test_no_benchmark_kpi_returns_none(self):
        repo_root = self._repo_root()
        if not (repo_root / "core/kpi_catalog/benchmarks.yaml").exists():
            pytest.skip("real repo layout not present")
        compiler = BracketCompiler(repo_root / "core/kpi_catalog", repo_root / "core/action_codes")
        assert compiler._benchmark_reference("does.not.exist") is None
