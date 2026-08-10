"""Live-render acceptance for the Visual Library — take idioms past determinism to actual pixels.

The golden tests prove each idiom reproduces byte-for-byte and (for Deneb) COMPILES. This module
goes one step further per tool track and produces / verifies a real rendered artifact:

- deneb_vegalite : rasterized to PNG headlessly via vl-convert (a genuine render, not a compile).
                   Un-gated — runs anywhere vl-convert is installed. This is what caught the
                   lollipop x/x2 bug that schema-validation missed.
- powerbi_native : materialized as a visual.json fragment ready to drop into a PBIR page — the
                   Desktop load itself stays Desktop-gated (see CHECKLIST.md).
- powerbi_svg_dax: the governed DAX is packaged + engine-validated in
                   products/fabric/powerbi/tooling/dax_udf/validate/acceptance.dax (Desktop-gated).
- web_recharts   : materialized as a self-contained HTML harness; the React/Recharts render stays
                   browser-gated (Recharts is not vendored in studio/node_modules).

CLI:
    render_acceptance.py png <out_dir>          # rasterize every Deneb golden to PNG (real render)
    render_acceptance.py materialize <out_dir>  # write one runnable artifact per tool + PNGs
    render_acceptance.py matrix                  # re-derive + freeze validation_matrix.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tooling" / "visual_library"))
import render  # noqa: E402

LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"
GOLDEN = LIB / "golden"


def _implemented() -> list[str]:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8")).get("implemented", [])


# One representative idiom per tool track for the end-to-end materialization.
REPRESENTATIVE = {
    "deneb_vegalite": "waterfall_pvm",
    "powerbi_native": "bar_ranking",
    "powerbi_svg_dax": "deviation_bar",
    "web_recharts": "line",
}


_CAT_HINT = ("unit", "cat", "region", "name", "label", "group", "series", "driver", "part")
_DATE_HINT = ("date", "period", "month")


def _deneb_field_names() -> list[str]:
    """Every ``"field": "X"`` any Deneb golden references."""
    import re

    fields: set[str] = set()
    for gp in GOLDEN.glob("*.deneb_vegalite*.json"):
        fields.update(re.findall(r'"field"\s*:\s*"([^"]+)"', gp.read_text(encoding="utf-8")))
    return sorted(fields)


def _rows(n: int, nums: list[float]) -> list[dict]:
    """n rows carrying every Deneb field; categorical/date fields get distinct labels, numeric
    fields cycle through ``nums`` — enough to draw, not to be meaningful."""
    labels = "ABCDEFGH"
    fields = _deneb_field_names()
    out = []
    for i in range(n):
        row = {}
        for fn in fields:
            fl = fn.lower()
            if any(h in fl for h in _DATE_HINT):
                row[fn] = f"2025-{(i % 12) + 1:02d}"
            elif any(h in fl for h in _CAT_HINT):
                row[fn] = labels[i % len(labels)]
            else:
                row[fn] = nums[i % len(nums)]
        out.append(row)
    return out


# Data scenarios the Deneb track is proven against — "does it still render when the data varies?"
SCENARIOS: dict[str, list[dict]] = {
    "typical": _rows(3, [10.0, 41.0, 52.0]),
    "negatives": _rows(3, [-18.0, 7.0, -3.0]),
    "single_category": _rows(1, [42.0]),
    "many_categories": _rows(8, [5, 12, 19, 26, 33, 40, 47, 54]),
    "extremes": _rows(4, [0.0, 0.001, 1e6, -1e6]),
}


def _field_covering_sample(rows: int = 3) -> list[dict]:
    """The default (typical) data sample used by the plain render helpers."""
    return _rows(rows, [10.0, 41.0, 52.0, 33.0, 27.0])


def _sized_with_data(spec: dict, sample: list[dict]) -> dict:
    """Bind the sample and force a positive canvas size (library templates are data-less and often
    size to their Deneb container) so the spec can rasterize headlessly."""
    spec = json.loads(json.dumps(spec))  # deep copy
    spec["data"] = {"values": sample}
    for dim in ("width", "height"):
        v = spec.get(dim)
        if not isinstance(v, (int, float)) or v <= 0:
            spec[dim] = 320 if dim == "width" else 200
    return spec


def render_deneb_png(idiom: str, profile: str | None = None) -> bytes:
    """Rasterize one Deneb golden to PNG. Raises ImportError if vl-convert is absent."""
    import vl_convert as vlc  # noqa: PLC0415 — optional dep, imported on use

    out, _ext = render.render(idiom, "deneb_vegalite", profile)
    spec = _sized_with_data(json.loads(out), _field_covering_sample())
    return vlc.vegalite_to_png(spec, scale=1)


def render_deneb_scenarios(idiom: str, profile: str | None = None) -> dict[str, bool]:
    """Render one Deneb realization under every SCENARIO. Returns {scenario: rendered?} where
    'rendered' means a non-trivial (>1 KB) PNG — proof the spec draws when the data varies."""
    import vl_convert as vlc  # noqa: PLC0415

    out, _ext = render.render(idiom, "deneb_vegalite", profile)
    base = json.loads(out)
    result: dict[str, bool] = {}
    for name, rows in SCENARIOS.items():
        try:
            png = vlc.vegalite_to_png(_sized_with_data(base, rows), scale=1)
            result[name] = len(png) > 1000
        except Exception:  # noqa: BLE001 — a scenario that can't render is a False, not a crash
            result[name] = False
    return result


# --------------------------------------------------------------------------- #
# Validation matrix — what is PROVEN per idiom x tool, and what stays gated.  #
# --------------------------------------------------------------------------- #

MATRIX_PATH = Path(__file__).resolve().parent / "validation_matrix.json"

# Honest status vocabulary. Only Deneb can be rendered here (vl-convert); the other three
# tracks are determinism + structure verified, but their live render is runtime-gated.
_TOOL_LIVE_GATE = {
    "powerbi_native": "Power BI Desktop load",
    "powerbi_svg_dax": "DAX engine (harness: products/fabric/powerbi/tooling/dax_udf/validate/acceptance.dax)",
    "web_recharts": "browser / React runtime",
}


def compute_validation_matrix() -> dict:
    """Derive the matrix from reality: render every Deneb realization across all SCENARIOS
    (needs vl-convert); mark the other tracks 'structural' (proven deterministic + structurally
    sound) with their live gate, or 'n/a' where the idiom doesn't realize that tool."""
    dp = render.default_profile()
    idioms: dict[str, dict] = {}
    for idiom in _implemented():
        entry = render.load_entry(idiom)
        tools: dict[str, dict] = {}
        for tool in ("powerbi_native", "powerbi_svg_dax", "deneb_vegalite", "web_recharts"):
            realization = entry["realizations"].get(tool, {})
            if not realization.get("applicable", True):
                tools[tool] = {"status": "n/a", "reason": realization.get("reason", "")}
                continue
            if tool == "deneb_vegalite":
                scen_ok: dict[str, bool] = {}
                for profile in render.profiles(idiom):
                    if "deneb_vegalite" not in render.tools(idiom, profile):
                        continue
                    for sc, ok in render_deneb_scenarios(idiom, None if profile == dp else profile).items():
                        scen_ok[sc] = scen_ok.get(sc, True) and ok
                passed = sorted(s for s, ok in scen_ok.items() if ok)
                tools[tool] = {
                    "status": "rendered" if len(passed) == len(SCENARIOS) else "partial",
                    "scenarios_ok": passed,
                    "scenarios_total": len(SCENARIOS),
                }
            else:
                tools[tool] = {"status": "structural", "live_gate": _TOOL_LIVE_GATE[tool]}
        idioms[idiom] = tools
    return {
        "scenarios": list(SCENARIOS),
        "legend": {
            "rendered": "headlessly rasterized to PNG under every data scenario (proven)",
            "structural": "byte-for-byte + structural gates pass; live render gated (not yet proven)",
            "n/a": "the idiom does not realize this tool (see reason)",
        },
        "idioms": idioms,
    }


