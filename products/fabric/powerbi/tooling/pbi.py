#!/usr/bin/env python3
"""
pbi.py — agent-read ergonomics over ``dist/`` (Epic D).

Read and bulk-edit the generated PBIP output with agent-friendly commands, with
**no third-party dependency**. This is the in-house parity for the useful parts of
``pbir.tools`` (``ls`` / ``tree`` / ``model`` / ``set``) — that CLI is
non-commercial-licensed and is a *benchmark only*, never bundled.

Subcommands::

    pbi inspect --report COM-001            # pages -> visuals -> bindings
    pbi inspect --model Commercial          # tables -> columns/measures/relationships
    pbi inspect --all [--json]              # everything under dist/
    pbi set --type lineChart --set visual.objects.general[0].properties.x=1  # bulk-set (dry-run)
    pbi set ... --apply                     # write the change

Reuses the trusted PBIR parser (``tooling.report_quality.pbir``) that H7 relies on.
``set`` refuses to touch ``visual.query`` (bindings), so a bulk-set is H7-invariant
by construction.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root

from tooling.report_quality.pbir import (
    iter_report_dirs,
    load_json,
    parse_report,
    write_json,
)

_SCRIPT_DIR = Path(__file__).resolve().parent
_DIST = _SCRIPT_DIR.parent / "dist"

_MEASURE_RE = re.compile(r"^\tmeasure '([^']+)'|^\tmeasure ([A-Za-z_][\w]*)")
_COLUMN_RE = re.compile(r"^\tcolumn '([^']+)'|^\tcolumn ([A-Za-z_][\w ]*?)\s*$")


# ─────────────────────────────────────────────────────────────────────────────
# Binding extraction
# ─────────────────────────────────────────────────────────────────────────────

def visual_bindings(visual_json: dict) -> Dict[str, List[str]]:
    """Return ``{role: ["Measure:Net Sales Amount", "Column:dim_date.X", ...]}`` from
    a visual's queryState projections."""
    out: Dict[str, List[str]] = {}
    qs = (((visual_json.get("visual") or {}).get("query") or {}).get("queryState") or {})
    for role, spec in qs.items():
        refs: List[str] = []
        for proj in (spec.get("projections") or []):
            field = proj.get("field") or {}
            if "Measure" in field:
                refs.append(f"Measure:{field['Measure'].get('Property', '?')}")
            elif "Column" in field:
                col = field["Column"]
                entity = (col.get("Expression") or {}).get("SourceRef", {}).get("Entity", "?")
                refs.append(f"Column:{entity}.{col.get('Property', '?')}")
            else:
                refs.append(proj.get("nativeQueryRef", "?"))
        out[role] = refs
    return out


def inspect_report(report_dir: Path) -> dict:
    parsed = parse_report(report_dir)
    pages = []
    for page in parsed.pages.values():
        visuals = []
        for vname, vjson in page.visuals.items():
            vis = vjson.get("visual") or {}
            pos = vjson.get("position") or {}
            visuals.append({
                "name": vname,
                "type": vis.get("visualType", "?"),
                "position": {k: pos.get(k) for k in ("x", "y", "width", "height")},
                "bindings": visual_bindings(vjson),
            })
        pages.append({"name": page.name, "display_name": page.display_name, "visuals": visuals})
    return {"report": report_dir.name, "pages": pages}


# ─────────────────────────────────────────────────────────────────────────────
# Semantic model parsing (TMDL — stdlib only)
# ─────────────────────────────────────────────────────────────────────────────

def _measures_in(tmdl: str) -> List[str]:
    out = []
    for line in tmdl.splitlines():
        m = _MEASURE_RE.match(line)
        if m:
            out.append(m.group(1) or m.group(2))
    return out


def _columns_in(tmdl: str) -> List[Tuple[str, bool]]:
    lines = tmdl.splitlines()
    out: List[Tuple[str, bool]] = []
    i = 0
    while i < len(lines):
        m = _COLUMN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = (m.group(1) or m.group(2) or "").strip()
        j = i + 1
        hidden = False
        while j < len(lines) and (lines[j].startswith("\t\t") or lines[j].strip() == ""):
            if lines[j].strip() == "isHidden":
                hidden = True
            j += 1
        out.append((name, hidden))
        i = j
    return out


