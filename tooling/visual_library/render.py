"""render.py — deterministic renderer for the ALUCA Visual Library.

The library (core/templates/page_templates/visual_library/<id>.yaml) is the Single
Source of Truth. Each idiom entry carries a `realizations` block with one runnable
template per tool (powerbi_native / powerbi_svg_dax / deneb_vegalite / web_recharts).

Determinism: a template is a PURE function of its parameters. `render()` fills every
`{{name}}` by literal substitution from `canonical_params` (the frozen sample) — no
logic, no ordering, no clock. Given the same entry it returns identical bytes every
time, so "10x the same request -> 10x the same result" is guaranteed and test-frozen
in golden/ (see tooling/visual_library/tests/test_visual_library.py).

At real generation time the same templates are filled from the semantic-model measure
names + governed tokens instead of canonical_params — identical mechanism.

Derived targets (A-31 R2): `fabric_app` and `html_vegalite` are not a fifth template per
idiom. They take the `deneb_vegalite` realization under the profile's notation and add the
profile's Vega-Lite `config` (style) — one Vega-Lite source, three runtimes (Deneb, Fabric
App `VegaVisual`, HTML via vega-embed). Colours of the brand are not part of a profile.

CLI:
    py -3 tooling/visual_library/render.py write <idiom>     # (re)freeze goldens
    py -3 tooling/visual_library/render.py show  <idiom> <tool> [profile]
    py -3 tooling/visual_library/render.py target <idiom> fabric_app|html_vegalite [profile]
"""
from __future__ import annotations

import copy
import functools
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
NOTATION = LIB / "_notation_profiles.yaml"
_LAYOUT_GRID = yaml.safe_load(
    (LIB.parent / "tokens" / "layout_grid.yaml").read_text(encoding="utf-8"))

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def grid_px(cols: int, rows: int, canvas: str = "design_base") -> "tuple[int, int]":
    """Resolve a {cols, rows} grid size to pixels on a canvas, from tokens/layout_grid.yaml.
    The logical unit (lu_w/lu_h) is computed for the design-base canvas; other canvases scale
    proportionally, so a grid size is inherently canvas-relative (the point of grid units)."""
    g = _LAYOUT_GRID
    base = g["canvas"]["design_base"]
    lu_w, lu_h = g["computed"]["lu_w"], g["computed"]["lu_h"]
    gutter = g["spacing"]["gutter"]
    w = cols * lu_w + (cols - 1) * gutter
    h = rows * lu_h + (rows - 1) * gutter
    if canvas != "design_base":
        c = g["canvas"][canvas]
        w *= c["width"] / base["width"]
        h *= c["height"] / base["height"]
    return round(w), round(h)


def min_grid_cols(width_px: float) -> int:
    """Smallest colSpan whose slot width (design base) covers width_px."""
    lu_w, gutter = _LAYOUT_GRID["computed"]["lu_w"], _LAYOUT_GRID["spacing"]["gutter"]
    c = 1
    while c * lu_w + (c - 1) * gutter < width_px:
        c += 1
    return c


def min_grid_rows(height_px: float) -> int:
    lu_h, gutter = _LAYOUT_GRID["computed"]["lu_h"], _LAYOUT_GRID["spacing"]["gutter"]
    r = 1
    while r * lu_h + (r - 1) * gutter < height_px:
        r += 1
    return r


