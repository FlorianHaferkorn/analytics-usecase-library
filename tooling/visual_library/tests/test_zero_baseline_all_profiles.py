"""Zero baseline for length-encoded marks under EVERY profile (Design-Lab finding 1).

A bar/area/rect encodes a value as a LENGTH from the baseline; a truncated value axis
(`scale.zero: false`, or an explicit domain that excludes 0) turns that length into a lie.
Line/point marks encode POSITION, and IBCS CH 1.1 / W-5
(docs/architecture/research/2026-09-30_visual-stack-r1/entscheidungsvorlage.yaml) allows a
capped axis there per profile — so the only allowed `zero: false` sits on line/point marks,
and never on a scale that a length mark shares (layers share scales unless resolved apart).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LENGTH_MARKS = {"bar", "area", "rect"}
EXEMPT_MARKS = {"line", "point"}          # position-encoded: capped axis allowed per profile
VALUE_CHANNELS = ("x", "y")


def _vega_idioms() -> list[str]:
    impl = yaml.safe_load((render.LIB / "index.yaml").read_text(encoding="utf-8"))["implemented"]
    return [i for i in impl if "deneb_vegalite" in render.tools(i)]


def _mark_type(mark) -> "str | None":
    return mark.get("type") if isinstance(mark, dict) else mark


def _units(spec: dict, inherited: "dict | None" = None) -> "list[tuple[str | None, dict]]":
    """(mark type, effective encoding) of every unit in one shared-scale group (a layer
    stack). Layer children inherit and override the parent's encoding."""
    enc = {**(inherited or {}), **(spec.get("encoding") or {})}
    if "layer" in spec:
        return [u for child in spec["layer"] for u in _units(child, enc)]
    if "mark" in spec:
        return [(_mark_type(spec["mark"]), enc)]
    return []


def _groups(spec: dict) -> "list[tuple[dict, list]]":
    """Shared-scale groups: each (group spec, units). Concat/facet children are separate."""
    for key in ("spec",):                                    # facet / repeat wrapper
        if isinstance(spec.get(key), dict):
            return _groups(spec[key])
    for key in ("hconcat", "vconcat", "concat"):
        if isinstance(spec.get(key), list):
            return [g for child in spec[key] for g in _groups(child)]
    return [(spec, _units(spec))]


def _quantitative(ch: dict) -> bool:
    return ch.get("type") == "quantitative" or ("aggregate" in ch and ch.get("type") is None)


def _truncates(ch: dict) -> bool:
    scale = ch.get("scale") or {}
    if scale.get("zero") is False:
        return True
    dom = scale.get("domain")
    if isinstance(dom, list) and len(dom) == 2 and all(isinstance(v, (int, float)) for v in dom):
        return not (min(dom) <= 0 <= max(dom))
    dmin = scale.get("domainMin")
    return isinstance(dmin, (int, float)) and dmin > 0


def _find_zero_false(node, path="") -> list[str]:
    hits = []
    if isinstance(node, dict):
        if node.get("zero") is False:
            hits.append(path or "/")
        for k, v in node.items():
            hits += _find_zero_false(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits += _find_zero_false(v, f"{path}[{i}]")
    return hits


def _violations(spec: dict) -> list[str]:
    out = []
    for group, units in _groups(spec):
        independent = ((group.get("resolve") or {}).get("scale") or {})
        for chan in VALUE_CHANNELS:
            truncating = [m for m, enc in units if chan in enc and _truncates(enc[chan])]
            lengths = [m for m, enc in units
                       if m in LENGTH_MARKS and chan in enc and _quantitative(enc[chan])]
            bad_exempt = [m for m in truncating if m not in EXEMPT_MARKS]
            if bad_exempt:
                out.append(f"{chan}: truncated axis on non-line/point mark(s) {bad_exempt}")
            elif truncating and lengths and independent.get(chan) != "independent":
                out.append(f"{chan}: length mark(s) {lengths} share a scale truncated by {truncating}")
    return out


def test_every_idiom_has_rendered_targets():
    idioms = _vega_idioms()
    assert idioms, "no deneb_vegalite idioms found — the gate would pass vacuously"
    assert sum(len(render.target_profiles(i)) for i in idioms) >= len(idioms)


def test_length_marks_keep_zero_baseline_under_every_profile():
    problems, checked = [], 0
    for idiom in _vega_idioms():
        for pid in render.target_profiles(idiom):
            out = json.loads(render.render_target(idiom, "fabric_app", pid)[0])
            checked += 1
            for v in _violations(out["spec"]):
                problems.append(f"{idiom}@{pid} {v}")
            cfg_hits = _find_zero_false(out.get("configVegaLite") or {})
            if cfg_hits:
                problems.append(f"{idiom}@{pid} configVegaLite sets zero:false at {cfg_hits}")
    assert checked > 0
    assert not problems, "truncated value axis on a length mark:\n  " + "\n  ".join(problems)


def test_gate_catches_a_truncated_bar():
    """Counter-check: the detector must see the defect it guards against."""
    bar = {"mark": "bar", "encoding": {"y": {"field": "v", "type": "quantitative",
                                             "scale": {"zero": False}}}}
    assert _violations(bar)
    layered = {"layer": [
        {"mark": "bar", "encoding": {"y": {"field": "v", "type": "quantitative"}}},
        {"mark": "line", "encoding": {"y": {"field": "v", "type": "quantitative",
                                            "scale": {"zero": False}}}}]}
    assert _violations(layered), "a line's zero:false truncates the bar it shares a scale with"
    waterfall = {"mark": "rect", "encoding": {"y": {"field": "a", "type": "quantitative",
                                                    "scale": {"domain": [50, 120]}}}}
    assert _violations(waterfall)
    line = {"mark": {"type": "line", "point": True},
            "encoding": {"y": {"field": "v", "type": "quantitative", "scale": {"zero": False}}}}
    assert _violations(line) == []
