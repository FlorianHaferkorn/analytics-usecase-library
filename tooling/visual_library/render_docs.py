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
COLOR = yaml.safe_load((LIB.parent / "tokens" / "color_semantics.yaml").read_text(encoding="utf-8"))
PROFILES = yaml.safe_load((LIB / "_notation_profiles.yaml").read_text(encoding="utf-8"))
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
    if s in ("rendered", "partial"):
        n = f" {len(cell['scenarios_ok'])}/{cell['scenarios_total']}" if "scenarios_ok" in cell else ""
        return (f"rendered ✓{n}" if s == "rendered" else f"partial{n}")
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
    out.append(f"> Evidence per idiom × tool, each proven by an ACTUAL headless render: **Deneb** rasterized "
               f"across {len(matrix['scenarios'])} data scenarios ({', '.join('`'+s+'`' for s in matrix['scenarios'])}) "
               "and **SVG-DAX** rasterized (its emitted SVG) via vl-convert; **Recharts** React-rendered via the "
               "Node harness `acceptance/render_recharts.mjs`. Only **Power BI native** stays `structural · gated` "
               "— PBIR is a visual config with no headless renderer, so its proof is a Desktop load "
               "(`acceptance/CHECKLIST.md`). Regenerate with `render_acceptance.py matrix`.")
    out.append("")
    out.append("| Idiom | Power BI · native | Power BI · SVG-DAX | Deneb / Vega-Lite | Web · Recharts |")
    out.append("|---|---|---|---|---|")
    for iid in _implemented():
        cells = matrix["idioms"].get(iid, {})
        row = " | ".join(_val_label(cells.get(t, {})) for t in _VAL_TOOLS)
        out.append(f"| `{iid}` | {row} |")
    out.append("")
    out.append("**Legend.** `rendered ✓` = actually rendered headlessly (Deneb shows the scenario count) · "
               "`structural · gated` = deterministic + structurally valid, live render needs its host (Desktop) · `—` = tool n/a.")
    out.append("")
    out.append("### Idioms")
    out.append("")
    for iid in _implemented():
        e = render.load_entry(iid)
        zone = " / ".join(e["zone"]) if isinstance(e["zone"], list) else str(e["zone"])
        out.append(f"#### `{iid}` — {e['name']}")
        ms = e.get("min_size") or {}
        minstr = ""
        if ms.get("cols"):
            bw, bh = render.grid_px(ms["cols"], ms["rows"])
            pw, ph = render.grid_px(ms["cols"], ms["rows"], "production")
            minstr = f" · **min size:** {ms['cols']}×{ms['rows']} grid ({bw}×{bh}px @1280, {pw}×{ph}px @1920)"
        out.append(f"- **Purpose:** {', '.join(e['purpose'])} · **zone:** {zone}"
                   + (f" · **best form for:** `{e['best_form_for']}`" if e.get("best_form_for") else "")
                   + minstr)
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
  --bg:#F1F4F9;--surface:#FFFFFF;--surface2:#F5F8FC;--glass:rgba(241,244,249,.72);
  --ink:#0E1421;--ink2:#56627A;--ink3:#8894A9;--line:#E4E9F2;--line2:#EEF2F8;
  --accent:#2563EB;--accent-ink:#FFFFFF;--accent-soft:rgba(37,99,235,.10);
  --pos:#12965A;--pos-soft:rgba(18,150,90,.13);--warn:#B8790F;--warn-soft:rgba(184,121,15,.15);
  --z-pulse:#7A5AF8;--z-analysis:#2563EB;--z-detail:#0E9488;
  --sans:"Segoe UI Variable","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
  --mono:"Cascadia Code","Cascadia Mono",ui-monospace,Consolas,monospace;
  --r:18px;--r2:13px;--r3:9px;--maxw:1220px;
  --sh1:0 1px 2px rgba(14,20,33,.05),0 1px 1px rgba(14,20,33,.03);
  --sh2:0 6px 16px rgba(14,20,33,.07),0 22px 48px -22px rgba(14,20,33,.24);
  --sh3:0 30px 80px -30px rgba(14,20,33,.5);
}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#090D15;--surface:#121826;--surface2:#0D131E;--glass:rgba(9,13,21,.7);
  --ink:#EAF0FA;--ink2:#94A1B6;--ink3:#5D6980;--line:#212B3C;--line2:#161E2B;
  --accent:#5288F5;--accent-ink:#050B15;--accent-soft:rgba(82,136,245,.16);
  --pos:#34C46E;--pos-soft:rgba(52,196,110,.16);--warn:#E2AB3E;--warn-soft:rgba(226,171,62,.16);
  --z-pulse:#9C86FF;--z-analysis:#5288F5;--z-detail:#2AC2B0;
  --sh1:0 1px 2px rgba(0,0,0,.45);--sh2:0 8px 20px rgba(0,0,0,.44),0 26px 54px -24px rgba(0,0,0,.75);
  --sh3:0 40px 100px -30px rgba(0,0,0,.85);
}}
:root[data-theme="dark"]{
  --bg:#090D15;--surface:#121826;--surface2:#0D131E;--glass:rgba(9,13,21,.7);
  --ink:#EAF0FA;--ink2:#94A1B6;--ink3:#5D6980;--line:#212B3C;--line2:#161E2B;
  --accent:#5288F5;--accent-ink:#050B15;--accent-soft:rgba(82,136,245,.16);
  --pos:#34C46E;--pos-soft:rgba(52,196,110,.16);--warn:#E2AB3E;--warn-soft:rgba(226,171,62,.16);
  --z-pulse:#9C86FF;--z-analysis:#5288F5;--z-detail:#2AC2B0;
  --sh1:0 1px 2px rgba(0,0,0,.45);--sh2:0 8px 20px rgba(0,0,0,.44),0 26px 54px -24px rgba(0,0,0,.75);
  --sh3:0 40px 100px -30px rgba(0,0,0,.85);
}
html{scroll-behavior:smooth;scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}code,.mono{font-family:var(--mono)}
::selection{background:var(--accent-soft)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}
button{font-family:inherit}

