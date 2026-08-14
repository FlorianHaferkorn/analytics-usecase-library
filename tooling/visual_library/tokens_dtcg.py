"""tokens_dtcg.py — export the governed design tokens in the W3C DTCG format.

`color_semantics.yaml` and `layout_grid.yaml` are ALUCA's SoT, but their shape is bespoke. The
Design Tokens Community Group format (W3C, first stable version 2025.10) is the vendor-neutral
interchange that Style Dictionary, Figma, Penpot and other tools read directly. This deterministically
projects the SoT into `tokens.dtcg.json` so the same governed colours/dimensions are portable, without
making DTCG the source of truth (the YAML stays authoritative; this is a generated view).

DTCG leaves carry `$value` (+ optional `$description`); groups carry `$type` (colours as hex strings,
dimensions as `{value, unit}` objects per the 2025.10 spec).

CLI:
  tokens_dtcg.py build [--out <path>]   # (re)generate tokens.dtcg.json from the SoT
  tokens_dtcg.py check [--json]         # committed export == fresh projection? (rc=1 on drift)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

TOKENS_DIR = render.LIB.parent / "tokens"
OUT = TOKENS_DIR / "tokens.dtcg.json"


def _color(value: str, desc: "str | None" = None) -> dict:
    t = {"$value": value}
    if desc:
        t["$description"] = desc
    return t


def _dim(px: float) -> dict:
    return {"$value": {"value": px, "unit": "px"}}


def build_tokens() -> dict:
    cs = yaml.safe_load((TOKENS_DIR / "color_semantics.yaml").read_text(encoding="utf-8"))
    lg = yaml.safe_load((TOKENS_DIR / "layout_grid.yaml").read_text(encoding="utf-8"))

    color: dict = {"$type": "color"}
    color["semantic"] = {k: _color(v) for k, v in cs.get("semantic", {}).items()}
    color["severity_tint"] = {k: _color(v) for k, v in cs.get("severity_tints", {}).items()}
    brand = cs.get("brand", {})
    color["brand"] = {"primary": _color(brand.get("primary")), "secondary": _color(brand.get("secondary"))}
    color["brand"]["data"] = {f"slot_{i}": _color(c) for i, c in enumerate(brand.get("data_colors", []))}
    color["surface"] = {k: _color(v) for k, v in cs.get("surface", {}).items()}
    color["text"] = {k: _color(v) for k, v in cs.get("text", {}).items()}
    color["border"] = {k: _color(v) for k, v in cs.get("border", {}).items()}
    color["colorblind_safe"] = {k: _color(v) for k, v in cs.get("colorblind_safe", {}).items()}
    cvd = cs.get("categorical_cvd_safe", {})
    color["categorical_cvd_safe"] = {
        c["name"]: _color(c["hex"], f"contrast_on_white {c['contrast_on_white']}:1; "
                                    f"solid_safe_on_white {c['solid_safe_on_white']}")
        for c in cvd.get("colors", [])
    }

    sp = lg.get("spacing", {})
    comp = lg.get("computed", {})
    canv = lg.get("canvas", {})
    dimension: dict = {"$type": "dimension",
                       "spacing": {k: _dim(v) for k, v in sp.items()},
                       "logical_unit": {"width": _dim(comp.get("lu_w")), "height": _dim(comp.get("lu_h"))},
                       "canvas": {name: {"width": _dim(c["width"]), "height": _dim(c["height"])}
                                  for name, c in canv.items()}}

    return {
        "$description": "ALUCA governed design tokens (DTCG export; generated from color_semantics.yaml "
                        "+ layout_grid.yaml — the YAML remains the source of truth).",
        "color": color,
        "dimension": dimension,
    }


def load_tokens() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def check() -> dict:
    fresh = build_tokens()
    try:
        committed = load_tokens()
    except FileNotFoundError:
        return {"in_sync": False, "reason": "tokens.dtcg.json missing — run `tokens_dtcg.py build`"}
    return {"in_sync": fresh == committed,
            "reason": "up to date" if fresh == committed else "stale — run `tokens_dtcg.py build`"}


def iter_leaves(node: dict, path=()):
    """Yield (path, token) for every DTCG leaf (a dict carrying $value)."""
    for k, v in node.items():
        if k.startswith("$"):
            continue
        if isinstance(v, dict) and "$value" in v:
            yield path + (k,), v
        elif isinstance(v, dict):
            yield from iter_leaves(v, path + (k,))


def main(argv: "list[str]") -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "build":
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else OUT
        tok = build_tokens()
        out.write_text(json.dumps(tok, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        n = sum(1 for _ in iter_leaves(tok))
        print(f"wrote {n} DTCG tokens -> {out}")
        return 0
    if cmd == "check":
        r = check()
        print(json.dumps(r) if "--json" in argv else f"in_sync={r['in_sync']} — {r['reason']}")
        return 0 if r["in_sync"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
