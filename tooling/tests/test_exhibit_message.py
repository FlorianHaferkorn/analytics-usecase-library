"""Tests for the BC-NARR-01 exhibit-message validator (K2).

Covers the pure classifier `classify_message` and the COM-002 pilot, which must
carry statement-style messages on every 30-second exhibit.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tooling.validation.check_exhibit_message import check_bracket, classify_message

REPO = Path(__file__).resolve().parents[2]


# ── Statements (pass) ────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "msg",
    [
        "Price concessions, not volume, explain the GM gap",
        "Gross Margin fell 12% vs plan",
        "GM% is concentrated below target in a few org units",
        "Deckungsbeitrag liegt unter Plan — Preis ist der Treiber",
        "Revenue is off track — down 8% on prior year",
    ],
)
def test_statements_pass(msg: str) -> None:
    status, _ = classify_message(msg)
    assert status is True


# ── Labels (fail — BC-NARR-01 violation) ─────────────────────────────────────
@pytest.mark.parametrize(
    "msg",
    [
        "Gross Margin by Region",
        "Revenue by Month",
        "GM by Product Category",
        "Sales by Channel",
    ],
)
def test_labels_fail(msg: str) -> None:
    status, reason = classify_message(msg)
    assert status is False
    assert "BC-NARR-01" in reason


# ── Absent / weak (advisory) ─────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [None, "", "   "])
def test_missing_is_advisory(msg) -> None:
    status, _ = classify_message(msg)
    assert status is None


def test_weak_message_is_advisory() -> None:
    # No comparison / quantity / verb signal and not a "X by Y" label.
    status, _ = classify_message("Commercial overview panel")
    assert status is None


def test_statement_containing_by_is_not_a_label() -> None:
    # "by" appears but the sentence has real structure + a verb signal.
    status, _ = classify_message("GM was eroded by price, not volume")
    assert status is True


# ── Pilot: COM-002 must pass BC-NARR-01 on every exhibit ─────────────────────
def test_com002_pilot_all_exhibits_are_statements() -> None:
    bracket = REPO / "core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml"
    assert bracket.exists()
    passed, warned, failed, _ = check_bracket(bracket)
    assert failed == 0
    assert warned == 0
    assert passed >= 3  # Main_1, Main_2, Main_3


# ── K6 gate: BC-NARR-01 knock-out enforced repo-wide ─────────────────────────
def test_no_label_titles_across_all_brackets():
    """Gate: no governed exhibit message may read as a label (BC-NARR-01 knock-out).

    Missing messages are advisory (not authored yet), but a message that IS a label
    is a hard violation anywhere in the library — this is what wires the rubric rule
    into the test gate so titles-as-labels can never regress (K6).
    """
    brackets = sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml"))
    assert brackets, "no UseCase_Bracket.yaml files found"
    offenders = []
    for b in brackets:
        _, _, failed, lines = check_bracket(b)
        if failed:
            offenders.append((b.relative_to(REPO), lines))
    assert not offenders, f"BC-NARR-01 label-title violations: {offenders}"


# ── A-34 / D-641: checked on the RENDERED titles, classifier always runs ───────
def _bracket(tmp_path, name, exhibits):
    import yaml
    d = tmp_path / "usecases" / name
    d.mkdir(parents=True)
    (d / "UseCase_Bracket.yaml").write_text(yaml.safe_dump(
        {"ux_layout_rules": {"page_1_summary": {"component_30s": exhibits}}}), encoding="utf-8")
    return d / "UseCase_Bracket.yaml"


def _visual(dist, name, title):
    import json
    vd = dist / f"{name}.Report" / "definition" / "pages" / "P" / "visuals" / "Main_1"
    vd.mkdir(parents=True)
    lit = "'" + title.replace("'", "''") + "'"
    (vd / "visual.json").write_text(json.dumps({"visual": {"visualContainerObjects": {"title": [
        {"properties": {"text": {"expr": {"Literal": {"Value": lit}}}}}]}}}), encoding="utf-8")


def test_rendered_title_carrying_the_message_fails(tmp_path):
    msg = "Gross Margin fell 12% vs plan"
    b = _bracket(tmp_path, "XX-001_Test", [{"slot_id": "Main_1", "question": "Is GM holding?", "message": msg}])
    dist = tmp_path / "dist"
    _visual(dist, "XX-001_Test", "  gross margin FELL 12% vs plan ")
    _, _, failed, lines = check_bracket(b, dist)
    assert failed == 1 and any("title is the message" in ln for ln in lines)


def test_rendered_descriptive_title_passes(tmp_path):
    b = _bracket(tmp_path, "XX-002_Test", [{"slot_id": "Main_1", "question": "Is GM holding?",
                                            "message": "Gross Margin fell 12% vs plan"}])
    dist = tmp_path / "dist"
    _visual(dist, "XX-002_Test", "Is GM holding?")
    passed, _, failed, lines = check_bracket(b, dist)
    assert (passed, failed) == (1, 0) and not any("NOT CHECKED" in ln for ln in lines)


def test_without_report_rendered_titles_are_not_checked(tmp_path):
    b = _bracket(tmp_path, "XX-003_Test", [{"slot_id": "Main_1", "message": "Gross Margin fell 12% vs plan"}])
    _, _, failed, lines = check_bracket(b, tmp_path / "dist")
    assert failed == 0 and any("NOT CHECKED" in ln for ln in lines)


def test_classifier_runs_even_when_question_equals_message(tmp_path):
    # Befund 2: a label message that equals the question used to skip classify_message
    b = _bracket(tmp_path, "XX-004_Test", [{"slot_id": "Main_1", "question": "Revenue by Month",
                                            "message": "Revenue by Month"}])
    _, _, failed, lines = check_bracket(b, tmp_path / "dist")
    assert failed == 1 and any("reads as a label" in ln for ln in lines)


def test_variant_report_is_checked_too(tmp_path):
    # Review Steward 09.10.2026: `<bracket>_<variant>.Report` (COM-001 ..._vs_Plan_LY) was never compared.
    msg = "Gross Margin fell 12% vs plan"
    b = _bracket(tmp_path, "XX-005_Test", [{"slot_id": "Main_1", "question": "Is GM holding?", "message": msg}])
    dist = tmp_path / "dist"
    _visual(dist, "XX-005_Test", "Is GM holding?")
    _visual(dist, "XX-005_Test_vs_Plan_LY", msg)
    _, _, failed, lines = check_bracket(b, dist)
    assert failed == 1 and any("XX-005_Test_vs_Plan_LY.Report" in ln for ln in lines)


def test_warn_line_quoting_not_checked_does_not_count_as_not_checked(tmp_path, monkeypatch, capsys):
    # Review Steward 09.10.2026: the summary counted any line containing "NOT CHECKED" as an unchecked report.
    import yaml
    from tooling.validation import check_exhibit_message as cem
    d = tmp_path / "core" / "usecases" / "XX-006_Test"
    d.mkdir(parents=True)
    (d / "UseCase_Bracket.yaml").write_text(yaml.safe_dump({"ux_layout_rules": {"page_1_summary": {
        "component_30s": [{"slot_id": "NOT CHECKED", "question": "Q?"}]}}}), encoding="utf-8")
    dist = tmp_path / "dist"
    _visual(dist, "XX-006_Test", "Q?")
    orig = cem.check_bracket
    monkeypatch.setattr(cem, "REPO", tmp_path)
    monkeypatch.setattr(cem, "check_bracket", lambda b: orig(b, dist))
    monkeypatch.setattr("sys.argv", ["check_exhibit_message", "--exit-zero"])
    cem.main()
    out = capsys.readouterr().out
    assert "WARN NOT CHECKED" in out
    assert "1 report(s) checked, 0 NOT CHECKED" in out