def load_matrix() -> dict:
    """The frozen, committed matrix (read by the doc generator so its output is deterministic
    without vl-convert)."""
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def write_matrix() -> dict:
    m = compute_validation_matrix()
    MATRIX_PATH.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    return m


def render_all_deneb_pngs(out_dir: Path) -> list[tuple[str, int]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dp = render.default_profile()
    results = []
    for idiom in _implemented():
        for profile in render.profiles(idiom):
            if "deneb_vegalite" not in render.tools(idiom, profile):
                continue
            png = render_deneb_png(idiom, profile)
            suffix = "" if profile == dp else f".{profile}"
            name = f"{idiom}.deneb{suffix}.png"
            (out_dir / name).write_bytes(png)
            results.append((name, len(png)))
    return results


def _recharts_html(idiom: str) -> str:
    """A self-contained HTML harness for one Recharts idiom. Recharts/React are NOT vendored here, so
    this documents the exact mount; open it after `npm i react react-dom recharts` + a bundler, or in
    any sandbox that provides them. The browser render stays gated."""
    jsx, _ = render.render(idiom, "web_recharts")
    sample = json.dumps(_field_covering_sample(6), indent=2)
    return f"""<!doctype html>
<meta charset="utf-8">
<title>AlucaViz recharts acceptance — {idiom}</title>
<div id="root" style="width:520px;height:340px;font-family:Segoe UI,sans-serif"></div>
<!-- GATED: provide React, ReactDOM and Recharts (not vendored). Then transpile the JSX below. -->
<script type="text/babel" data-idiom="{idiom}">
  const data = {sample};
  function Chart() {{
    return (
{_indent(jsx, 6)}
    );
  }}
  // ReactDOM.createRoot(document.getElementById('root')).render(<Chart/>);
</script>
"""


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line if line else line for line in text.rstrip().splitlines())


