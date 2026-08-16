"""Tests for tokens_dtcg.py — the W3C DTCG export of the governed tokens."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import tokens_dtcg as T  # noqa: E402

TOKENS_DIR = REPO_ROOT / "core" / "templates" / "page_templates" / "tokens"


def test_committed_export_is_current():
    r = T.check()
    assert r["in_sync"], f"tokens.dtcg.json is stale — run `tokens_dtcg.py build` ({r})"


def test_groups_carry_type_and_leaves_carry_value():
    tok = T.build_tokens()
    assert tok["color"]["$type"] == "color"
    assert tok["dimension"]["$type"] == "dimension"
    leaves = list(T.iter_leaves(tok))
    assert len(leaves) >= 30
    for path, leaf in leaves:
        assert "$value" in leaf, f"{path}: DTCG leaf missing $value"


def test_colors_match_the_source_of_truth():
    cs = yaml.safe_load((TOKENS_DIR / "color_semantics.yaml").read_text(encoding="utf-8"))
    tok = T.build_tokens()
    assert tok["color"]["semantic"]["positive"]["$value"] == cs["semantic"]["positive"]
    # the CVD-safe palette travels intact (8 colours, blue first)
    cvd = tok["color"]["categorical_cvd_safe"]
    assert cvd["blue"]["$value"] == "#0072B2" and len(cvd) == 8


def test_dimensions_use_value_unit_objects():
    lg = yaml.safe_load((TOKENS_DIR / "layout_grid.yaml").read_text(encoding="utf-8"))
    tok = T.build_tokens()
    gutter = tok["dimension"]["spacing"]["gutter"]["$value"]
    assert gutter == {"value": lg["spacing"]["gutter"], "unit": "px"}
