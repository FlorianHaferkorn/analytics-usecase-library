#!/usr/bin/env python3
"""
compose_narrative.py — ADR-0017 Stage 2: compose the Big Idea from the verified headline (D3 + D4).

Closes the ADR-0017 loop deterministically:
    Stage 1 (score_insights) → rank findings, pick the VERIFIED headline
    → Stage 2 (here): pick a template SHAPE from the headline's shape, fill it from governed slots
    → a recomputed, re-verified Big Idea string (never free-form LLM text).

This replaces today's static, hand-authored `big_idea` — which nothing recomputes and which goes
stale silently — with a value derived from the top-scored *verified* finding every run. Per D4, the
static `big_idea` in the bracket is kept as the **fallback** when no finding verifies (ADR-0009: never
render an unverified claim; fall back to the human-curated floor).

Reconciliation with the render enforcer (single source of truth — no parallel render path).
`design_rules_enforcer.check_header_text_equals_big_idea` requires the rendered page-1 Header to equal
`ux_layout_rules.page_1_summary.big_idea` **verbatim**. That bracket field stays the ONE rendered
source; this module is its *generator/proposer*, never a second render path that would fight the
verbatim check. The contract is therefore single-valued: the rendered header == the bracket `big_idea`,
and that field is either produced by this composer (verified) or hand-authored (the D4 fallback floor).
`--check` reports drift — where the governed static field no longer matches what the current verified
evidence composes — so a maintainer can refresh the field deliberately (keeping the verbatim rule
valid). It never auto-writes: adopting a proposal is a governed edit to the bracket, not a side effect.

D3 — the closed set of template shapes, selected deterministically from the headline record's shape
(the dimensions Stage 1 already scored — no new judgment layer):
  • driver_lever       — the headline sits on the causal thread and the use case has actions
  • concentration      — the headline is specific (names a concrete locus)
  • trajectory_vs_plan — the headline is a vs-plan / off-target level
  • verdict            — grounded headline with no stronger shape (default)
  • fallback           — no verified headline → the static big_idea (or an UNCOMPUTED marker)

Usage:
    python tooling/storyline/compose_narrative.py            # composed Big Idea per use case
    python tooling/storyline/compose_narrative.py FIN-001
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]


def _load(mod_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / mod_path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m          # dataclasses in the loaded module need it in sys.modules
    spec.loader.exec_module(m)
    return m


def _trim(s: Optional[str]) -> str:
    return (s or "").strip().rstrip(".")


def select_shape(headline: dict[str, Any], storyline: dict[str, Any]) -> str:
    """D3: deterministic template-shape selection from the headline's already-scored dimensions."""
    if headline is None:
        return "fallback"
    dims = headline.get("dims", {})
    ans = (headline.get("answer") or "").lower()
    if storyline.get("causal_thread") and storyline.get("actions") and dims.get("depth", 0) >= 0.5:
        return "driver_lever"
    if dims.get("specificity", 0) >= 0.4:
        return "concentration"
    if any(w in ans for w in ("vs plan", "vs. plan", "below target", "off track", "trailing plan", "toward")):
        return "trajectory_vs_plan"
    return "verdict"


def compose(storyline: dict[str, Any], ranked: dict[str, Any], kpi_keys: dict[str, str],
            static_big_idea: Optional[str]) -> dict[str, Any]:
    """Stage 2: produce the Big Idea for page 1 from the verified headline (or the D4 fallback)."""
    headline = ranked.get("headline")
    subj = kpi_keys.get(storyline.get("strategic_kpi"), storyline.get("strategic_kpi") or "This KPI")
    shape = select_shape(headline, storyline)

    if shape == "fallback":
        if static_big_idea:
            return {"use_case": storyline["use_case"], "shape": "fallback",
                    "big_idea": static_big_idea, "verified": False, "fallback_used": True,
                    "source": None}
        return {"use_case": storyline["use_case"], "shape": "fallback",
                "big_idea": f"{subj}: UNCOMPUTED — no verified insight this run.",
                "verified": False, "fallback_used": True, "source": None}

    ans = _trim(headline.get("answer"))
    # the so_what (the lever) lives on the storyline finding, not the ranked record — look it up
    sw = ""
    for pg in storyline.get("pages", []):
        for v in pg.get("visuals", []):
            if v.get("seq") == headline["seq"] and v.get("kpi_id") == headline.get("kpi_id"):
                sw = _trim(v.get("so_what"))

    if shape == "driver_lever":
        big = f"{subj} is under pressure: {ans}" + (f". {sw}." if sw else ".")
    elif shape == "concentration":
        big = f"{subj}: {ans} — focus where it concentrates."
    elif shape == "trajectory_vs_plan":
        big = f"{subj} is off plan: {ans}."
    else:  # verdict
        big = f"{subj}: {ans}."

    return {"use_case": storyline["use_case"], "shape": shape, "big_idea": big,
            "verified": True, "fallback_used": False,
            "source": {"seq": headline["seq"], "kpi_id": headline["kpi_id"],
                       "score": headline["score"],
                       "value_verified": headline.get("value_verified")}}


