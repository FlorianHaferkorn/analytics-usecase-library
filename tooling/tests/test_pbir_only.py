"""PBIR only (I-21 W5.8): every committed report in dist/ is PBIR, none PBIR-Legacy.

Learn (power-bi/developer/projects/projects-report, read 2026-10-01): PBIR is generally
available and the default; `report.json` at the report root is the PBIR-Legacy file, the
`definition/` folder replaces it, and definition.pbir version 4.0 or higher is required for
PBIR. Learn (rest/api/fabric/articles/item-management/definitions/report-definition, read
2026-10-01): the two formats are mutually exclusive.

The test counts the reports first, so "nothing found" fails instead of passing silently.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

DIST = Path(__file__).resolve().parents[2] / "products" / "fabric" / "powerbi" / "dist"
REPORTS = sorted(DIST.glob("*.Report")) if DIST.is_dir() else []


def test_dist_has_reports() -> None:
    assert REPORTS, f"no *.Report folder under {DIST}: gate did not run"


@pytest.mark.parametrize("report", REPORTS, ids=lambda p: p.name)
def test_report_is_pbir_not_legacy(report: Path) -> None:
    assert not (report / "report.json").exists(), "PBIR-Legacy report.json at the report root"
    assert (report / "definition" / "report.json").is_file(), "PBIR definition/report.json missing"
    assert (report / "definition" / "pages").is_dir(), "PBIR definition/pages/ missing"


@pytest.mark.parametrize("report", REPORTS, ids=lambda p: p.name)
def test_definition_pbir_version_supports_pbir(report: Path) -> None:
    pbir = json.loads((report / "definition.pbir").read_text(encoding="utf-8"))
    major = int(str(pbir.get("version", "0")).split(".")[0])
    assert major >= 4, f"definition.pbir version {pbir.get('version')!r} allows PBIR-Legacy only"
