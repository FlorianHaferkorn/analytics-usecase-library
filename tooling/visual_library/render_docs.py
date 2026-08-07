"""render_docs.py — generate the human docs FROM the Visual Library (closes the SoT loop).

The library YAML is the single source of truth. This renders two deterministic outputs:
  * Part D markdown  -> pasted into the design spec (governed catalog, never hand-edited)
  * an HTML artifact -> the shareable reference (chooser + per-idiom metadata + code/tool)

Both are pure functions of the library files (index.yaml + <idiom>.yaml + golden/*), so
re-running produces identical bytes. golden-frozen in tests/golden_docs/ and asserted by
test_visual_library.py::test_docs_render_matches_golden.

CLI:
    py -3 tooling/visual_library/render_docs.py md    > Part_D.md
    py -3 tooling/visual_library/render_docs.py html  > library.html
    py -3 tooling/visual_library/render_docs.py write        # write both into out/
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

LIB = render.LIB
REPO_ROOT = render.REPO_ROOT
SCHEMA = yaml.safe_load((LIB / "_schema.yaml").read_text(encoding="utf-8"))
TOOL_LABEL = {
    "powerbi_native": "Power BI · native",
    "powerbi_svg_dax": "Power BI · SVG-DAX",
    "deneb_vegalite": "Deneb / Vega-Lite",
    "web_recharts": "Web · Recharts",
}
EXT_LANG = {"json": "json", "dax": "dax", "jsx": "jsx"}


def _index() -> dict:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))


def _implemented() -> "list[str]":
    return _index()["implemented"]


def _golden_code(idiom: str, tool: str, profile: "str | None" = None) -> "tuple[str, str]":
    """The frozen output for a runnable idiom x tool x profile (from golden/)."""
    entry = render.load_entry(idiom)
    real = render._realization(entry, tool, profile or render.default_profile())
    ext = real["ext"]
    return render.golden_path(idiom, tool, ext, profile).read_text(encoding="utf-8"), ext


def _nondefault_profiles(idiom: str) -> "list[str]":
    """Notation profiles an idiom opts into beyond house_default (e.g. `ibcs`)."""
    dp = render.default_profile()
    return [p for p in render.profiles(idiom) if p != dp]


# ---------------------------------------------------------------- markdown (Part D)

def render_part_d() -> str:
    idx = _index()
    out: "list[str]" = []
    out.append("## Part D — the visual idiom catalog")
    out.append("")
    out.append("> **Generated** from `core/templates/page_templates/visual_library/` — do not hand-edit; "
               "run `tooling/visual_library/render_docs.py`. The library is the single source of truth; "
               "the runnable code per tool lives in `<idiom>.yaml` and is byte-for-byte frozen in `golden/`.")
    out.append("")
    out.append("**Encoding rule (governed).** Magnitude → length/position (rank 1–3), never the colour of a "
               "number (rank 9–10); direction → colour **and** sign; size is the only highlight (`cookbook.md`).")
    out.append("")
    out.append("### D.0 Which visual, when — the chooser")
    out.append("")
    out.append("| Purpose | Question | Best idiom | Zone | Candidates |")
    out.append("|---|---|---|---|---|")
    for pid, p in idx["purposes"].items():
        zone = p["zone"] if isinstance(p["zone"], str) else " / ".join(p["zone"])
        cands = " · ".join(f"`{c}`" for c in p["candidates"])
        out.append(f"| **{pid}** | {p['question']} | `{p['best']}` | {zone} | {cands} |")
    out.append("")
    out.append(f"**Deny (never emit):** {' · '.join('`'+d+'`' for d in idx['deny'])}.")
    out.append("")
    out.append("**Situational / out:** `sankey` and `decomposition_tree` are situational "
               "[`Visual_Whitelist.md`](../../../../../core/templates/page_templates/governance/Visual_Whitelist.md) "
               "extensions (flow-structure only / Detail drill, one measure); `powerbi_smart_narrative` is out for "
               "Power BI (templated / unreliable) and kept other-tools only.")
    out.append("")
    out.append("**Placement (unified with §A.8 layout).** 3s Pulse → `kpi_card` (deviation / bullet / hero); "
               "30s Analysis → `line` → `waterfall_pvm` → `bar_ranking` → `area_stacked` / `scatter`; "
               "300s Detail → `matrix_evidence` · `decomposition_tree` · `sankey`. "
               "Rule: question → idiom → zone → composition.")
    out.append("")
    out.append("### Idioms")
    out.append("")
    for iid in _implemented():
        e = render.load_entry(iid)
        zone = " / ".join(e["zone"]) if isinstance(e["zone"], list) else str(e["zone"])
        out.append(f"#### `{iid}` — {e['name']}")
        out.append(f"- **Purpose:** {', '.join(e['purpose'])} · **zone:** {zone}"
                   + (f" · **best form for:** `{e['best_form_for']}`" if e.get("best_form_for") else ""))
        out.append(f"- **Avoid:** {', '.join(e['anti_patterns'])}")
        tool_bits = []
        for tool in SCHEMA["tools"]:
            r = e["realizations"][tool]
            if r.get("applicable", True) and "template" in r:
                tool_bits.append(f"{TOOL_LABEL[tool]} ✓")
            else:
                tool_bits.append(f"{TOOL_LABEL[tool]} n/a ({r['reason']} → {r['use']})")
        out.append("- **Tools:** " + " · ".join(tool_bits))
        nd = _nondefault_profiles(iid)
        if nd:
            out.append(f"- **Notation profiles:** `{render.default_profile()}` · "
                       + " · ".join(f"`{p}`" for p in nd)
                       + " — the same idiom in another convention (see `_notation_profiles.yaml`)")
        out.append(f"- **Code:** `visual_library/{iid}.yaml` (+ `golden/{iid}.*`)")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- html artifact

_CSS = """
:root{--bg:#EBEEF2;--surface:#fff;--surface2:#F6F8FB;--ink:#18202A;--ink2:#586472;--line:#E1E7EE;--accent:#0078D4;--pos:#107C10;--neg:#A4262C;--sans:"Segoe UI",system-ui,sans-serif;--mono:"Cascadia Code",Consolas,ui-monospace,monospace;--r:14px;--sh:0 1px 2px rgba(20,30,45,.06),0 10px 26px -14px rgba(20,30,45,.16)}
@media(prefers-color-scheme:dark){:root{--bg:#0D1116;--surface:#161C23;--surface2:#1C232B;--ink:#E9EFF5;--ink2:#98A6B3;--line:#26313B;--accent:#3AA0EA;--pos:#3FB950;--neg:#F17A78;--sh:0 1px 2px rgba(0,0,0,.4),0 12px 32px -16px rgba(0,0,0,.6)}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55}
.wrap{max-width:1040px;margin:0 auto;padding:56px 28px 100px}
.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 12px}
h1{font-size:38px;line-height:1.06;margin:0 0 14px;font-weight:680;letter-spacing:-.02em}
.lede{font-size:19px;color:var(--ink2);margin:0;max-width:64ch}
h2{font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);margin:52px 0 16px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
th{text-align:left;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--ink2);padding:11px 13px;border-bottom:1px solid var(--line)}
td{padding:10px 13px;border-bottom:1px solid var(--line);color:var(--ink2);vertical-align:top}
td b{color:var(--ink)}tr:last-child td{border-bottom:none}
.idiom{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--sh);padding:20px 22px;margin:14px 0}
.idiom h3{margin:0 0 4px;font-size:18px;font-weight:660}.idiom h3 code{font-size:14px;color:var(--accent);background:none;padding:0}
.meta{font-size:13px;color:var(--ink2);margin:0 0 12px}.meta b{color:var(--ink)}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.b{font-family:var(--mono);font-size:11px;padding:3px 8px;border-radius:6px;border:1px solid}
.b.ok{color:var(--pos);border-color:var(--pos)}.b.na{color:var(--ink2);border-color:var(--line)}
details{border-top:1px solid var(--line);padding-top:10px;margin-top:8px}summary{cursor:pointer;font-family:var(--mono);font-size:11.5px;color:var(--accent)}
pre{overflow-x:auto;background:var(--surface2);border:1px solid var(--line);border-radius:8px;padding:12px 14px;font-family:var(--mono);font-size:11.5px;line-height:1.55;color:var(--ink);margin:8px 0 0}
code{font-family:var(--mono)}.foot{margin-top:60px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink2);font-size:12.5px}
"""


def _html_idiom(iid: str) -> str:
    e = render.load_entry(iid)
    zone = " / ".join(e["zone"]) if isinstance(e["zone"], list) else str(e["zone"])
    parts = [f'<div class="idiom"><h3>{_esc(e["name"])} · <code>{iid}</code></h3>']
    best = f' · best form for <b>{_esc(e["best_form_for"])}</b>' if e.get("best_form_for") else ""
    parts.append(f'<p class="meta"><b>Purpose:</b> {_esc(", ".join(e["purpose"]))} · '
                 f'<b>zone:</b> {_esc(zone)}{best}<br><b>Avoid:</b> {_esc(", ".join(e["anti_patterns"]))}</p>')
    if e.get("preview_svg"):
        parts.append(f'<div style="max-width:360px;margin:0 0 12px">{e["preview_svg"]}</div>')
    parts.append('<div class="badges">')
    for tool in SCHEMA["tools"]:
        r = e["realizations"][tool]
        ok = r.get("applicable", True) and "template" in r
        parts.append(f'<span class="b {"ok" if ok else "na"}">{_esc(TOOL_LABEL[tool])} {"✓" if ok else "n/a"}</span>')
    parts.append('</div>')
    for tool in render.tools(iid):
        code, ext = _golden_code(iid, tool)
        parts.append(f'<details><summary>{_esc(TOOL_LABEL[tool])} · {ext}</summary>'
                     f'<pre>{_esc(code)}</pre></details>')
    for profile in _nondefault_profiles(iid):
        parts.append(f'<p class="meta" style="margin-top:12px"><b>Notation profile · {_esc(profile)}</b> — '
                     f'the same idiom in the {_esc(profile)} convention (see <code>_notation_profiles.yaml</code>)</p>')
        for tool in render.tools(iid, profile):
            code, ext = _golden_code(iid, tool, profile)
            parts.append(f'<details><summary>{_esc(TOOL_LABEL[tool])} · {_esc(profile)} · {ext}</summary>'
                         f'<pre>{_esc(code)}</pre></details>')
    for tool in SCHEMA["tools"]:
        r = e["realizations"][tool]
        if not (r.get("applicable", True) and "template" in r):
            parts.append(f'<p class="meta"><b>{_esc(TOOL_LABEL[tool])} n/a:</b> {_esc(r["reason"])} → '
                         f'<b>{_esc(r["use"])}</b></p>')
    parts.append('</div>')
    return "".join(parts)


def _esc(s) -> str:
    return html.escape(str(s))


def render_artifact_html() -> str:
    idx = _index()
    rows = []
    for pid, p in idx["purposes"].items():
        zone = p["zone"] if isinstance(p["zone"], str) else " / ".join(p["zone"])
        cands = " · ".join(f"<code>{_esc(c)}</code>" for c in p["candidates"])
        rows.append(f"<tr><td><b>{_esc(pid)}</b></td><td>{_esc(p['question'])}</td>"
                    f"<td><code>{_esc(p['best'])}</code></td><td>{_esc(zone)}</td><td>{cands}</td></tr>")
    idioms_html = "".join(_html_idiom(i) for i in _implemented())
    return (
        f'<title>ALUCA · Visual Library (generated)</title>\n<style>{_CSS}</style>\n'
        f'<div class="wrap">\n'
        f'<p class="eyebrow">ALUCA · Report Design System · generated from the library</p>\n'
        f'<h1>Visual Library — the deterministic reference.</h1>\n'
        f'<p class="lede">Generated from <code>core/templates/page_templates/visual_library/</code> — '
        f'each idiom with runnable, byte-for-byte-frozen code per tool. The chooser maps a question to its '
        f'best idiom; every entry is reproducible.</p>\n'
        f'<h2>The chooser — which visual, when</h2>\n'
        f'<table><thead><tr><th>Purpose</th><th>Question</th><th>Best</th><th>Zone</th><th>Candidates</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>\n'
        f'<h2>Idioms ({len(_implemented())})</h2>\n{idioms_html}\n'
        f'<p class="foot">Deny: {" · ".join("<code>"+_esc(d)+"</code>" for d in idx["deny"])}. '
        f'Generated by <code>render_docs.py</code>; governed by <code>pbi-design/references/charts.md</code> + '
        f'<code>cookbook.md</code>. Determinism frozen in <code>golden/</code>.</p>\n</div>\n'
    )


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "md":
        print(render_part_d(), end="")
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "html":
        print(render_artifact_html(), end="")
        return 0
    if len(sys.argv) >= 2 and sys.argv[1] == "write":
        (LIB.parent.parent.parent.parent / "tooling" / "visual_library" / "out").mkdir(parents=True, exist_ok=True)
        outdir = REPO_ROOT / "tooling" / "visual_library" / "out"
        (outdir / "Part_D.generated.md").write_text(render_part_d(), encoding="utf-8", newline="\n")
        (outdir / "library.generated.html").write_text(render_artifact_html(), encoding="utf-8", newline="\n")
        print("wrote out/Part_D.generated.md + out/library.generated.html")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
