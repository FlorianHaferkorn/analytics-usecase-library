from __future__ import annotations

import json
from pathlib import Path

from report_quality.models import Violation
from report_quality.pbir import parse_report
from report_quality.report_scorecard import (
    KNOCKOUT_MIXED_SCALE,
    KNOCKOUT_UNSORTED_EVIDENCE,
    THRESHOLD_PCT,
    compute_scorecard,
    detect_mixed_scale,
    detect_unsorted_evidence,
    parse_measure_format_strings,
    passes,
    scale_family,
    score_from_violations,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Pure weighted-point scoring (no filesystem)
# ---------------------------------------------------------------------------


def test_score_no_violations_is_max():
    assert score_from_violations([]) == 100


def test_score_deducts_by_severity_weight():
    violations = [
        Violation("x", "critical", "p", "m"),
        Violation("x", "warning", "p", "m"),
        Violation("x", "info", "p", "m"),
    ]
    # 100 - 15 (critical) - 5 (warning) - 1 (info) = 79
    assert score_from_violations(violations) == 79


def test_score_never_goes_below_zero():
    violations = [Violation("x", "critical", "p", "m") for _ in range(50)]
    assert score_from_violations(violations) == 0


def test_score_excludes_knockout_checks_from_point_deduction():
    violations = [Violation(KNOCKOUT_MIXED_SCALE, "critical", "p", "m")]
    assert score_from_violations(violations) == 100


def test_threshold_boundary_exact_pass():
    # 2 criticals = 100 - 30 = 70, exactly at THRESHOLD_PCT -> must pass.
    violations = [Violation("x", "critical", "p", "m") for _ in range(2)]
    score = score_from_violations(violations)
    assert score == THRESHOLD_PCT
    assert passes(score, knockouts=[]) is True


def test_threshold_boundary_just_below_fails():
    # 3 criticals = 100 - 45 = 55, below threshold.
    violations = [Violation("x", "critical", "p", "m") for _ in range(3)]
    score = score_from_violations(violations)
    assert score < THRESHOLD_PCT
    assert passes(score, knockouts=[]) is False


def test_high_score_still_fails_with_a_knockout():
    knockout = [Violation(KNOCKOUT_MIXED_SCALE, "critical", "p", "m")]
    assert passes(100, knockouts=knockout) is False


# ---------------------------------------------------------------------------
# scale_family classification
# ---------------------------------------------------------------------------


def test_scale_family_percent():
    assert scale_family("0.0%") == "percent"


def test_scale_family_amount():
    assert scale_family("#,0") == "amount"


def test_scale_family_unknown_when_missing():
    assert scale_family(None) == "unknown"
    assert scale_family("") == "unknown"


# ---------------------------------------------------------------------------
# parse_measure_format_strings
# ---------------------------------------------------------------------------


def test_parse_measure_format_strings(tmp_path: Path):
    tmdl = tmp_path / "Commercial.SemanticModel" / "definition" / "tables" / "_Measures.tmdl"
    tmdl.parent.mkdir(parents=True)
    tmdl.write_text(
        "table _Measures\n"
        "\tmeasure 'Gross Margin %' = DIVIDE ( [GM], [NS] )\n"
        '\t\tformatString: "0.0%"\n'
        "\t\tdisplayFolder: \"COM-001\"\n"
        "\n"
        "\tmeasure 'Price Effect Amount' = SUMX ( fact_sales, 1 )\n"
        '\t\tformatString: "#,0"\n'
        "\t\tdisplayFolder: \"COM-001\"\n",
        encoding="utf-8",
    )
    formats = parse_measure_format_strings(tmp_path)
    assert formats["Gross Margin %"] == "0.0%"
    assert formats["Price Effect Amount"] == "#,0"


# ---------------------------------------------------------------------------
# detect_mixed_scale / detect_unsorted_evidence (synthetic PBIR fixtures)
# ---------------------------------------------------------------------------


def _measure_projection(measure_name: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": measure_name}},
        "queryRef": f"_Measures.{measure_name}",
    }


def _write_minimal_report(root: Path, *, visuals: dict[str, dict]) -> Path:
    report = root / "TEST-001_Scorecard.Report"
    _write_json(report / "definition/pages/pages.json", {"pageOrder": ["Page_TEST001_Overview"]})
    _write_json(
        report / "definition/pages/Page_TEST001_Overview/page.json",
        {"name": "Page_TEST001_Overview", "displayName": "Overview", "width": 1920, "height": 1080},
    )
    for name, visual_body in visuals.items():
        _write_json(report / f"definition/pages/Page_TEST001_Overview/visuals/{name}/visual.json", visual_body)
    return report


def test_detect_mixed_scale_flags_percent_and_amount_on_same_axis(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Main_1": {
                "name": "Main_1",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {
                    "visualType": "waterfallChart",
                    "query": {
                        "queryState": {
                            "Y": {
                                "projections": [
                                    _measure_projection("Gross Margin %"),
                                    _measure_projection("Price Effect Amount"),
                                ]
                            }
                        }
                    },
                },
            }
        },
    )
    report = parse_report(report_dir)
    measure_formats = {"Gross Margin %": "0.0%", "Price Effect Amount": "#,0"}
    violations = detect_mixed_scale(report, measure_formats)
    assert len(violations) == 1
    assert violations[0].check == KNOCKOUT_MIXED_SCALE