@functools.lru_cache(maxsize=256)
def _yaml_cached(path: str, mtime_ns: int, size: int) -> object:
    """Parsed YAML keyed by path and file state — a changed file is re-read, never served stale."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _yaml(path: Path) -> object:
    """A private copy of the parsed file (callers may mutate what they get)."""
    st = path.stat()
    return copy.deepcopy(_yaml_cached(str(path), st.st_mtime_ns, st.st_size))


def load_entry(idiom: str) -> dict:
    """Load and lightly validate an idiom entry against the required schema keys."""
    data = _yaml(LIB / f"{idiom}.yaml")
    schema = _yaml(LIB / "_schema.yaml")
    missing = [k for k in schema["required_keys"] if k not in data]
    if missing:
        raise ValueError(f"{idiom}.yaml missing required keys: {missing}")
    return data


def _registry() -> dict:
    """The notation-profile registry (the second axis). See _notation_profiles.yaml."""
    return _yaml(NOTATION)


def default_profile() -> str:
    return _registry().get("default", "house_default")


def profiles(idiom: str) -> "list[str]":
    """Notation profiles this idiom supports: the default always first, then any it
    opts into via its `profiles:` block. house_default is the `realizations` baseline."""
    entry = load_entry(idiom)
    dp = default_profile()
    declared = list((entry.get("profiles") or {}).keys())
    return [dp] + [p for p in declared if p != dp]


def _effective_params(entry: dict, profile: str) -> dict:
    """canonical_params overlaid with the profile's param_overrides (default = none)."""
    params = dict(entry["canonical_params"])
    if profile != default_profile():
        prof = (entry.get("profiles") or {}).get(profile)
        if prof is None:
            raise KeyError(f"{entry['id']} does not declare notation profile '{profile}'")
        params.update(prof.get("param_overrides") or {})
    return params


def _realization(entry: dict, tool: str, profile: str) -> "dict | None":
    """The realization for tool under profile: a profile override if present, else the
    house_default base template (so a pure param overlay restyles every base tool)."""
    if profile != default_profile():
        prof = (entry.get("profiles") or {}).get(profile) or {}
        override = (prof.get("realizations") or {}).get(tool)
        if override is not None:
            return override
    return entry["realizations"].get(tool)


def fill(template: str, params: dict) -> str:
    """Substitute every {{name}} with str(params[name]). Fails loudly on a gap."""
    def _sub(m: "re.Match[str]") -> str:
        key = m.group(1)
        if key not in params:
            raise KeyError(f"template references {{{{{key}}}}} not in canonical_params")
        return str(params[key])
    return _PLACEHOLDER.sub(_sub, template)


def render(idiom: str, tool: str, profile: "str | None" = None) -> "tuple[str, str]":
    """Return (rendered_output, ext) for one idiom x tool x notation profile, filled
    from canonical_params (plus the profile's param_overrides). profile defaults to
    house_default, so render(idiom, tool) is unchanged from before the profile axis."""
    entry = load_entry(idiom)
    profile = profile or default_profile()
    real = _realization(entry, tool, profile)
    if real is None:
        raise KeyError(f"{idiom} has no realization for tool '{tool}'")
    if not real.get("applicable", True):
        raise KeyError(f"{idiom}.{tool} is not applicable under profile '{profile}'")
    out = fill(real["template"], _effective_params(entry, profile))
    return out, real["ext"]


def tools(idiom: str, profile: "str | None" = None) -> "list[str]":
    """Tool tracks with a runnable template under a profile. Not every idiom exists in
    every tool — e.g. SVG-DAX is for cell micro-charts, not full waterfalls; a tool that
    does not fit is marked ``applicable: false`` (with a reason) and skipped here. A
    non-default profile may mark a base-runnable tool n/a (its IBCS form needs a
    structural override that does not exist yet)."""
    entry = load_entry(idiom)
    profile = profile or default_profile()
    out = []
    for t in entry["realizations"]:
        real = _realization(entry, t, profile)
        if real and real.get("applicable", True) and "template" in real:
            out.append(t)
    return out


def addressed(idiom: str) -> "list[str]":
    """Every tool the entry addresses — runnable OR an explicit applicable:false."""
    return list(load_entry(idiom)["realizations"].keys())


def golden_path(idiom: str, tool: str, ext: str, profile: "str | None" = None) -> Path:
    """house_default keeps `<id>.<tool>.<ext>` (no churn); other profiles get a suffix."""
    profile = profile or default_profile()
    if profile == default_profile():
        return LIB / "golden" / f"{idiom}.{tool}.{ext}"
    return LIB / "golden" / f"{idiom}.{tool}.{profile}.{ext}"


