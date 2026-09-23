"""Tests for tooling/validation/check_ai_surface_hygiene.py (Epic C).

C1 — visible surrogate/FK keys: detection, idempotent --fix (insert isHidden after
dataType), 0 on the cleaned real Commercial model.
C2 — weak descriptions: name-restating / low-info detection, 0 on real Commercial.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "tooling" / "validation"))

from check_ai_surface_hygiene import (
    hide_visible_keys,
    main,
    visible_keys,
    weak_descriptions,
    weak_reason,
)

_DIST = _REPO_ROOT / "products" / "fabric" / "powerbi" / "dist"


def _seed_table(root: Path, domain: str, body: str) -> Path:
    tdir = root / f"{domain}.SemanticModel" / "definition" / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    f = tdir / "fact_x.tmdl"
    f.write_text(body, encoding="utf-8")
    return f


_FACT_WITH_VISIBLE_KEY = (
    "table fact_x\n"
    "\tcolumn DateKey\n"
    "\t\tdataType: int64\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: DateKey\n"
    "\n"
    "\tcolumn Amount\n"
    "\t\tdataType: decimal\n"
    "\t\tsummarizeBy: sum\n"
    "\t\tsourceColumn: Amount\n"
)


# ---------------------------------------------------------------------------
# C1 — visible keys
# ---------------------------------------------------------------------------

def test_visible_keys_flags_unhidden_key(tmp_path):
    _seed_table(tmp_path, "Commercial", _FACT_WITH_VISIBLE_KEY)
    assert visible_keys(tmp_path, "Commercial") == ["fact_x.DateKey"]


def test_hide_inserts_ishidden_after_datatype_and_is_idempotent(tmp_path):
    f = _seed_table(tmp_path, "Commercial", _FACT_WITH_VISIBLE_KEY)
    fixed = hide_visible_keys(tmp_path, "Commercial")
    assert fixed == ["fact_x.DateKey"]
    lines = f.read_text(encoding="utf-8").splitlines()
    di = lines.index("\t\tdataType: int64")
    assert lines[di + 1] == "\t\tisHidden"          # inserted right after dataType
    assert visible_keys(tmp_path, "Commercial") == []
    assert hide_visible_keys(tmp_path, "Commercial") == []  # idempotent


def test_non_key_columns_untouched(tmp_path):
    _seed_table(tmp_path, "Commercial", _FACT_WITH_VISIBLE_KEY)
    hide_visible_keys(tmp_path, "Commercial")
    body = (tmp_path / "Commercial.SemanticModel" / "definition" / "tables" / "fact_x.tmdl").read_text(encoding="utf-8")
    # the measure column 'Amount' must not have been hidden
    amount_block = body.split("column Amount", 1)[1]
    assert "isHidden" not in amount_block


def test_real_commercial_has_no_visible_keys():
    # the committed model was cleaned in this epic
    assert visible_keys(_DIST, "Commercial") == []


# ---------------------------------------------------------------------------
# C2 — weak descriptions
# ---------------------------------------------------------------------------

def test_weak_reason_classification():
    assert weak_reason("Region", "Region") == "restates the name"
    assert weak_reason("Region", "region") == "restates the name"
    assert "below" in weak_reason("Region", "the region")          # <3 words
    assert "adds <2" in weak_reason("Net Sales", "net sales total")  # only 'total' is new
    # a genuinely informative description clears the bar
    assert weak_reason("Region", "Sales region grouping countries together") is None
    # absence is a coverage gap, not a quality violation
    assert weak_reason("Region", "") is None


def test_real_commercial_descriptions_clear_the_bar():
    assert weak_descriptions(_REPO_ROOT, "Commercial") == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_strict_clean_on_real_commercial():
    assert main(["--domain", "Commercial", "--strict"]) == 0
