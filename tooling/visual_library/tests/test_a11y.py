"""Tests for a11y.py — accessible-name + data-table generation for the Visual Library.

Guarantees:
- every implemented idiom composes a real, per-idiom alt-text (its name + what it shows), never empty;
- the a11y layer covers every analytical purpose in the chooser (no purpose can ship label-less);
- alt-text is data-driven when a summary is supplied (not a fixed label);
- the data-table fallback is well-formed accessible HTML (caption + scope) and escapes content.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402
import a11y  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"


def _implemented():
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]


def test_every_idiom_has_nonempty_alt_text_with_its_name():
    for iid in _implemented():
        name = render.load_entry(iid)["name"]
        alt = a11y.alt_text(iid)
        assert alt and name in alt, f"{iid}: alt-text missing the idiom name"
        assert alt.endswith(".") and len(alt) > len(name) + 8, f"{iid}: alt-text not composed"


def test_purpose_phrases_cover_the_chooser():
    purposes = set(yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))["purposes"])
    missing = purposes - set(a11y.PURPOSE_PHRASE)
    assert not missing, f"purposes without an a11y phrase: {sorted(missing)}"


def test_alt_text_is_data_driven_when_summary_supplied():
    static = a11y.alt_text("bar_ranking")
    summary = {"n": 8, "unit": "categories",
               "top": {"label": "Fashion", "value": "12.4M"},
               "bottom": {"label": "Books", "value": "0.9M"}, "direction": "up"}
    rich = a11y.alt_text("bar_ranking", summary)
    assert rich != static and static in rich
    assert "Fashion" in rich and "8 categories" in rich and "up" in rich


def test_explicit_a11y_override_is_respected(monkeypatch):
    monkeypatch.setattr(render, "load_entry",
                        lambda _i: {"name": "X", "purpose": ["part_to_whole"],
                                    "a11y": {"alt": "Custom governed description."}})
    assert a11y.alt_text("whatever") == "Custom governed description."


def test_aria_label_and_vegalite_description_nonempty():
    for iid in ("donut", "line", "waterfall_pvm"):
        assert a11y.aria_label(iid)
        assert a11y.vegalite_description(iid) == a11y.alt_text(iid)


def test_data_table_is_wellformed_and_escapes():
    t = a11y.data_table(["Category", "Sales"], [["Fashion", "12.4M"], ["<b>x</b>", "1"]],
                        caption="Sales by category")
    h = t["html"]
    assert h.startswith("<table>") and "<caption>Sales by category</caption>" in h
    assert h.count('scope="col"') == 2
    assert h.count("<tr>") == 3            # 1 header + 2 body rows
    assert "&lt;b&gt;x&lt;/b&gt;" in h and "<b>x</b>" not in h  # escaped
    md = t["markdown"]
    assert md.count("\n| ") >= 3 and "| --- | --- |" in md


def test_data_table_without_caption_omits_caption():
    t = a11y.data_table(["A"], [["1"]])
    assert "<caption>" not in t["html"]


def test_structured_tree_is_navigable_and_escapes():
    t = a11y.structured_tree("bar_ranking", ["Category", "Sales"],
                             [["Fashion", "12.4M"], ["<b>x</b>", "1"]])
    assert t["nodes"] == 2
    assert 'role="tree"' in t["html"] and t["html"].count('role="treeitem"') == 3  # root + 2 rows
    assert "&lt;b&gt;x&lt;/b&gt;" in t["html"] and "<b>x</b>" not in t["html"]
    assert t["text"].startswith(a11y.alt_text("bar_ranking"))
    assert t["text"].count("\n  - ") == 2