def write_goldens(idiom: str) -> "list[Path]":
    """Freeze the rendered output of every tool x profile into golden/. Deterministic."""
    (LIB / "golden").mkdir(parents=True, exist_ok=True)
    written = []
    for profile in profiles(idiom):
        for tool in tools(idiom, profile):
            out, ext = render(idiom, tool, profile)
            p = golden_path(idiom, tool, ext, profile)
            p.write_text(out, encoding="utf-8", newline="\n")
            written.append(p)
    return written


DERIVED_TARGETS = ("fabric_app", "html_vegalite")

# The capability flags `VegaVisual` accepts (@microsoft/fabric-visuals 4.0.0, dist/index.d.ts,
# interface VegaVisualCapabilities). A profile may only set these.
VEGAVISUAL_CAPABILITIES = (
    "disableStackedDataLabels", "disableArcDataLabels", "disableNiceAxisBounds",
    "disableLineChartCrosshairTooltip", "disableTextTruncation", "disableLegendTruncation",
    "disableLegendScroll", "disableCategoricalScroll", "disableMinBarSize",
    "disableDonutInnerRadius", "disableDynamicAxisLabelOverlap",
    "disableNonZeroQuantitativeBaseline", "disablePointMarkClip", "disablePointRangeInset",
    "disableSelfHighlight", "disableCompactNumberFormatting",
)


def profile_def(profile: str) -> dict:
    """One entry of _notation_profiles.yaml; KeyError if unknown."""
    profs = _registry().get("profiles") or {}
    if profile not in profs:
        raise KeyError(f"unknown profile '{profile}'")
    return profs[profile]


def all_profiles(kind: "str | None" = None) -> "list[str]":
    """Registered profile ids, optionally only one kind (notation | style)."""
    profs = _registry().get("profiles") or {}
    return [p for p, d in profs.items() if kind is None or d.get("kind", "notation") == kind]


def notation_of(profile: str) -> str:
    """The notation profile a (notation or style) profile draws the idiom in."""
    d = profile_def(profile)
    return profile if d.get("kind", "notation") == "notation" else d.get("base_notation", default_profile())


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def vegalite_config(profile: str) -> dict:
    """house_default's config overlaid by the profile's own (a style inherits the baseline)."""
    base = profile_def(default_profile()).get("vegalite_config") or {}
    if profile == default_profile():
        return copy.deepcopy(base)
    return _deep_merge(base, profile_def(profile).get("vegalite_config") or {})


def target_profiles(idiom: str) -> "list[str]":
    """Profiles under which an idiom has a derived target: every style profile, plus the
    notation profiles the idiom opts into — each only where its Vega-Lite track runs."""
    out = []
    for p in all_profiles():
        n = notation_of(p)
        if n != default_profile() and n not in profiles(idiom):
            continue
        if "deneb_vegalite" in tools(idiom, n):
            out.append(p)
    return out


SLOT_ROLES = ("value", "variance", "time", "category", "series", "step", "period",
              "plan", "prior", "x", "y", "start", "end")


def data_slots(idiom: str) -> dict:
    """{param: {role, required}} of the idiom's Vega-Lite track (empty if none declared)."""
    return load_entry(idiom).get("data_slots") or {}


def bind(idiom: str, columns: dict) -> dict:
    """Map {role: column name} onto the idiom's column params. KeyError if a required role is
    missing; optional roles that are absent keep their canonical sample name."""
    out = {}
    for param, slot in data_slots(idiom).items():
        role = slot["role"]
        if role in columns:
            name = str(columns[role])
            # Vega-Lite reads "." and "[" in a field name as a nested-field access — the chart would
            # stay empty without an error. Fail loudly instead of drawing nothing.
            if any(c in name for c in ".[]\\'\""):
                raise ValueError(f"{idiom}: column name {name!r} for role '{role}' contains . [ ] \\ or a quote; "
                                 "rename the column (Vega-Lite would read it as a nested field)")
            out[param] = name
        elif slot.get("required", True):
            raise KeyError(f"{idiom}: required role '{role}' ({param}) not bound")
    return out


