"""AP-8 (24.09.2026): jede Überschreibung in visual.json gegen das aktive Theme eingestuft.

Drei Ebenen mit fester Vorrangregel (pbir-theme.md, „Three-Level Inheritance"): visual.json vor
visualStyles[<visualType>]["*"] vor visualStyles["*"]["*"]; Visual-Objekte verschmelzen mit dem
Theme Eigenschaft für Eigenschaft. Die Einstufung sagt, ob eine Überschreibung etwas tut:
`doppelt` (entfernbar), `widersprechend` (Theme wird umgangen), `neu` (Theme setzt dort nichts).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from products.fabric.powerbi.tooling.validation import check_report_theme_compliance as c  # noqa: E402


def _lit(s):
    return {"expr": {"Literal": {"Value": s}}}


THEME = {"visualStyles": {
    "*": {"*": {"title": [{"show": True, "fontSize": 12}],
                "labels": [{"labelPosition": "Auto", "color": {"solid": {"color": "#333333"}}}]}},
    "clusteredBarChart": {"*": {"labels": [{"labelPosition": "OutsideEnd"}]}},
}}


def test_each_class_is_recognised():
    visual = {"visualType": "lineChart",
              "objects": {
                  "labels": [{"properties": {"labelPosition": _lit("'OutsideEnd'"),
                                             "color": {"solid": {"color": _lit("'#333333'")}},
                                             "fontSize": _lit("9D")}},
                             {"selector": {"metadata": "M"}, "properties": {"color": _lit("'#FF0000'")}}],
                  "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": {"Measure": {}}}}}}}]},
              "visualContainerObjects": {"title": [{"properties": {"show": _lit("true"), "fontSize": _lit("14D")}}]}}
    k = c.klassifiziere_ueberschreibungen(visual, THEME)
    assert k["doppelt"] == ["labels.color", "title.show"]           # '#333333' wie Theme, true wie Theme
    assert k["widersprechend"] == ["labels.labelPosition", "title.fontSize"]   # Auto bzw. 12 im Theme
    assert k["neu"] == ["labels.fontSize"]
    assert k["gebunden"] == ["dataPoint.fill"]
    assert k["gezielt"] == ["labels.color"]


def test_visual_type_level_beats_the_wildcard():
    """Beim Balken setzt das Theme `OutsideEnd` auf Visualtyp-Ebene; das Visual wiederholt es nur."""
    visual = {"visualType": "clusteredBarChart",
              "objects": {"labels": [{"properties": {"labelPosition": _lit("'OutsideEnd'")}}]}}
    assert c.klassifiziere_ueberschreibungen(visual, THEME)["doppelt"] == ["labels.labelPosition"]
    visual["visualType"] = "lineChart"                                # dort gilt nur `Auto` aus `*`
    assert c.klassifiziere_ueberschreibungen(visual, THEME)["widersprechend"] == ["labels.labelPosition"]


def test_literal_forms_are_compared_by_value():
    assert c.literal_wert(_lit("12D")) == 12.0 and c.literal_wert(_lit("8L")) == 8.0
    assert c.literal_wert(_lit("'#ffffff'")) == "#FFFFFF"
    assert c.literal_wert(_lit("false")) is False
    assert c.literal_wert({"expr": {"Measure": {}}}) is c._GEBUNDEN


def test_the_shipped_reports_are_classified_against_their_active_theme():
    """Gegenprobe am echten Bericht, von Hand nachgesehen 24.09.2026: COM-001 `Main_3` setzt
    `labels.labelPosition` auf `OutsideEnd`, das Theme auf `Auto`; `Main_1` setzt `title.show`
    auf `true` wie das Theme."""
    _, warnungen = c.audit_report(REPO / "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report")
    zeilen = [w for w in warnungen if "overrides vs active theme" in w or " e.g. " in w]
    assert any("widersprechend e.g." in w and "Main_3 clusteredBarChart.labels.labelPosition" in w for w in zeilen)
    assert any("doppelt e.g." in w and "Main_1 lineChart.title.show" in w for w in zeilen)
