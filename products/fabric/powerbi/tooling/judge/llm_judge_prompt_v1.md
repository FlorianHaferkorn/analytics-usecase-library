# LLM-Judge Prompt — Report Visual Acceptance (R4.2)

version: 1.0.0
status: versioned, not yet run (blocked on R4.1 — needs a real Desktop
  screenshot; see `docs/plans/UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` R4.1/R4.2 ledger rows)

> Implements `docs/plans/UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` Cut C4 / **R4.2
> LLM-Judge-Abnahme**. Half-automatic: the judge scores and explains; a human
> reads the verdict and decides accept/reject. The judge's output is never
> auto-applied to the ledger or auto-merged — it is a decision aid.

## Why this exists

Structural PBIR validation (Tier 0/1 checks, fab-inspector, the scorecard,
R3.1–R3.4) proves a report is well-formed. It cannot prove a report actually
*communicates* — whether the Big Idea lands in five seconds, whether a chart
is legible, whether the narrative text is grounded in what the visuals show.
Only a rendered screenshot plus human-grade judgment can assess that, which
is exactly why this is a *judge* prompt, not another structural check.

## Inputs the judge needs

1. **The screenshot(s)** from R4.1's `desktop_bridge_screenshot.ps1` run —
   Overview page at minimum; Detail page if evaluating evidence quality.
2. **Grounding context**, extracted from the report's `UseCase_Bracket.yaml`
   (do not let the judge invent what the report is "supposed" to say):
   - `orchestration.narrative.decision_question` (or the bracket's actual
     path — verify against the specific report's Bracket before running)
   - `orchestration.narrative.big_idea`
   - the curated `evidence_columns` list, if evaluating the Detail page
3. **Report identifier** (e.g. `COM-002_Margin_Price_Performance`) for
   traceability in the ledger.

## The prompt

Paste the screenshot(s) as image input alongside this text (fill in the
`{{...}}` placeholders from the Bracket before sending):

```
You are a Business Intelligence report reviewer. You will be shown a
screenshot of a Power BI report page. Score it on the five dimensions below.
Be specific and cite what you actually see in the image — do not assume
content you cannot verify from the screenshot itself.

CONTEXT (from the governed Use Case definition — do not treat this as
proof the report says it; verify it against the image):
  Decision question: "{{decision_question}}"
  Big idea (intended headline takeaway): "{{big_idea}}"
  Report: {{report_id}}, page: {{page_name}}

Score each dimension 1-5 (1 = fails badly, 3 = acceptable with caveats,
5 = excellent) with a one-sentence justification citing what is visible:

1. INFORMATIVENESS — Does the page surface the KPI state and the answer to
   the decision question without requiring the viewer to hunt for it?
2. CLARITY / COHERENCE — Is the layout scannable in ~5 seconds? Is there
   visual clutter, overlap, truncated text, or illegible small text?
3. VISUALIZATION QUALITY — Are chart types appropriate for the data shown
   (no pie/donut/gauge, no mixed-scale axes, readable data labels/axes)?
4. NARRATIVE QUALITY — Does any narrative/textbox content on the page state
   a clear, specific claim (not generic boilerplate), and does it match what
   the charts actually show?
5. FACTUAL CORRECTNESS — Does the visible big-idea/headline text on the page
   match the "Big idea" given in the context above in substance (not
   necessarily verbatim)? Flag any visible number that looks implausible
   (e.g. a percentage over 1000%, a negative count) — you cannot verify
   exact figures against the data warehouse from a screenshot, so only flag
   implausibility, never claim a number is "correct."

Then give:
  - overall_recommendation: "accept" | "accept_with_notes" | "reject"
  - top_issues: up to 3 concrete, actionable issues (empty list if none)

Respond ONLY with JSON matching this shape:
{
  "report_id": "string",
  "page_name": "string",
  "dimensions": {
    "informativeness":        {"score": 1-5, "justification": "string"},
    "clarity_coherence":      {"score": 1-5, "justification": "string"},
    "visualization_quality":  {"score": 1-5, "justification": "string"},
    "narrative_quality":      {"score": 1-5, "justification": "string"},
    "factual_correctness":    {"score": 1-5, "justification": "string"}
  },
  "overall_recommendation": "accept | accept_with_notes | reject",
  "top_issues": ["string", ...]
}
```

## How a human uses the output

The judge's JSON is a **decision aid, not a gate**. A human:

1. Reads the `dimensions` scores and justifications against the actual
   screenshot (don't trust the judge blindly — spot-check at least one
   dimension against the image yourself).
2. Decides accept / accept-with-followups / reject — the judge's
   `overall_recommendation` is a suggestion, not a verdict.
3. Records the run in `docs/plans/UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`'s R4.2 ledger row:
   date, report/page, the judge's JSON (or a summary), and the human's final
   decision + any follow-up tasks filed.

## Versioning

Bump the `version` header (semver) whenever the rubric, dimensions, or
output schema change, and keep prior versions in this folder
(`llm_judge_prompt_v1.md`, `llm_judge_prompt_v2.md`, ...) rather than
overwriting — a changed rubric makes prior runs non-comparable, and the
ledger should record which prompt version produced which verdict.

## Status of this version

Written and versioned per the DoD ("Judge-Prompt im Repo versioniert"), but
**not yet run against a real screenshot** — that requires R4.1's Desktop
Bridge capture to have actually happened first (maintainer-only, see
`desktop-bridge-screenshot-workflow.md`). The DoD's other half ("ein
dokumentierter Durchlauf auf COM-002 mit Ergebnis im Ledger") is the next
step once a real COM-002 screenshot exists.

## References

| Source | What it gave us |
|---|---|
| `docs/plans/UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` R4.2 row | The five named dimensions (Informativeness, Clarity/Coherence, Visualization Quality, Narrative Quality, Factual Correctness) and the half-automatic judge-then-human posture |
| `core/usecases/core/COM-002_Margin_Price_Performance/UseCase_Bracket.yaml` | `decision_question`/`big_idea` field paths used for grounding context |
| `desktop-bridge-screenshot-workflow.md` (R4.1) | Where the input screenshots come from |