def materialize(out_dir: Path) -> dict:
    """Write one runnable artifact per tool track + all Deneb PNGs. Returns a manifest dict."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"representative": REPRESENTATIVE, "artifacts": {}}

    # deneb — real PNGs for every idiom, plus the representative highlighted
    pngs = render_all_deneb_pngs(out_dir / "deneb_png")
    manifest["artifacts"]["deneb_vegalite"] = {
        "rendered_png": len(pngs), "dir": "deneb_png",
        "representative": f"{REPRESENTATIVE['deneb_vegalite']}.deneb.png",
    }

    # powerbi_native — a visual.json fragment ready for a PBIR page
    nat = REPRESENTATIVE["powerbi_native"]
    nat_out, _ = render.render(nat, "powerbi_native")
    (out_dir / f"{nat}.visual.json").write_text(nat_out, encoding="utf-8")
    manifest["artifacts"]["powerbi_native"] = {"file": f"{nat}.visual.json", "gated": "Desktop load"}

    # powerbi_svg_dax — the DAX, and a pointer to the engine-validated UDF harness
    dax = REPRESENTATIVE["powerbi_svg_dax"]
    dax_out, _ = render.render(dax, "powerbi_svg_dax")
    (out_dir / f"{dax}.dax").write_text(dax_out, encoding="utf-8")
    manifest["artifacts"]["powerbi_svg_dax"] = {
        "file": f"{dax}.dax",
        "engine_validation": "products/fabric/powerbi/tooling/dax_udf/validate/acceptance.dax",
        "gated": "DAX engine",
    }

    # web_recharts — a self-contained HTML harness (browser-gated)
    rc = REPRESENTATIVE["web_recharts"]
    (out_dir / f"{rc}.recharts.html").write_text(_recharts_html(rc), encoding="utf-8")
    manifest["artifacts"]["web_recharts"] = {"file": f"{rc}.recharts.html", "gated": "browser render"}

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "matrix":  # re-derive + freeze the validation matrix (needs vl-convert)
        m = write_matrix()
        for idiom, tools in m["idioms"].items():
            cells = " ".join(
                f"{t.split('_')[-1]}:{v['status']}"
                + (f"({len(v['scenarios_ok'])}/{v['scenarios_total']})" if v["status"] in ("rendered", "partial") else "")
                for t, v in tools.items()
            )
            print(f"{idiom:20s} {cells}")
        print(f"\nfrozen -> {MATRIX_PATH}")
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = Path(argv[1])
    if cmd == "png":
        results = render_all_deneb_pngs(out)
        for name, n in results:
            print(f"{name:45s} {n:>7d} bytes")
        print(f"\n{len(results)} Deneb goldens rendered to PNG -> {out}")
        return 0
    if cmd == "materialize":
        m = materialize(out)
        print(json.dumps(m, indent=2))
        return 0
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
