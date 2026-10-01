"""PBIR page/visual rules of tooling/validation/validate_report.ps1 (01.10.2026).

Until 01.10.2026 REDUCE_PAGES, REDUCE_VISUALS_ON_PAGE, ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY and
ENSURE_ALTTEXT read the PBIR-Legacy shape (`sections`) and never ran on PBIR: all 17 dist reports
passed with "0 findings". These tests build small PBIR reports and check that each rule fires,
that its threshold comes from the governed source (bpa-rules-report.json, layout_grid.yaml), and
that a rule which cannot run says so instead of reporting nothing.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tooling" / "validation" / "validate_report.ps1"
BPA = REPO / "tooling" / "linters" / "powerbi" / "bpa-rules-report.json"
LAYOUT_GRID = REPO / "core" / "templates" / "page_templates" / "tokens" / "layout_grid.yaml"
DESIGN_SPEC = REPO / "core" / "templates" / "page_templates" / "Design_Spec_3_30_300.md"
PWSH = os.environ.get("ALUCA_PWSH") or shutil.which("pwsh")

needs_pwsh = pytest.mark.skipif(not PWSH, reason="pwsh not installed (set ALUCA_PWSH or put pwsh on PATH)")

PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
VISUAL_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
)


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _visual(
    name: str, vtype: str = "cardVisual", *, alt: Any = None, hidden: bool = False, parent: str | None = None
) -> dict[str, Any]:
    v: dict[str, Any] = {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": {"x": 0, "y": 0, "z": 0, "width": 100, "height": 100},
        "visual": {"visualType": vtype},
    }
    if alt is not None:
        v["visual"]["visualContainerObjects"] = {"general": [{"properties": {"altText": {"expr": alt}}}]}
    if hidden:
        v["isHidden"] = True
    if parent:
        v["parentGroupName"] = parent
    return v


def _group(name: str, *, hidden: bool = False) -> dict[str, Any]:
    g: dict[str, Any] = {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": {"x": 0, "y": 0, "z": 0, "width": 100, "height": 100},
        "visualGroup": {"displayName": name, "groupMode": "ScaleMode"},
    }
    if hidden:
        g["isHidden"] = True
    return g


def _page(
    name: str,
    width: int = 1920,
    height: int = 1080,
    display: str = "FitToPage",
    visuals: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    page = {
        "$schema": PAGE_SCHEMA,
        "name": name,
        "displayName": name,
        "displayOption": display,
        "width": width,
        "height": height,
        **extra,
    }
    return {"page": page, "visuals": visuals or []}


def _report(root: Path, pages: list[dict[str, Any]]) -> Path:
    rep = root / "T.Report"
    _write(rep / "definition" / "report.json", {"themeCollection": {}})
    pages_dir = rep / "definition" / "pages"
    _write(pages_dir / "pages.json", {"pageOrder": [p["page"]["name"] for p in pages]})
    for p in pages:
        pdir = pages_dir / p["page"]["name"]
        _write(pdir / "page.json", p["page"])
        for v in p["visuals"]:
            _write(pdir / "visuals" / v["name"] / "visual.json", v)
    return rep


def _bpa(tmp_path: Path, *, alt_enabled: bool) -> Path:
    data = json.loads(BPA.read_text(encoding="utf-8"))
    for rule in data["rules"]:
        if rule["id"] == "ENSURE_ALTTEXT":
            rule["disabled"] = not alt_enabled
    out = tmp_path / "bpa.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    return out


def _run(report: Path, *extra: str, script: Path = SCRIPT) -> tuple[int, dict[str, Any], str]:
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(script), "-ReportPath", str(report), *extra],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    out = proc.stdout
    match = re.search(r"^\{\s*$", out, re.M)
    assert match, out + proc.stderr
    return proc.returncode, json.loads(out[match.start() :]), out + proc.stderr


def _ids(result: dict[str, Any], key: str) -> list[str]:
    return [x["RuleId"] for x in result.get(key) or []]


# --- source of the thresholds -------------------------------------------------------------------


def test_visual_limit_in_bpa_matches_design_spec() -> None:
    """Design_Spec section 10 states the limit in prose; bpa-rules-report.json is what the script reads."""
    rule = next(r for r in json.loads(BPA.read_text(encoding="utf-8"))["rules"] if r["id"] == "REDUCE_VISUALS_ON_PAGE")
    param = rule["test"][1]["paramMaxVisualsPerPage"]
    row = re.search(r"^\| Visible visuals per page \| ≤ (\d+) \|", DESIGN_SPEC.read_text(encoding="utf-8"), re.M)
    assert row, "Design_Spec_3_30_300.md section 10 lost its 'Visible visuals per page' row"
    assert int(row.group(1)) == param


def test_layout_grid_canvases_are_the_two_governed_ones() -> None:
    canvas = yaml.safe_load(LAYOUT_GRID.read_text(encoding="utf-8"))["canvas"]
    assert canvas["design_base"] == {"width": 1280, "height": 720}
    assert canvas["production"] == {"width": 1920, "height": 1080}


# --- clean report ---------------------------------------------------------------------------------


@needs_pwsh
def test_canvas_pages_pass_and_rules_report_as_evaluated(tmp_path: Path) -> None:
    alt = {"Literal": {"Value": "'Net Sales Amount by Region'"}}
    rep = _report(
        tmp_path,
        [
            _page("P1", visuals=[_visual("V1", alt=alt)]),
            _page("P2", 1280, 720, "FitToWidth", visuals=[_visual("V2", alt=alt)]),
        ],
    )
    rc, res, log = _run(rep)
    assert rc == 0, log
    assert not res["Errors"] and not res["Warnings"] and not res["Info"], log
    # ENSURE_ALTTEXT is active in the shipped bpa-rules-report.json since 01.10.2026
    assert sorted(_ids(res, "Evaluated")) == [
        "ENSURE_ALTTEXT",
        "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY",
        "REDUCE_PAGES",
        "REDUCE_VISUALS_ON_PAGE",
    ]
    assert _ids(res, "Disabled") == []


@needs_pwsh
def test_disabled_rule_is_listed_as_disabled_not_as_zero_findings(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("P1", visuals=[_visual("NoAlt")])])
    _, res, log = _run(rep, "-BpaRulesPath", str(_bpa(tmp_path, alt_enabled=False)))
    assert _ids(res, "Disabled") == ["ENSURE_ALTTEXT"], log
    assert "ENSURE_ALTTEXT" not in _ids(res, "Info")


def test_alt_text_rule_is_enabled_in_shipped_bpa() -> None:
    """Decision 01.10.2026: alt text comes from the generator, the rule is on (severity stays Info)."""
    rule = next(r for r in json.loads(BPA.read_text(encoding="utf-8"))["rules"] if r["id"] == "ENSURE_ALTTEXT")
    assert rule["disabled"] is False


# --- ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY --------------------------------------------------------


@needs_pwsh
def test_too_high_fit_to_width_page_is_a_warning_with_actual_and_target(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Tall", 1280, 900, "FitToWidth")])
    rc, res, log = _run(rep)
    assert rc == 0, log
    warn = [w for w in res["Warnings"] if w["RuleId"] == "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"]
    assert len(warn) == 1, log
    assert warn[0]["Page"] == "Tall" and warn[0]["Value"] == 900 and warn[0]["Threshold"] == 720
    assert "1280x900" in warn[0]["Description"] and "1920x1080" in warn[0]["Description"]


@needs_pwsh
def test_non_canvas_page_within_ratio_passes(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Wide", 1600, 900, "FitToWidth")])
    _, res, log = _run(rep)
    assert not res["Warnings"] and not res["Info"], log


@needs_pwsh
def test_fit_to_page_oversize_does_not_scroll_but_is_flagged_as_info(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Poster", 1280, 2000, "FitToPage")])
    rc, res, log = _run(rep)
    assert rc == 0 and not res["Warnings"], log
    info = [i for i in res["Info"] if i["RuleId"] == "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"]
    assert len(info) == 1 and "shrunk" in info[0]["Description"], log


@needs_pwsh
def test_actual_size_larger_than_production_canvas_scrolls(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Big", 2560, 1440, "ActualSize")])
    _, res, log = _run(rep)
    assert _ids(res, "Warnings") == ["ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"], log


@needs_pwsh
def test_hidden_and_tooltip_pages_are_not_checked_for_scrolling(tmp_path: Path) -> None:
    rep = _report(
        tmp_path,
        [
            _page("Hidden", 1280, 2000, "FitToWidth", visibility="HiddenInViewMode"),
            _page("Tip", 320, 240, "FitToWidth", type="Tooltip"),
        ],
    )
    _, res, log = _run(rep)
    assert not res["Warnings"] and not res["Info"], log


@needs_pwsh
def test_canvas_comes_from_layout_grid_yaml(tmp_path: Path) -> None:
    grid = tmp_path / "layout_grid.yaml"
    grid.write_text(
        "canvas:\n  design_base: {width: 1000, height: 1000}\n  production: {width: 1000, height: 1000}\n",
        encoding="utf-8",
    )
    rep = _report(tmp_path, [_page("Square", 1000, 1000, "FitToWidth")])
    _, default_res, _ = _run(rep)
    _, custom_res, log = _run(rep, "-LayoutGridPath", str(grid))
    assert _ids(default_res, "Warnings") == ["ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY"]
    assert not custom_res["Warnings"], log


@needs_pwsh
def test_missing_layout_grid_is_not_evaluated_not_clean(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Tall", 1280, 900, "FitToWidth")])
    _, res, log = _run(rep, "-LayoutGridPath", str(tmp_path / "missing.yaml"))
    assert "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" in _ids(res, "NotEvaluated"), log
    assert "ENSURE_PAGES_DO_NOT_SCROLL_VERTICALLY" not in _ids(res, "Evaluated")


# --- REDUCE_VISUALS_ON_PAGE -----------------------------------------------------------------------


@needs_pwsh
def test_too_many_visuals_is_a_warning(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("Busy", visuals=[_visual(f"V{i}") for i in range(21)])])
    _, res, log = _run(rep)
    warn = [w for w in res["Warnings"] if w["RuleId"] == "REDUCE_VISUALS_ON_PAGE"]
    assert len(warn) == 1 and warn[0]["Value"] == 21 and warn[0]["Threshold"] == 20, log


@needs_pwsh
def test_excluded_types_hidden_visuals_and_groups_do_not_count(tmp_path: Path) -> None:
    visuals = [_visual(f"V{i}") for i in range(20)]
    visuals += [_visual(f"S{i}", t) for i, t in enumerate(["slicer", "textbox", "shape", "actionButton"])]
    visuals += [_visual("H", hidden=True), _group("G", hidden=True), _visual("InHiddenGroup", parent="G"), _group("G2")]
    rep = _report(tmp_path, [_page("Edge", visuals=visuals)])
    _, res, log = _run(rep)
    assert "REDUCE_VISUALS_ON_PAGE" not in _ids(res, "Warnings"), log


@needs_pwsh
def test_children_of_a_visible_group_are_counted(tmp_path: Path) -> None:
    visuals = [_group("G")] + [_visual(f"C{i}", parent="G") for i in range(21)]
    rep = _report(tmp_path, [_page("Grouped", visuals=visuals)])
    _, res, log = _run(rep)
    assert "REDUCE_VISUALS_ON_PAGE" in _ids(res, "Warnings"), log


# --- REDUCE_PAGES ---------------------------------------------------------------------------------


@needs_pwsh
def test_eleven_pages_is_an_error_ten_are_not(tmp_path: Path) -> None:
    rc10, res10, _ = _run(_report(tmp_path / "a", [_page(f"P{i}") for i in range(10)]))
    rc11, res11, log = _run(_report(tmp_path / "b", [_page(f"P{i}") for i in range(11)]))
    assert rc10 == 0 and not res10["Errors"]
    assert rc11 == 1 and _ids(res11, "Errors") == ["REDUCE_PAGES"], log
    assert res11["Errors"][0]["Value"] == 11 and res11["Errors"][0]["Threshold"] == 10


# --- ENSURE_ALTTEXT -------------------------------------------------------------------------------


@needs_pwsh
def test_missing_alt_text_is_reported_when_rule_enabled(tmp_path: Path) -> None:
    visuals = [
        _visual("NoAlt"),
        _visual("EmptyLiteral", alt={"Literal": {"Value": "''"}}),
        _visual("WithAlt", alt={"Literal": {"Value": "'Umsatz je Region'"}}),
        _visual("MeasureAlt", alt={"Measure": {"Expression": {"SourceRef": {"Entity": "_M"}}, "Property": "Alt"}}),
        _visual("Deko", "shape"),
        _visual("Hidden", hidden=True),
        _visual("Text", "textbox"),
    ]
    rep = _report(tmp_path, [_page("A11y", visuals=visuals)])
    _, res, log = _run(rep, "-BpaRulesPath", str(_bpa(tmp_path, alt_enabled=True)))
    missing = sorted(i["Visual"] for i in res["Info"] if i["RuleId"] == "ENSURE_ALTTEXT")
    assert missing == ["EmptyLiteral", "NoAlt", "Text"], log
    assert "ENSURE_ALTTEXT" in _ids(res, "Evaluated")


@needs_pwsh
def test_legacy_report_json_still_rejected(tmp_path: Path) -> None:
    rep = _report(tmp_path, [_page("P1")])
    _write(rep / "report.json", {"sections": []})
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(SCRIPT), "-ReportPath", str(rep)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    assert proc.returncode == 1 and "PBIR-Legacy" in proc.stderr + proc.stdout