/* nav */
.nav{position:sticky;top:0;z-index:50;background:var(--glass);backdrop-filter:saturate(1.7) blur(16px);-webkit-backdrop-filter:saturate(1.7) blur(16px);border-bottom:1px solid var(--line)}
.nav-in{max-width:var(--maxw);margin:0 auto;padding:11px 24px;display:flex;align-items:center;gap:16px}
.brand{display:flex;align-items:center;gap:9px;font-weight:700;letter-spacing:-.01em;font-size:15px}
.brand .mk{width:23px;height:23px;border-radius:7px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--z-pulse));color:#fff;box-shadow:var(--sh1)}
.brand .mk svg{width:14px;height:14px}
.brand .sub{color:var(--ink3);font-weight:500}
.nav-links{display:flex;gap:2px;margin-left:4px}
.nav-links a{font-size:13.5px;color:var(--ink2);padding:7px 11px;border-radius:8px;font-weight:500;transition:.15s}
.nav-links a:hover{color:var(--ink);background:var(--surface2)}
.nav-links a.on{color:var(--accent);background:var(--accent-soft)}
.nav-tools{margin-left:auto;display:flex;align-items:center;gap:9px}
.search{position:relative;display:flex;align-items:center}
.search svg{position:absolute;left:11px;width:15px;height:15px;color:var(--ink3);pointer-events:none}
.search input{width:220px;max-width:42vw;font:inherit;font-size:13.5px;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:8px 12px 8px 33px;transition:.15s}
.search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.iconbtn{width:37px;height:37px;display:grid;place-items:center;border:1px solid var(--line);background:var(--surface);color:var(--ink2);border-radius:11px;cursor:pointer;transition:.15s}
.iconbtn:hover{color:var(--ink);border-color:var(--ink3)}.iconbtn svg{width:17px;height:17px}

.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}

/* hero */
.hero{padding:60px 0 30px}
.eyebrow{font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:640;margin:0}
.hero h1{font-size:clamp(32px,5.4vw,56px);line-height:1.03;letter-spacing:-.028em;font-weight:730;margin:15px 0 0;max-width:17ch;text-wrap:balance}
.hero .lede{font-size:clamp(15px,1.9vw,18.5px);color:var(--ink2);margin:18px 0 0;max-width:56ch}
.metabar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px;margin:30px 0 0}
.chipstat{display:flex;align-items:baseline;gap:7px;font-size:13.5px;color:var(--ink2)}
.chipstat b{font-size:19px;font-weight:720;color:var(--ink);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.chipstat.pos b{color:var(--pos)}
.legend{display:flex;flex-wrap:wrap;gap:6px 15px;margin:20px 0 0;font-size:12.5px;color:var(--ink3)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;display:inline-block}
.dot.d-ok{background:var(--pos)}.dot.d-warn{background:var(--warn)}
.dot.d-gate{background:var(--ink3)}.dot.d-na{background:transparent;box-shadow:inset 0 0 0 1.5px var(--line)}

/* section frame */
.section{padding:40px 0;border-top:1px solid var(--line)}
.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin:0 0 22px}
.section-head .k{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:640}
.section-head h2{font-size:clamp(21px,3vw,28px);letter-spacing:-.02em;font-weight:720;margin:8px 0 0}
.section-head p{color:var(--ink2);font-size:14.5px;margin:8px 0 0}
.count{font-size:.52em;font-weight:600;color:var(--ink3);font-variant-numeric:tabular-nums;margin-left:9px;border:1px solid var(--line);border-radius:20px;padding:3px 10px;vertical-align:middle}

/* chooser */
.chooser{display:flex;flex-wrap:wrap;gap:9px}
.qpill{display:inline-flex;align-items:center;gap:9px;text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:11px 14px;cursor:pointer;font:inherit;color:inherit;box-shadow:var(--sh1);transition:transform .16s,box-shadow .16s,border-color .16s;max-width:340px}
.qpill:hover{transform:translateY(-2px);box-shadow:var(--sh2);border-color:color-mix(in srgb,var(--accent) 40%,var(--line))}
.qpill .q{font-size:13.5px;font-weight:560;line-height:1.3}
.qpill .b{font-family:var(--mono);font-size:11.5px;color:var(--accent);background:var(--accent-soft);padding:3px 8px;border-radius:7px;white-space:nowrap;flex:0 0 auto}

/* sticky toolbar */
.toolbar{position:sticky;top:59px;z-index:30;display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;padding:13px 0;margin:0 0 8px;background:var(--glass);backdrop-filter:saturate(1.6) blur(12px);-webkit-backdrop-filter:saturate(1.6) blur(12px)}
.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.chips .lbl{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin-right:3px;font-weight:640}
.chip{font:inherit;font-size:12.5px;color:var(--ink2);background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:6px 13px;cursor:pointer;transition:.14s}
.chip:hover{color:var(--ink);border-color:var(--ink3)}
.chip.on{color:var(--accent-ink);background:var(--accent);border-color:var(--accent)}
.pickbar{display:none;align-items:center;gap:11px;margin:0 0 16px;font-size:13.5px;color:var(--ink2)}
.pickbar.show{display:flex}.pickbar b{color:var(--ink)}
.pickbar button{font:inherit;font-size:12.5px;color:var(--accent);background:var(--accent-soft);border:none;border-radius:9px;padding:6px 12px;cursor:pointer}

/* gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(236px,1fr));gap:16px}
.tile{position:relative;display:flex;flex-direction:column;text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);overflow:hidden;cursor:pointer;padding:0;color:inherit;box-shadow:var(--sh1);animation:rise .5s cubic-bezier(.2,.7,.2,1) both;animation-delay:var(--d,0ms);transition:transform .18s,box-shadow .18s,border-color .18s}
.tile:hover{transform:translateY(-4px);box-shadow:var(--sh2);border-color:color-mix(in srgb,var(--accent) 34%,var(--line))}
.tile:hover .viz svg{transform:scale(1.045)}
.tile.hide{display:none}
.viz{position:relative;background:#fff;aspect-ratio:340/150;overflow:hidden;border-bottom:1px solid var(--line2)}
.viz svg{width:100%;height:100%;display:block;transition:transform .3s cubic-bezier(.2,.7,.2,1)}
.ztag{position:absolute;top:9px;left:9px;z-index:2;font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.03em;padding:3px 8px;border-radius:20px;color:#fff;background:var(--z-analysis);box-shadow:var(--sh1)}
.ztag.z-pulse{background:var(--z-pulse)}.ztag.z-analysis{background:var(--z-analysis)}.ztag.z-detail{background:var(--z-detail)}
.open-hint{position:absolute;top:9px;right:9px;z-index:2;width:26px;height:26px;border-radius:8px;display:grid;place-items:center;background:var(--glass);backdrop-filter:blur(6px);color:var(--ink2);opacity:0;transform:scale(.8);transition:.18s}
.tile:hover .open-hint{opacity:1;transform:none}.open-hint svg{width:15px;height:15px}
.tmeta{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 14px}
.tname{font-size:14px;font-weight:640;letter-spacing:-.01em;display:flex;flex-direction:column;gap:2px;min-width:0}
.tname em{font-style:normal;font-family:var(--mono);font-size:10.5px;color:var(--ink3);font-weight:400}
.dots{display:flex;gap:5px;flex:0 0 auto}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.empty{display:none;text-align:center;color:var(--ink3);font-size:15px;padding:56px 0}
.empty.show{display:block}

/* modal */
.modal{position:fixed;inset:0;z-index:100;display:none;align-items:flex-start;justify-content:center;padding:6vh 20px 20px}
.modal.show{display:flex}
.backdrop{position:fixed;inset:0;background:rgba(8,12,20,.5);backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);animation:fade .2s ease}
.modal-card{position:relative;z-index:1;width:min(760px,100%);max-height:86vh;overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--sh3);animation:pop .24s cubic-bezier(.2,.8,.2,1);scrollbar-width:thin}
.modal-close{position:sticky;top:0;float:right;margin:12px 12px 0 0;z-index:3;width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--surface2);border:1px solid var(--line);color:var(--ink2);cursor:pointer;transition:.15s}
.modal-close:hover{color:var(--ink);border-color:var(--ink3)}.modal-close svg{width:16px;height:16px}
.detail{padding:24px 26px 26px}
.d-head{display:flex;gap:18px;align-items:flex-start;margin:0 0 16px}
.d-viz{flex:0 0 170px;width:170px;background:#fff;border:1px solid var(--line);border-radius:var(--r3);overflow:hidden;aspect-ratio:340/150;box-shadow:var(--sh1)}
.d-viz svg{width:100%;height:100%;display:block}
.detail h3{margin:0;font-size:22px;font-weight:700;letter-spacing:-.02em;display:flex;flex-wrap:wrap;align-items:baseline;gap:9px}
.detail h3 code{font-size:13px;color:var(--accent);background:var(--accent-soft);padding:3px 8px;border-radius:7px;font-weight:600}
.d-sub{font-size:13.5px;color:var(--ink3);margin:8px 0 0;line-height:1.45}
.d-sub .minpx{font-family:var(--mono);font-size:11px;color:var(--ink3);opacity:.8}
.status{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 0}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;border:1px solid transparent}
.pill::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.pill.rendered{color:var(--pos);background:var(--pos-soft)}
.pill.partial{color:var(--warn);background:var(--warn-soft)}
.pill.gate{color:var(--ink2);background:var(--surface2);border-color:var(--line)}
.pill.no{color:var(--ink3);background:transparent;border-color:var(--line2)}.pill.no::before{opacity:.4}
.avoid{font-size:12.5px;color:var(--ink3);margin:16px 0 0;line-height:1.5}
.avoid b{color:var(--warn);font-weight:600;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;margin-right:7px}
.na{font-size:12.5px;color:var(--ink3);margin:14px 0 0;line-height:1.55}.na b{color:var(--ink2)}

/* modal — encoding spec + alternatives + how-to (the "why" & "how") */
.dblock{margin:18px 0 0}
.dlabel{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink3);font-weight:640;margin:0 0 8px}
.espec{display:flex;flex-wrap:wrap;gap:7px}
.enc{display:inline-flex;align-items:center;gap:7px;font-size:12px;background:var(--surface2);border:1px solid var(--line);border-radius:9px;padding:6px 10px}
.enc b{font-family:var(--mono);font-size:10.5px;color:var(--ink3);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.enc span{color:var(--ink);font-weight:500}
.alts{display:flex;flex-wrap:wrap;gap:6px}
.altlink{font:inherit;font-family:var(--mono);font-size:11.5px;color:var(--accent);background:var(--accent-soft);border:1px solid transparent;border-radius:8px;padding:5px 10px;cursor:pointer;transition:.14s}
.altlink:hover{border-color:var(--accent)}
.fam{display:flex;flex-direction:column;gap:6px}
.famrow{display:flex;align-items:center;gap:10px;font-size:12.5px}
.famrow .fl{font:inherit;font-family:var(--mono);font-size:11.5px;color:var(--accent);background:var(--accent-soft);border:1px solid transparent;border-radius:8px;padding:4px 9px;cursor:pointer;transition:.14s;flex:0 0 auto}
.famrow .fl:hover{border-color:var(--accent)}
.famrow .fu{color:var(--ink2)}
.ship{margin:18px 0 0;border:1px solid var(--line);border-radius:var(--r2);padding:14px 16px;background:var(--surface2)}
.ship .row{display:flex;gap:11px;padding:8px 0;border-top:1px solid var(--line2)}
.ship .row:first-of-type{border-top:none}
.ship .tt{flex:0 0 84px;font-family:var(--mono);font-size:11px;color:var(--accent);font-weight:600;padding-top:1px}
.ship ol{margin:0;padding:0 0 0 16px;display:flex;flex-direction:column;gap:4px}
.ship li{font-size:12px;color:var(--ink2);line-height:1.45}

.code{margin:18px 0 0;border:1px solid var(--line);border-radius:var(--r2);overflow:hidden;background:var(--surface2)}
.tabbar{display:flex;gap:2px;padding:7px 7px 0;overflow-x:auto;border-bottom:1px solid var(--line);scrollbar-width:none}
.tabbar::-webkit-scrollbar{display:none}
.tab{position:relative;font-family:var(--mono);font-size:11.5px;color:var(--ink3);background:none;border:none;padding:9px 12px;cursor:pointer;white-space:nowrap;border-radius:7px 7px 0 0;transition:color .14s}
.tab:hover{color:var(--ink2)}.tab[aria-selected="true"]{color:var(--accent)}
.tab[aria-selected="true"]::after{content:"";position:absolute;left:8px;right:8px;bottom:-1px;height:2px;background:var(--accent);border-radius:2px}
.panel{position:relative}.panel[hidden]{display:none}
.copy{position:absolute;top:9px;right:9px;z-index:2;font-family:var(--mono);font-size:11px;color:var(--ink2);background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:5px 11px;cursor:pointer;transition:.15s}
.copy:hover{color:var(--accent);border-color:var(--accent)}.copy.done{color:var(--pos);border-color:var(--pos)}
pre{overflow:auto;margin:0;padding:14px 16px;font-family:var(--mono);font-size:11.5px;line-height:1.6;color:var(--ink);max-height:44vh;scrollbar-width:thin}
pre code{color:inherit}

.foot{padding:40px 0 96px;color:var(--ink3);font-size:13px;line-height:1.6}.foot b{color:var(--ink2)}
.totop{position:fixed;right:22px;bottom:22px;z-index:40;width:42px;height:42px;border-radius:50%;display:grid;place-items:center;background:var(--surface);color:var(--ink2);border:1px solid var(--line);box-shadow:var(--sh2);cursor:pointer;opacity:0;transform:translateY(8px);pointer-events:none;transition:.2s}
.totop.show{opacity:1;transform:none;pointer-events:auto}.totop:hover{color:var(--accent)}.totop svg{width:18px;height:18px}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,14px);z-index:110;background:var(--ink);color:var(--bg);font-size:13px;font-weight:500;padding:10px 18px;border-radius:12px;box-shadow:var(--sh2);opacity:0;pointer-events:none;transition:.2s}
.toast.show{opacity:1;transform:translate(-50%,0)}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes pop{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:none}}

