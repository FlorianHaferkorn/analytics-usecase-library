#!/usr/bin/env python3
"""ALUCA reference graph — use-case-rooted map of the core artifact families.

Use cases are the content root. From the 16 use cases we walk:
  use_case --(bracket)--> KPIs, action_codes, data_contract
  action_code --(use_case_links / kpis / nested metric_kpi_id)--> use_cases, KPIs
  decision_spine --(DecisionSpine_UseCase_Map / nested metric_kpi_id)--> use_cases, KPIs
  KPI --(depends_on_measures)--> KPIs        (transitive)
  KPI --(technical.lineage)--> fact.Column   (data contract)

Anything in the catalog/action-code families NOT reachable from a use case (and not on
the planned.yaml roadmap) is an *orphan* candidate. Anything a use case / action code /
decision spine references that does NOT exist is a *dangling* reference.

Usage:
  python tooling/reference_graph.py            # write docs/architecture/reference_graph.md
  python tooling/reference_graph.py --check    # exit 1 if dangling refs exist (CI gate)
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
UC_DIR = REPO / "core/usecases/core"
KPI_DIR = REPO / "core/kpi_catalog/kpis"
AC_DIR = REPO / "core/action_codes"
SPINE_DIR = AC_DIR / "decision_spines"
PLANNED = REPO / "core/kpi_catalog/planned.yaml"
REPORT = REPO / "docs/architecture/reference_graph.md"


def _load(p: Path) -> dict:
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _collect(obj, key: str) -> list:
    """All string values stored under `key`, anywhere in a nested dict/list."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and isinstance(v, str):
                out.append(v)
            else:
                out += _collect(v, key)
    elif isinstance(obj, list):
        for x in obj:
            out += _collect(x, key)
    return out


