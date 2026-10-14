"""Generator emits only formatting objects the official PBIR catalogue knows (07.10.2026).

Anlass: `powerbi-report-author validate` (Pin 0.4.0) meldete in 15 dist-Reports
`PBIR_FORMATTING_OBJECT_UNKNOWN` fuer `calloutValue` an `cardVisual` (KPI_Cards) und
`PBIR_FORMATTING_PROP_UNKNOWN` fuer `text.text` an der Header-Textbox. Quelle war der
Generator, nicht das Artefakt. Diese Tests pruefen die Emitter gegen den vendorten Katalog
(`tooling/schemas/pbir/formatting_metadata_snapshot.json`) — offline, ohne CLI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from page_scaffold_generator import design_rules_enforcer as dre  # noqa: E402
from page_scaffold_generator import PageScaffoldGenerator  # noqa: E402
from page_scaffold_generator.layout_calculator import Position  # noqa: E402
from page_scaffold_generator.visual_builder import (  # noqa: E402
    VisualBuilder, textbox_objects, unquote_literal,
)
from products.fabric.powerbi.tooling import generate_action_payload as gap  # noqa: E402
from tooling.report_quality import formatting_metadata as fm  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[6]
POS = Position(x=0, y=0, width=400, height=200)


def _paragraph_text(visual: dict) -> str:
    general = visual["visual"]["objects"]["general"]
    return "".join(r["value"] for p in general[0]["properties"]["paragraphs"] for r in p["textRuns"])


class TestKpiCardsMulti:
    def test_display_units_in_value_object_with_default_selector(self):
        v = VisualBuilder().build_kpi_cards_multi(POS, ["A", "B"])
        objects = v["visual"]["objects"]
        assert "calloutValue" not in objects
        (entry,) = objects["value"]
        assert entry["selector"] == {"id": "default"}
        assert entry["properties"]["labelDisplayUnits"] == {"expr": {"Literal": {"Value": "0D"}}}

    def test_all_objects_known_to_catalogue(self):
        assert fm.unknown_visual_objects(VisualBuilder().build_kpi_cards_multi(POS, ["A"])) == []


class TestClusteredColumn:
    def test_labels_not_datalabels(self):
        v = VisualBuilder().build_clustered_column(POS, measures=["A", "B"])
        assert "dataLabels" not in v["visual"]["objects"]
        assert fm.unknown_visual_objects(v) == []


class TestTextbox:
    def test_textbox_objects_shape(self):
        objects = textbox_objects("It's on", align="right")
        para = objects["general"][0]["properties"]["paragraphs"][0]
        assert para["textRuns"] == [{"value": "It's on"}]
        assert para["horizontalTextAlignment"] == "right"
        assert fm.unknown_visual_objects({"visual": {"visualType": "textbox", "objects": objects}}) == []

    def test_unquote_literal(self):
        assert unquote_literal("'It''s'") == "It's"
        assert unquote_literal("plain") == "plain"

    def test_catalogue_rejects_the_former_text_text(self):
        """Gegenprobe: der Test faengt die alte Form (sonst prueft er nichts)."""
        old = {"visual": {"visualType": "textbox", "objects": {
            "text": [{"properties": {"text": {"expr": {"Literal": {"Value": "'x'"}}}}}]}}}
        assert fm.unknown_visual_objects(old) == ["text.text"]

    def test_header_emitted_as_paragraphs_and_satisfies_big_idea_rule(self):
        gen = PageScaffoldGenerator("SCM-002", "overview", repo_root=REPO_ROOT)
        gen.load_config()
        gen.generate()
        header = next(v for v in gen.page_structure["visuals"] if v.get("name") == "Header")
        assert "text" not in header["visual"]["objects"]
        assert fm.unknown_visual_objects(header) == []
        text = _paragraph_text(header)
        assert "Expected finding — " in text
        rule = next(r for r in dre.load_design_rules() if r["id"] == "BIG_IDEA_HEADER_ZONE")
        big_idea = text.split("Expected finding — ", 1)[1]
        assert dre.check_header_text_equals_big_idea(rule, big_idea, [header]) == []

    def test_generated_overview_and_detail_objects_all_known(self):
        found = []
        for page in ("overview", "detail"):
            gen = PageScaffoldGenerator("SCM-002", page, repo_root=REPO_ROOT)
            gen.load_config()
            gen.generate()
            for v in gen.page_structure["visuals"] + gen.page_structure.get("slicers", []):
                found += [f"{page}/{v.get('name')}: {f}" for f in fm.unknown_visual_objects(v)]
        assert found == []


class TestActionPayloadWriter:
    def test_writes_paragraphs_with_plain_text(self, tmp_path):
        detail = tmp_path / "definition" / "pages" / "Page_X_Detail"
        detail.mkdir(parents=True)
        out = gap.write_action_panel_visual(tmp_path, "Owner's action")
        visual = json.loads(out.read_text(encoding="utf-8"))
        assert "text" not in visual["visual"]["objects"]
        assert _paragraph_text(visual) == "Owner's action"
        assert fm.unknown_visual_objects(visual) == []
