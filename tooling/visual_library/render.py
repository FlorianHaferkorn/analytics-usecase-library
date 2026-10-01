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
              "plan", "prior", "forecast", "x", "y", "start", "end")


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
    "forecast": ("quantitative", ",.1~f"),
    "start": ("quantitative", ",.1~f"), "end": ("quantitative", ",.1~f"),
    "x": ("quantitative", ",.1~f"), "y": ("quantitative", ",.1~f"), "variance": ("quantitative", "+,.1~f"),
}
_ORDER = ("category", "step", "series", "period", "time",
          "value", "plan", "forecast", "prior", "variance", "start", "end", "x", "y")
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


#: Rest modes for Top N (A-31 R7): `sum` folds the rest into one summed bar — only valid for an
#: additive measure (amounts, contributions); `none` keeps the rest as a labelled category without a
#: value, because the sum of rates or days is a wrong number, not an imprecise one.
REST_MODES = ("none", "sum")
REST_LABEL = "Übrige"


def _slot_column(idiom: str, eff: dict, role: str) -> "str | None":
    for param, slot in data_slots(idiom).items():
        col = eff.get(param)
        if slot["role"] == role and col and col != _NO_VALUE:
            return col
    return None


def _vega_str(text: str) -> str:
    """Text for a single-quoted Vega expression string."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def with_top_n(spec: dict, idiom: str, eff: dict, n: int, rest: str, label: str = REST_LABEL) -> dict:
    """Keep the first `n` categories in display order and fold the others into one rest row
    ("Übrige (k)"), drawn last (A-31 R7, BC-CHART-10). Silent truncation hides data; a rest row
    says how much is folded. Applies to the top-level data, so every layer (bar, label, reference)
    reads the same rows; sorts on the value field are redirected so the rest stays at the end.
    `label` names the rest row in the reader's language (German default, "Other" in English)."""
    if rest not in REST_MODES:
        raise ValueError(f"rest must be one of {REST_MODES}, not {rest!r}")
    cat, val = _slot_column(idiom, eff, "category"), _slot_column(idiom, eff, "value")
    if not cat or not val:
        raise KeyError(f"{idiom}: Top N needs a bound category and value column")
    measures = [val] + [c for c in (_slot_column(idiom, eff, r) for r in ("prior", "plan")) if c]

    order = "descending"

    def find_order(node):
        nonlocal order
        if isinstance(node, dict):
            s = node.get("sort")
            if isinstance(s, dict) and s.get("field") == val and s.get("order"):
                order = s["order"]
                return True
            return any(find_order(v) for v in node.values())
        if isinstance(node, list):
            return any(find_order(v) for v in node)
        return False

    find_order(spec)
    last = 1e300 if order == "ascending" else -1e300
    # Welche n bleiben, entscheidet die Richtung der Kennzahl, nicht die Anzeigereihenfolge: unter IBCS
    # sortiert bar_ranking absteigend, und Top 3 behielt die drei besten — die schwächste Region lag
    # in „Übrige“ (Cockpit 01.10.2026, UC-COM-003: CEE 22,4 % von fünf Regionen ausgeblendet).
    keep = eff.get("worst_first") if eff.get("worst_first") in ("ascending", "descending") else order
    fold = [
        {"window": [{"op": "row_number", "as": "_rank"}], "sort": [{"field": val, "order": keep}]},
        {"joinaggregate": [{"op": "count", "as": "_rows"}]},
        {"calculate": f"datum._rank > {n}", "as": "_rest"},
        {"calculate": f"datum._rest ? '{_vega_str(label)} (' + (datum._rows - {n}) + ')' : datum['{cat}']", "as": cat},
    ]
    if rest == "none":
        fold += [{"calculate": f"datum._rest ? null : datum['{m}']", "as": m} for m in measures]
    fold += [
        {"aggregate": [{"op": "sum" if rest == "sum" else "max", "field": m, "as": m} for m in measures],
         "groupby": [cat, "_rest"]},
        {"calculate": f"datum._rest ? {last} : datum['{val}']", "as": "_ord"},
    ]

    # A rest is not an item: rating it against a per-item target says nothing, so it takes the
    # idiom's neutral colour where the colour encodes a rating.
    neutral = next((eff[k] for k in ("col_ref", "col_neutral") if eff.get(k) and eff[k] != _NO_VALUE), None)

    def redirect(node):
        if isinstance(node, dict):
            out = {k: redirect(v) for k, v in node.items()}
            s = out.get("sort")
            if isinstance(s, dict) and s.get("field") == val:
                out["sort"] = {**s, "field": "_ord"}
            color = out.get("color")
            if neutral and isinstance(color, dict) and "condition" in color and "field" not in color:
                cond = color["condition"]
                out["color"] = {**color, "condition": [{"test": "datum._rest", "value": neutral}]
                                + (cond if isinstance(cond, list) else [cond])}
            return out
        if isinstance(node, list):
            return [redirect(v) for v in node]
        return node

    spec = redirect(spec)
    spec["transform"] = fold + list(spec.get("transform") or [])
    return spec