def _static_big_idea(bracket: dict[str, Any]) -> Optional[str]:
    p = (bracket.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {}
    return p.get("big_idea")


def compose_all(uc_filter: Optional[str]) -> list[dict[str, Any]]:
    ds = _load("tooling/storyline/derive_storyline.py", "derive_storyline")
    si = _load("tooling/storyline/score_insights.py", "score_insights")
    ss = _load("tooling/storyline/snapshot_signal.py", "snapshot_signal")
    kpi_domains, kpi_keys, action_related = ds._kpi_domains(), ds._kpi_keys(), ds._action_related()
    exists, has_ref = si._grounding_maps()
    out = []
    for b in ds.load_brackets(uc_filter):
        bracket = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        s = ds.build_storyline(bracket, kpi_domains, kpi_keys, action_related)
        vv = ss.value_verified_map(s.get("use_case"))
        ranked = si.rank_storyline(s, exists, has_ref, value_verified=vv)
        out.append(compose(s, ranked, kpi_keys, _static_big_idea(bracket)))
    return out


def check_drift(uc_filter: Optional[str]) -> list[dict[str, Any]]:
    """Compare each composed Big Idea against the bracket's static `big_idea` (the rendered source).

    Status per use case (advisory — the static field is legitimately hand-curated; compose only proposes):
      • agree    — the composer verifies and its Big Idea already matches the governed static field
      • drift    — the composer verifies but its Big Idea differs from the static field (field may be stale)
      • fallback — the composer did not verify; the static field remains the floor (nothing to reconcile)
      • missing  — no static big_idea set at all (the enforcer skips it; compose has nothing to compare)
    """
    ds = _load("tooling/storyline/derive_storyline.py", "derive_storyline")
    out = []
    for r in compose_all(uc_filter):
        static = None
        for b in ds.load_brackets(r["use_case"]):
            static = _static_big_idea(yaml.safe_load(b.read_text(encoding="utf-8")) or {})
        if not static:
            status = "missing"
        elif r["fallback_used"]:
            status = "fallback"
        elif r["big_idea"].strip() == static.strip():
            status = "agree"
        else:
            status = "drift"
        out.append({"use_case": r["use_case"], "status": status,
                    "composed": r["big_idea"], "static": static})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="ADR-0017 Stage-2: compose the Big Idea from the verified headline")
    ap.add_argument("use_case_id", nargs="?", help="filter by ID substring")
    ap.add_argument("--check", action="store_true",
                    help="report drift between the composed Big Idea and the governed static big_idea (never writes)")
    args = ap.parse_args()

    if args.check:
        rows = check_drift(args.use_case_id)
        drift = [r for r in rows if r["status"] == "drift"]
        for r in rows:
            print(f"[{r['status']:>8}] {r['use_case']}")
            if r["status"] == "drift":
                print(f"           static  : {r['static']}")
                print(f"           composed: {r['composed']}")
        print(f"\ncompose_narrative --check: {len(rows)} use cases · {len(drift)} drift "
              f"(static field trails the current verified evidence — refresh deliberately). Advisory; nothing written.")
        return 0

    for r in compose_all(args.use_case_id):
        gate = "verified" if r["verified"] else ("fallback→static" if r["fallback_used"] else "unverified")
        print(f"## {r['use_case']}  [{r['shape']} · {gate}]")
        print(f"   {r['big_idea']}")
        if r.get("source"):
            print(f"   ↳ from finding Q{r['source']['seq']} `{r['source']['kpi_id']}` (score {r['source']['score']})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
