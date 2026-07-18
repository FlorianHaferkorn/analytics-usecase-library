#!/usr/bin/env python3
"""
score_insights.py — Stage-1 insight scoring over the storyline contract (ADR-0017, deterministic-first).

The storyline (`derive_storyline.py --json`) gives every visual as a *finding* (question + answer +
so-what + KPI). This layer scores each finding, ranks them, and picks the page **headline** — the
finding that should lead. It is the Stage-1 seam of ADR-0017's two-stage generator, built
DETERMINISTICALLY first: the `Scorer` interface is where a bounded LLM scorer slots in later, but the
default `DeterministicScorer` needs no LLM, and the **grounding/verification** dimension stays
deterministic either way (ADR-0009 "UNCOMPUTED, never asserted") — an ungrounded finding can never be
the headline, no matter how good it reads.

Four dimensions (ADR-0017), each 0..1, scored from the governed narrative fields only — no live
numbers, nothing invented:
  • depth        — does it decompose/attribute, not just state a level? (waterfall/decomposition
                   visual, attribution language, on the causal spine)
  • specificity  — does it name a concrete locus / contrast / threshold, not a vague trend?
  • actionability— does the so-what point to a lever, and does the page carry actions?
  • grounding    — is the KPI governed (in the catalog) and audit-grade (carries standard_ref)?
                   This is the verification gate: grounding == 0 ⇒ not eligible to be the headline.

Usage:
    python tooling/storyline/score_insights.py            # ranked findings + headline per use case
    python tooling/storyline/score_insights.py FIN-001
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: pyyaml not installed.", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]

# weights sum to 1.0; grounding kept modest as a score but decisive as a gate (see verified).
_W = {"depth": 0.30, "specificity": 0.25, "actionability": 0.30, "grounding": 0.15}

_DECOMP_VISUALS = {"waterfall", "decomposition_tree", "bar_chart_horizontal", "stacked_bar",
                   "hundred_percent_stacked_bar", "stacked_bar_100pct"}
_ATTRIBUTION = re.compile(r"\b(driven by|explains?|because|not\s+\w+,?\s+but|rather than|"
                          r"is the component|concentrat\w+|dragging|behind the)\b", re.I)
_LOCUS = re.compile(r"\b(a few|a handful|handful|couple of|concentrat\w+|mid-tier|segment|"
                    r"lane|region|business unit|line[s]?|team[s]?|SKU|category|categories)\b", re.I)
_CONTRAST = re.compile(r"\b(not\s+\w+,?\s+but|rather than|instead of|not just)\b", re.I)
_THRESHOLD = re.compile(r"\b(below target|toward\b.*\bthreshold|safety[- ]margin|above target|"
                        r"vs\.? plan|breach\w*)\b", re.I)
_LEVER = re.compile(r"\b(intervene|fix|prioritis\w+|prioritiz\w+|focus\w*|target\w*|recalibrat\w+|"
                    r"redesign|contain\w+|rebalanc\w+|protect\w+|address\w+|shift\b)\b", re.I)


@dataclass(frozen=True)
class InsightScore:
    depth: float
    specificity: float
    actionability: float
    grounding: float

    @property
    def total(self) -> float:
        return round(_W["depth"] * self.depth + _W["specificity"] * self.specificity
                     + _W["actionability"] * self.actionability + _W["grounding"] * self.grounding, 4)

    @property
    def verified(self) -> bool:
        """Verification gate: a finding with no grounding may not lead (ADR-0009)."""
        return self.grounding > 0.0


class Scorer(Protocol):
    """Stage-1 scoring seam. A bounded, verified LLM scorer can implement this later; the
    grounding dimension must stay deterministic regardless (it is the verification gate)."""
    def score(self, finding: dict[str, Any], context: dict[str, Any]) -> InsightScore: ...


class DeterministicScorer:
    """No-LLM scorer over the governed narrative fields. Trustworthy and auditable."""

    def score(self, finding: dict[str, Any], context: dict[str, Any]) -> InsightScore:
        ans = finding.get("answer") or ""
        sw = finding.get("so_what") or ""
        text = f"{ans} {sw}"
        vt = finding.get("visual_type") or ""
        kid = finding.get("kpi_id")

        depth = 0.0
        if vt in _DECOMP_VISUALS:
            depth += 0.5
        if _ATTRIBUTION.search(text):
            depth += 0.3
        c = context.get("causal_thread") or {}
        if kid and kid in (c.get("driver"), c.get("target")):
            depth += 0.2

        spec = 0.0
        if _LOCUS.search(ans):
            spec += 0.4
        if _CONTRAST.search(ans):
            spec += 0.3
        if _THRESHOLD.search(text):
            spec += 0.3

        action = 0.0
        if sw and _LEVER.search(sw):
            action += 0.4
        if context.get("has_actions"):
            action += 0.3
        if sw and _LOCUS.search(sw):
            action += 0.3

        # grounding / verification — deterministic, from the catalog + the standards program
        exists = context.get("kpi_exists") or set()
        has_ref = context.get("kpi_has_ref") or set()
        if kid and kid in has_ref:
            grounding = 1.0                        # governed KPI, audit-grade (carries standard_ref)
        elif kid and kid in exists:
            grounding = 0.6                        # governed KPI, no standard_ref yet
        elif vt in _DECOMP_VISUALS:
            grounding = 0.3                        # governed decomposition (waterfall/etc.), no single catalog KPI
        else:
            grounding = 0.0                        # references nothing resolvable → unverified, cannot headline

        clip = lambda x: round(min(1.0, x), 3)
        return InsightScore(clip(depth), clip(spec), clip(action), clip(grounding))


def _grounding_maps() -> tuple[set[str], set[str]]:
    exists, has_ref = set(), set()
    for f in (REPO / "core/kpi_catalog/kpis").glob("*.yaml"):
        if f.stem == "_index":
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        kid = d.get("kpi_id", f.stem)
        exists.add(kid)
        if d.get("standard_ref"):
            has_ref.add(kid)
    return exists, has_ref


def rank_storyline(storyline: dict[str, Any], exists: set[str], has_ref: set[str],
                   scorer: Optional[Scorer] = None) -> dict[str, Any]:
    """Score + rank every finding; pick the headline (top verified finding overall)."""
    scorer = scorer or DeterministicScorer()
    ctx_base = {"causal_thread": storyline.get("causal_thread"),
                "has_actions": bool(storyline.get("actions")),
                "kpi_exists": exists, "kpi_has_ref": has_ref}
    ranked_pages = []
    all_findings: list[dict[str, Any]] = []
    for p in storyline.get("pages", []):
        ctx = {**ctx_base, "has_actions": ctx_base["has_actions"] or bool(p.get("evidence"))}
        scored = []
        for v in p.get("visuals", []):
            s = scorer.score(v, ctx)
            entry = {"seq": v.get("seq"), "kpi_id": v.get("kpi_id"), "question": v.get("question"),
                     "answer": v.get("answer"),
                     "score": s.total, "verified": s.verified,
                     "dims": {"depth": s.depth, "specificity": s.specificity,
                              "actionability": s.actionability, "grounding": s.grounding}}
            scored.append(entry)
            all_findings.append({**entry, "page": p.get("id")})
        scored.sort(key=lambda e: (-e["score"]))
        ranked_pages.append({"page": p.get("id"), "findings": scored})
    verified = [f for f in all_findings if f["verified"]]
    headline = max(verified, key=lambda f: f["score"]) if verified else None
    return {"use_case": storyline.get("use_case"), "headline": headline, "pages": ranked_pages}


def _fmt(r: dict[str, Any]) -> str:
    L = [f"## {r['use_case']}"]
    h = r.get("headline")
    if h:
        L.append(f"**Headline** ({h['score']}): [{h['page']}] {h['question']} — {h['answer']}")
    else:
        L.append("**Headline**: — (no verified finding)")
    for pg in r["pages"]:
        L.append(f"  {pg['page']}:")
        for f in pg["findings"]:
            v = "✓" if f["verified"] else "✗unverified"
            d = f["dims"]
            L.append(f"    [{f['score']:.3f} {v}] Q{f['seq']} `{f['kpi_id']}` "
                     f"(d{d['depth']:.1f}/s{d['specificity']:.1f}/a{d['actionability']:.1f}/g{d['grounding']:.1f}) "
                     f"— {f['answer']}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-1 deterministic insight scoring over storylines")
    ap.add_argument("use_case_id", nargs="?", help="filter by ID substring")
    args = ap.parse_args()

    import importlib.util
    spec = importlib.util.spec_from_file_location("derive_storyline", REPO / "tooling/storyline/derive_storyline.py")
    ds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ds)
    kpi_domains, kpi_keys, action_related = ds._kpi_domains(), ds._kpi_keys(), ds._action_related()
    exists, has_ref = _grounding_maps()

    for b in ds.load_brackets(args.use_case_id):
        s = ds.build_storyline(yaml.safe_load(b.read_text(encoding="utf-8")) or {},
                               kpi_domains, kpi_keys, action_related)
        print(_fmt(rank_storyline(s, exists, has_ref)))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
