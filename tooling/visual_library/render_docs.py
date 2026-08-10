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
sys.path.insert(0, str(Path(__file__).resolve().parent / "acceptance"))
import render  # noqa: E402
import render_acceptance  # noqa: E402  (reads the frozen matrix — no vl-convert needed)

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
_VAL_TOOLS = ("powerbi_native", "powerbi_svg_dax", "deneb_vegalite", "web_recharts")


def _val_label(cell: dict) -> str:
    """Compact proof label for one idiom×tool from the frozen validation matrix."""
    s = cell.get("status")
    if s == "rendered":
        return f"rendered ✓ {len(cell['scenarios_ok'])}/{cell['scenarios_total']}"
    if s == "partial":
        return f"partial {len(cell['scenarios_ok'])}/{cell['scenarios_total']}"
    if s == "structural":
        return "structural · gated"
    return "—"


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
    out.append("### D.1 Validation status — what is proven, and what stays gated")
    out.append("")
    matrix = render_acceptance.load_matrix()
    out.append(f"> Evidence per idiom × tool. **Deneb** is proven by headless rasterization across "
               f"{len(matrix['scenarios'])} data scenarios ({', '.join('`'+s+'`' for s in matrix['scenarios'])}) — "
               "regenerate with `render_acceptance.py matrix`. The other three tracks are byte-for-byte + "
               "structurally gated; their **live render is runtime-gated** (Desktop / DAX engine / browser) "
               "and signed off via `acceptance/CHECKLIST.md`, so they read `structural · gated` — not yet proven.")
    out.append("")
    out.append("| Idiom | Power BI · native | Power BI · SVG-DAX | Deneb / Vega-Lite | Web · Recharts |")
    out.append("|---|---|---|---|---|")
    for iid in _implemented():
        cells = matrix["idioms"].get(iid, {})
        row = " | ".join(_val_label(cells.get(t, {})) for t in _VAL_TOOLS)
        out.append(f"| `{iid}` | {row} |")
    out.append("")
    out.append("**Legend.** `rendered ✓ n/5` = actually rasterized under n of 5 data scenarios · "
               "`structural · gated` = deterministic + structurally valid, live render not yet run · `—` = tool n/a.")
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
*{box-sizing:border-box}
:root{
  --bg:#EEF1F5;--surface:#FFFFFF;--surface2:#F4F7FA;--field:#FFFFFF;
  --ink:#101720;--ink2:#54606F;--ink3:#8A94A2;--line:#E3E8EE;--line2:#EDF1F5;
  --accent:#0A6ED1;--accent-ink:#FFFFFF;--accent-soft:rgba(10,110,209,.10);
  --pos:#147A3D;--pos-soft:rgba(20,122,61,.12);--warn:#B0740F;--warn-soft:rgba(176,116,15,.14);
  --sans:"Segoe UI Variable","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
  --mono:"Cascadia Code","Cascadia Mono",ui-monospace,Consolas,monospace;
  --r:16px;--r2:11px;--r3:8px;--maxw:1140px;
  --sh1:0 1px 2px rgba(16,23,32,.05),0 1px 1px rgba(16,23,32,.03);
  --sh2:0 4px 10px rgba(16,23,32,.06),0 18px 40px -20px rgba(16,23,32,.24);
  --nav:rgba(238,241,245,.78);
}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0B0F14;--surface:#141A21;--surface2:#0F151B;--field:#0F161D;
  --ink:#E9EFF6;--ink2:#9AA7B5;--ink3:#6B7787;--line:#242E39;--line2:#1A222B;
  --accent:#4DA3F0;--accent-ink:#07121C;--accent-soft:rgba(77,163,240,.14);
  --pos:#40B45F;--pos-soft:rgba(64,180,95,.16);--warn:#E2AB3E;--warn-soft:rgba(226,171,62,.16);
  --sh1:0 1px 2px rgba(0,0,0,.4);--sh2:0 6px 16px rgba(0,0,0,.42),0 20px 46px -20px rgba(0,0,0,.7);
  --nav:rgba(11,15,20,.72);
}}
:root[data-theme="dark"]{
  --bg:#0B0F14;--surface:#141A21;--surface2:#0F151B;--field:#0F161D;
  --ink:#E9EFF6;--ink2:#9AA7B5;--ink3:#6B7787;--line:#242E39;--line2:#1A222B;
  --accent:#4DA3F0;--accent-ink:#07121C;--accent-soft:rgba(77,163,240,.14);
  --pos:#40B45F;--pos-soft:rgba(64,180,95,.16);--warn:#E2AB3E;--warn-soft:rgba(226,171,62,.16);
  --sh1:0 1px 2px rgba(0,0,0,.4);--sh2:0 6px 16px rgba(0,0,0,.42),0 20px 46px -20px rgba(0,0,0,.7);
  --nav:rgba(11,15,20,.72);
}
html{scroll-behavior:smooth;scroll-padding-top:76px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased;font-feature-settings:"cv01","ss01"}
a{color:inherit;text-decoration:none}
code,.mono{font-family:var(--mono)}
::selection{background:var(--accent-soft)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}