def inspect_model(model_dir: Path) -> dict:
    def_dir = model_dir / "definition"
    tbl_dir = def_dir / "tables"
    tables = []
    measures: List[str] = []
    for f in sorted(tbl_dir.glob("*.tmdl")) if tbl_dir.is_dir() else []:
        text = f.read_text(encoding="utf-8")
        if f.stem.startswith("_"):
            measures.extend(_measures_in(text))
            continue
        cols = _columns_in(text)
        tables.append({
            "name": f.stem,
            "columns": [{"name": n, "hidden": h} for n, h in cols],
            "measure_table": False,
        })
    rels = sorted((def_dir / "relationships").glob("*.tmdl")) if (def_dir / "relationships").is_dir() else []
    return {
        "model": model_dir.name,
        "tables": tables,
        "measures": sorted(measures),
        "relationship_count": len(rels),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Text rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_report_text(rep: dict) -> str:
    out = [rep["report"]]
    for page in rep["pages"]:
        out.append(f"  {page['name']}  \"{page['display_name']}\"")
        for v in page["visuals"]:
            p = v["position"]
            out.append(f"    {v['name']:<18} {v['type']:<16} @ ({p.get('x')},{p.get('y')} {p.get('width')}x{p.get('height')})")
            for role, refs in v["bindings"].items():
                if refs:
                    out.append(f"        {role}: {', '.join(refs)}")
    return "\n".join(out)


def render_model_text(model: dict) -> str:
    out = [model["model"]]
    out.append(f"  measures: {len(model['measures'])}")
    if model["measures"]:
        out.append("    " + ", ".join(model["measures"]))
    out.append(f"  relationships: {model['relationship_count']}")
    for t in model["tables"]:
        hidden = sum(1 for c in t["columns"] if c["hidden"])
        out.append(f"  {t['name']:<22} {len(t['columns'])} columns ({hidden} hidden)")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# Bulk-set (parity with `pbir set`) — presentation only, never bindings
# ─────────────────────────────────────────────────────────────────────────────

_PATH_TOKEN = re.compile(r"([^.\[\]]+)(?:\[(\d+)\])?")


def _parse_path(path: str) -> List[Tuple[str, int | None]]:
    return [(m.group(1), int(m.group(2)) if m.group(2) is not None else None) for m in _PATH_TOKEN.finditer(path)]


def set_in(obj: dict, path: str, value: Any) -> None:
    """Set ``value`` at a dotted ``path`` (``a.b[0].c``), creating intermediates."""
    tokens = _parse_path(path)
    cur: Any = obj
    for i, (key, idx) in enumerate(tokens):
        last = i == len(tokens) - 1
        if last:
            if idx is None:
                cur[key] = value
            else:
                cur.setdefault(key, [])
                while len(cur[key]) <= idx:
                    cur[key].append({})
                cur[key][idx] = value
            return
        nxt = cur.get(key)
        if idx is None:
            if not isinstance(nxt, dict):
                nxt = {}
                cur[key] = nxt
            cur = nxt
        else:
            if not isinstance(nxt, list):
                nxt = []
                cur[key] = nxt
            while len(nxt) <= idx:
                nxt.append({})
            cur = nxt[idx]


def bulk_set(
    dist_root: Path,
    path: str,
    value: Any,
    report_glob: str = "*",
    page_glob: str = "*",
    visual_glob: str = "*",
    type_glob: str = "*",
    apply: bool = False,
) -> List[str]:
    """Set ``value`` at ``path`` on every visual matching the globs. Returns the list
    of changed ``report/page/visual`` pointers. ``path`` must not target bindings."""
    if path.startswith("visual.query") or path == "visual.query":
        raise ValueError("refusing to bulk-set visual.query (bindings) — H7-protected")
    changed: List[str] = []
    for report_dir in iter_report_dirs(dist_root):
        if not fnmatch.fnmatch(report_dir.name, report_glob) and report_glob not in report_dir.name:
            continue
        parsed = parse_report(report_dir)
        for page in parsed.pages.values():
            if not (fnmatch.fnmatch(page.name, page_glob) or fnmatch.fnmatch(page.display_name, page_glob)):
                continue
            for vname, vjson in page.visuals.items():
                if not fnmatch.fnmatch(vname, visual_glob):
                    continue
                vtype = (vjson.get("visual") or {}).get("visualType", "")
                if not fnmatch.fnmatch(vtype, type_glob):
                    continue
                set_in(vjson, path, value)
                changed.append(f"{report_dir.name}/{page.name}/{vname}")
                if apply:
                    write_json(page.page_dir / "visuals" / vname / "visual.json", vjson)
    return changed


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_reports(dist_root: Path, selector: str | None) -> List[Path]:
    reports = iter_report_dirs(dist_root)
    if not selector:
        return reports
    return [r for r in reports if selector in r.name or fnmatch.fnmatch(r.name, selector)]


def _cmd_inspect(args) -> int:
    dist_root = Path(args.dist_root)
    payload: Dict[str, Any] = {}
    if args.model:
        model_dir = dist_root / f"{args.model}.SemanticModel"
        if not model_dir.is_dir():
            print(f"model not found: {model_dir}", file=sys.stderr)
            return 1
        payload["model"] = inspect_model(model_dir)
    if args.report or (not args.model and not args.all):
        for r in _resolve_reports(dist_root, args.report):
            payload.setdefault("reports", []).append(inspect_report(r))
    if args.all:
        for r in iter_report_dirs(dist_root):
            payload.setdefault("reports", []).append(inspect_report(r))
        for m in sorted(dist_root.glob("*.SemanticModel")):
            payload.setdefault("models", []).append(inspect_model(m))

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if "model" in payload:
        print(render_model_text(payload["model"]))
    for m in payload.get("models", []):
        print(render_model_text(m))
    for rep in payload.get("reports", []):
        print(render_report_text(rep))
    return 0


def _cmd_set(args) -> int:
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value  # treat as bare string
    try:
        changed = bulk_set(
            Path(args.dist_root), args.path, value,
            report_glob=args.report or "*", page_glob=args.page or "*",
            visual_glob=args.visual or "*", type_glob=args.type or "*",
            apply=args.apply,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    verb = "set" if args.apply else "would set (dry-run)"
    print(f"{verb} {args.path} = {json.dumps(value)} on {len(changed)} visual(s):")
    for c in changed:
        print(f"    {c}")
    if not args.apply and changed:
        print("  (re-run with --apply to write)")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pbi", description="Agent-read ergonomics over dist/ (Epic D).")
    parser.add_argument("--dist-root", default=str(_DIST))
    sub = parser.add_subparsers(dest="cmd", required=True)

    insp = sub.add_parser("inspect", help="List report pages/visuals/bindings and model tables/measures.")
    insp.add_argument("--report", "-r", help="Report id/name selector (substring or glob)")
    insp.add_argument("--model", "-m", help="Domain semantic model, e.g. Commercial")
    insp.add_argument("--all", "-a", action="store_true", help="Everything under dist/")
    insp.add_argument("--json", action="store_true")
    insp.set_defaults(func=_cmd_inspect)

    st = sub.add_parser("set", help="Wildcard bulk-set a visual property (dry-run unless --apply).")
    st.add_argument("setexpr", metavar="PATH=VALUE", help="e.g. visual.objects.general[0].properties.x=1")
    st.add_argument("--report", "-r")
    st.add_argument("--page", "-p")
    st.add_argument("--visual", "-v")
    st.add_argument("--type", "-t", help="visualType glob, e.g. lineChart")
    st.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    st.set_defaults(func=_cmd_set)

    args = parser.parse_args(argv)
    if args.cmd == "set":
        if "=" not in args.setexpr:
            parser.error("set expects PATH=VALUE")
        args.path, args.value = args.setexpr.split("=", 1)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
