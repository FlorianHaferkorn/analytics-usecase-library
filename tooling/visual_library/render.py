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

CLI:
    py -3 tooling/visual_library/render.py write <idiom>     # (re)freeze goldens
    py -3 tooling/visual_library/render.py show  <idiom> <tool>
"""
from __future__ import annotations

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


def load_entry(idiom: str) -> dict:
    """Load and lightly validate an idiom entry against the required schema keys."""
    path = LIB / f"{idiom}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = yaml.safe_load((LIB / "_schema.yaml").read_text(encoding="utf-8"))
    missing = [k for k in schema["required_keys"] if k not in data]
    if missing:
        raise ValueError(f"{idiom}.yaml missing required keys: {missing}")
    return data


def _registry() -> dict:
    """The notation-profile registry (the second axis). See _notation_profiles.yaml."""
    return yaml.safe_load(NOTATION.read_text(encoding="utf-8"))


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


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "write":
        for p in write_goldens(sys.argv[2]):
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
