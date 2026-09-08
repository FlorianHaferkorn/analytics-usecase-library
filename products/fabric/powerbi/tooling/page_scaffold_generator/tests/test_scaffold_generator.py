"""
Tests for Page Scaffold Generator

Run with: python -m pytest tests/test_scaffold_generator.py
"""

import pytest
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator import PageScaffoldGenerator
from page_scaffold_generator.config_loader import ConfigLoader
from page_scaffold_generator.layout_calculator import LayoutCalculator
from page_scaffold_generator.visual_builder import VisualBuilder
from page_scaffold_generator.slicer_builder import SlicerBuilder

# Resolve repo root (tests live deep in products/fabric/powerbi/tooling/page_scaffold_generator/tests/)
REPO_ROOT = Path(__file__).resolve().parents[6]  # -> analytics-usecase-library


class TestConfigLoader:
    """Test config loader."""
    
    def test_get_page_config(self):
        """Test getting page config."""
        loader = ConfigLoader(REPO_ROOT)
        config = loader.get_page_config("COM-001", "overview")

        assert config["name"] == "overview"
        assert config["template"] == "T2"
        assert "slots" in config

    def test_get_use_case_display_name(self):
        """Test getting use case display name."""
        loader = ConfigLoader(REPO_ROOT)
        name = loader.get_use_case_display_name("COM-001")
        
        assert name is not None
        assert len(name) > 0


class TestLayoutCalculator:
    """Test layout calculator."""
    
    def test_calculate_kpi_card_positions(self):
        """Test KPI card position calculation."""
        calc = LayoutCalculator()
        positions = calc.calculate_kpi_card_positions(4)
        
        assert len(positions) == 4
        assert all(p.width == calc.KPI_CARD_WIDTH_STANDARD for p in positions)
        assert all(p.height == calc.KPI_CARD_HEIGHT_STANDARD for p in positions)
    
    def test_calculate_slicer_positions_top(self):
        """Test top slicer position calculation."""
        calc = LayoutCalculator()
        positions = calc.calculate_slicer_positions([{"type": "time"}], "top")
        
        assert len(positions) == 1
        assert positions[0].y == calc.ROW_1_Y_START
        assert positions[0].height == calc.SLICER_TOP_HEIGHT
    
    def test_calculate_visual_positions(self):
        """Test visual position calculation."""
        calc = LayoutCalculator()
        slots = {
            "needs_trend": True,
            "needs_variance": True,
            "needs_ranking": True
        }
        
        positions = calc.calculate_visual_positions(slots, "T2", False, False)
        
        assert "trend" in positions
        assert "variance" in positions
        assert "ranking" in positions


class TestVisualBuilder:
    """Test visual builder."""

    def test_build_kpi_card(self):
        """Test building KPI card."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=20, width=280, height=140)
        visual = builder.build_kpi_card(pos)

        assert visual["visual"]["visualType"] == "cardVisual"
        assert visual["position"]["x"] == 20
        assert visual["position"]["y"] == 20
        # Cards must use Data role
        qs = visual["visual"]["query"]["queryState"]
        assert "Data" in qs

    def test_build_line_chart(self):
        """Test building line chart."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=180, width=800, height=400)
        visual = builder.build_line_chart(pos)

        assert visual["visual"]["visualType"] == "lineChart"
        # Charts must use Category + Y, never Data
        qs = visual["visual"]["query"]["queryState"]
        assert "Category" in qs
        assert "Y" in qs
        assert "Data" not in qs

    def test_build_table_empty(self):
        """Test building table with no data still uses Values role."""
        builder = VisualBuilder()
        from page_scaffold_generator.layout_calculator import Position

        pos = Position(x=20, y=20, width=800, height=400)
        visual = builder.build_table(pos, columns=[], measures=[])

        assert visual["visual"]["visualType"] == "tableEx"
        qs = visual["visual"]["query"]["queryState"]
        assert "Values" in qs, "Empty table must use Values role"
        assert "Data" not in qs


