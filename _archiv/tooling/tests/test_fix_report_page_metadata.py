"""Tests for fix_com001_stub / fix_report_page_metadata alignment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tooling/scripts"))

from fix_com001_stub import fix_report_page_metadata  # noqa: E402


def test_fix_report_page_metadata_aligns_page_json(tmp_path: Path):
    report = tmp_path / "COM-001_Sales_Performance.Report"
    pages = report / "definition/pages"
    overview = pages / "Page_COM001_Overview"
    detail = pages / "Page_COM001_Detail"
    overview.mkdir(parents=True)
    detail.mkdir(parents=True)

    (overview / "page.json").write_text(
        json.dumps({"name": "Page_COM002_Overview", "displayName": "COM-002 - Overview"}),
        encoding="utf-8",
    )
    (detail / "page.json").write_text(
        json.dumps({"name": "Page_COM002_Detail", "displayName": "COM-002 - Detail"}),
        encoding="utf-8",
    )
    (pages / "pages.json").write_text(
        json.dumps({"pageOrder": ["Page_COM001_Overview", "Page_COM001_Detail"], "activePageName": "Page_COM001_Overview"}),
        encoding="utf-8",
    )

    changes = fix_report_page_metadata(report)
    assert any("Page_COM001_Overview" in c for c in changes)

    ov = json.loads((overview / "page.json").read_text(encoding="utf-8"))
    assert ov["name"] == "Page_COM001_Overview"
    assert ov["displayName"] == "COM-001 - Overview"

    meta = json.loads((pages / "pages.json").read_text(encoding="utf-8"))
    assert meta["pageOrder"] == ["Page_COM001_Overview", "Page_COM001_Detail"]
    assert meta["activePageName"] == "Page_COM001_Overview"


def test_fix_report_page_metadata_raises_when_all_page_json_missing(tmp_path: Path):
    import pytest

    report = tmp_path / "COM-001_Sales_Performance.Report"
    pages = report / "definition/pages"
    (pages / "Page_COM001_Overview").mkdir(parents=True)
    (pages / "Page_COM001_Detail").mkdir(parents=True)
    (pages / "pages.json").write_text(
        json.dumps({"pageOrder": ["Page_COM001_Overview"], "activePageName": "Page_COM001_Overview"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No valid page.json files"):
        fix_report_page_metadata(report)