/* foundations */
.founds{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.fcard{background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);padding:20px 22px;box-shadow:var(--sh1)}
.fcard h3{margin:0;font-size:15px;font-weight:680;letter-spacing:-.01em}
.fcard .lead{font-size:13px;color:var(--ink2);margin:8px 0 0;line-height:1.5}
.rules{list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:9px}
.rules li{font-size:12.5px;color:var(--ink2);line-height:1.45}
.rules b{display:block;font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);font-weight:640;margin-bottom:2px}
.src{font-size:11.5px;color:var(--ink3);margin:14px 0 0;line-height:1.5}
.deny{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}
.deny span{font-family:var(--mono);font-size:11px;color:var(--warn);background:var(--warn-soft);border-radius:8px;padding:4px 9px;text-decoration:line-through;text-decoration-color:color-mix(in srgb,var(--warn) 55%,transparent)}
.swatches{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 0}
.sw{display:flex;flex-direction:column;gap:6px;align-items:flex-start}
.sw .chip{width:52px;height:34px;border-radius:9px;border:1px solid var(--line);box-shadow:var(--sh1)}
.sw .nm{font-size:10.5px;color:var(--ink2);line-height:1.2}
.sw .hx{font-family:var(--mono);font-size:9.5px;color:var(--ink3)}
.scen{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 0}
.scen figure{margin:0;display:flex;flex-direction:column;gap:6px;align-items:center;font-size:10.5px;color:var(--ink2)}
.scen .box{width:44px;height:26px;border-radius:6px;border:1.5px solid var(--accent)}
.scen .solid{background:var(--accent)}
.scen .outlined{background:transparent}
.scen .hatched{background:repeating-linear-gradient(45deg,var(--accent) 0 3px,transparent 3px 6px)}
.scen .py{background:var(--accent);opacity:.5}
.scen em{font-style:normal;font-family:var(--mono);color:var(--ink3);font-size:9.5px}

