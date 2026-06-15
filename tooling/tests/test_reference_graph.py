"""Phase 2 integrity gate — referential integrity across the artifact families.

Backed by tooling/reference_graph.py (use-case-rooted graph). Runs in stage1's
python-checks (pytest) so "everything grounded, nothing dangling" is enforced on
every push — not aspirational.

  * test_no_dangling_references — a use case / action code may not reference a KPI
    or action code that doesn't exist in the catalog.
  * test_reference_graph_report_in_sync — docs/architecture/reference_graph.md is a
    generated view; it must match the source (no stale doc).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "docs/architecture/reference_graph.md"


def _rg():
    spec = importlib.util.spec_from_file_location("reference_graph", REPO / "tooling/reference_graph.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_dangling_references():
    rg = _rg()
    _, a = rg.build()
    assert not a["dangling_kpi"], (
        f"use cases/action codes reference KPIs missing from the catalog: {a['dangling_kpi']}"
    )
    assert not a["dangling_ac"], (
        f"use cases reference action codes that do not exist: {a['dangling_ac']}"
    )


def test_reference_graph_report_in_sync():
    rg = _rg()
    g, a = rg.build()
    expected = rg.render(g, a)
    actual = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    assert actual == expected, (
        "docs/architecture/reference_graph.md is stale — "
        "regenerate with: python tooling/reference_graph.py"
    )
