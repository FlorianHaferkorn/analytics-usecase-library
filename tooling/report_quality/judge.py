#!/usr/bin/env python3
"""
judge.py — Boutique-Craft judge harness (K6 §9, the `check: judge` half)

The rubric splits into `check: structural` (machine-checkable from the spec/PBIR — wired
via boutique_scorecard.WIRED) and `check: judge` (needs assessment of a *rendered*
report). This harness is the addressable home for the judge rules. Its key move: a few
rules the rubric conservatively marked `judge` are in fact **decidable from the governed
spec without a render** — those get a deterministic heuristic here and count honestly; the
genuinely render-only rules get a pluggable LLM/human backend and, until that runs,
**abstain** (score=None) rather than fake a verdict.

Architecture:
    Judge (Protocol)          — evaluate(rule_id, ctx) -> Verdict
    SpecHeuristicJudge        — deterministic; scores the spec-decidable judge rules,
                                abstains on render-only rules (never invents a score)
    <LLM judge>               — future backend over a render + screenshot (opt-in;
                                needs a renderer + model, a maintainer/runtime concern)

A Verdict with score=None (abstain) leaves the rule `not_scored` in the scorecard — the
same honesty rule as the structural side: coverage only counts what was actually decided.

Usage (library): run_judges(load_rubric(), ctx, SpecHeuristicJudge())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, Union

try:
    import yaml
except ImportError:  # pragma: no cover
    raise

REPO = Path(__file__).resolve().parents[2]
_RUBRIC = REPO / "core/templates/page_templates/tokens/boutique_craft_rubric.yaml"

import sys
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
# Shared honesty contract (single source): deterministic default ships; LLM may slot in but must
# ABSTAIN rather than fabricate; the gate stays deterministic. See tooling/quality/verification_seam.py.
from tooling.quality.verification_seam import ABSTAIN  # noqa: E402


@dataclass
class Verdict:
    rule_id: str
    score: Optional[float]   # 0.0 / 0.5 / 1.0, or None = abstain (not decided)
    method: str              # "spec_heuristic" | "llm" | "abstain"
    rationale: str


class Judge(Protocol):
    def evaluate(self, rule_id: str, ctx: "JudgeContext") -> Verdict: ...


@dataclass
class JudgeContext:
    """Everything a judge may read. Deterministic heuristics read the governed spec;
    a future LLM judge would additionally carry render/screenshot handles."""
    repo: Path = REPO

    def brackets(self) -> list[dict[str, Any]]:
        out = []
        for p in sorted(self.repo.glob("core/usecases/**/UseCase_Bracket.yaml")):
            out.append(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
        return out

    def exhibits(self) -> list[dict[str, Any]]:
        """All component_30s exhibits across brackets (the 30-second evidence layer)."""
        out = []
        for b in self.brackets():
            page = (b.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {}
            for ex in page.get("component_30s") or []:
                if isinstance(ex, dict):
                    out.append({**ex, "_bracket": b.get("id", "?")})
        return out


#: Regelarten, die ein Judge-Urteil brauchen. `both` heisst: ein Validator entscheidet
#: die strukturelle Haelfte, ein Judge die semantische — beide zaehlen. Ohne `both` in
#: dieser Menge waeren die zwei betroffenen Regeln (BC-NARR-01, BC-BRAND-02) still aus
#: der Judge-Menge gefallen; die Aufwertung von `judge` auf `both` haette dann GENAU
#: das bewirkt, was sie beheben soll — ein Urteil, das niemand einholt.
JUDGE_KINDS = ("judge", "both")


def judge_rules(rubric: dict[str, Any]) -> list[dict[str, Any]]:
    """Alle Regeln, die ein Judge-Urteil brauchen (`check: judge` oder `both`)."""
    out = []
    for dim in rubric["dimensions"]:
        for r in dim["rules"]:
            if r.get("check") in JUDGE_KINDS:
                out.append({**r, "dimension": dim["id"]})
    return out


def load_rubric() -> dict[str, Any]:
    return yaml.safe_load(_RUBRIC.read_text(encoding="utf-8"))


# ── Deterministic spec-heuristics for the spec-decidable judge rules ─────────

def _bc_narr_03(ctx: JudgeContext) -> Verdict:
    """So-what chain: signal → reason → implication → action. Spec-decidable: every
    exhibit that states a `message` (signal/conclusion) must also carry a `so_what`
    (implication); the action leg is the governed `action_code_id`. An exhibit with a
    message but no so_what has a broken chain."""
    exhibits = [e for e in ctx.exhibits() if str(e.get("message", "")).strip()]
    if not exhibits:
        return Verdict("BC-NARR-03", ABSTAIN, "abstain", "no governed messages to assess")
    broken = [f"{e['_bracket']}/{e.get('slot_id', '?')}"
              for e in exhibits if not str(e.get("so_what", "")).strip()]
    if broken:
        return Verdict("BC-NARR-03", 0.0, "spec_heuristic",
                       f"{len(broken)} exhibit(s) state a message without a so-what: {broken[:5]}")
    return Verdict("BC-NARR-03", 1.0, "spec_heuristic",
                   f"all {len(exhibits)} message-bearing exhibits carry a so-what chain")


def _bc_layout_03(ctx: JudgeContext) -> Verdict:
    """Hero-insight pattern: the 3-second zone leads with ONE dominant statement, not a
    flat grid. Spec-decidable: the governed layout dictates the hierarchy — every summary
    page must declare a single-lead `component_3s` hero (one kpi_id), distinct from the
    supporting `component_30s` exhibits. No hero (or a heroless page) = flat hierarchy."""
    pages = [(b.get("id", "?"), (b.get("ux_layout_rules", {}) or {}).get("page_1_summary", {}) or {})
             for b in ctx.brackets()]
    pages = [(bid, p) for bid, p in pages if p]
    if not pages:
        return Verdict("BC-LAYOUT-03", ABSTAIN, "abstain", "no summary pages to assess")
    flat = []
    for bid, p in pages:
        hero = p.get("component_3s")
        lead = hero.get("kpi_id") if isinstance(hero, dict) else None
        if not lead:
            flat.append(bid)
    if flat:
        return Verdict("BC-LAYOUT-03", 0.0, "spec_heuristic",
                       f"{len(flat)} page(s) lead with no single dominant hero (flat): {flat[:5]}")
    return Verdict("BC-LAYOUT-03", 1.0, "spec_heuristic",
                   f"all {len(pages)} summary pages lead with a single-lead component_3s hero")


_HEURISTICS: dict[str, Callable[[JudgeContext], Verdict]] = {
    "BC-NARR-03": _bc_narr_03,
    "BC-LAYOUT-03": _bc_layout_03,
}


class SpecHeuristicJudge:
    """Scores judge rules that are decidable from the governed spec; abstains on the
    render-only ones (never invents a verdict)."""

    def evaluate(self, rule_id: str, ctx: JudgeContext) -> Verdict:
        fn = _HEURISTICS.get(rule_id)
        if fn is None:
            return Verdict(rule_id, ABSTAIN, "abstain", "needs a rendered report + judge (LLM/human)")
        return fn(ctx)


def run_judges(rubric: dict[str, Any], ctx: JudgeContext, judge: Judge) -> dict[str, Verdict]:
    """Evaluate every judge rule with `judge`. Abstentions (score=None) stay not_scored."""
    return {r["id"]: judge.evaluate(r["id"], ctx) for r in judge_rules(rubric)}


# ── Rendered evidence: text and images ───────────────────────────────────────
# D-826 (Freelancing-Register, 27.10.2026): kein positives Urteil ohne passende Bild-Evidenz.
# Die render-only-Regeln (alles ausser den Spec-Heuristiken) urteilen ueber das, was ein Leser
# sieht: abgeschnittene Beschriftungen, Farbgewicht, Hierarchie. HTML-Quelltext zeigt das nicht —
# ein Text-Urteil darf deshalb einen Mangel melden (0.0), aber nie bestehen lassen.

@dataclass(frozen=True)
class ImageEvidence:
    """Ein gerenderter Bildausschnitt. `label` benennt Prüfling und Variante, z. B.
    `UC-FIN-002/desktop/hell/1` — Seite, Breite, Modus, Kachel."""
    path: Path
    label: str

    @property
    def variant(self) -> frozenset[str]:
        return frozenset(self.label.split("/"))


@dataclass(frozen=True)
class Evidence:
    """Was ein Judge sieht: Text (HTML, Beschreibung) und Bilder. Bewusst ohne Feld fuer eine
    Bau-Begruendung — der Judge bekommt den Prüfling, nicht die Argumente seines Autors."""
    text: str = ""
    images: tuple[ImageEvidence, ...] = field(default_factory=tuple)

    def __bool__(self) -> bool:
        return bool(self.text.strip() or self.images)


def as_evidence(raw: Union[str, Evidence, None]) -> Evidence:
    """Altes Text-Protokoll (`render_provider -> str`) und neues Bild-Protokoll gleich behandeln."""
    if raw is None:
        return Evidence()
    return raw if isinstance(raw, Evidence) else Evidence(text=str(raw))


def render_only_rule(rule_id: str) -> bool:
    """Render-only = keine Spec-Heuristik entscheidet die Regel; nur ein Blick aufs Bild kann es."""
    return rule_id not in _HEURISTICS


def missing_variants(evidence: Evidence, required: frozenset[str]) -> frozenset[str]:
    """Pflichtvarianten (`desktop`, `mobil`, `hell`, `dunkel` …), die kein Bild der Evidenz traegt."""
    seen: set[str] = set()
    for img in evidence.images:
        seen |= img.variant
    return frozenset(required - seen)


# ── Pluggable LLM backend (the render-only half) ─────────────────────────────
# The genuinely render-dependent judge rules (muted context, visual hierarchy, direct
# labelling …) need a model looking at a rendered report. This is the integration seam:
# a `complete(prompt) -> str` callable (any model) + a `render_provider(rule) -> evidence`
# are injected. Both pieces are a runtime/maintainer concern (a renderer + an API key),
# so with neither wired the LLMJudge abstains — it never guesses. The prompt builder and
# verdict parser are pure and unit-tested, so the contract is verified without a model.

_RUBRIC_BY_ID: dict[str, dict[str, Any]] = {}


def _rule_meta(rule_id: str, rubric: Optional[dict] = None) -> dict[str, Any]:
    global _RUBRIC_BY_ID
    if not _RUBRIC_BY_ID:
        for dim in (rubric or load_rubric())["dimensions"]:
            for r in dim["rules"]:
                _RUBRIC_BY_ID[r["id"]] = {**r, "dimension": dim["id"]}
    return _RUBRIC_BY_ID.get(rule_id, {"id": rule_id, "statement": "", "machine_hint": ""})


def build_judge_prompt(rule: dict[str, Any], evidence: Union[str, Evidence]) -> str:
    """Deterministic judge prompt for one rule + rendered evidence. Pure — unit-tested.

    Bilder gehen als eigene Bloecke an das Modell (`complete(prompt, images)`); der Prompt nennt
    sie in derselben Reihenfolge mit Label, damit die Begruendung eine Variante benennen kann."""
    ev = as_evidence(evidence)
    shots = ""
    if ev.images:
        listed = "\n".join(f"  [{i}] {img.label}" for i, img in enumerate(ev.images, start=1))
        shots = (f"SCREENSHOTS (attached in this order):\n{listed}\n"
                 "Judge what a reader sees in the screenshots. Clipped or overlapping text, "
                 "unreadable labels and horizontal overflow count against the rule they affect.\n\n")
    text = f"RENDERED EVIDENCE:\n{ev.text}\n\n" if ev.text.strip() else ""
    return (
        "You are a boutique data-visualization critic scoring ONE craft rule against a "
        "rendered report.\n\n"
        f"RULE {rule.get('id')}: {rule.get('statement')}\n"
        f"WHAT TO LOOK FOR: {rule.get('machine_hint')}\n\n"
        f"{shots}{text}"
        "Respond in exactly this format, nothing else:\n"
        "SCORE: <0.0 | 0.5 | 1.0>\n"
        "RATIONALE: <one sentence>"
    )


def parse_verdict(rule_id: str, text: str) -> Verdict:
    """Parse an LLM completion into a Verdict. Malformed → abstain (never guess a pass)."""
    score: Optional[float] = None
    rationale = ""
    for line in (text or "").splitlines():
        s = line.strip()
        if s.upper().startswith("SCORE:"):
            tok = s.split(":", 1)[1].strip()
            try:
                val = float(tok.split()[0])
                if val in (0.0, 0.5, 1.0):
                    score = val
            except (ValueError, IndexError):
                score = None
        elif s.upper().startswith("RATIONALE:"):
            rationale = s.split(":", 1)[1].strip()
    if score is None:
        return Verdict(rule_id, ABSTAIN, "abstain", "LLM output unparseable — abstaining")
    return Verdict(rule_id, score, "llm", rationale or "(no rationale)")


class LLMJudge:
    """Render-based judge. `complete(prompt)->str` is any model; `render_provider(rule_id)`
    supplies the rendered evidence (`str` or `Evidence`). With either missing, abstains.

    Mit Bildern ruft er `complete(prompt, images)`. Fuer render-only-Regeln gilt D-826: ein
    positives Urteil (0.5/1.0) ohne Bild, oder ohne jede Pflichtvariante aus `required_variants`,
    wird zur Enthaltung; ein Mangel (0.0) bleibt stehen."""

    def __init__(self, complete: Optional[Callable[..., str]] = None,
                 render_provider: Optional[Callable[[str], Union[str, Evidence, None]]] = None,
                 rubric: Optional[dict] = None,
                 required_variants: frozenset[str] = frozenset()):
        self._complete = complete
        self._render = render_provider
        self._rubric = rubric
        self._required = frozenset(required_variants)

    def evaluate(self, rule_id: str, ctx: JudgeContext) -> Verdict:
        if self._complete is None or self._render is None:
            return Verdict(rule_id, ABSTAIN, "abstain", "no model + render wired (runtime concern)")
        evidence = as_evidence(self._render(rule_id))
        if not evidence:
            return Verdict(rule_id, ABSTAIN, "abstain", "no rendered evidence available")
        prompt = build_judge_prompt(_rule_meta(rule_id, self._rubric), evidence)
        raw = self._complete(prompt, list(evidence.images)) if evidence.images else self._complete(prompt)
        verdict = parse_verdict(rule_id, raw)
        if verdict.score and render_only_rule(rule_id):
            if not evidence.images:
                return Verdict(rule_id, ABSTAIN, "abstain",
                               f"positive verdict without image evidence (D-826): {verdict.rationale}")
            fehlt = missing_variants(evidence, self._required)
            if fehlt:
                return Verdict(rule_id, ABSTAIN, "abstain",
                               f"positive verdict without variants {sorted(fehlt)} (D-826): {verdict.rationale}")
        return verdict


# ── Gesäter Fehler: findet der Judge, was er finden muss? ─────────────────────

@dataclass(frozen=True)
class SeedResult:
    rule_id: str
    clean: Verdict
    seeded: Verdict

    @property
    def outcome(self) -> str:
        """`gefunden`: der gesäte Stand wurde entschieden und schlechter bewertet als der saubere.
        `nicht_messbar`: der saubere Stand besteht die Regel selbst nicht (0.0 oder Enthaltung) —
        unter dem Boden kann ein Fehler nicht schlechter werden; der Seed braucht einen Prüfling,
        der die Regel besteht. `nicht_gefunden`: sonst, auch bei Enthaltung auf dem Fehler.
        Gemessen 28.10.2026 an UC-FIN-002 (Aurora): BC-COLOR-01 sauber 0.0 → nicht messbar,
        obwohl die Begruendung den Seed beschrieb; ein bloßes `seeded == 0.0` haette ihn gezaehlt."""
        s, c = self.seeded.score, self.clean.score
        if c is None or c == 0.0:
            return "nicht_messbar"
        if s is not None and s < c:
            return "gefunden"
        return "nicht_gefunden"

    @property
    def found(self) -> bool:
        return self.outcome == "gefunden"


def seed_check(judge: Judge, rule_id: str, clean: Evidence, seeded: Evidence,
               ctx: Optional[JudgeContext] = None) -> SeedResult:
    """Denselben Judge auf sauberen und gesäten Stand derselben Seite ansetzen (D-826)."""
    ctx = ctx or JudgeContext()

    def run(ev: Evidence) -> Verdict:
        return _with_evidence(judge, ev).evaluate(rule_id, ctx)

    return SeedResult(rule_id, run(clean), run(seeded))


def _with_evidence(judge: Judge, evidence: Evidence) -> Judge:
    """Ein LLMJudge mit fest verdrahteter Evidenz; andere Judges bleiben unveraendert."""
    if isinstance(judge, LLMJudge):
        return LLMJudge(judge._complete, lambda _rid: evidence, judge._rubric, judge._required)
    return judge


class CompositeJudge:
    """Try each judge in order; the first non-abstaining verdict wins (spec-heuristic
    before LLM, so cheap/deterministic decisions preempt a model call)."""

    def __init__(self, judges: list[Judge]):
        self._judges = judges

    def evaluate(self, rule_id: str, ctx: JudgeContext) -> Verdict:
        last = Verdict(rule_id, ABSTAIN, "abstain", "no judge decided")
        for j in self._judges:
            v = j.evaluate(rule_id, ctx)
            if v.score is not None:
                return v
            last = v
        return last