def build():
    g: dict = {"use_cases": {}, "kpis": {}, "action_codes": {}, "decision_spines": {}, "measures": {}}

    # --- KPI catalog ---
    for p in KPI_DIR.glob("*.yaml"):
        if p.name == "_index.yaml":
            continue
        d = _load(p)
        g["kpis"][p.stem] = {
            "depends_on": list((d.get("technical") or {}).get("depends_on_measures") or []),
            "lineage": list((d.get("technical") or {}).get("lineage") or []),
        }
    planned = {e.get("kpi_id") for e in (_load(PLANNED) if PLANNED.exists() else []) if isinstance(e, dict)}

    # --- semantic measures: only the structured measure.kpi_id_ref -> KPI edge ---
    # (registry + view drift are enforced separately by test_measure_dictionary_files;
    #  fuzzy measure->measure prose deps are deliberately NOT modelled — they'd make the gate flaky)
    for p in (REPO / "core/semantic_models").rglob("measures/*.yaml"):
        d = _load(p)
        if not isinstance(d, dict) or "measure_name" not in d:
            continue
        g["measures"][p.stem] = {"kpi_id_ref": (d.get("kpi_id_ref") or "").strip()}

    # --- action codes (exclude decision_spines/ and *_business_case.yaml) ---
    for p in AC_DIR.rglob("*.yaml"):
        if p.name.endswith("_business_case.yaml") or SPINE_DIR in p.parents:
            continue
        d = _load(p)
        acid = d.get("id")
        if not acid:
            continue
        links = d.get("use_case_links") or {}
        kp = d.get("kpis") or {}
        kpis = list(kp.get("trigger_kpis") or []) + list(kp.get("guardrail_kpis") or []) + list(kp.get("outcome_kpis") or [])
        kpis += _collect(d, "metric_kpi_id")  # nested guardrail / escalation-level refs
        g["action_codes"][acid] = {
            "use_cases": list(links.get("core_use_cases") or []) + list(links.get("related_use_cases") or []),
            "kpis": sorted(set(kpis)),
        }

    # --- decision spines (own family; linked via DecisionSpine_UseCase_Map.yaml) ---
    spine_map = (_load(SPINE_DIR / "DecisionSpine_UseCase_Map.yaml").get("decision_spines") or {}) if SPINE_DIR.exists() else {}
    for p in SPINE_DIR.glob("*.yaml") if SPINE_DIR.exists() else []:
        if p.name == "DecisionSpine_UseCase_Map.yaml":
            continue
        d = _load(p)
        sid = d.get("id")
        if not sid:
            continue
        g["decision_spines"][sid] = {
            "use_cases": list((spine_map.get(sid) or {}).get("use_cases") or []),
            "kpis": sorted(set(_collect(d, "metric_kpi_id"))),
        }

    # --- use cases (brackets) ---
    for d in sorted(UC_DIR.iterdir()):
        b = d / "UseCase_Bracket.yaml"
        if not b.exists():
            continue
        bd = _load(b)
        o = bd.get("orchestration") or {}
        kpis = ([o["strategic_kpi_id"]] if o.get("strategic_kpi_id") else []) + \
               list(o.get("influencing_kpi_ids") or []) + list(o.get("supporting_kpi_ids") or [])
        g["use_cases"][bd.get("id", d.name)] = {
            "folder": d.name,
            "kpis": kpis,
            "action_codes": list(o.get("action_code_ids") or []),
            "data_contract": (bd.get("overrides") or {}).get("data_contract_ref"),
            "has_evidence_pack": (d / "Domain_Evidence_Pack.yaml").exists(),
            "has_factsheet": (d / "Business_Factsheet.md").exists(),
        }

    # --- reachability fixpoint from the use cases ---
    uc = g["use_cases"]
    reach_ac = {a for u in uc.values() for a in u["action_codes"]}
    reach_ac |= {acid for acid, a in g["action_codes"].items() if set(a["use_cases"]) & set(uc)}
    reach_spine = {sid for sid, s in g["decision_spines"].items() if set(s["use_cases"]) & set(uc)}

    reach_kpi = {k for u in uc.values() for k in u["kpis"]}
    reach_kpi |= {k for acid in reach_ac for k in g["action_codes"].get(acid, {}).get("kpis", [])}
    reach_kpi |= {k for sid in reach_spine for k in g["decision_spines"].get(sid, {}).get("kpis", [])}
    frontier = set(reach_kpi)
    while frontier:
        nxt = set()
        for k in frontier:
            for dep in g["kpis"].get(k, {}).get("depends_on", []):
                if dep not in reach_kpi:
                    reach_kpi.add(dep); nxt.add(dep)
        frontier = nxt

    catalog = set(g["kpis"])
    all_ac = set(g["action_codes"])
    backed_kpis = {m["kpi_id_ref"] for m in g["measures"].values() if m["kpi_id_ref"]}
    referenced_kpi = ({k for u in uc.values() for k in u["kpis"]}
                      | {k for a in g["action_codes"].values() for k in a["kpis"]}
                      | {k for s in g["decision_spines"].values() for k in s["kpis"]})
    referenced_ac = {a for u in uc.values() for a in u["action_codes"]}

    return g, dict(
        planned=planned,
        reach_kpi=reach_kpi & catalog,
        reach_ac=reach_ac & all_ac,
        reach_spine=reach_spine,
        orphan_kpi=sorted(catalog - reach_kpi - planned),
        orphan_ac=sorted(all_ac - reach_ac),
        orphan_spine=sorted(set(g["decision_spines"]) - reach_spine),
        dangling_kpi=sorted(referenced_kpi - catalog),
        dangling_ac=sorted(referenced_ac - all_ac),
        dangling_measure_kpi=sorted(backed_kpis - catalog),
        kpis_without_measure=sorted((reach_kpi & catalog) - backed_kpis),
        n_measures=len(g["measures"]), n_backed=len(backed_kpis & catalog),
        catalog=catalog, all_ac=all_ac,
    )