_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
#: Decorative strokes: salience kept, no contrast floor (WCAG 1.4.11 exempts gridlines).
_DECORATIVE_COLOR_KEYS = {"gridColor"}
#: Keys that colour TEXT (axis labels, titles): contrast floor 4.5 instead of 3.0.
_TEXT_COLOR_KEYS = {"labelColor", "titleColor", "subtitleColor"}


def _is_text_mark(node: dict) -> bool:
    m = node.get("mark")
    return m == "text" or (isinstance(m, dict) and m.get("type") == "text")


def on_background(node, bg: str, _key: "str | None" = None, _text: bool = False):
    """A light-card spec/config redrawn for a dark ground `bg` (A-31 R6): every colour literal
    mapped by `contrast.for_dark_ground`, which keeps its salience (ink stays loudest, gridlines
    stay quiet, PY stays quieter than AC), then floored — text 4.5:1, marks 3:1, gridlines none.
    A white `fill` (hollow marker) becomes the ground. Pure, returns a new tree."""
    if isinstance(node, dict):
        text = _text or _is_text_mark(node)
        return {k: on_background(v, bg, k, text) for k, v in node.items()}
    if isinstance(node, list):
        return [on_background(v, bg, _key, _text) for v in node]
    if _key == "fill" and isinstance(node, str) and node.lower() in ("white", "#ffffff"):
        return bg   # a white fill is the card showing through (hollow marker), not a colour
    if isinstance(node, str) and _HEX.match(node):
        floor = None if _key in _DECORATIVE_COLOR_KEYS else (
            4.5 if (_text or _key in _TEXT_COLOR_KEYS) else 3.0)
        return _contrast().for_dark_ground(node, bg, min_ratio=floor)
    return node


