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


def _field_covering_sample(rows: int = 3) -> list[dict]:
    """A deterministic sample that carries every ``"field": "X"`` any Deneb golden references, so a
    data-less template (which binds its data at report time) can still rasterize here. Categorical
    fields get distinct labels; numeric fields get varied numbers — enough to draw, not to be
    meaningful."""
    import re

    fields: set[str] = set()
    for gp in GOLDEN.glob("*.deneb_vegalite*.json"):
        fields.update(re.findall(r'"field"\s*:\s*"([^"]+)"', gp.read_text(encoding="utf-8")))
    cat_hint = ("unit", "cat", "region", "name", "label", "group", "series", "driver", "part")
    date_hint = ("date", "period", "month")
    labels = ["A", "B", "C", "D", "E"]
    nums = [10.0, 41.0, 52.0, 33.0, 27.0]
    sample = []
    for i in range(rows):
        row = {}
        for fn in sorted(fields):
            fl = fn.lower()
            if any(h in fl for h in date_hint):
                row[fn] = f"2025-0{i + 1}"
            elif any(h in fl for h in cat_hint):
                row[fn] = labels[i % len(labels)]
            else:
                row[fn] = nums[i % len(nums)]
        sample.append(row)
    return sample


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
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, out = argv[0], Path(argv[1])
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
