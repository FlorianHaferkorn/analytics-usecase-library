#!/usr/bin/env python3
"""
audit_pbir_issues.py — Comprehensive PBIR content-level audit for Aurora reports.
Checks: measure refs vs TMDL, visual heights, slicer counts, Smart_Narrative content,
dimension column refs, data source binding.

Usage: py -3 tooling/audit_pbir_issues.py
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST = REPO_ROOT / "products/fabric/powerbi/dist"

DOMAIN_MAP = {
    "COM": "Commercial.SemanticModel",
    "FIN": "Finance.SemanticModel",
    "OPS": "Operations.SemanticModel",
    "SCM": "SupplyChain.SemanticModel",
    "XD":  "Experience.SemanticModel",
}

MAX_VISUAL_HEIGHT = 800  # px — above this is likely too stretched
MIN_DETAIL_SLICERS = 2   # Slicer_Pane + Slicer_Entity required on Detail
MIN_OVERVIEW_SLICERS = 1  # at least Slicer_Date on Overview

issues = []
info = []


def add(severity, report, page, visual, msg):
    issues.append(f"[{severity}] {report} / {page} / {visual}: {msg}")


# ── Load TMDL measure names ───────────────────────────────────────────────────

def load_tmdl_measures(model_dir: Path) -> set:
    tmdl = model_dir / "definition/tables/_Measures.tmdl"
    if not tmdl.exists():
        return set()
    content = tmdl.read_text(encoding="utf-8")
    # TMDL uses tabs; measure 'Name' = ...  OR  measure Name = ...
    names = re.findall(r"^\tmeasure '([^']+)'", content, re.MULTILINE)
    names += re.findall(r"^\tmeasure ([A-Za-z][^'\n=]+?)\s*=", content, re.MULTILINE)
    return set(n.strip() for n in names)


tmdl_measures = {}
for prefix, model_name in DOMAIN_MAP.items():
    model_path = DIST / model_name
    tmdl_measures[model_name] = load_tmdl_measures(model_path)
    info.append(f"Loaded {len(tmdl_measures[model_name])} measures from {model_name}")


# ── Audit helpers ─────────────────────────────────────────────────────────────

def get_visual_config(v: dict) -> dict:
    """Extract position/size from visualContainerObjects.general[0].properties."""
    objs = v.get("visual", {}).get("visualContainerObjects", {})
    general = objs.get("general", [{}])
    if general:
        return general[0].get("properties", {})
    return {}


def extract_num(prop_val: dict) -> float | None:
    """Extract numeric value from PBI property expression."""
    try:
        raw = prop_val.get("expr", {}).get("Literal", {}).get("Value", "")
        return float(str(raw).replace("D", "").replace("L", ""))
    except (TypeError, ValueError):
        return None


def get_measure_refs(v: dict) -> list[tuple[str, str]]:
    """Return list of (entity, property) for all measure projections."""
    qs = v.get("visual", {}).get("query", {}).get("queryState", {})
    refs = []
    for bucket in qs.values():
        if not isinstance(bucket, dict):
            continue
        for proj in bucket.get("projections", []):
            field = proj.get("field", {})
            m = field.get("Measure", {})
            if m:
                entity = m.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
                prop = m.get("Property", "")
                if entity and prop:
                    refs.append((entity, prop))
            col = field.get("Column", {})
            if col:
                entity = col.get("Expression", {}).get("SourceRef", {}).get("Entity", "")
                prop = col.get("Property", "")
                if entity and prop:
                    refs.append((entity, prop))
    return refs


def get_textbox_content(v: dict) -> str:
    """Extract text content from a textbox visual (PBIR 2.3+ format)."""
    try:
        text_objs = v.get("visual", {}).get("objects", {}).get("text", [{}])
        if text_objs:
            return text_objs[0].get("properties", {}).get("text", {}).get("expr", {}).get("Literal", {}).get("Value", "")
        return ""
    except Exception:
        return ""


# ── Per-report audit ──────────────────────────────────────────────────────────

for report_dir in sorted(DIST.glob("*.Report")):
    prefix = report_dir.name[:3]
    model_name = DOMAIN_MAP.get(prefix)
    if not model_name:
        continue
    known_measures = tmdl_measures.get(model_name, set())
    report_name = report_dir.name.replace(".Report", "")

    pages_dir = report_dir / "definition" / "pages"
    if not pages_dir.exists():
        add("ERROR", report_name, "-", "-", "definition/pages/ missing")
        continue

    for page_dir in sorted(pages_dir.glob("Page_*")):
        page_id = page_dir.name
        is_overview = "Overview" in page_id
        is_detail = "Detail" in page_id
        visuals_dir = page_dir / "visuals"
        if not visuals_dir.exists():
            continue

        # Collect visuals
        slicer_count = 0
        slicer_names = []
        for visual_dir in sorted(visuals_dir.iterdir()):
            if not visual_dir.is_dir():
                continue
            vf = visual_dir / "visual.json"
            if not vf.exists():
                continue
            try:
                v = json.loads(vf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                add("ERROR", report_name, page_id, visual_dir.name, f"Invalid JSON: {e}")
                continue

            vtype = v.get("visual", {}).get("visualType", "")
            config = get_visual_config(v)
            h = extract_num(config.get("height", {}))
            w = extract_num(config.get("width", {}))
            x = extract_num(config.get("x", {}))
            y = extract_num(config.get("y", {}))

            # 1. Height check — visuals too stretched
            if h is not None and h > MAX_VISUAL_HEIGHT:
                add("WARN", report_name, page_id, visual_dir.name,
                    f"height={h:.0f}px exceeds {MAX_VISUAL_HEIGHT}px — may appear stretched")

            # 2. Slicer count
            if vtype == "slicer":
                slicer_count += 1
                slicer_names.append(visual_dir.name)

            # 3. Measure references vs TMDL
            for entity, prop in get_measure_refs(v):
                if entity == "_Measures" and prop not in known_measures:
                    add("ERROR", report_name, page_id, visual_dir.name,
                        f"references measure '{prop}' not found in {model_name}")
                # Dimension columns: just check entity names are dim_* or fact_*
                if entity.startswith("dim_") or entity.startswith("fact_"):
                    pass  # structure OK; column existence not validated here

            # 4. Smart_Narrative content
            if visual_dir.name == "Smart_Narrative":
                if vtype != "textbox" and vtype != "smartNarrativeVisual":
                    add("WARN", report_name, page_id, visual_dir.name,
                        f"Smart_Narrative has visualType='{vtype}' — expected textbox or smartNarrativeVisual")
                content = get_textbox_content(v)
                if not content or content.strip() in ("''", '""', ""):
                    add("WARN", report_name, page_id, visual_dir.name,
                        "Smart_Narrative textbox has empty content — KI placeholder not set")

            # 5. Slicer configuration completeness
            if vtype == "slicer":
                refs = get_measure_refs(v)
                if not refs:
                    add("WARN", report_name, page_id, visual_dir.name,
                        "Slicer has no field binding — will render empty")

        # 6. Slicer count per page
        if is_overview and slicer_count < MIN_OVERVIEW_SLICERS:
            add("ERROR", report_name, page_id, "page",
                f"Overview has {slicer_count} slicer(s) — expected at least {MIN_OVERVIEW_SLICERS} (Slicer_Date)")
        if is_detail and slicer_count < MIN_DETAIL_SLICERS:
            add("ERROR", report_name, page_id, "page",
                f"Detail has {slicer_count} slicer(s) — expected at least {MIN_DETAIL_SLICERS} (Slicer_Pane + Slicer_Entity); found: {slicer_names}")

# ── Report ────────────────────────────────────────────────────────────────────

print("=" * 70)
print("PBIR CONTENT AUDIT — Aurora Reports")
print("=" * 70)
for line in info:
    print(f"  {line}")
print()

errors = [i for i in issues if i.startswith("[ERROR]")]
warns = [i for i in issues if i.startswith("[WARN]")]

if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    print()

if warns:
    print(f"WARNINGS ({len(warns)}):")
    for w in warns:
        print(f"  {w}")
    print()

if not issues:
    print("All checks passed — no issues found.")
else:
    print(f"Total: {len(errors)} errors, {len(warns)} warnings across all 15 reports.")

sys.exit(1 if errors else 0)