def with_time_axis(spec: dict, fmt: str, ticks: "list | None") -> dict:
    """Format (d3-time-format, z. B. "KW %V" für ISO-Wochen) für jede Zeitachse und jeden
    Zeit-Tooltip, Achsenmarken an den gegebenen Zeitpunkten (A-31 R8). Ohne Angabe wählt Vega die
    Marken selbst: bei vier Wochenpunkten Tagesmarken "Mo 09, Mi 11, Fr 13", mit Intervall "week"
    Sonntage — nach ISO die Vorwoche, also um eine Woche falsch beschriftet (Cockpit, 01.10.2026).
    Marken außerhalb des gezeigten Zeitraums verwirft Vega; überlappende dünnt labelOverlap aus."""
    def walk(node):
        if isinstance(node, dict):
            out = {k: walk(v) for k, v in node.items()}
            if out.get("type") == "temporal" and "field" in out:
                if "title" in out and "axis" not in out and "scale" not in out:
                    out["format"] = fmt                     # a tooltip entry
                elif out.get("axis") is not None:
                    axis = {**(out.get("axis") or {}), "format": fmt, "labelOverlap": True}
                    if ticks:
                        axis["values"] = list(ticks)
                    out["axis"] = axis
            return out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(spec)


#: Grau der Datenmarken unter einem focus-Profil, wenn der Aufrufer keines gibt: 3,4:1 auf Weiß (WCAG 1.4.11).
FOCUS_GREY = "#8C8C8C"
KEY_PARAM = "kernaussage"
KEY_VALUES = "kernaussage_werte"
KEY_DIM = 0.25


def _mark_kind(node: dict) -> "str | None":
    m = node.get("mark")
    return m if isinstance(m, str) else (m or {}).get("type") if isinstance(m, dict) else None


def with_focus(spec: dict, grey: str) -> dict:
    """Profil mit `focus` (story): jede Datenmarke grau (Farben aus dem Template, ob fest oder als Bedingung
    der Bewertung). Textmarken behalten ihre Farbe — Beschriftung trägt Textfarbe, nie Serienfarbe. Feldbasierte
    Farbskalen (Serien mit Legende) bleiben: ihre Unterscheidung trägt Information. Die Akzentfarbe vergibt
    erst die Kernaussage (with_highlight mit accent)."""
    hexa = re.compile(r"^#[0-9a-fA-F]{6}$")

    def grey_of(v):
        return grey if isinstance(v, str) and hexa.match(v) else v

    def channel(enc_val):
        if not isinstance(enc_val, dict) or "field" in enc_val:
            return enc_val
        out = {k: grey_of(v) for k, v in enc_val.items()}
        if "condition" in enc_val:
            conds = enc_val["condition"] if isinstance(enc_val["condition"], list) else [enc_val["condition"]]
            fixed = [{**c, "value": grey_of(c.get("value"))} if isinstance(c, dict) else c for c in conds]
            out["condition"] = fixed if isinstance(enc_val["condition"], list) else fixed[0]
        return out

    def walk(node):
        if isinstance(node, dict):
            out = {k: walk(v) for k, v in node.items() if k != "encoding"}
            if "encoding" in node:
                out["encoding"] = node["encoding"]
            if "mark" in out and _mark_kind(out) != "text":
                if isinstance(out["mark"], dict):
                    out["mark"] = {k: (grey_of(v) if k in ("color", "fill", "stroke") else v)
                                   for k, v in out["mark"].items()}
                enc = dict(out.get("encoding") or {})
                for ch in ("color", "fill", "stroke"):
                    if ch in enc:
                        enc[ch] = channel(enc[ch])
                if enc:
                    out["encoding"] = enc
            return out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(spec)