def render(g, a) -> str:
    uc = g["use_cases"]
    L = ["# ALUCA — Reference Graph",
         "",
         "> Generated by `tooling/reference_graph.py`. Use cases are the content root; every other",
         "> artifact is judged by reachability from them. Do not edit by hand — regenerate.",
         "",
         "## Coverage",
         "",
         f"- Use cases: **{len(uc)}**  (evidence packs: {sum(u['has_evidence_pack'] for u in uc.values())}/{len(uc)}, factsheets: {sum(u['has_factsheet'] for u in uc.values())}/{len(uc)})",
         f"- KPIs in catalog: **{len(a['catalog'])}**  — reachable: **{len(a['reach_kpi'])}**, roadmap (planned.yaml): {len(a['planned'])}, orphan: **{len(a['orphan_kpi'])}**",
         f"- Action codes: **{len(a['all_ac'])}**  — reachable: **{len(a['reach_ac'])}**, orphan: **{len(a['orphan_ac'])}**",
         f"- Decision spines: **{len(g['decision_spines'])}**  — use-case-mapped: **{len(a['reach_spine'])}**, unmapped: **{len(a['orphan_spine'])}**",
         f"- Semantic measures: **{a['n_measures']}**  — backing a catalog KPI: **{a['n_backed']}** (registry/drift gated by `test_measure_dictionary_files`)",
         "",
         "## Integrity (must be empty)",
         "",
         f"- Dangling KPI references (used but not in catalog): **{a['dangling_kpi'] or 'none'}**",
         f"- Dangling action-code references (used but missing): **{a['dangling_ac'] or 'none'}**",
         f"- Measures backing a non-existent KPI (dangling): **{a['dangling_measure_kpi'] or 'none'}**",
         "",
         "## Per use case",
         "",
         "| Use case | KPIs | Action codes | Evidence pack | Data contract |",
         "|----------|-----:|-------------:|:-------------:|---------------|"]
    for uid in sorted(uc):
        u = uc[uid]
        L.append(f"| {uid} | {len(u['kpis'])} | {len(u['action_codes'])} | {'✓' if u['has_evidence_pack'] else '—'} | {(u['data_contract'] or '').split('/')[-1]} |")
    L += ["", "## Orphans (not reachable from any use case; review)", "",
          "**KPIs** (excludes planned.yaml roadmap):", "",
          "\n".join(f"- `{k}`" for k in a["orphan_kpi"]) or "_none_", "",
          "**Action codes:**", "",
          "\n".join(f"- `{k}`" for k in a["orphan_ac"]) or "_none_", "",
          "**Decision spines (unmapped):**", "",
          "\n".join(f"- `{k}`" for k in a["orphan_spine"]) or "_none_", "",
          "## Reachable KPIs with no backing measure (review — not a gate)", "",
          "\n".join(f"- `{k}`" for k in a["kpis_without_measure"]) or "_none_", ""]
    return "\n".join(L)


def main(argv):
    g, a = build()
    if "--check" in argv:
        problems = []
        if a["dangling_kpi"]:
            problems.append(f"dangling KPI refs: {a['dangling_kpi']}")
        if a["dangling_ac"]:
            problems.append(f"dangling action-code refs: {a['dangling_ac']}")
        if a["dangling_measure_kpi"]:
            problems.append(f"measures backing non-existent KPIs: {a['dangling_measure_kpi']}")
        if problems:
            print("REFERENCE GRAPH FAIL:\n  " + "\n  ".join(problems)); return 1
        print("reference graph OK — no dangling references"); return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render(g, a), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO)}")
    print(f"  orphans: {len(a['orphan_kpi'])} KPI, {len(a['orphan_ac'])} action code, {len(a['orphan_spine'])} spine; "
          f"dangling: {len(a['dangling_kpi'])} KPI, {len(a['dangling_ac'])} AC, {len(a['dangling_measure_kpi'])} measure; "
          f"measures: {a['n_measures']} ({a['n_backed']} KPI-backing); KPIs w/o measure: {len(a['kpis_without_measure'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
