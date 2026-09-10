#!/usr/bin/env python3
"""
derive_storyline.py — derive the guided use-case-to-decision storyline from a bracket.

A use case is already a storyboard: the 3-30-300 layout, the per-page `decision_question`
(the spine each page answers), the per-visual `message` (the conclusion the visual delivers) +
`so_what` (the bridge to the next beat), the `component_300s` evidence (worst-first + Top-N) and
`action_code_ids` (the decision payoff), plus the `value_driver_model` causal thread. This tool
reads those governed fields and emits, per use case, the storyline as guided storytelling:

    overall arc → PAGE 1 spine question
        [3s] the one-number verdict
        [30s] each visual: QUESTION → answer (message) → so-what (bridge)
        ↓ handoff (the page-1 so-whats ladder into the page-2 question)
      PAGE 2 spine question
        [300s] evidence (grain, worst-first sort, Top-N) → ACTIONS

Two depth layers beyond the page skeleton — both deterministic, both from data already in the repo:
  • Causal thread: value_driver_model.primary_driver → strategic KPI (+ the decomposition the
    30-second visuals show), so the storyline says *which lever moves the headline*.
  • Cross-domain edges: KPIs pulled into this use case whose `domain_tag` differs from the use
    case's own domain, and related use cases reached via action-code `use_case_links` — so a
    Finance cash story can point at the Supply-Chain reliability it connects to.

Everything here is deterministic and auditable — no LLM, no invented numbers or KPIs. The
per-visual `question` is read from `component_30s.question` when present (governed, first-class);
otherwise it is derived as a stub so the storyboard still renders.

Usage:
    python tooling/storyline/derive_storyline.py                 # all use cases → stdout
    python tooling/storyline/derive_storyline.py FIN-001          # one use case
    python tooling/storyline/derive_storyline.py --render <file>  # write the combined storyboard
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
UC_GLOB = "core/usecases/**/UseCase_Bracket.yaml"


def _kpi_domains() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in sorted((REPO / "core/kpi_catalog/kpis").glob("*.yaml")):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        out[d.get("kpi_id", f.stem)] = d.get("domain_tag") or []
    return out


def _kpi_keys() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted((REPO / "core/kpi_catalog/kpis").glob("*.yaml")):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        out[d.get("kpi_id", f.stem)] = d.get("kpi_key") or f.stem
    return out


def _action_related() -> dict[str, list[str]]:
    """action_code_id -> related use-case ids (from use_case_links).

    Two guards, one curative and one preventive (both from a CI failure on 01.08.2026):

    The FIX is skipping ``*_business_case.yaml``. Such a file carries the SAME ``id`` as its
    action code but has no ``use_case_links``, so reading it as an action code replaced the
    real links with an empty list — all 22 governed action codes with a business case were
    affected. ``tooling/superversion/bridge.py`` already applies exactly this guard.

    ``sorted()`` is PREVENTIVE, not curative: once the business cases are skipped, no two files
    share an ``id`` any more, so nothing depends on order today. It stays because the failure
    mode was never the collision itself — it was that ``rglob`` let the checkout pick the
    winner, which is why this was green here and ``use_case_storylines.md is stale`` on the
    runner. A generator that reads a directory must not let the directory decide the result.
    """
    out: dict[str, list[str]] = {}
    for f in sorted((REPO / "core/action_codes").rglob("*.yaml")):
        if f.name.endswith("_business_case.yaml"):
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if not isinstance(d, dict):
            continue
        links = (d.get("use_case_links") or {})
        rel = list(links.get("core_use_cases", []) or []) + list(links.get("related_use_cases", []) or [])
        if d.get("id"):
            out[d["id"]] = rel
    return out


def _derive_question(comp: dict[str, Any], kpi_keys: dict[str, str]) -> str:
    """Explicit governed question if present; else a derived stub."""
    q = (comp.get("question") or "").strip()
    if q:
        return q
    kid = comp.get("kpi_id")
    label = kpi_keys.get(kid, kid) if kid else "this measure"
    return f"How is {label} tracking? (derived — add an explicit `question`)"


def cross_domain_edges(bracket: dict[str, Any], kpi_domains: dict[str, list[str]],
                       action_related: dict[str, list[str]]) -> tuple[dict[str, list[str]], list[str]]:
    """Return ({foreign-domain: [kpi_ids]}, related use-case ids)."""
    own = bracket.get("domain")
    orch = bracket.get("orchestration", {}) or {}
    kpis = ([orch.get("strategic_kpi_id")] +
            list(orch.get("influencing_kpi_ids", []) or []) +
            list(orch.get("supporting_kpi_ids", []) or []))
    by_domain: dict[str, list[str]] = {}
    for kid in kpis:
        if not kid:
            continue
        doms = kpi_domains.get(kid, [])
        # a KPI whose domain set doesn't include this use case's own domain = a cross-domain pull;
        # attribute it to its first foreign domain (the primary lens it drags in)
        foreign_doms = [d for d in doms if d != own]
        if doms and own and own not in doms and foreign_doms:
            by_domain.setdefault(foreign_doms[0], []).append(kid)
    related: list[str] = []
    self_id = bracket.get("id")
    for ac in (orch.get("action_code_ids", []) or []):
        for uc in action_related.get(ac, []):
            if uc and uc != self_id and uc not in related:
                related.append(uc)
    return by_domain, related


def build_storyline(bracket: dict[str, Any], kpi_domains, kpi_keys, action_related) -> dict[str, Any]:
    """The structured storyline model — the deterministic contract the report generator and the
    (future, bounded) LLM interpretation layer both consume. No numbers/KPIs invented; every field
    traces to a governed bracket field."""
    orch = bracket.get("orchestration", {}) or {}
    vdm = bracket.get("value_driver_model", {}) or {}
    ux = bracket.get("ux_layout_rules", {}) or {}
    strategic = orch.get("strategic_kpi_id")
    driver = vdm.get("primary_driver")
    causal = None
    if driver and strategic and driver != strategic:
        causal = {"driver": driver, "target": strategic,
                  "direction": vdm.get("impact_direction"),
                  "logic": (vdm.get("impact_logic") or "").strip()}

    pages: list[dict[str, Any]] = []
    for pk in ("page_1_summary", "page_2_execution"):
        p = ux.get(pk) or {}
        if not p:
            continue
        c3 = p.get("component_3s") or {}
        visuals = [{
            "seq": i,
            "question": _derive_question(comp, kpi_keys),
            "visual_type": comp.get("visual_type"),
            "kpi_id": comp.get("kpi_id"),
            "answer": comp.get("message"),
            "so_what": comp.get("so_what"),
            "unit": comp.get("unit"),
        } for i, comp in enumerate(p.get("component_30s") or [], 1)]
        c300 = p.get("component_300s") or {}
        evidence = None
        if c300:
            srt = c300.get("sort_by") or {}
            evidence = {"grain": c300.get("evidence_grain"), "sort_measure": srt.get("measure"),
                        "sort_direction": srt.get("direction"), "top_n": c300.get("top_n"),
                        "action_panel": bool(c300.get("action_panel"))}
        pages.append({
            "id": pk, "type": p.get("page_type", ""),
            "decision_question": p.get("decision_question"),
            "verdict": ({"kpi_id": c3.get("kpi_id"), "comparison": c3.get("comparison"),
                         "status_logic": c3.get("status_logic")} if c3 else None),
            "visuals": visuals, "evidence": evidence,
        })

    by_domain, related = cross_domain_edges(bracket, kpi_domains, action_related)
    return {
        "use_case": bracket.get("id"), "title": bracket.get("title"), "domain": bracket.get("domain"),
        "strategic_kpi": strategic, "causal_thread": causal, "pages": pages,
        "actions": orch.get("action_code_ids") or [],
        "cross_domain": by_domain, "connects_to": sorted(related),
    }


def render_markdown(s: dict[str, Any]) -> str:
    """Human-readable storyboard from the structured model."""
    L: list[str] = [f"## {s['use_case']} — {s['title']}", ""]
    c = s.get("causal_thread")
    if c:
        L.append(f"**Causal thread:** `{c['driver']}` → `{c['target']}` "
                 f"({c.get('direction', 'impact')}). {c.get('logic', '')}")
        L.append("")
    elif s.get("strategic_kpi"):
        L.append(f"**Headline KPI:** `{s['strategic_kpi']}`.")
        L.append("")
    for idx, p in enumerate(s["pages"]):
        arrow = "↓ handoff" if idx == 0 and len(s["pages"]) == 2 else None
        L.append(f"### {p['id'].replace('_', ' ').title()} · {p.get('type', '')}")
        L.append(f"**Spine question:** {p.get('decision_question') or '—'}")
        v = p.get("verdict")
        if v:
            L.append(f"- **[3s verdict]** `{v.get('kpi_id')}` "
                     f"{v.get('comparison', '')} ({v.get('status_logic', '')})")
        for vis in p["visuals"]:
            L.append(f"- **[30s Q{vis['seq']}]** {vis['question']}")
            L.append(f"    - visual: `{vis.get('visual_type')}` · `{vis.get('kpi_id')}`")
            L.append(f"    - answer: {vis.get('answer') or '—'}")
            L.append(f"    - so what → {vis.get('so_what') or '—'}")
        ev = p.get("evidence")
        if ev:
            L.append(f"- **[300s evidence]** grain `{ev.get('grain')}`, "
                     f"worst-first by `{ev.get('sort_measure')}` ({ev.get('sort_direction')}), "
                     f"Top-{ev.get('top_n')}" + (" · action panel" if ev.get("action_panel") else ""))
        if arrow:
            L.append(f"\n{arrow} →\n")
    if s.get("actions"):
        L.append(f"**Decision payoff (actions):** {', '.join(s['actions'])}")
    if s.get("cross_domain"):
        parts = []
        for dom, kids in sorted(s["cross_domain"].items(), key=lambda kv: -len(kv[1])):
            ex = ", ".join(f"`{k}`" for k in kids[:3])
            more = f" +{len(kids) - 3}" if len(kids) > 3 else ""
            parts.append(f"{dom} ({len(kids)}: {ex}{more})")
        L.append(f"**Cross-domain pull:** {'; '.join(parts)}")
    if s.get("connects_to"):
        L.append(f"**Connects to use cases:** {', '.join(s['connects_to'])}")
    L.append("")
    return "\n".join(L)


def storyboard(bracket: dict[str, Any], kpi_domains, kpi_keys, action_related) -> str:
    """Markdown storyboard for one bracket (model → view)."""
    return render_markdown(build_storyline(bracket, kpi_domains, kpi_keys, action_related))


def load_brackets(uc_filter: Optional[str]) -> list[Path]:
    bs = sorted(REPO.glob(UC_GLOB))
    if uc_filter:
        bs = [b for b in bs if uc_filter.lower() in str(b).lower()]
    return bs


def storylines_json(brackets, kpi_domains, kpi_keys, action_related) -> list[dict[str, Any]]:
    return [build_storyline(yaml.safe_load(b.read_text(encoding="utf-8")) or {},
                            kpi_domains, kpi_keys, action_related) for b in brackets]


def main() -> int:
    ap = argparse.ArgumentParser(description="Derive the guided storyline from a use-case bracket")
    ap.add_argument("use_case_id", nargs="?", help="filter by ID substring")
    ap.add_argument("--render", metavar="FILE", help="write the combined Markdown storyboard to FILE")
    ap.add_argument("--json", metavar="FILE", nargs="?", const="-",
                    help="emit the structured storyline model as JSON (the generator/LLM contract); "
                         "'-' or no value = stdout")
    args = ap.parse_args()

    kpi_domains, kpi_keys, action_related = _kpi_domains(), _kpi_keys(), _action_related()
    brackets = load_brackets(args.use_case_id)

    if args.json is not None:
        import json
        data = storylines_json(brackets, kpi_domains, kpi_keys, action_related)
        payload = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.json in ("-", ""):
            print(payload, end="")
        else:
            Path(args.json).write_text(payload, encoding="utf-8", newline="\n")
            print(f"wrote {args.json} ({len(data)} storylines)")
        return 0

    header = ("# Use-case storylines (derived)\n\n"
              "> Generated by `tooling/storyline/derive_storyline.py` from the governed brackets — "
              "deterministic, no LLM. Each visual answers a question; the questions ladder to the "
              "page's decision, and page 1 hands off to page 2 to cover the whole use-case-to-decision arc.\n")
    parts = [header]
    for b in brackets:
        data = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        parts.append(storyboard(data, kpi_domains, kpi_keys, action_related))

    out = "\n".join(parts)
    if args.render:
        Path(args.render).write_text(out, encoding="utf-8", newline="\n")
        print(f"wrote {args.render} ({len(brackets)} use cases)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