/* topbar */
.nav{position:sticky;top:0;z-index:50;background:var(--nav);backdrop-filter:saturate(1.6) blur(14px);-webkit-backdrop-filter:saturate(1.6) blur(14px);border-bottom:1px solid var(--line)}
.nav-in{max-width:var(--maxw);margin:0 auto;padding:11px 24px;display:flex;align-items:center;gap:18px}
.brand{display:flex;align-items:center;gap:9px;font-weight:680;letter-spacing:-.01em;font-size:15px}
.brand .mk{width:22px;height:22px;border-radius:6px;display:grid;place-items:center;background:var(--accent);color:var(--accent-ink);font-size:13px;box-shadow:var(--sh1)}
.brand .sub{color:var(--ink3);font-weight:500}
.nav-links{display:flex;gap:2px;margin-left:6px}
.nav-links a{font-size:13.5px;color:var(--ink2);padding:7px 12px;border-radius:8px;font-weight:500;transition:color .15s,background .15s}
.nav-links a:hover{color:var(--ink);background:var(--surface2)}
.nav-links a.on{color:var(--accent);background:var(--accent-soft)}
.nav-tools{margin-left:auto;display:flex;align-items:center;gap:10px}
.search{position:relative;display:flex;align-items:center}
.search svg{position:absolute;left:11px;width:15px;height:15px;color:var(--ink3);pointer-events:none}
.search input{width:210px;max-width:40vw;font:inherit;font-size:13.5px;color:var(--ink);background:var(--field);border:1px solid var(--line);border-radius:10px;padding:8px 12px 8px 33px;transition:border .15s,box-shadow .15s}
.search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.iconbtn{width:36px;height:36px;display:grid;place-items:center;border:1px solid var(--line);background:var(--field);color:var(--ink2);border-radius:10px;cursor:pointer;transition:color .15s,border .15s}
.iconbtn:hover{color:var(--ink);border-color:var(--ink3)}
.iconbtn svg{width:17px;height:17px}

.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.eyebrow{font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:640;margin:0}

/* hero */
.hero{padding:74px 0 30px}
.hero h1{font-size:clamp(34px,6vw,60px);line-height:1.02;letter-spacing:-.028em;font-weight:720;margin:16px 0 0;max-width:16ch;text-wrap:balance}
.hero .lede{font-size:clamp(16px,2.1vw,20px);color:var(--ink2);margin:20px 0 0;max-width:60ch;line-height:1.5}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin:34px 0 0}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);padding:14px 18px;box-shadow:var(--sh1);min-width:104px}
.stat b{display:block;font-size:26px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1}
.stat span{display:block;font-size:11.5px;color:var(--ink3);margin-top:6px;letter-spacing:.02em}
.stat.pos{border-color:color-mix(in srgb,var(--pos) 40%,var(--line));background:var(--pos-soft)}
.stat.pos b{color:var(--pos)}
.strip{display:flex;gap:12px;overflow-x:auto;margin:34px -24px 0;padding:4px 24px 8px;scrollbar-width:thin}
.strip figure{margin:0;flex:0 0 auto;width:210px}
.tile{background:#fff;border:1px solid var(--line);border-radius:var(--r2);overflow:hidden;box-shadow:var(--sh1);aspect-ratio:340/150}
.tile svg{width:100%;height:100%;display:block}
.strip figcaption{font-family:var(--mono);font-size:11px;color:var(--ink3);margin-top:7px;padding-left:2px}

/* sections */
.section{padding:56px 0;border-top:1px solid var(--line)}
.section-head{margin:0 0 26px;max-width:64ch}
.section-head .k{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:640}
.section-head h2{font-size:clamp(23px,3.4vw,32px);letter-spacing:-.02em;font-weight:700;margin:9px 0 0}
.section-head p{color:var(--ink2);font-size:16px;margin:11px 0 0;line-height:1.5}
.count{font-size:.5em;font-weight:600;color:var(--ink3);font-variant-numeric:tabular-nums;vertical-align:middle;margin-left:8px;border:1px solid var(--line);border-radius:20px;padding:3px 10px}

/* chooser */
.chooser{display:grid;grid-template-columns:repeat(auto-fill,minmax(266px,1fr));gap:12px}
.purpose{text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);padding:17px 18px;cursor:pointer;font:inherit;color:inherit;box-shadow:var(--sh1);transition:transform .16s,box-shadow .16s,border-color .16s;display:flex;flex-direction:column;gap:11px}
.purpose:hover{transform:translateY(-2px);box-shadow:var(--sh2);border-color:color-mix(in srgb,var(--accent) 34%,var(--line))}
.purpose .q{font-size:14.5px;font-weight:600;color:var(--ink);line-height:1.35}
.purpose .r{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--ink3)}
.purpose .best{font-family:var(--mono);font-size:12px;color:var(--accent);background:var(--accent-soft);padding:2px 8px;border-radius:6px}
.purpose .zone{border:1px solid var(--line);border-radius:20px;padding:2px 9px;letter-spacing:.02em}