def test_detect_mixed_scale_allows_same_family(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Main_1": {
                "name": "Main_1",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {
                    "visualType": "waterfallChart",
                    "query": {
                        "queryState": {
                            "Y": {
                                "projections": [
                                    _measure_projection("Price Effect Amount"),
                                    _measure_projection("Volume Effect Amount"),
                                ]
                            }
                        }
                    },
                },
            }
        },
    )
    report = parse_report(report_dir)
    measure_formats = {"Price Effect Amount": "#,0", "Volume Effect Amount": "#,0"}
    assert detect_mixed_scale(report, measure_formats) == []


def test_detect_mixed_scale_ignores_single_measure(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Main_1": {
                "name": "Main_1",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {
                    "visualType": "waterfallChart",
                    "query": {"queryState": {"Y": {"projections": [_measure_projection("Gross Margin %")]}}},
                },
            }
        },
    )
    report = parse_report(report_dir)
    assert detect_mixed_scale(report, {"Gross Margin %": "0.0%"}) == []


def test_detect_unsorted_evidence_flags_missing_sort(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Detail_Matrix": {
                "name": "Detail_Matrix",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {"visualType": "tableEx", "query": {"queryState": {}}},
            }
        },
    )
    report = parse_report(report_dir)
    violations = detect_unsorted_evidence(report)
    assert len(violations) == 1
    assert violations[0].check == KNOCKOUT_UNSORTED_EVIDENCE


def test_detect_unsorted_evidence_passes_with_default_sort(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Detail_Matrix": {
                "name": "Detail_Matrix",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {
                    "visualType": "tableEx",
                    "query": {
                        "queryState": {},
                        "sortDefinition": {
                            "sort": [{"field": _measure_projection("Gross Margin %")["field"], "direction": "Ascending"}],
                            "isDefaultSort": True,
                        },
                    },
                },
            }
        },
    )
    report = parse_report(report_dir)
    assert detect_unsorted_evidence(report) == []


def test_detect_unsorted_evidence_ignores_non_evidence_visuals(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Main_1": {
                "name": "Main_1",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {"visualType": "lineChart", "query": {"queryState": {}}},
            }
        },
    )
    report = parse_report(report_dir)
    assert detect_unsorted_evidence(report) == []


# ---------------------------------------------------------------------------
# compute_scorecard (integration of both mechanisms)
# ---------------------------------------------------------------------------


def test_compute_scorecard_fails_on_knockout_even_with_perfect_content(tmp_path: Path):
    report_dir = _write_minimal_report(
        tmp_path,
        visuals={
            "Detail_Matrix": {
                "name": "Detail_Matrix",
                "position": {"x": 0, "y": 0, "width": 100, "height": 80},
                "visual": {"visualType": "tableEx", "query": {"queryState": {}}},
            }
        },
    )
    result = compute_scorecard(report_dir, measure_formats={})
    assert result.passed is False
    assert any(k.check == KNOCKOUT_UNSORTED_EVIDENCE for k in result.knockouts)


# ---------------------------------------------------------------------------
# Mixed polarity (R6.3, 23.09.2026)
# ---------------------------------------------------------------------------

from report_quality.report_scorecard import (  # noqa: E402
    KNOCKOUT_MIXED_POLARITY,
    detect_mixed_polarity,
    load_measure_good_is,
)


def _bar(*measures: str) -> dict:
    return {
        "name": "Main_2",
        "position": {"x": 0, "y": 0, "width": 100, "height": 80},
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {"queryState": {"Y": {"projections": [_measure_projection(m) for m in measures]}}},
        },
    }


def test_mixed_polarity_flags_higher_next_to_lower_on_one_axis(tmp_path: Path):
    report = parse_report(_write_minimal_report(tmp_path, visuals={"Main_2": _bar("OTIF %", "Stockout Rate %")}))
    got = detect_mixed_polarity(report, {"OTIF %": "higher", "Stockout Rate %": "lower"})
    assert [v.check for v in got] == [KNOCKOUT_MIXED_POLARITY]


def test_same_direction_or_unknown_direction_is_not_a_knockout(tmp_path: Path):
    report = parse_report(_write_minimal_report(
        tmp_path, visuals={"Main_2": _bar("Unplanned Downtime %", "Spare Parts Stockout %", "Headcount")}))
    richtung = {"Unplanned Downtime %": "lower", "Spare Parts Stockout %": "lower"}
    assert detect_mixed_polarity(report, richtung) == []


def test_domain_suffix_variant_inherits_the_direction(tmp_path: Path):
    report = parse_report(_write_minimal_report(tmp_path, visuals={"Main_2": _bar("OTIF % (XD)", "Overtime %")}))
    assert detect_mixed_polarity(report, {"OTIF %": "higher", "Overtime %": "lower"})


def test_measure_directions_come_from_the_catalog():
    g = load_measure_good_is()
    assert g["OTIF %"] == "higher" and g["Stockout Rate %"] == "lower"
    assert "Net Sales Amount" not in g        # Basisgroesse: bewusst ohne Richtung