@media(max-width:640px){.nav-links{display:none}.d-head{flex-direction:column}.d-viz{width:100%;flex-basis:auto}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
"""

_JS = """
(function(){
  var root=document.documentElement,$=function(s,c){return (c||document).querySelector(s)},$$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  var state={q:"",zone:"",tool:"",proof:"",pick:null};

  try{var sv=localStorage.getItem("vl-theme");if(sv)root.setAttribute("data-theme",sv)}catch(e){}
  var tb=$("#theme");
  if(tb)tb.addEventListener("click",function(){var c=root.getAttribute("data-theme");var n=c==="dark"?"light":(c==="light"?"":"dark");if(n)root.setAttribute("data-theme",n);else root.removeAttribute("data-theme");try{n?localStorage.setItem("vl-theme",n):localStorage.removeItem("vl-theme")}catch(e){}});

  var tiles=$$(".tile"),countEl=$("#count"),emptyEl=$("#empty"),pickbar=$("#pickbar");
  function apply(){
    var q=state.q.trim().toLowerCase(),n=0;
    tiles.forEach(function(t){
      var ok=true;
      if(state.pick)ok=state.pick.indexOf(t.getAttribute("data-id"))>=0;
      if(ok&&state.zone)ok=(" "+t.getAttribute("data-zones")+" ").indexOf(" "+state.zone+" ")>=0;
      if(ok&&state.tool)ok=(" "+t.getAttribute("data-tools")+" ").indexOf(" "+state.tool+" ")>=0;
      if(ok&&state.proof)ok=t.getAttribute("data-proof")===state.proof;
      if(ok&&q)ok=t.getAttribute("data-search").indexOf(q)>=0;
      t.classList.toggle("hide",!ok);if(ok)n++;
    });
    if(countEl)countEl.textContent=n;
    if(emptyEl)emptyEl.classList.toggle("show",n===0);
  }
  var qEl=$("#q");if(qEl)qEl.addEventListener("input",function(){state.q=this.value;apply()});
  $$(".chips").forEach(function(g){var key=g.getAttribute("data-filter");g.addEventListener("click",function(e){var c=e.target.closest(".chip");if(!c)return;$$(".chip",g).forEach(function(x){x.classList.remove("on")});c.classList.add("on");state[key]=c.getAttribute("data-val")||"";apply()})});
  $$(".qpill").forEach(function(p){p.addEventListener("click",function(){state.pick=(p.getAttribute("data-cands")||"").split(",").filter(Boolean);if(pickbar){pickbar.classList.add("show");var b=$("#pickq");if(b)b.textContent=p.getAttribute("data-q")}apply();var t=document.getElementById("gallery");if(t)t.scrollIntoView({behavior:"smooth"})})});
  var clr=$("#pickclear");if(clr)clr.addEventListener("click",function(){state.pick=null;if(pickbar)pickbar.classList.remove("show");apply()});

  // modal open/close (+ shareable #idiom= deep link)
  var modal=$("#modal"),mbody=$("#modal-body"),lastFocus=null,hashLock=false;
  function openModal(id,fromHash){var d=document.getElementById(id);if(!d)return;mbody.innerHTML=d.innerHTML;modal.classList.add("show");document.body.style.overflow="hidden";lastFocus=document.activeElement;var cl=$(".modal-close",modal);if(cl)cl.focus();if(!fromHash){hashLock=true;try{location.hash="idiom="+id.replace(/^d-/,"")}catch(e){}hashLock=false}}
  function closeModal(){if(!modal.classList.contains("show"))return;modal.classList.remove("show");mbody.innerHTML="";document.body.style.overflow="";if(location.hash.indexOf("idiom=")>=0){hashLock=true;try{history.replaceState(null,"",location.pathname+location.search)}catch(e){location.hash=""}hashLock=false}if(lastFocus&&lastFocus.focus)lastFocus.focus()}
  tiles.forEach(function(t){t.addEventListener("click",function(){openModal(t.getAttribute("data-detail"))})});
  if(modal){modal.addEventListener("click",function(e){if(e.target.classList.contains("backdrop")||e.target.closest(".modal-close"))closeModal()});}
  // alternatives inside the modal jump to that idiom
  document.addEventListener("click",function(e){var a=e.target.closest(".altlink");if(!a)return;openModal(a.getAttribute("data-detail"))});
  function fromHash(){var m=(location.hash||"").match(/idiom=([\\w-]+)/);if(m){openModal("d-"+m[1],true)}else if(modal.classList.contains("show")){closeModal()}}
  window.addEventListener("hashchange",function(){if(!hashLock)fromHash()});
  if((location.hash||"").indexOf("idiom=")>=0)fromHash();
  document.addEventListener("keydown",function(e){
    if(e.key==="Escape"){closeModal();return}
    if(e.key==="/"&&!/^(INPUT|TEXTAREA)$/.test((e.target.tagName||""))){e.preventDefault();var q=$("#q");if(q)q.focus()}
  });

  // tabs (delegated — works inside modal)
  document.addEventListener("click",function(e){var tab=e.target.closest(".tab");if(!tab)return;var bar=tab.parentNode,code=bar.parentNode;$$(".tab",bar).forEach(function(t){t.setAttribute("aria-selected","false")});tab.setAttribute("aria-selected","true");$$(".panel",code).forEach(function(pn){pn.hidden=pn.getAttribute("data-panel")!==tab.getAttribute("data-panel")})});
  // copy
  var toast=$("#toast"),tt;
  document.addEventListener("click",function(e){var b=e.target.closest(".copy");if(!b)return;var pre=$("pre",b.parentNode);if(!pre)return;var txt=pre.innerText;var done=function(){b.classList.add("done");var o=b.textContent;b.textContent="Copied";if(toast){toast.classList.add("show");clearTimeout(tt);tt=setTimeout(function(){toast.classList.remove("show")},1400)}setTimeout(function(){b.classList.remove("done");b.textContent=o},1400)};try{navigator.clipboard.writeText(txt).then(done,function(){fb(txt);done()})}catch(err){fb(txt);done()}});
  function fb(t){try{var a=document.createElement("textarea");a.value=t;document.body.appendChild(a);a.select();document.execCommand("copy");document.body.removeChild(a)}catch(e){}}

  // scrollspy
  var links=$$(".nav-links a"),secs=links.map(function(a){return document.querySelector(a.getAttribute("href"))}).filter(Boolean);
  if("IntersectionObserver" in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){var id="#"+en.target.id;links.forEach(function(a){a.classList.toggle("on",a.getAttribute("href")===id)})}})},{rootMargin:"-45% 0px -50% 0px"});secs.forEach(function(s){io.observe(s)})}
  var top=$("#totop");if(top){window.addEventListener("scroll",function(){top.classList.toggle("show",window.scrollY>640)},{passive:true});top.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})})}
})();
"""

TOOL_SHORT = {
    "powerbi_native": "PBI native",
    "powerbi_svg_dax": "SVG-DAX",
    "deneb_vegalite": "Deneb",
    "web_recharts": "Recharts",
}
_STATUS_WORD = {"rendered": "proven", "partial": "partial", "structural": "gated"}
_DOT_CLS = {"rendered": "d-ok", "partial": "d-warn", "structural": "d-gate"}
_PILL_CLS = {"rendered": "rendered", "partial": "partial", "structural": "gate"}

# How to ship each tool track (generic, accurate wiring steps shown in the modal).
_RECIPES = {
    "powerbi_native": [
        "Drop the fragment into a PBIR page (…/pages/&lt;p&gt;/visuals/&lt;id&gt;/visual.json) or add it with the pbir CLI.",
        "Bind its projections to your measures / dimension — the [HITL] placeholders mark the required roles.",
    ],
    "powerbi_svg_dax": [
        "Add as an extension measure in reportExtensions.json — dataType Text, dataCategory ImageUrl.",
        "Bind in a table/matrix (set the column's image height/width) or a new cardVisual (callout.imageFX).",
        "Or install the AlucaViz UDF package and call the function instead of pasting the measure.",
    ],
    "deneb_vegalite": [
        "Add a Deneb visual, paste the spec, and map its dataset to your fields.",
        "It is a standalone Vega-Lite v5 spec — it also runs anywhere Vega-Lite does.",
    ],
    "web_recharts": [
        "Drop the JSX into a React app with recharts installed.",
        "Pass your rows as data and keep the dataKeys, or remap them to your columns.",
    ],
}

# Chart families — the same visual TYPE across different questions. Answers
# "which form of this chart fits my question" (e.g. a bar for ranking vs for magnitude).
_FAMILY = {
    "bar_ranking": "bar", "bar_absolute": "bar", "deviation_bar": "bar",
    "line": "line", "indexed_line": "line", "slope": "line", "area_stacked": "line", "small_multiples": "line",
    "waterfall_pvm": "waterfall", "waterfall_buildup": "waterfall", "waterfall_variance": "waterfall",
    "donut": "part", "stacked_100": "part",
    "histogram": "dist", "boxplot": "dist",
    "scatter": "point", "lollipop": "point",
    "bullet": "target", "matrix_evidence": "table",
    "sankey": "flow", "decomposition_tree": "flow",
}
_FAMILY_LABEL = {"bar": "Bar / column", "line": "Line / area", "waterfall": "Waterfall",
                 "part": "Part-to-whole", "dist": "Distribution", "point": "Point",
                 "target": "Target vs actual", "table": "Table", "flow": "Flow / structure"}
# short "use" per purpose id — how each family member is distinguished
_USE = {
    "time_comparison": "over time", "deviation_from_target": "vs target",
    "compare_categories": "rank categories", "contribution_to_change": "what drove the change",
    "part_to_whole": "share of the whole", "correlation": "two variables relate",
    "flow_between_stages": "flow between stages", "driver_breakdown": "which dimension drives",
    "distribution": "spread / outliers", "evidence_detail": "worst rows + action",
    "value_verdict": "headline value",
}


def _use_of(iid: str) -> str:
    e = render.load_entry(iid)
    purposes = e.get("purpose") or []
    return _USE.get(purposes[0], purposes[0].replace("_", " ")) if purposes else ""

_ICON_SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>')
_ICON_THEME = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
               '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none"/></svg>')
_ICON_UP = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>')
_ICON_EXPAND = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>')
_ICON_CLOSE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
               '<path d="M18 6 6 18M6 6l12 12"/></svg>')
_BRAND_MK = ('<svg viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="8" width="3" height="7" rx="1"/>'
             '<rect x="6.5" y="4" width="3" height="11" rx="1"/><rect x="12" y="1" width="3" height="14" rx="1"/></svg>')


def _esc(s) -> str:
    return html.escape(str(s))


def _base_idiom(cand: str) -> str:
    return cand.split("@", 1)[0]


def _pill(tool: str, cell: dict) -> str:
    s = cell.get("status")
    cls = _PILL_CLS.get(s, "no")
    word = _STATUS_WORD.get(s, "n/a")
    if s == "rendered":
        word = f"proven {len(cell['scenarios_ok'])}/{cell['scenarios_total']}" if "scenarios_ok" in cell else "proven"
    return f'<span class="pill {cls}">{_esc(TOOL_SHORT[tool])} · {word}</span>'


def _dot(tool: str, cell: dict) -> str:
    s = cell.get("status")
    cls = _DOT_CLS.get(s, "d-na")
    word = _STATUS_WORD.get(s, "n/a")
    return f'<i class="dot {cls}" title="{_esc(TOOL_SHORT[tool])}: {word}"></i>'


def _tile(iid: str, matrix: dict) -> str:
    e = render.load_entry(iid)
    zones = e["zone"] if isinstance(e["zone"], list) else [e["zone"]]
    cells = matrix["idioms"].get(iid, {})
    applicable = render.tools(iid)
    search = " ".join([iid, e["name"], *e["purpose"], *zones, *e.get("anti_patterns", [])]).lower()
    proof = "proven" if cells.get("deneb_vegalite", {}).get("status") == "rendered" else "gated"
    dots = "".join(_dot(t, cells.get(t, {})) for t in SCHEMA["tools"])
    viz = e.get("preview_svg", "")
    return (
        f'<button class="tile" data-detail="d-{_esc(iid)}" data-id="{_esc(iid)}" '
        f'data-zones="{_esc(" ".join(zones))}" data-tools="{_esc(" ".join(applicable))}" '
        f'data-proof="{proof}" data-search="{_esc(search)}" aria-label="Open {_esc(e["name"])}">'
        f'<span class="ztag z-{_esc(zones[0])}">{_esc(zones[0])}</span>'
        f'<span class="open-hint">{_ICON_EXPAND}</span>'
        f'<span class="viz">{viz}</span>'
        f'<span class="tmeta"><span class="tname">{_esc(e["name"])}<em>{_esc(iid)}</em></span>'
        f'<span class="dots">{dots}</span></span>'
        f'</button>'
    )


def _detail(iid: str, matrix: dict) -> str:
    e = render.load_entry(iid)
    zones = e["zone"] if isinstance(e["zone"], list) else [e["zone"]]
    cells = matrix["idioms"].get(iid, {})
    applicable = render.tools(iid)
    best = f' · best for <b>{_esc(e["best_form_for"])}</b>' if e.get("best_form_for") else ""

    p = [f'<div class="detail" id="d-{_esc(iid)}" hidden>']
    p.append('<div class="d-head">')
    p.append(f'<div class="d-viz">{e["preview_svg"]}</div>' if e.get("preview_svg") else '<div class="d-viz"></div>')
    p.append('<div>')
    p.append(f'<h3>{_esc(e["name"])} <code>{_esc(iid)}</code></h3>')
    ms = e.get("min_size") or {}
    minsz = ""
    if ms.get("cols"):
        bw, bh = render.grid_px(ms["cols"], ms["rows"])
        pw, ph = render.grid_px(ms["cols"], ms["rows"], "production")
        minsz = (f' · min <b>{ms["cols"]}×{ms["rows"]} grid</b> '
                 f'<span class="minpx">{bw}×{bh}px @1280 · {pw}×{ph}px @1920</span>')
    p.append(f'<p class="d-sub">{_esc(", ".join(e["purpose"]))} · {_esc(" / ".join(zones))}{best}{minsz}</p>')
    if applicable:
        p.append('<div class="status">' + "".join(_pill(t, cells.get(t, {})) for t in SCHEMA["tools"]
                                                    if t in applicable) + '</div>')
    p.append('</div></div>')
    if e.get("anti_patterns"):
        p.append(f'<p class="avoid"><b>Avoid</b>{_esc(", ".join(e["anti_patterns"]))}</p>')

    # the "why": governed encoding rationale (magnitude → position, colour only for meaning, …)
    enc = e.get("encoding") or {}
    if enc:
        rows = "".join(
            f'<span class="enc"><b>{_esc(k)}</b><span>{_esc((", ".join(v) if isinstance(v, list) else str(v)).replace("_", " "))}</span></span>'
            for k, v in enc.items())
        p.append('<div class="dblock"><p class="dlabel">Encoding — the governed why</p>'
                 f'<div class="espec">{rows}</div></div>')
    # alternatives serving the same question → jump to that idiom
    alts = [a for a in (e.get("alternatives") or []) if a in set(_implemented())]
    if alts:
        chips = "".join(f'<button class="altlink" type="button" data-detail="d-{_esc(a)}">{_esc(a)}</button>' for a in alts)
        p.append('<div class="dblock"><p class="dlabel">Alternatives for the same question</p>'
                 f'<div class="alts">{chips}</div></div>')

    # same chart family — the other forms of this visual TYPE, and which question each fits
    fam = _FAMILY.get(iid)
    sibs = [s for s in _implemented() if _FAMILY.get(s) == fam and s != iid] if fam else []
    if sibs:
        rows = "".join(
            f'<div class="famrow"><button class="fl" type="button" data-detail="d-{_esc(s)}">{_esc(s)}</button>'
            f'<span class="fu">{_esc(_use_of(s))}</span></div>' for s in sibs)
        p.append(f'<div class="dblock"><p class="dlabel">Same family ({_esc(_FAMILY_LABEL.get(fam, fam))}) — which form fits the question</p>'
                 f'<div class="fam">{rows}</div></div>')

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
            panels.append(f'<div class="panel" data-panel="{_esc(pid)}"{"" if i == 0 else " hidden"}>'
                          f'<button class="copy" type="button">Copy</button>'
                          f'<pre><code>{_esc(code)}</code></pre></div>')
        p.append('<div class="code"><div class="tabbar" role="tablist">' + "".join(tabs) + '</div>'
                 + "".join(panels) + '</div>')

    # how to ship — the wiring steps per applicable tool
    if applicable:
        rows = "".join(
            f'<div class="row"><span class="tt">{_esc(TOOL_SHORT[t])}</span>'
            f'<ol>' + "".join(f'<li>{step}</li>' for step in _RECIPES[t]) + '</ol></div>'
            for t in SCHEMA["tools"] if t in applicable)
        p.append('<div class="dblock"><p class="dlabel">How to ship it</p>'
                 f'<div class="ship">{rows}</div></div>')

    na = [t for t in SCHEMA["tools"] if not (e["realizations"][t].get("applicable", True) and "template" in e["realizations"][t])]
    if na:
        bits = [f'<b>{_esc(TOOL_SHORT[t])}</b> n/a — {_esc(e["realizations"][t]["reason"])} → {_esc(e["realizations"][t]["use"])}' for t in na]
        p.append('<p class="na">' + "<br>".join(bits) + '</p>')
    p.append('</div>')
    return "".join(p)


def _swatch(name: str, hexv: str) -> str:
    return (f'<div class="sw"><span class="chip" style="background:{_esc(hexv)}"></span>'
            f'<span class="nm">{_esc(name)}</span><span class="hx">{_esc(hexv)}</span></div>')


def _foundations_html() -> str:
    """The governance & design foundation: the encoding rule, the deny-list, the notation
    profiles (house vs IBCS, the second axis), and the semantic / scenario colour tokens —
    all read from the SoT so they never diverge from what the idioms actually use."""
    deny = _index().get("deny", [])
    prin = (
        '<div class="fcard"><h3>Encoding discipline</h3>'
        '<p class="lead">Magnitude → length or position (perceptual rank 1–3), never the colour of a number. '
        'Direction → colour <b>and</b> sign. Colour is reserved for meaning; grey is the recede tool; one accent per page.</p>'
        '<p class="dlabel" style="margin:16px 0 0">Never emit</p>'
        '<div class="deny">' + "".join(f'<span>{_esc(d)}</span>' for d in deny) + '</div>'
        '<p class="src">Grounded in Cleveland &amp; McGill (1984) · Few (2012) · Munzner (2014) · Tufte (1983).</p></div>'
    )
    profs = []
    for pid, pr in PROFILES.get("profiles", {}).items():
        items = "".join(f'<li><b>{_esc(k.replace("_", " "))}</b>{_esc(v)}</li>' for k, v in (pr.get("rules") or {}).items())
        src = pr.get("source") or []
        profs.append(
            f'<div class="fcard"><h3>{_esc(pr.get("name", pid))}</h3>'
            f'<p class="lead">{_esc(" ".join(str(pr.get("description", "")).split()))}</p>'
            f'<ul class="rules">{items}</ul>'
            + (f'<p class="src">{_esc(src[0])}</p>' if src else "") + '</div>'
        )
    sem = COLOR.get("semantic", {})
    sw = "".join(_swatch(k, v) for k, v in sem.items())
    dat = "".join(_swatch(f"data {i}", c) for i, c in enumerate((COLOR.get("brand") or {}).get("data_colors", [])[:6]))
    scen = ('<div class="scen">'
            '<figure><span class="box solid"></span>AC<em>solid</em></figure>'
            '<figure><span class="box outlined"></span>PL<em>outlined</em></figure>'
            '<figure><span class="box hatched"></span>FC<em>outlined + hatched</em></figure>'
            '<figure><span class="box py"></span>PY<em>lighter solid</em></figure></div>')
    palette = (
        '<div class="fcard"><h3>Palette &amp; scenario tokens</h3>'
        '<p class="dlabel">Semantic — reserved, never the brand colour</p><div class="swatches">' + sw + '</div>'
        '<p class="dlabel" style="margin:16px 0 0">Series — brand data colours</p><div class="swatches">' + dat + '</div>'
        '<p class="dlabel" style="margin:16px 0 0">IBCS scenario (Standards 2.0, UN 3.2) — fill distinguishes, colour is shared</p>' + scen + '</div>'
    )
    return f'<div class="founds">{prin}{"".join(profs)}{palette}</div>'


def render_artifact_html() -> str:
    idx = _index()
    matrix = render_acceptance.load_matrix()
    impl = _implemented()

    # render-proof across ALL tracks: how many applicable realizations actually render headlessly
    _cells = [c for v in matrix["idioms"].values() for c in v.values()]
    proven = sum(1 for c in _cells if c.get("status") == "rendered")
    applicable = sum(1 for c in _cells if c.get("status") in ("rendered", "partial", "structural"))
    n_scen = len(matrix["scenarios"])

    qpills = []
    for pid, pp in idx["purposes"].items():
        cands = ",".join(dict.fromkeys(_base_idiom(c) for c in pp["candidates"]))
        qpills.append(
            f'<button class="qpill" data-cands="{_esc(cands)}" data-q="{_esc(pp["question"])}">'
            f'<span class="q">{_esc(pp["question"])}</span>'
            f'<span class="b">{_esc(pp["best"])}</span></button>'
        )

    zones_present = [z for z in ("pulse", "analysis", "detail")
                     if any(z in ((render.load_entry(i)["zone"]) if isinstance(render.load_entry(i)["zone"], list)
                            else [render.load_entry(i)["zone"]]) for i in impl)]
    zone_chips = '<span class="lbl">Zone</span><button class="chip on" data-val="">All</button>' + "".join(
        f'<button class="chip" data-val="{_esc(z)}">{_esc(z)}</button>' for z in zones_present)
    tool_chips = '<span class="lbl">Tool</span><button class="chip on" data-val="">All</button>' + "".join(
        f'<button class="chip" data-val="{_esc(t)}">{_esc(TOOL_SHORT[t])}</button>' for t in SCHEMA["tools"])
    proof_chips = ('<span class="lbl">Proof</span><button class="chip on" data-val="">All</button>'
                   '<button class="chip" data-val="proven">Deneb-proven</button>'
                   '<button class="chip" data-val="gated">Has gated</button>')

    tiles = "".join(_tile(i, matrix) for i in impl)
    details = "".join(_detail(i, matrix) for i in impl)

    return (
        f'<title>ALUCA · Visual Library</title>\n<style>{_CSS}</style>\n'
        f'<header class="nav"><div class="nav-in">'
        f'<a class="brand" href="#top"><span class="mk">{_BRAND_MK}</span>ALUCA <span class="sub">Visual Library</span></a>'
        f'<nav class="nav-links"><a href="#chooser">Chooser</a><a href="#gallery">Gallery</a>'
        f'<a href="#foundations">Foundations</a></nav>'
        f'<div class="nav-tools"><label class="search">{_ICON_SEARCH}'
        f'<input id="q" type="search" placeholder="Search idioms…" aria-label="Search idioms" autocomplete="off"></label>'
        f'<button class="iconbtn" id="theme" type="button" aria-label="Toggle theme" title="Theme">{_ICON_THEME}</button>'
        f'</div></div></header>\n'

        f'<main class="wrap" id="top">\n'
        f'<section class="hero">'
        f'<p class="eyebrow">Report Design System · a living catalog</p>'
        f'<h1>The visual language of your reports.</h1>'
        f'<p class="lede">Browse governed chart idioms for Power BI, Deneb and the web — each a real preview with '
        f'runnable, byte-for-byte-frozen code per tool. Open one to copy it.</p>'
        f'<div class="metabar">'
        f'<span class="chipstat"><b>{len(impl)}</b>idioms</span>'
        f'<span class="chipstat"><b>4</b>tool tracks</span>'
        f'<span class="chipstat"><b>3</b>notations · house / IBCS / print-safe</span>'
        f'<span class="chipstat pos"><b>{proven}/{applicable}</b>realizations render-proven</span>'
        f'</div>'
        f'<div class="legend"><span><i class="dot d-ok"></i> proven — Deneb rasterized ({n_scen} scenarios), SVG-DAX SVG rasterized, Recharts React-rendered</span>'
        f'<span><i class="dot d-gate"></i> gated — Power BI native (PBIR is a config; needs Desktop)</span>'
        f'<span><i class="dot d-na"></i> tool n/a</span></div>'
        f'</section>\n'

        f'<section class="section" id="chooser"><div class="section-head"><div>'
        f'<span class="k">Chooser</span><h2>Start from the question</h2>'
        f'<p>Pick a question to filter the gallery to its best-fit idioms.</p></div></div>'
        f'<div class="chooser">{"".join(qpills)}</div></section>\n'

        f'<section class="section" id="gallery"><div class="section-head"><div>'
        f'<span class="k">Catalog</span><h2>Idioms <span class="count" id="count">{len(impl)}</span></h2></div></div>'
        f'<div class="toolbar"><div class="chips" data-filter="zone">{zone_chips}</div>'
        f'<div class="chips" data-filter="tool">{tool_chips}</div>'
        f'<div class="chips" data-filter="proof">{proof_chips}</div></div>'
        f'<div class="pickbar" id="pickbar"><span>Question: <b id="pickq"></b></span>'
        f'<button id="pickclear" type="button">Clear</button></div>'
        f'<div class="gallery" id="grid">{tiles}</div>'
        f'<p class="empty" id="empty">No idiom matches those filters.</p></section>\n'

        f'<section class="section" id="foundations"><div class="section-head"><div>'
        f'<span class="k">Foundations</span><h2>The rules behind the picture</h2>'
        f'<p>Why these visuals, the notation profiles they can be drawn in, and the governed colour tokens.</p>'
        f'</div></div>{_foundations_html()}</section>\n'
        f'</main>\n'

        f'<div class="details-store" hidden>{details}</div>\n'
        f'<div class="modal" id="modal" aria-modal="true" role="dialog"><div class="backdrop"></div>'
        f'<div class="modal-card"><button class="modal-close" type="button" aria-label="Close">{_ICON_CLOSE}</button>'
        f'<div id="modal-body"></div></div></div>\n'

        f'<footer class="wrap foot">Deny (never emit): {" · ".join("<code>"+_esc(d)+"</code>" for d in idx["deny"])}.<br>'
        f'Generated from <b>core/templates/page_templates/visual_library/</b> by <code>render_docs.py</code>; '
        f'determinism frozen in <code>golden/</code>, render-proof in <code>acceptance/validation_matrix.json</code>.</footer>\n'
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