/* validation */
.valgrid{display:grid;grid-template-columns:1.15fr 1fr;gap:14px;margin:0 0 24px}
@media(max-width:720px){.valgrid{grid-template-columns:1fr}}
.vcard{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:20px 22px;box-shadow:var(--sh1)}
.vcard .big{font-size:34px;font-weight:720;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1}
.vcard.pos .big{color:var(--pos)}.vcard .sub{color:var(--ink2);font-size:14px;margin-top:9px;line-height:1.5}
.legend{display:flex;flex-direction:column;gap:11px;justify-content:center}
.legend .row{display:flex;gap:11px;align-items:flex-start;font-size:13px;color:var(--ink2)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);box-shadow:var(--sh1)}
table.val{width:100%;border-collapse:collapse;font-size:13px;min-width:560px}
table.val th{position:sticky;top:0;text-align:left;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink3);padding:12px 15px;background:var(--surface2);border-bottom:1px solid var(--line);white-space:nowrap}
table.val td{padding:11px 15px;border-bottom:1px solid var(--line2);vertical-align:middle}
table.val tr:last-child td{border-bottom:none}
table.val td:first-child{font-family:var(--mono);font-size:12.5px;color:var(--ink)}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;white-space:nowrap;border:1px solid transparent}
.pill::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;flex:0 0 auto}
.pill.rendered{color:var(--pos);background:var(--pos-soft)}
.pill.partial{color:var(--warn);background:var(--warn-soft)}
.pill.gate{color:var(--ink2);background:var(--surface2);border-color:var(--line)}
.pill.no{color:var(--ink3);background:transparent;border-color:var(--line2)}
.pill.no::before{opacity:.4}

