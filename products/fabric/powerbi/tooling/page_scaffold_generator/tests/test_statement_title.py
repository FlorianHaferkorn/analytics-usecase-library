"""K3: the governed exhibit `message` (BC-NARR-01) renders as the visual header.

Verifies the statement_title path in VisualBuilder.build_by_ux_visual_type — it must
emit the statement as the header for EVERY visual type (not only clustered columns),
escape apostrophes for the PBIR literal, and leave label-only visuals unchanged
(no regression to reports without messages, e.g. COM-001).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.visual_builder import VisualBuilder
from page_scaffold_generator.layout_calculator import Position


def _title_literal(visual):
    try:
        return visual["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
    except (KeyError, IndexError, TypeError):
        return None


def _pos() -> Position:
    return Position(x=20, y=20, width=400, height=300)


def test_statement_title_renders_for_all_main_visual_types():
    b = VisualBuilder()
    for vt in ("trend_line", "waterfall", "bar_chart", "clustered_column"):
        v = b.build_by_ux_visual_type(
            vt, _pos(), name="Main_1", measures=["M"], title="Some Label",
            statement_title="GM fell 12% vs plan",
        )
        assert _title_literal(v) == "'GM fell 12% vs plan'", f"{vt} did not render the statement title"


def test_statement_title_escapes_apostrophes():
    b = VisualBuilder()
    v = b.build_by_ux_visual_type(
        "trend_line", _pos(), name="X", measures=["M"], title="Label",
        statement_title="We're below plan",
    )
    assert _title_literal(v) == "'We''re below plan'"


def test_no_statement_leaves_line_chart_untitled():
    # COM-001 behaviour: without a message, line/waterfall stay untitled (no label header).
    b = VisualBuilder()
    v = b.build_by_ux_visual_type("trend_line", _pos(), name="X", measures=["M"], title="Some Label")
    assert _title_literal(v) is None


def test_clustered_column_keeps_label_header_without_statement():
    # COM-001 behaviour unchanged: clustered_column still headers from its label.
    b = VisualBuilder()
    v = b.build_by_ux_visual_type("clustered_column", _pos(), name="X", measures=["M"], title="Margin Gm Amount")
    assert _title_literal(v) == "'Margin Gm Amount'"