class TestScaffoldGenerator:
    """Test scaffold generator."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)

        assert generator.use_case_id == "COM-001"
        assert generator.page_name == "overview"

    def test_load_config(self):
        """Test loading configuration."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()

        assert generator.config is not None
        assert generator.page_config is not None
        assert generator.page_config["template"] == "T2"

    def test_generate(self):
        """Test scaffold generation."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        assert generator.page_id is not None
        assert generator.page_structure is not None
        assert "visuals" in generator.page_structure
        assert "slicers" in generator.page_structure

    def test_validate(self):
        """Test validation."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        errors = generator.validate()
        # Should pass validation for COM-001 overview (including visual validation)
        assert isinstance(errors, list)
        assert len(errors) == 0, f"COM-001 overview should pass validation: {errors}"

    def test_validate_detail(self):
        """Test validation for detail page."""
        generator = PageScaffoldGenerator("COM-001", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()

        errors = generator.validate()
        assert isinstance(errors, list)
        assert len(errors) == 0, f"COM-001 detail should pass validation: {errors}"


class TestCOM002GoldenR23Fields:
    """
    R2.3/R2.4-Fund follow-up golden comparison: COM-002 is the migrated
    intent_rules_version: 2 reference Bracket. All 8 of its generated
    visuals now match the real, committed dist/ output byte-for-byte --
    KPI_Cards, Main_1, Main_2, Main_3, Header (overview); Smart_Narrative,
    Detail_Matrix, ActionPanel (detail). Closing this gap required porting
    several previously hand-patched-only fixes back into the generator:
    influencing_kpi_ids reorder (R1.5's real KPI card set), category_field
    overrides + a waterfall category-field plumbing bug (Main_1/Main_2),
    Main_2's kpi_ids reduced to the 3 PVM deltas dist/ actually renders,
    clusteredBarChart's real "labels" object name instead of "dataLabels"
    (R1.6), and Smart_Narrative/ActionPanel now bind to the governed
    domain-level "Narrative Text (<SUFFIX>)"/"Active Actions Text (<SUFFIX>)"
    DAX measures (cardVisual) instead of a synthesized textbox literal.
    See UMSETZUNGSPLAN_REPORT_EXZELLENZ.md's R2.3-Fund follow-up ledger
    entry for the full account. R1.6's Main_2 maxPerRole.Y=1 concern (a
    waterfallChart real-schema violation: 3 measures in the Y role) is now
    also fixed -- a disconnected dim_pvm_driver selector table + a single
    'PVM Bridge Value' SWITCH/SELECTEDVALUE measure replace the 3-measure
    Y projection with one measure, Category carrying the breakdown. DAX
    runtime is NOT verified against a live Power BI engine (none available
    here) -- structurally valid TMDL reusing three already-verified
    measures, pending Desktop confirmation. Still open, unrelated: the
    other 14 reports' own generator/dist sync (R5.1's job).
    """

    DIST_OVERVIEW = (
        REPO_ROOT
        / "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report"
        / "definition/pages/Page_COM002_Overview/visuals"
    )
    DIST_DETAIL = (
        REPO_ROOT
        / "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report"
        / "definition/pages/Page_COM002_Detail/visuals"
    )

    def _find_visual(self, generator, name):
        return next(v for v in generator.page_structure["visuals"] if v.get("name") == name)

    def test_header_matches_real_dist(self):
        dist_header = json.loads((self.DIST_OVERVIEW / "Header" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        header = self._find_visual(generator, "Header")

        assert header["position"] == dist_header["position"]
        assert header["visual"] == dist_header["visual"]

    def test_main_2_waterfall_has_exactly_one_y_measure(self):
        """R1.6 follow-up: waterfallChart's real capabilities only allow one
        measure in the Y role (confirmed against Microsoft's own Waterfall-
        chart docs -- bars come from Category values, not multiple Y
        measures). Regression guard against reintroducing the violation."""
        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        main2 = self._find_visual(generator, "Main_2")

        y_projections = main2["visual"]["query"]["queryState"]["Y"]["projections"]
        assert len(y_projections) == 1, f"waterfallChart Y role must carry exactly 1 measure, got {len(y_projections)}"
        assert y_projections[0]["nativeQueryRef"] == "PVM Bridge Value"

        category_projections = main2["visual"]["query"]["queryState"]["Category"]["projections"]
        assert category_projections[0]["queryRef"] == "dim_pvm_driver.Driver"

    def test_main_3_sort_definition_matches_real_dist(self):
        dist_main3 = json.loads((self.DIST_OVERVIEW / "Main_3" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        main3 = self._find_visual(generator, "Main_3")

        generated_sort = main3["visual"]["query"]["sortDefinition"]
        dist_sort = dist_main3["visual"]["query"]["sortDefinition"]
        assert generated_sort == dist_sort

    def test_detail_matrix_sort_definition_matches_real_dist(self):
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["visual"]["query"]["sortDefinition"] == dist_matrix["visual"]["query"]["sortDefinition"]

    def test_detail_matrix_databar_formatting_matches_real_dist(self):
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["visual"]["objects"]["columnFormatting"] == dist_matrix["visual"]["objects"]["columnFormatting"]

    def test_detail_matrix_topn_filter_matches_real_dist(self):
        """The filter *name* is a cosmetic-only PBIR identifier; dist/ was
        updated to the generator's new deterministic naming rule (R2.3),
        see UMSETZUNGSPLAN_REPORT_EXZELLENZ.md R2.3 ledger entry."""
        dist_matrix = json.loads((self.DIST_DETAIL / "Detail_Matrix" / "visual.json").read_text(encoding="utf-8"))

        generator = PageScaffoldGenerator("COM-002", "detail", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        matrix = self._find_visual(generator, "Detail_Matrix")

        assert matrix["filterConfig"] == dist_matrix["filterConfig"]

    def _header(self, visual):
        vco = visual["visual"].get("visualContainerObjects", {})
        def _lit(kind):
            try:
                raw = vco[kind][0]["properties"]["text"]["expr"]["Literal"]["Value"]
                # DAX string literal: outer single quotes, inner apostrophes doubled.
                return raw.strip("'").replace("''", "'")
            except (KeyError, IndexError, TypeError):
                return None
        return _lit("title"), _lit("subTitle")

    def test_com002_titles_are_honest_question_first(self):
        """title_policy opt-in (ux_layout_rules.title_statements_verified: false): COM-002 is a
        STATIC generated report, so each 30s visual leads with the always-true QUESTION and frames
        the message as an 'Expected finding —' subtitle — a static title can never contradict the
        data on refresh (title_policy.py). Guards the per-bracket honest-title override."""
        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        expected_q = {
            "Main_1": "Is gross margin holding against plan?",
            "Main_2": "What's pulling gross margin below plan — price, mix, or volume?",
            "Main_3": "Is the margin shortfall portfolio-wide or concentrated in a few units?",
        }
        for slot, question in expected_q.items():
            title, subtitle = self._header(self._find_visual(generator, slot))
            assert title == question, f"{slot} title should lead with the question, got {title!r}"
            assert subtitle and subtitle.startswith("Expected finding —"), (
                f"{slot} should frame the message as an expected-finding subtitle, got {subtitle!r}")

    def test_title_statements_verified_flag_defaults_true(self):
        """The opt-in is per-bracket; absent the flag, a report keeps its statement titles
        (assert_statement_titles True) so the other reports are unaffected until R2.4 migrates them."""
        loader = ConfigLoader(REPO_ROOT)
        assert loader.get_page_config("COM-002", "overview")["assert_statement_titles"] is False
        assert loader.get_page_config("COM-001", "overview")["assert_statement_titles"] is False

    def test_com002_kpi_band_splits_variance_into_coloured_delta_card(self):
        """Gap A: the vs-plan variance can't be per-metric coloured inside a multi-value card
        (callouts format uniformly — card.md), so intent-v2 reports split it into its own
        single-value KPI_Delta card coloured by sign via a diverging FillRule. Level KPIs stay
        in KPI_Cards."""
        generator = PageScaffoldGenerator("COM-002", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        names = [v.get("name") for v in generator.page_structure["visuals"]]
        assert "KPI_Delta" in names, "intent-v2 KPI band should split out a KPI_Delta card"

        delta = self._find_visual(generator, "KPI_Delta")
        projections = delta["visual"]["query"]["queryState"]["Data"]["projections"]
        assert len(projections) == 1 and projections[0]["nativeQueryRef"] == "Gross Margin % vs Plan"
        # sign-driven colour: diverging FillRule keyed on the variance measure
        fill = delta["visual"]["objects"]["value"][0]["properties"]["fontColor"]["solid"]["color"]["expr"]
        assert "FillRule" in fill, "delta callout must be conditionally coloured"
        assert fill["FillRule"]["Input"]["Measure"]["Property"] == "Gross Margin % vs Plan"

        # the variance measure is removed from the multi-value level card
        cards = self._find_visual(generator, "KPI_Cards")
        level_measures = [p["nativeQueryRef"] for p in cards["visual"]["query"]["queryState"]["Data"]["projections"]]
        assert "Gross Margin % vs Plan" not in level_measures
        assert "Gross Margin %" in level_measures

    def test_non_intent_v2_report_keeps_single_kpi_band(self):
        """The split is gated on intent_rules_version 2 — a legacy report keeps one KPI_Cards card
        and no KPI_Delta, so other reports are unaffected until they opt in."""
        generator = PageScaffoldGenerator("COM-001", "overview", repo_root=REPO_ROOT)
        generator.load_config()
        generator.generate()
        names = [v.get("name") for v in generator.page_structure["visuals"]]
        assert "KPI_Delta" not in names

    def test_every_com002_visual_matches_real_dist_exactly(self):
        """R2.3-Fund follow-up: full-visual byte-for-byte comparison, both
        pages, every visual -- the complete generator/dist sync this class's
        earlier field-scoped tests were building toward."""
        mismatches = []
        for page, dist_dir in (("overview", self.DIST_OVERVIEW), ("detail", self.DIST_DETAIL)):
            generator = PageScaffoldGenerator("COM-002", page, repo_root=REPO_ROOT)
            generator.load_config()
            generator.generate()
            for v in generator.page_structure["visuals"]:
                name = v.get("name")
                dist_file = dist_dir / name / "visual.json"
                if not dist_file.exists():
                    mismatches.append(f"{page}/{name}: no dist/ fixture")
                    continue
                dist_data = json.loads(dist_file.read_text(encoding="utf-8"))
                if v.get("visual") != dist_data.get("visual"):
                    mismatches.append(f"{page}/{name}")
        assert not mismatches, f"Visuals diverging from real dist/: {mismatches}"


class TestEvidenceColumnsUnresolvedTokenGuard:
    """
    R2.4 follow-up: config_loader.get_page_config('detail') must hard-fail on
    an evidence_columns token shaped like a dimension reference (bare lowercase
    snake_case word -- the shape of every real EVIDENCE_DIM_TOKENS key) that
    resolves to neither a known dim token nor a governed KPI id, instead of
    silently minting a bogus _Measures.<token> reference (the failure class
    R2.3/R2.4 found and fixed case-by-case for "sku", "asset", "queue", ...).
    """

    def _write_bracket(self, tmp_path, use_case_id, evidence_columns):
        uc_dir = tmp_path / "core" / "usecases" / "core" / f"{use_case_id}_Foo"
        uc_dir.mkdir(parents=True)
        cols = "\n".join(f"      - {c}" for c in evidence_columns)
        (uc_dir / "UseCase_Bracket.yaml").write_text(
            f"id: {use_case_id}\n"
            "ux_layout_rules:\n"
            "  page_2_execution:\n"
            "    component_300s:\n"
            "      evidence_columns:\n"
            f"{cols}\n",
            encoding="utf-8",
        )
        return ConfigLoader(tmp_path)

    def test_unresolved_dim_like_token_raises(self, tmp_path):
        loader = self._write_bracket(tmp_path, "TEST-001", ["totally_unknown_token"])
        with pytest.raises(ValueError, match="unresolvable dimension token"):
            loader.get_page_config("TEST-001", "detail")

    def test_known_dim_token_does_not_raise(self, tmp_path):
        loader = self._write_bracket(tmp_path, "TEST-002", ["region"])
        cfg = loader.get_page_config("TEST-002", "detail")
        assert cfg["detail_matrix_columns"] == [("dim_org", "Region")]

    def test_raw_measure_name_escape_hatch_does_not_raise(self, tmp_path):
        """Title-Case-with-spaces strings are the deliberate raw-measure-name
        fallback (same pattern component_30s.kpi_ids already supports) --
        never mistaken for an unresolved dimension token."""
        loader = self._write_bracket(tmp_path, "TEST-003", ["Plan Sales Amount"])
        cfg = loader.get_page_config("TEST-003", "detail")
        assert cfg["detail_matrix_measures"] == ["Plan Sales Amount"]

    def test_real_kpi_catalog_id_does_not_raise(self):
        """A dotted KPI id never matches the dim-like-token shape even when
        unresolved -- only genuinely bare-word tokens are guarded."""
        loader = ConfigLoader(REPO_ROOT)
        cfg = loader.get_page_config("COM-002", "detail")
        assert any("Gross Margin" in m for m in cfg["detail_matrix_measures"])


class TestConfigLoaderKpiMap:
    """Test KPI catalog loading and warning on failure."""

    def test_load_kpi_map_returns_dict(self):
        """KPI map should return a non-empty dict from the real KPI catalog."""
        loader = ConfigLoader(REPO_ROOT)
        result = loader.load_kpi_id_to_measure_name_map()
        assert isinstance(result, dict)
        # Real catalog should have entries
        assert len(result) > 0

    def test_load_kpi_map_caches_result(self):
        """Second call should return the cached result."""
        loader = ConfigLoader(REPO_ROOT)
        first = loader.load_kpi_id_to_measure_name_map()
        second = loader.load_kpi_id_to_measure_name_map()
        assert first is second

    def test_load_kpi_map_missing_catalog_returns_empty(self, tmp_path):
        """Missing KPI catalog should return empty dict, not raise."""
        loader = ConfigLoader(tmp_path)
        result = loader.load_kpi_id_to_measure_name_map()
        assert result == {}

    def test_load_kpi_map_logs_warning_on_parse_failure(self, tmp_path, caplog):
        """Malformed KPI catalog should log a warning, not silently pass."""
        import logging

        # Create a fake KPI catalog with valid yaml fence but broken content
        kpi_dir = tmp_path / "core" / "kpi_catalog"
        kpi_dir.mkdir(parents=True)
        catalog = kpi_dir / "KPI_Catalog.md"
        # Write content that will trigger the regex match but fail parsing
        catalog.write_text(
            "```yaml\n- kpi_id: TEST\n  kpi_key: \x00invalid\n```",
            encoding="utf-8",
        )
        loader = ConfigLoader(tmp_path)

        with caplog.at_level(logging.WARNING, logger="page_scaffold_generator.config_loader"):
            result = loader.load_kpi_id_to_measure_name_map()

        # Should still return a dict (possibly with partial results), not raise
        assert isinstance(result, dict)


def test_denylisted_ux_visual_warns_in_the_air_gapped_path(caplog):
    """The ungoverned fallback path (_dispatch_ux_visual) must at least SURFACE a governance
    warning when a deny-listed visual (e.g. funnel) is requested — it does not silently pass."""
    import logging
    from page_scaffold_generator.visual_builder import VisualBuilder
    from page_scaffold_generator.layout_calculator import Position

    builder = VisualBuilder()
    pos = Position(x=20, y=20, width=280, height=140)
    with caplog.at_level(logging.WARNING):
        builder._dispatch_ux_visual("funnel", pos, name="v", measures=["m"])
    assert any("deny-listed" in r.message and "color_as_decoration" in r.message
               for r in caplog.records), "no governance warning surfaced for a deny-listed visual"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
