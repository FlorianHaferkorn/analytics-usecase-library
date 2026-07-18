"""Tests for the storyline layer — deriver + governance.

Guards: every visual answers a stated question, every page has a decision spine, the page-1→page-2
handoff holds, and the generated storyboard doc stays in sync with the deriver.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tooling.validation.check_storyline import check_bracket, render_out_of_sync

REPO = Path(__file__).resolve().parents[2]


def test_every_visual_has_a_question():
    missing = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        d = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        for pk in ("page_1_summary", "page_2_execution"):
            p = (d.get("ux_layout_rules", {}) or {}).get(pk, {}) or {}
            for c in (p.get("component_30s") or []):
                if not (c.get("question") or "").strip():
                    missing.append(f"{d.get('id')}/{pk}/{c.get('kpi_id')}")
    assert not missing, "component_30s visuals without a `question`: " + ", ".join(missing)


def test_storyline_structure_clean():
    violations = []
    for b in sorted(REPO.glob("core/usecases/**/UseCase_Bracket.yaml")):
        violations += check_bracket(yaml.safe_load(b.read_text(encoding="utf-8")) or {})
    assert not violations, "storyline structure violations:\n" + "\n".join(violations)


def test_storyboard_doc_in_sync():
    stale = render_out_of_sync()
    assert stale is None, stale
