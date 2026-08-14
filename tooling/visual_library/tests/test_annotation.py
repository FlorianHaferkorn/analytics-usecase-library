"""Tests for the optional grid-template `annotation` field — the IBCS commentary layer.

A template MAY reserve a narrative commentary region as a top-level `annotation` object (semantic,
no fixed geometry, so it never collides with `slots` nor pollutes the manifest slot catalog). This
validates the field's shape wherever it appears, and that the two example templates carry it.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GRID = REPO_ROOT / "core" / "templates" / "page_templates" / "grid_templates"
_PLACEMENTS = {"footer", "header", "rail"}


def _templates():
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(GRID.glob("*.json"))}


def test_annotation_blocks_are_well_formed():
    annotated = 0
    for name, tpl in _templates().items():
        ann = tpl.get("annotation")
        if ann is None:
            continue
        annotated += 1
        assert ann.get("role"), f"{name}: annotation needs a role"
        assert ann.get("placement") in _PLACEMENTS, f"{name}: placement must be one of {_PLACEMENTS}"
        assert isinstance(ann.get("content_hint"), str) and ann["content_hint"], f"{name}: content_hint required"
        assert isinstance(ann.get("max_chars"), int) and ann["max_chars"] > 0, f"{name}: max_chars must be a positive int"
        # a top-level field, never smuggled into a slot (keeps the manifest slot catalog clean)
        assert not any(s.get("slot_id") == "annotation" for s in tpl.get("slots", [])), \
            f"{name}: annotation must be top-level, not a slot"
    assert annotated >= 2, f"expected the example templates to carry an annotation region, got {annotated}"


def test_example_templates_declare_annotation():
    tpls = _templates()
    for name in ("executive_kpi.json", "investigator.json"):
        assert tpls[name].get("annotation", {}).get("role") == "commentary", f"{name}: missing commentary annotation"