@functools.lru_cache(maxsize=1)
def _contrast():
    """contrast.py next to this file, loaded by path: works however render was imported (a
    mirror may import render and then drop its directory from sys.path)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("visual_library_contrast", Path(__file__).with_name("contrast.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: Stand-in for a data value (a target) that real data did not supply; never drawn.
_NO_VALUE = "-987654321.123"


def _drop_missing_values(spec: dict, idiom: str, missing: "list[str]") -> dict:
    """Remove what depends on a data value the caller did not supply (A-31 R6): a colour
    `condition` that tests against it falls back to its plain `value`, a layer that draws it (the
    reference rule, an unbound optional series) goes. The sample's target (44.1 in the canonical
    bar_ranking) must never reach
    real data — measured 30.09.2026: the Cockpit coloured contribution bars red below 44.1."""
    def walk(node):
        if isinstance(node, str) and _NO_VALUE in node and "datum[" in node:
            # an expression reading a missing column reads null (guard it with isValid in the template)
            return re.sub(r"datum\[(['\"])" + re.escape(_NO_VALUE) + r"\1\]", "null", node)
        if isinstance(node, dict):
            out = {k: walk(v) for k, v in node.items()
                   if not (k == "condition" and _NO_VALUE in json.dumps(v))}
            if "layer" in out:
                out["layer"] = [lay for lay in out["layer"] if _NO_VALUE not in json.dumps(lay)]
            return out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    spec = walk(spec)
    if _NO_VALUE in json.dumps(spec):
        raise KeyError(f"{idiom}: needs params {missing} (the template cannot drop them)")
    return spec


#: Tooltip formats per data role, the same as the data labels (A-31 R6). Time as month/year.
_TOOLTIP_ROLE = {
    "time": ("temporal", "%m/%Y"), "period": ("nominal", None), "category": ("nominal", None),
    "series": ("nominal", None), "step": ("nominal", None),
    "value": ("quantitative", ",.1~f"), "plan": ("quantitative", ",.1~f"), "prior": ("quantitative", ",.1~f"),
    "start": ("quantitative", ",.1~f"), "end": ("quantitative", ",.1~f"),
    "x": ("quantitative", ",.1~f"), "y": ("quantitative", ",.1~f"), "variance": ("quantitative", "+,.1~f"),
}
_ORDER = ("category", "step", "series", "period", "time",
          "value", "plan", "prior", "variance", "start", "end", "x", "y")
#: Marks that carry data a reader can point at; text labels and reference rules do not.
_TOOLTIP_MARKS = {"bar", "line", "point", "area", "rect", "circle", "square", "tick", "arc"}


def tooltip_fields(idiom: str, eff: dict, spec: dict) -> "list[dict]":
    """One tooltip entry per bound data column the spec draws, in reading order (dimensions,
    then measures), formatted like the data labels. A variance shown in percent (`fmt` with %)
    keeps that format. Only columns the spec actually references are listed."""
    text = json.dumps(spec)
    rows = []
    for param, slot in data_slots(idiom).items():
        col = eff.get(param)
        if not col or col == _NO_VALUE or f'"{col}"' not in text:
            continue
        typ, fmt = _TOOLTIP_ROLE[slot["role"]]
        if slot["role"] == "variance" and "%" in str(eff.get("fmt", "")):
            fmt = str(eff["fmt"])
        entry = {"field": col, "type": typ, "title": col}
        if fmt:
            entry["format"] = fmt
        rows.append((_ORDER.index(slot["role"]), entry))
    return [e for _, e in sorted(rows, key=lambda r: r[0])]


def with_tooltips(spec: dict, idiom: str, eff: dict) -> dict:
    """Details on demand for every data mark (A-31 R6): the library states what a hover shows
    instead of leaving it to the host — measured 30.09.2026, Fabric's VegaVisual filled the gap
    with raw field names, an English date ("Dec 30, 2024") and unformatted numbers ("27.95").
    Layers that aggregate or bin (histogram, boxplot) show what they encode instead: their rows are
    summaries, not the bound columns."""
    fields = tooltip_fields(idiom, eff, spec)

    def mark_type(node: dict) -> "str | None":
        m = node.get("mark")
        return m if isinstance(m, str) else (m or {}).get("type")

    def walk(node: dict) -> dict:
        node = dict(node)
        if "layer" in node:
            node["layer"] = [walk(lay) for lay in node["layer"]]
        if isinstance(node.get("spec"), dict):          # facet / repeat: the inner unit spec
            node["spec"] = walk(node["spec"])
        for key in ("vconcat", "hconcat", "concat"):   # stacked tiers (multi_tier_column)
            if key in node:
                node[key] = [walk(part) for part in node[key]]
        dump = json.dumps({k: node.get(k) for k in ("transform", "encoding")})
        kind = mark_type(node)
        if kind == "text":
            mark = node["mark"] if isinstance(node["mark"], dict) else {"type": node["mark"]}
            node["mark"] = {**mark, "tooltip": None}   # a label is the value already; no host tooltip
            return node
        if kind == "rule" and node.get("params"):
            kind = "hover_rule"                             # the nearest-date hover carries the tooltip
        if kind in _TOOLTIP_MARKS or kind in ("boxplot", "hover_rule"):
            if aggregated or '"aggregate"' in dump or '"bin"' in dump or kind == "boxplot":
                # rows are summaries, not the bound columns: show what the marks encode
                mark = node["mark"] if isinstance(node["mark"], dict) else {"type": node["mark"]}
                node["mark"] = {**mark, "tooltip": mark.get("tooltip", {"content": "encoding"})}
            else:
                enc = dict(node.get("encoding") or {})
                enc.setdefault("tooltip", fields)
                node["encoding"] = enc
        return node

    top = json.dumps(spec.get("transform", []))
    aggregated = '"aggregate"' in top or '"bin"' in top
    return walk(spec)


def render_target(idiom: str, target: str, profile: "str | None" = None,
                  bindings: "dict | None" = None, params: "dict | None" = None,
                  background: "str | None" = None) -> "tuple[str, str]":
    """Derived target output for one idiom x profile. Deterministic JSON.

    `bindings` ({role: column}) binds real data columns through `data_slots`; `params` overrides
    any other template parameter (e.g. polarity -1 for a lower-is-better measure). Without both,
    the frozen canonical sample is used — that is what the goldens freeze. `background` (hex)
    redraws the colours for that dark ground (`on_background`, salience kept)."""
    if target not in DERIVED_TARGETS:
        raise KeyError(f"unknown derived target '{target}'")
    profile = profile or default_profile()
    notation = notation_of(profile)
    if notation != default_profile() and notation not in profiles(idiom):
        raise KeyError(f"{idiom} has no '{notation}' reading")
    if bindings or params:
        entry = load_entry(idiom)
        real = _realization(entry, "deneb_vegalite", notation)
        if real is None or not real.get("applicable", True):
            raise KeyError(f"{idiom}.deneb_vegalite is not applicable under '{notation}'")
        eff = dict(_effective_params(entry, notation))
        bound = bind(idiom, bindings or {}) if bindings else {}
        eff.update(bound)
        dv = entry.get("data_values") or {}
        dv = dict.fromkeys(dv) if isinstance(dv, list) else dict(dv)
        given = params or {}
        missing = [v for v, fb in dv.items() if v not in given and fb is None]
        missing += [p for p, slot in data_slots(idiom).items()
                    if p not in bound and not slot.get("required", True) and p not in given]
        eff.update({v: _NO_VALUE for v in missing})
        eff.update({v: eff[fb] for v, fb in dv.items() if v not in given and fb is not None})
        eff.update({k: str(v) for k, v in given.items()})
        spec = json.loads(fill(real["template"], eff))
        if missing:
            spec = _drop_missing_values(spec, idiom, missing)
    else:
        spec = json.loads(render(idiom, "deneb_vegalite", notation)[0])
        eff = dict(_effective_params(load_entry(idiom), notation))
    spec = with_tooltips(spec, idiom, eff)
    config = vegalite_config(profile)
    if background:
        spec, config = on_background(spec, background), on_background(config, background)
    if target == "html_vegalite":
        out = dict(spec)
        out["config"] = config
    else:
        caps = {**(profile_def(default_profile()).get("vegavisual_capabilities") or {}),
                **(profile_def(profile).get("vegavisual_capabilities") or {})}
        unknown = sorted(set(caps) - set(VEGAVISUAL_CAPABILITIES))
        if unknown:
            raise KeyError(f"profile '{profile}' sets unknown VegaVisual capabilities {unknown}")
        out = {"idiom": idiom, "profile": profile, "notation": notation,
               "data_name": (spec.get("data") or {}).get("name"),
               "spec": spec, "configVegaLite": config, "capabilities": dict(sorted(caps.items()))}
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n", "json"


def target_golden_path(idiom: str, target: str, profile: "str | None" = None) -> Path:
    profile = profile or default_profile()
    return LIB / "golden" / "targets" / f"{idiom}.{target}.{profile}.json"


def write_target_goldens(idiom: str) -> "list[Path]":
    """Freeze fabric_app for every NOTATION profile of the idiom. Style profiles only swap the
    config (a pure merge of the registry, tested directly) and html_vegalite only moves the
    config into the spec — both are proven by rendering, not frozen a second time."""
    written = []
    for profile in [p for p in target_profiles(idiom) if profile_def(p).get("kind", "notation") == "notation"]:
        out, _ = render_target(idiom, "fabric_app", profile)
        p = target_golden_path(idiom, "fabric_app", profile)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out, encoding="utf-8", newline="\n")
        written.append(p)
    return written


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "write":
        for p in write_goldens(sys.argv[2]):
            print("wrote", p.relative_to(REPO_ROOT).as_posix())
        return 0
    if len(sys.argv) >= 4 and sys.argv[1] == "target":
        prof = sys.argv[4] if len(sys.argv) >= 5 else None
        out, _ = render_target(sys.argv[2], sys.argv[3], prof)
        print(out)
        return 0
    if len(sys.argv) >= 3 and sys.argv[1] == "write-targets":
        for p in write_target_goldens(sys.argv[2]):
            print("wrote", p.relative_to(REPO_ROOT).as_posix())
        return 0
    if len(sys.argv) >= 4 and sys.argv[1] == "show":
        prof = sys.argv[4] if len(sys.argv) >= 5 else None
        out, _ = render(sys.argv[2], sys.argv[3], prof)
        print(out)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