def with_highlight(spec: dict, field: str, values: "list | None" = None, temporal: bool = False,
                   accent: "str | None" = None) -> dict:
    """Kernaussage hervorheben (D-631 Nachtrag, feat-109): zwei Vega-Parameter, `kernaussage` (an/aus,
    Standard aus) und `kernaussage_werte` (die Treffer). Gedämpft wird jede Marke, deren Zeile `field`
    trägt und nicht zu den Treffern gehört; Marken ohne das Feld (Referenzlinie, Zielwert) bleiben
    unberührt, die Restzeile ist kein Treffer. Die Treffer sind ein Parameter, keine Konstante im Test:
    die Oberfläche rechnet die Aussage auf der gefilterten Tabelle neu (key_message.ts) und setzt nur die
    Werte — die Spec bleibt eine. Zeitwerte als Zeitpunkt (ms, UTC), weil Vega-Lite Zeitfelder zu Datum
    parst (`key_message.highlight_keys`).

    `accent` (Profil mit focus, story): statt die übrigen Marken zu dämpfen, bekommen die Treffer die
    Akzentfarbe; Textmarken bleiben in Textfarbe."""
    probe = f"time(datum[{json.dumps(field)}])" if temporal else f"datum[{json.dumps(field)}]"
    hit = f"{KEY_PARAM} && isValid(datum[{json.dumps(field)}]) && indexof({KEY_VALUES}, {probe}) >= 0"
    test = (f"{KEY_PARAM} && isValid(datum[{json.dumps(field)}]) && indexof({KEY_VALUES}, {probe}) < 0")
    dim = {"test": test, "value": KEY_DIM}

    def accent_unit(node: dict) -> dict:
        # Nur diskrete Marken: eine Linie, Fläche oder Hilfslinie ist eine Marke über alle Zeilen und würde
        # ganz akzentfarben (gemessen 01.10.2026: beide Linien und die Hover-Regel); Text bleibt Textfarbe.
        if _mark_kind(node) in ("text", "line", "area", "trail", "rule"):
            return node
        enc = dict(node.get("encoding") or {})
        cond = {"test": hit, "value": accent}
        old = enc.get("color")
        base = (node["mark"].get("color") if isinstance(node.get("mark"), dict) else None)
        if isinstance(old, dict) and "condition" in old:
            conds = old["condition"] if isinstance(old["condition"], list) else [old["condition"]]
            enc["color"] = {**old, "condition": [cond, *conds]}
        elif isinstance(old, dict):
            enc["color"] = {"condition": cond, **old}
        elif base:
            enc["color"] = {"condition": cond, "value": base}
        else:
            return node
        return {**node, "encoding": enc}

    def mark_unit(node: dict) -> dict:
        if accent:
            return accent_unit(node)
        enc = dict(node.get("encoding") or {})
        old = enc.get("opacity")
        if isinstance(old, dict) and "condition" in old:
            conds = old["condition"] if isinstance(old["condition"], list) else [old["condition"]]
            enc["opacity"] = {**old, "condition": [dim, *conds]}
        elif isinstance(old, dict):
            enc["opacity"] = {"condition": dim, **old}
        else:
            enc["opacity"] = {"condition": dim, "value": 1}
        return {**node, "encoding": enc}

    def walk(node):
        if isinstance(node, dict):
            out = {k: walk(v) for k, v in node.items() if k not in ("encoding",)}
            if "encoding" in node:
                out["encoding"] = node["encoding"]
            return mark_unit(out) if "mark" in out else out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    from key_message import highlight_keys  # gleiche Umrechnung wie die Oberfläche (eine Stelle)

    keys = highlight_keys({"values": values or [], "temporal": temporal})
    out = walk(spec)
    out["params"] = [p for p in out.get("params") or [] if p.get("name") not in (KEY_PARAM, KEY_VALUES)] + [
        {"name": KEY_PARAM, "value": False}, {"name": KEY_VALUES, "value": keys}]
    return out


