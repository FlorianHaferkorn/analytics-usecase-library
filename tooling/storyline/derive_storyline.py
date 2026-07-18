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
    for f in (REPO / "core/kpi_catalog/kpis").glob("*.yaml"):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        out[d.get("kpi_id", f.stem)] = d.get("domain_tag") or []
    return out


def _kpi_keys() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in (REPO / "core/kpi_catalog/kpis").glob("*.yaml"):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        out[d.get("kpi_id", f.stem)] = d.get("kpi_key") or f.stem
    return out


def _action_related() -> dict[str, list[str]]:
    """action_code_id -> related use-case ids (from use_case_links)."""
    out: dict[str, list[str]] = {}
    for f in (REPO / "core/action_codes").rglob("*.yaml"):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
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


def storyboard(bracket: dict[str, Any], kpi_domains, kpi_keys, action_related) -> str:
    ucid = bracket.get("id")
    title = bracket.get("title")
    orch = bracket.get("orchestration", {}) or {}
    vdm = bracket.get("value_driver_model", {}) or {}
    ux = bracket.get("ux_layout_rules", {}) or {}
    strategic = orch.get("strategic_kpi_id")

    L: list[str] = [f"## {ucid} — {title}", ""]
    # causal thread
    driver = vdm.get("primary_driver")
    if driver and strategic and driver != strategic:
        L.append(f"**Causal thread:** `{driver}` → `{strategic}` "
                 f"({vdm.get('impact_direction', 'impact')}). "
                 f"{(vdm.get('impact_logic') or '').strip()}")
        L.append("")
    elif strategic:
        L.append(f"**Headline KPI:** `{strategic}` ({vdm.get('impact_direction', 'impact')}). "
                 f"{(vdm.get('impact_logic') or '').strip()}")
        L.append("")

    for pk, arrow in (("page_1_summary", "↓ handoff"), ("page_2_execution", None)):
        p = ux.get(pk) or {}
        if not p:
            continue
        ptype = p.get("page_type", "")
        L.append(f"### {pk.replace('_', ' ').title()} · {ptype}")
        L.append(f"**Spine question:** {p.get('decision_question', '—')}")
        c3 = p.get("component_3s") or {}
        if c3:
            L.append(f"- **[3s verdict]** `{c3.get('kpi_id')}` "
                     f"{c3.get('comparison', '')} ({c3.get('status_logic', '')})")
        for i, comp in enumerate(p.get("component_30s") or [], 1):
            q = _derive_question(comp, kpi_keys)
            L.append(f"- **[30s Q{i}]** {q}")
            L.append(f"    - visual: `{comp.get('visual_type')}` · `{comp.get('kpi_id')}`")
            L.append(f"    - answer: {comp.get('message', '—')}")
            L.append(f"    - so what → {comp.get('so_what', '—')}")
        c300 = p.get("component_300s") or {}
        if c300:
            srt = c300.get("sort_by") or {}
            L.append(f"- **[300s evidence]** grain `{c300.get('evidence_grain')}`, "
                     f"worst-first by `{srt.get('measure')}` ({srt.get('direction')}), "
                     f"Top-{c300.get('top_n')}"
                     + (" · action panel" if c300.get("action_panel") else ""))
        if arrow:
            L.append(f"\n{arrow} →\n")

    if orch.get("action_code_ids"):
        L.append(f"**Decision payoff (actions):** {', '.join(orch['action_code_ids'])}")
    by_domain, related = cross_domain_edges(bracket, kpi_domains, action_related)
    if by_domain:
        parts = []
        for dom, kids in sorted(by_domain.items(), key=lambda kv: -len(kv[1])):
            ex = ", ".join(f"`{k}`" for k in kids[:3])
            more = f" +{len(kids) - 3}" if len(kids) > 3 else ""
            parts.append(f"{dom} ({len(kids)}: {ex}{more})")
        L.append(f"**Cross-domain pull:** {'; '.join(parts)}")
    if related:
        L.append(f"**Connects to use cases:** {', '.join(sorted(related))}")
    L.append("")
    return "\n".join(L)


def load_brackets(uc_filter: Optional[str]) -> list[Path]:
    bs = sorted(REPO.glob(UC_GLOB))
    if uc_filter:
        bs = [b for b in bs if uc_filter.lower() in str(b).lower()]
    return bs


def main() -> int:
    ap = argparse.ArgumentParser(description="Derive the guided storyline from a use-case bracket")
    ap.add_argument("use_case_id", nargs="?", help="filter by ID substring")
    ap.add_argument("--render", metavar="FILE", help="write the combined storyboard to FILE")
    args = ap.parse_args()

    kpi_domains, kpi_keys, action_related = _kpi_domains(), _kpi_keys(), _action_related()
    brackets = load_brackets(args.use_case_id)

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
        Path(args.render).write_text(out, encoding="utf-8")
        print(f"wrote {args.render} ({len(brackets)} use cases)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
