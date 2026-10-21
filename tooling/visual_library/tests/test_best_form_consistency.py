"""Eine Stelle definiert die Bestform je Zweck: index.yaml `purposes.<p>.best`.

Idiom-Dateien (`best_form_for`) und der Skill-Text folgen ihr; dieser Test haelt beide
deckungsgleich. Part-to-whole: stacked_100 fuehrt, donut ist nur Alternative fuer <= 3 Teile.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
VL = ROOT / "core" / "templates" / "page_templates" / "visual_library"
SKILL = ROOT / "docs" / "agent" / "skills" / "visual-library.md"


def _index() -> dict:
    return yaml.safe_load((VL / "index.yaml").read_text(encoding="utf-8"))


def _idioms() -> dict[str, dict]:
    out = {}
    for p in VL.glob("*.yaml"):
        if p.name.startswith("_") or p.name == "index.yaml":
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if "id" in d:
            out[d["id"]] = d
    return out


def _base(idiom_ref: str) -> str:
    return idiom_ref.split("@", 1)[0]


def test_best_form_for_matches_index_best() -> None:
    purposes = _index()["purposes"]
    idioms = _idioms()
    assert len(idioms) >= 20, f"nur {len(idioms)} Idiome gelesen"
    # Richtung 1: jede best_form_for-Angabe ist die Index-Bestform ihres Zwecks
    for iid, d in idioms.items():
        p = d.get("best_form_for")
        if p:
            assert p in purposes, f"{iid}: best_form_for {p} ist kein Zweck"
            assert _base(purposes[p]["best"]) == iid, (
                f"{iid}: best_form_for {p}, Index nennt {purposes[p]['best']}")
    # Richtung 2: jede Index-Bestform (falls Idiom) traegt best_form_for = Zweck
    for p, spec in purposes.items():
        best = _base(spec.get("best") or "")
        if best in idioms:
            assert idioms[best].get("best_form_for") == p, (
                f"{p}: Index-best {best} traegt best_form_for={idioms[best].get('best_form_for')}")


def test_part_to_whole_stacked_first_donut_only_alternative() -> None:
    ptw = _index()["purposes"]["part_to_whole"]
    assert ptw["best"] == "stacked_100"
    assert "donut" in ptw["candidates"] and ptw["candidates"][0] != "donut"
    donut = _idioms()["donut"]
    assert donut.get("best_form_for") is None
    assert donut["params"]["category"]["max"] == 3


def test_pie_deny_id_names_the_limit_three() -> None:
    idx = _index()
    assert "pie_gt_3" in idx["deny"] and "pie_gt_4" not in idx["deny"]
    ap = yaml.safe_load((VL / "_anti_patterns.yaml").read_text(encoding="utf-8"))["patterns"]
    assert "pie_or_donut_gt_3" in ap and "pie_or_donut_gt_4" not in ap


def test_skill_deny_line_equals_index_deny() -> None:
    text = SKILL.read_text(encoding="utf-8")
    section = text.split("## Deny (never emit)", 1)[1]
    line = re.search(r"`([^`]+)`", section).group(1)
    assert [x.strip() for x in line.split("·")] == list(_index()["deny"])


def test_skill_has_no_fixed_idiom_counter() -> None:
    text = SKILL.read_text(encoding="utf-8")
    n = len(_index()["implemented"])
    for m in re.finditer(r"\b(\d+)\s+idioms?\b", text):
        assert int(m.group(1)) == n, f"Skill nennt '{m.group(0)}', index.yaml implemented = {n}"