#: Number and date formats per reader language (d3 locale). German is the profiles' own `vegalite_config.locale`;
#: English (en-GB) replaces it when the caller passes params `lang: "en"` (Freelancing L1, 01.10.2026: the Cockpit in
#: English drew "27,9" because the German locale was fixed in the config).
LOCALES: dict = {
    "en": {
        "number": {"decimal": ".", "thousands": ",", "grouping": [3], "currency": ["€", ""]},
        "time": {
            "dateTime": "%A, %e %B %Y, %X", "date": "%d/%m/%Y", "time": "%H:%M:%S", "periods": ["AM", "PM"],
            "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "shortDays": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                       "October", "November", "December"],
            "shortMonths": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        },
    },
}


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
        eff.update({k: str(v) for k, v in given.items()
                    if k not in ("top_n", "rest", "rest_label", "time_format", "time_ticks", "highlight", "accent",
                                  "focus_grey", "lang")})
        if (entry.get("encoding") or {}).get("order") == "worst_first" and "worst_first" not in given:
            # worst first: for a lower-is-better measure the worst value is the highest (A-31 R7)
            eff["worst_first"] = "descending" if float(eff.get("polarity", 1)) < 0 else "ascending"
        spec = json.loads(fill(real["template"], eff))
        if missing:
            spec = _drop_missing_values(spec, idiom, missing)
        limit = (entry.get("params") or {}).get("top_n")
        if bindings and isinstance(limit, dict) and limit.get("role") == "limit":
            # real data always gets the limit the idiom declares; the caller may lower or raise it
            spec = with_top_n(spec, idiom, eff, int(given.get("top_n", limit.get("default", 20))),
                              str(given.get("rest", "none")), str(given.get("rest_label", REST_LABEL)))
    else:
        spec = json.loads(render(idiom, "deneb_vegalite", notation)[0])
        eff = dict(_effective_params(load_entry(idiom), notation))
    spec = with_tooltips(spec, idiom, eff)
    if params and params.get("time_format"):
        spec = with_time_axis(spec, str(params["time_format"]), params.get("time_ticks"))
    if profile_def(profile).get("focus"):
        # story: Daten grau; das Grau kommt vom Aufrufer (Brand-Tokens, Klasse C), sonst ein Grau mit 3,4:1 auf Weiß
        spec = with_focus(spec, str((params or {}).get("focus_grey") or FOCUS_GREY))
    if params and params.get("highlight"):
        h = params["highlight"]
        accent = params.get("accent") if profile_def(profile).get("focus") else None
        spec = with_highlight(spec, h["field"], list(h.get("values") or []), bool(h.get("temporal")), accent)
    config = vegalite_config(profile)
    lang = str((params or {}).get("lang") or "de")
    if lang != "de":
        if lang not in LOCALES:
            raise KeyError(f"unknown lang '{lang}' (de, {', '.join(LOCALES)})")
        config = {**config, "locale": LOCALES[lang]}
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
