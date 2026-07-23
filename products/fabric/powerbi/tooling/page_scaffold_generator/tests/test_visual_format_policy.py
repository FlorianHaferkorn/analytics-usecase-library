"""Governed axis / format / deviation / semantic-colour policy."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from page_scaffold_generator.visual_format_policy import (
    classify, deviation_spec, format_spec, format_string, good_direction,
    semantic_tokens, tooltip_measures, value_axis,
)


def test_format_string_by_unit():
    assert format_string("% (1 decimal)") == "0.0%"
    assert format_string("% (0 decimal)") == "0%"
    assert format_string("EUR (0 decimals)") == '"€"#,0'
    assert format_string("days") == '#,0 "d"'
    assert format_string("ratio") == '0.0"x"'
    assert format_string("count") == "#,0"


def test_value_axis_zero_baseline_only_for_bar_family():
    assert value_axis("bar_chart", "% (1 decimal)")["zero_based"] is True
    assert value_axis("clustered_column", "EUR")["zero_based"] is True
    assert value_axis("trend_line", "% (1 decimal)")["zero_based"] is False   # a line may zoom the y-range


def test_semantic_tokens_are_the_governed_palette():
    t = semantic_tokens()
    assert t["positive"] == "#107C10" and t["negative"] == "#A4262C"


def test_classify_reads_direction_and_target():
    # higher-is-better, below target → negative; at/above → positive; just under → warning
    assert classify("higher_is_better", 0.90, 1.00) == "negative"
    assert classify("higher_is_better", 1.02, 1.00) == "positive"
    assert classify("higher_is_better", 0.985, 1.00, warn_frac=0.05) == "warning"
    # lower-is-better flips
    assert classify("lower_is_better", 0.12, 0.10) == "negative"
    assert classify("lower_is_better", 0.08, 0.10) == "positive"
    # no target/direction → neutral, never a fabricated verdict
    assert classify(None, 5, None) == "neutral"
    assert classify("higher_is_better", 5, None) == "neutral"


def test_good_direction_falls_back_to_benchmark():
    assert good_direction("higher_is_better") == "higher"
    assert good_direction(None, "lower_is_better") == "lower"
    assert good_direction(None, None) is None


def test_deviation_only_for_vs_reference():
    d = deviation_spec("vs_target", "higher_is_better")
    assert d["show"] and d["positive_is_good"] is True
    assert deviation_spec("none", "higher_is_better")["show"] is False


def test_tooltip_measures_strategic_first_capped():
    t = tooltip_measures("k.strat", ["a", "b", "c", "d", "e"], cap=4)
    assert t[0] == "k.strat" and len(t) == 4


def test_format_spec_composes_all():
    fs = format_spec("supply.otif.pct", "bar_chart", "% (1 decimal)", "higher_is_better", "vs_target",
                     strategic="supply.otif.pct", influencing=["supply.on_time.pct"])
    assert fs.value_axis["zero_based"] is True and fs.value_axis["format"] == "0.0%"
    assert fs.semantic["good_direction"] == "higher"
    assert fs.deviation["show"] is True
    assert "supply.otif.pct" in fs.tooltip


def test_builder_applies_zero_baseline_only_when_opted_in():
    from page_scaffold_generator.visual_builder import VisualBuilder
    from page_scaffold_generator.layout_calculator import Position
    b = VisualBuilder()
    pos = Position(x=10, y=10, width=400, height=300)
    fs = format_spec("supply.otif.pct", "bar_chart", "% (1 decimal)", "higher_is_better", "vs_target")

    # default (no spec) → no valueAxis, emission unchanged
    plain = b.build_by_ux_visual_type("bar_chart", pos, name="M", measures=["M"])
    assert "valueAxis" not in plain["visual"].get("objects", {})

    # opted in → governed zero baseline present
    formatted = b.build_by_ux_visual_type("bar_chart", pos, name="M", measures=["M"], format_spec=fs)
    va = formatted["visual"]["objects"]["valueAxis"][0]["properties"]["start"]["expr"]["Literal"]["Value"]
    assert va == "0D"

    # a trend line is NOT pinned to zero (may zoom its y-range)
    line = b.build_by_ux_visual_type("trend_line", pos, name="M", measures=["M"],
                                     format_spec=format_spec("x", "trend_line", "% (1 decimal)",
                                                             "higher_is_better", "vs_target"))
    assert "valueAxis" not in line["visual"].get("objects", {})