/* idioms toolbar + grid */
.toolbar{display:flex;flex-wrap:wrap;gap:16px;align-items:center;margin:0 0 22px}
.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chips .lbl{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin-right:2px;font-weight:600}
.chip{font:inherit;font-size:12.5px;color:var(--ink2);background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:6px 13px;cursor:pointer;transition:color .14s,background .14s,border-color .14s}
.chip:hover{color:var(--ink);border-color:var(--ink3)}
.chip.on{color:var(--accent-ink);background:var(--accent);border-color:var(--accent)}
.pickbar{display:none;align-items:center;gap:10px;margin:0 0 18px;font-size:13.5px;color:var(--ink2)}
.pickbar.show{display:flex}
.pickbar b{color:var(--ink)}
.pickbar button{font:inherit;font-size:12.5px;color:var(--accent);background:var(--accent-soft);border:none;border-radius:8px;padding:6px 12px;cursor:pointer}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--sh1);padding:18px;display:flex;flex-direction:column;gap:14px;transition:box-shadow .18s,border-color .18s}
.card:hover{box-shadow:var(--sh2)}
.card.hide{display:none}
.card-top{display:flex;gap:14px;align-items:flex-start}
.thumb{flex:0 0 118px;width:118px;border:1px solid var(--line);border-radius:var(--r3);overflow:hidden;background:#fff;aspect-ratio:340/150;box-shadow:var(--sh1)}
.thumb svg{width:100%;height:100%;display:block}
.card h3{margin:0;font-size:16.5px;font-weight:660;letter-spacing:-.01em;display:flex;flex-wrap:wrap;align-items:baseline;gap:7px}
.card h3 code{font-size:12.5px;color:var(--accent);background:var(--accent-soft);padding:2px 7px;border-radius:6px;font-weight:600}
.card .purpose-line{font-size:12.5px;color:var(--ink3);margin:6px 0 0;line-height:1.4}
.card .zone-tag{color:var(--ink2)}
.status{display:flex;flex-wrap:wrap;gap:6px}
.avoid{font-size:12px;color:var(--ink3);margin:0;line-height:1.45}
.avoid b{color:var(--warn);font-weight:600;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;margin-right:6px}
.na{font-size:12px;color:var(--ink3);margin:0;line-height:1.5}.na b{color:var(--ink2)}

/* code viewer */
.code{border:1px solid var(--line);border-radius:var(--r2);overflow:hidden;background:var(--surface2)}
.tabbar{display:flex;gap:2px;padding:6px 6px 0;overflow-x:auto;border-bottom:1px solid var(--line);scrollbar-width:none}
.tabbar::-webkit-scrollbar{display:none}
.tab{position:relative;font:inherit;font-family:var(--mono);font-size:11.5px;color:var(--ink3);background:none;border:none;padding:9px 12px;cursor:pointer;white-space:nowrap;border-radius:7px 7px 0 0;transition:color .14s}
.tab:hover{color:var(--ink2)}
.tab[aria-selected="true"]{color:var(--accent)}
.tab[aria-selected="true"]::after{content:"";position:absolute;left:8px;right:8px;bottom:-1px;height:2px;background:var(--accent);border-radius:2px}
.panel{position:relative}
.panel[hidden]{display:none}
.copy{position:absolute;top:9px;right:9px;z-index:2;font:inherit;font-family:var(--mono);font-size:11px;color:var(--ink2);background:var(--surface);border:1px solid var(--line);border-radius:7px;padding:5px 10px;cursor:pointer;opacity:0;transition:opacity .15s,color .15s,border-color .15s}
.panel:hover .copy,.copy:focus-visible{opacity:1}
.copy:hover{color:var(--accent);border-color:var(--accent)}
.copy.done{color:var(--pos);border-color:var(--pos);opacity:1}
pre{overflow-x:auto;margin:0;padding:14px 16px;font-family:var(--mono);font-size:11.5px;line-height:1.6;color:var(--ink);max-height:340px}
pre code{color:inherit}

.empty{display:none;text-align:center;color:var(--ink3);font-size:15px;padding:50px 0}
.empty.show{display:block}
.foot{padding:44px 0 90px;color:var(--ink3);font-size:13px;line-height:1.6}
.foot b{color:var(--ink2)}
.totop{position:fixed;right:22px;bottom:22px;z-index:40;width:42px;height:42px;border-radius:50%;display:grid;place-items:center;background:var(--surface);color:var(--ink2);border:1px solid var(--line);box-shadow:var(--sh2);cursor:pointer;opacity:0;transform:translateY(8px);pointer-events:none;transition:opacity .2s,transform .2s,color .15s}
.totop.show{opacity:1;transform:none;pointer-events:auto}
.totop:hover{color:var(--accent)}.totop svg{width:18px;height:18px}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,14px);z-index:60;background:var(--ink);color:var(--bg);font-size:13px;font-weight:500;padding:10px 18px;border-radius:11px;box-shadow:var(--sh2);opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}
.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:640px){.nav-links{display:none}.card-top{flex-direction:column}.thumb{width:100%;flex-basis:auto}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
"""

_JS = """
(function(){
  var root=document.documentElement, $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  var state={q:"",zone:"",tool:"",pick:null};

  // theme toggle: system -> light -> dark -> system
  try{var saved=localStorage.getItem("vl-theme"); if(saved){root.setAttribute("data-theme",saved)}}catch(e){}
  var tbtn=$("#theme");
  if(tbtn) tbtn.addEventListener("click",function(){
    var cur=root.getAttribute("data-theme");
    var next=cur==="dark"?"light":(cur==="light"?"":"dark");
    if(next){root.setAttribute("data-theme",next)}else{root.removeAttribute("data-theme")}
    try{next?localStorage.setItem("vl-theme",next):localStorage.removeItem("vl-theme")}catch(e){}
  });

  // filtering
  var cardsEl=$("#cards"), cards=$$(".card"), countEl=$("#count"), emptyEl=$("#empty"), pickbar=$("#pickbar");
  function apply(){
    var q=state.q.trim().toLowerCase(), n=0;
    cards.forEach(function(c){
      var ok=true;
      if(state.pick){ok = state.pick.indexOf(c.getAttribute("data-id"))>=0}
      if(ok && state.zone) ok=(" "+c.getAttribute("data-zones")+" ").indexOf(" "+state.zone+" ")>=0;
      if(ok && state.tool) ok=(" "+c.getAttribute("data-tools")+" ").indexOf(" "+state.tool+" ")>=0;
      if(ok && q) ok=c.getAttribute("data-search").indexOf(q)>=0;
      c.classList.toggle("hide",!ok); if(ok)n++;
    });
    if(countEl)countEl.textContent=n;
    if(emptyEl)emptyEl.classList.toggle("show",n===0);
  }
  var qEl=$("#q"); if(qEl) qEl.addEventListener("input",function(){state.q=this.value;apply()});
  $$(".chips").forEach(function(group){
    var key=group.getAttribute("data-filter");
    group.addEventListener("click",function(e){
      var chip=e.target.closest(".chip"); if(!chip)return;
      $$(".chip",group).forEach(function(x){x.classList.remove("on")});
      chip.classList.add("on"); state[key]=chip.getAttribute("data-val")||""; apply();
    });
  });
  // purpose -> pick candidate idioms
  $$(".purpose").forEach(function(p){
    p.addEventListener("click",function(){
      state.pick=(p.getAttribute("data-cands")||"").split(",").filter(Boolean);
      if(pickbar){pickbar.classList.add("show"); var b=$("#pickq"); if(b)b.textContent=p.getAttribute("data-q")}
      apply();
      var t=document.getElementById("idioms"); if(t)t.scrollIntoView({behavior:"smooth"});
    });
  });
  var clr=$("#pickclear"); if(clr) clr.addEventListener("click",function(){state.pick=null; if(pickbar)pickbar.classList.remove("show"); apply()});

  // code tabs (delegated)
  document.addEventListener("click",function(e){
    var tab=e.target.closest(".tab"); if(!tab)return;
    var bar=tab.parentNode, code=bar.parentNode;
    $$(".tab",bar).forEach(function(t){t.setAttribute("aria-selected","false")});
    tab.setAttribute("aria-selected","true");
    $$(".panel",code).forEach(function(pn){pn.hidden = pn.id!==tab.getAttribute("data-panel")});
  });
  // copy
  var toast=$("#toast"), toastT;
  document.addEventListener("click",function(e){
    var btn=e.target.closest(".copy"); if(!btn)return;
    var pre=$("pre",btn.parentNode); if(!pre)return;
    var txt=pre.innerText;
    var done=function(){btn.classList.add("done");var o=btn.textContent;btn.textContent="Copied";
      if(toast){toast.classList.add("show");clearTimeout(toastT);toastT=setTimeout(function(){toast.classList.remove("show")},1400)}
      setTimeout(function(){btn.classList.remove("done");btn.textContent=o},1400);};
    try{navigator.clipboard.writeText(txt).then(done,function(){fallback(txt);done()})}catch(err){fallback(txt);done()}
  });
  function fallback(t){try{var ta=document.createElement("textarea");ta.value=t;document.body.appendChild(ta);ta.select();document.execCommand("copy");document.body.removeChild(ta)}catch(e){}}

  // scrollspy
  var links=$$(".nav-links a"), secs=links.map(function(a){return document.querySelector(a.getAttribute("href"))}).filter(Boolean);
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(en){
      if(en.isIntersecting){var id="#"+en.target.id; links.forEach(function(a){a.classList.toggle("on",a.getAttribute("href")===id)})}
    })},{rootMargin:"-45% 0px -50% 0px"});
    secs.forEach(function(s){io.observe(s)});
  }
  // back to top
  var top=$("#totop");
  if(top){window.addEventListener("scroll",function(){top.classList.toggle("show",window.scrollY>640)},{passive:true});
    top.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})});}
})();
"""


TOOL_SHORT = {
    "powerbi_native": "PBI native",
    "powerbi_svg_dax": "SVG-DAX",
    "deneb_vegalite": "Deneb",
    "web_recharts": "Recharts",
}
_STATUS_WORD = {"rendered": "proven", "partial": "partial", "structural": "gated"}


def _pill(tool: str, cell: dict) -> str:
    """A compact per-tool proof pill for an idiom card, coloured by validation status."""
    s = cell.get("status")
    cls = {"rendered": "rendered", "partial": "partial", "structural": "gate"}.get(s, "no")
    word = _STATUS_WORD.get(s, "n/a")
    if s == "rendered":
        word = f"proven {len(cell['scenarios_ok'])}/{cell['scenarios_total']}"
    return f'<span class="pill {cls}">{_esc(TOOL_SHORT[tool])} · {word}</span>'


def _html_idiom(iid: str, matrix: dict) -> str:
    e = render.load_entry(iid)
    zones = e["zone"] if isinstance(e["zone"], list) else [e["zone"]]
    cells = matrix["idioms"].get(iid, {})
    applicable = render.tools(iid)  # runnable tools, default profile
    search = " ".join([iid, e["name"], *e["purpose"], *zones, *e.get("anti_patterns", [])]).lower()

    p = []
    p.append(
        f'<article class="card" data-id="{_esc(iid)}" data-zones="{_esc(" ".join(zones))}" '
        f'data-tools="{_esc(" ".join(applicable))}" data-search="{_esc(search)}">'
    )
    # header: real preview + identity
    p.append('<div class="card-top">')
    p.append(f'<div class="thumb">{e["preview_svg"]}</div>' if e.get("preview_svg") else '<div class="thumb"></div>')
    best = f' · best for <b>{_esc(e["best_form_for"])}</b>' if e.get("best_form_for") else ""
    p.append('<div>')
    p.append(f'<h3>{_esc(e["name"])} <code>{_esc(iid)}</code></h3>')
    p.append(f'<p class="purpose-line">{_esc(", ".join(e["purpose"]))} '
             f'<span class="zone-tag">· {_esc(" / ".join(zones))}</span>{best}</p>')
    p.append('</div></div>')

    # proof pills (applicable tools only)
    if applicable:
        p.append('<div class="status">' + "".join(_pill(t, cells.get(t, {})) for t in SCHEMA["tools"]
                                                    if t in applicable) + '</div>')
    # avoid
    if e.get("anti_patterns"):
        p.append(f'<p class="avoid"><b>Avoid</b>{_esc(", ".join(e["anti_patterns"]))}</p>')

    # code viewer — tabs across tools (default profile) then non-default profiles
    variants = [(t, None) for t in applicable]
    for profile in _nondefault_profiles(iid):
        variants += [(t, profile) for t in render.tools(iid, profile)]
    if variants:
        tabs, panels = [], []
        for i, (tool, profile) in enumerate(variants):
            pid = f'{iid}-{tool}' + (f'-{profile}' if profile else '')
            label = TOOL_SHORT[tool] + (f' · {profile}' if profile else '')
            code, _ext = _golden_code(iid, tool, profile)
            sel = "true" if i == 0 else "false"
            tabs.append(f'<button class="tab" role="tab" aria-selected="{sel}" data-panel="{_esc(pid)}">{_esc(label)}</button>')
            panels.append(f'<div class="panel" id="{_esc(pid)}"{"" if i == 0 else " hidden"}>'
                          f'<button class="copy" type="button">Copy</button>'
                          f'<pre><code>{_esc(code)}</code></pre></div>')
        p.append('<div class="code"><div class="tabbar" role="tablist">' + "".join(tabs) + '</div>'
                 + "".join(panels) + '</div>')

    # not-applicable notes
    na = [t for t in SCHEMA["tools"] if not (e["realizations"][t].get("applicable", True) and "template" in e["realizations"][t])]
    if na:
        bits = []
        for t in na:
            r = e["realizations"][t]
            bits.append(f'<b>{_esc(TOOL_SHORT[t])}</b> n/a — {_esc(r["reason"])} → {_esc(r["use"])}')
        p.append('<p class="na">' + "<br>".join(bits) + '</p>')

    p.append('</article>')
    return "".join(p)


def _esc(s) -> str:
    return html.escape(str(s))


_ICON_SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>')
_ICON_THEME = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
               '<circle cx="12" cy="12" r="9"/>'
               '<path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none"/></svg>')
_ICON_UP = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>')
_BRAND_MK = ('<svg viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="8" width="3" height="7" rx="1"/>'
             '<rect x="6.5" y="4" width="3" height="11" rx="1"/><rect x="12" y="1" width="3" height="14" rx="1"/></svg>')


def _base_idiom(cand: str) -> str:
    """A chooser candidate like 'deviation_bar@ibcs' filters to its base idiom card."""
    return cand.split("@", 1)[0]


def render_artifact_html() -> str:
    idx = _index()
    matrix = render_acceptance.load_matrix()
    impl = _implemented()

    # hero stats
    deneb_proven = sum(1 for i in impl if matrix["idioms"].get(i, {}).get("deneb_vegalite", {}).get("status") == "rendered")
    deneb_appl = sum(1 for i in impl if matrix["idioms"].get(i, {}).get("deneb_vegalite", {}).get("status") in ("rendered", "partial"))
    n_scen = len(matrix["scenarios"])

    # preview strip — a curated set of real idiom thumbnails
    strip_ids = [i for i in ["deviation_bar", "line", "waterfall_pvm", "bar_ranking", "bullet", "scatter"] if i in impl]
    strip = "".join(
        f'<figure><div class="tile">{render.load_entry(i).get("preview_svg", "")}</div>'
        f'<figcaption>{_esc(i)}</figcaption></figure>' for i in strip_ids
    )

    # chooser — purpose cards
    purposes = []
    for pid, p in idx["purposes"].items():
        zone = p["zone"] if isinstance(p["zone"], str) else " / ".join(p["zone"])
        cands = ",".join(dict.fromkeys(_base_idiom(c) for c in p["candidates"]))  # base ids, order-preserving unique
        purposes.append(
            f'<button class="purpose" data-cands="{_esc(cands)}" data-q="{_esc(p["question"])}">'
            f'<span class="q">{_esc(p["question"])}</span>'
            f'<span class="r"><span class="best">{_esc(p["best"])}</span>'
            f'<span class="zone">{_esc(zone)}</span></span></button>'
        )

    # validation — summary + legend + per-idiom table with pills
    _cls = {"rendered": "rendered", "partial": "partial", "structural": "gate"}
    val_rows = []
    for iid in impl:
        cells = matrix["idioms"].get(iid, {})
        tds = "".join(
            f'<td><span class="pill {_cls.get(cells.get(t, {}).get("status"), "no")}">{_esc(_val_label(cells.get(t, {})))}</span></td>'
            for t in _VAL_TOOLS
        )
        val_rows.append(f'<tr><td>{_esc(iid)}</td>{tds}</tr>')
    scen = ", ".join(f"<code>{_esc(s)}</code>" for s in matrix["scenarios"])

    # zone chips
    zones_present = [z for z in ("pulse", "analysis", "detail")
                     if any(z in ((render.load_entry(i)["zone"]) if isinstance(render.load_entry(i)["zone"], list)
                            else [render.load_entry(i)["zone"]]) for i in impl)]
    zone_chips = '<span class="lbl">Zone</span><button class="chip on" data-val="">All</button>' + "".join(
        f'<button class="chip" data-val="{_esc(z)}">{_esc(z)}</button>' for z in zones_present)
    tool_chips = '<span class="lbl">Tool</span><button class="chip on" data-val="">All</button>' + "".join(
        f'<button class="chip" data-val="{_esc(t)}">{_esc(TOOL_SHORT[t])}</button>' for t in SCHEMA["tools"])

    idioms_html = "".join(_html_idiom(i, matrix) for i in impl)

    return (
        f'<title>ALUCA · Visual Library</title>\n<style>{_CSS}</style>\n'
        f'<header class="nav"><div class="nav-in">'
        f'<a class="brand" href="#top"><span class="mk">{_BRAND_MK}</span>ALUCA <span class="sub">Visual Library</span></a>'
        f'<nav class="nav-links"><a href="#chooser">Chooser</a><a href="#validation">Validation</a>'
        f'<a href="#idioms">Idioms</a></nav>'
        f'<div class="nav-tools"><label class="search">{_ICON_SEARCH}'
        f'<input id="q" type="search" placeholder="Search idioms…" aria-label="Search idioms" autocomplete="off"></label>'
        f'<button class="iconbtn" id="theme" type="button" aria-label="Toggle theme" title="Theme">{_ICON_THEME}</button>'
        f'</div></div></header>\n'

        f'<main class="wrap" id="top">\n'
        f'<section class="hero">'
        f'<p class="eyebrow">Report Design System · generated from the library</p>'
        f'<h1>One question. One governed visual.</h1>'
        f'<p class="lede">A deterministic catalog of chart idioms for Power BI, Deneb and the web — each with '
        f'runnable, byte-for-byte-frozen code per tool and a house / IBCS notation axis. Ask a question, get the '
        f'right visual, copy the exact code.</p>'
        f'<div class="stats">'
        f'<div class="stat"><b>{len(impl)}</b><span>idioms</span></div>'
        f'<div class="stat"><b>4</b><span>tool tracks</span></div>'
        f'<div class="stat"><b>2</b><span>notations · house / IBCS</span></div>'
        f'<div class="stat pos"><b>{deneb_proven}/{deneb_appl}</b><span>Deneb proven · {n_scen} scenarios</span></div>'
        f'</div>'
        f'<div class="strip">{strip}</div>'
        f'</section>\n'

        f'<section class="section" id="chooser"><div class="section-head"><span class="k">Chooser</span>'
        f'<h2>Which visual, when</h2><p>Start from the analytical question, not the chart. Pick one to filter the '
        f'idioms below to its candidates.</p></div>'
        f'<div class="chooser">{"".join(purposes)}</div></section>\n'

        f'<section class="section" id="validation"><div class="section-head"><span class="k">Validation</span>'
        f'<h2>Proven vs. gated</h2><p>What is actually verified to render — not just declared.</p></div>'
        f'<div class="valgrid">'
        f'<div class="vcard pos"><div class="big">{deneb_proven}/{deneb_appl}</div>'
        f'<p class="sub"><b>Deneb</b> realizations rasterized headlessly under all {n_scen} data scenarios '
        f'({scen}) — proven to render when the data varies.</p></div>'
        f'<div class="vcard"><div class="legend">'
        f'<div class="row"><span class="pill rendered">proven 5/5</span> rasterized under every scenario</div>'
        f'<div class="row"><span class="pill gate">structural · gated</span> deterministic + structurally valid; live render not yet run</div>'
        f'<div class="row"><span class="pill no">—</span> tool not applicable to this idiom</div>'
        f'</div></div></div>'
        f'<p class="na" style="margin:0 0 16px">Native (Power BI Desktop), SVG-DAX (DAX engine) and Recharts '
        f'(browser) stay runtime-gated; sign off via <code>acceptance/CHECKLIST.md</code>.</p>'
        f'<div class="tablewrap"><table class="val"><thead><tr><th>Idiom</th><th>PBI native</th>'
        f'<th>SVG-DAX</th><th>Deneb / Vega-Lite</th><th>Recharts</th></tr></thead>'
        f'<tbody>{"".join(val_rows)}</tbody></table></div></section>\n'

        f'<section class="section" id="idioms"><div class="section-head"><span class="k">Catalog</span>'
        f'<h2>Idioms <span class="count" id="count">{len(impl)}</span></h2>'
        f'<p>Every idiom with its real preview, proof status, and runnable code per tool. Search or filter to narrow.</p></div>'
        f'<div class="pickbar" id="pickbar"><span>Filtered to <b id="pickq"></b></span>'
        f'<button id="pickclear" type="button">Clear filter</button></div>'
        f'<div class="toolbar"><div class="chips" data-filter="zone">{zone_chips}</div>'
        f'<div class="chips" data-filter="tool">{tool_chips}</div></div>'
        f'<div class="cards" id="cards">{idioms_html}</div>'
        f'<p class="empty" id="empty">No idiom matches those filters.</p></section>\n'
        f'</main>\n'

        f'<footer class="wrap foot">Deny (never emit): {" · ".join("<code>"+_esc(d)+"</code>" for d in idx["deny"])}.<br>'
        f'Generated from <b>core/templates/page_templates/visual_library/</b> by <code>render_docs.py</code>; '
        f'governed by <code>pbi-design/references/charts.md</code>. Determinism frozen in <code>golden/</code>, '
        f'render-proof in <code>acceptance/validation_matrix.json</code>.</footer>\n'
        f'<button class="totop" id="totop" type="button" aria-label="Back to top">{_ICON_UP}</button>'
        f'<div class="toast" id="toast">Copied to clipboard</div>'
        f'<script>{_JS}</script>\n'
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
