---
title: "T1 — Per-Task Model Routing (multi-provider)"
theme: T1
charter: ALUCA I-6.6
date: 2026-06-24
status: research-draft
feeds: ADR-0008
governing_principle: "LLM-agnostic + customer-agnostic — the core knows NO provider/model IDs; models are addressed via capability/role abstractions behind a provider-adapter seam; every task class servable by ≥2 providers (no lock-in)."
---

# T1 — Per-Task Model Routing (multi-provider)

> **Grounding note (Ehrlichkeit v3).** Every pricing/benchmark claim below carries a source
> URL and a retrieval date of **2026-06-24**. Anthropic/Claude figures were verified against
> the **official** `platform.claude.com` model docs and are high-confidence. Google (Gemini)
> and OpenAI (GPT) figures could **not** be fetched from the official pricing pages — both
> returned HTTP 403 to the fetch tool on 2026-06-24 — so those numbers come from **secondary
> aggregators** and are flagged `[secondary]` and `[unverified-official]`. Where aggregators
> disagree, the disagreement is stated rather than papered over. Do not treat the non-Anthropic
> prices as authoritative without a live check against the vendor's own pricing page.

---

## Executive summary

1. **Routing exists on a spectrum**: static rules → learned classifier router (single-shot
   model pick) → confidence/escalation **cascade** (try cheap, escalate on low confidence) →
   LLM-as-router (a model decides). The current research consensus (ICML/ICLR 2025) is that
   **"cascade routing"** — a unified scheme that picks the next model adaptively and can stop
   early — dominates both pure routing and pure cascading, *provided you have a good quality
   estimator*. The quality estimator is the single most load-bearing component.
2. **For ALUCA's L0 universal-optimal default we recommend a 2-tier rule + cascade hybrid**,
   not a learned router. Reason: ALUCA task classes are few, well-defined, and individually
   gate-checkable (the existing Quality-Gate / `check_index.py` / TMDL+PBIR hooks already give
   us a near-free, *deterministic* "is this output acceptable" signal — exactly the quality
   estimator that learned cascades have to approximate). A learned classifier router adds
   training/data overhead with little marginal benefit at our task count.
3. **The design must be LLM-agnostic and customer-agnostic.** The core references **roles**
   (`fast-cheap`, `strong-reasoning`, `long-context`, `vision`), never model IDs. A
   **provider-adapter registry** maps role → concrete (provider, model, params) at the edge.
   Every role is satisfiable by ≥2 providers today (Anthropic / Google / OpenAI), so no task
   class is locked to a vendor.
4. **Cross-provider "quality × reliability" is measured with a deterministic gate first**
   (does the artifact pass `check_index.py --strict`, TMDL/PBIR hooks, schema validation?),
   then a tie-broken **LLM-as-judge** layer — but the judge literature (2026) shows judges are
   themselves unreliable and provider-biased, so judging must be: (a) blinded to provider,
   (b) panel/ensemble, (c) used only where the deterministic gate cannot decide.
5. **Cheap→escalate cascade pays off** when the cheap model's *first-pass success rate* is high
   and the *acceptance check is cheap and reliable*. It does **not** pay off when the check is
   expensive/unreliable, when escalation tail-latency is unacceptable, or when the cheap model
   almost never succeeds (then you just paid twice). Decision rule formalised in §5.

---

## 1. Model-routing strategies and their trade-offs

| Strategy | How it decides | Strengths | Weaknesses | Best for |
|---|---|---|---|---|
| **Static rules** (task-class → role table) | Hand-written mapping from task class / input features to a model role | Deterministic, debuggable, zero added latency, no training data, trivially cacheable, easy to audit/govern | Doesn't adapt per-instance; coarse; misroutes outliers; humans must maintain the table | Few, well-characterised task classes (ALUCA's case) |
| **Classifier router** (e.g. RouteLLM) | A trained model predicts P(strong model wins) for the query, routes to one model in a single shot | No extra inference calls (one model runs); ~2× cost cut at equal quality reported | Needs preference/training data; commits up-front with no recovery if wrong; a black box to govern | High query volume, heterogeneous traffic, where collecting routing labels is feasible |
| **Confidence / escalation cascade** (e.g. FrugalGPT) | Run cheapest first; a scoring function `g(q,a)∈[0,1]` decides accept-or-escalate; climb the ladder until accepted | Big cost cuts when cheap model often suffices (FrugalGPT: up to ~98% cost reduction matching GPT-4 on its benchmark); only pays for capability when needed | Adds a scoring step + escalation **tail latency**; bad threshold either leaks errors or over-escalates; multiple LLM calls per hard query | Tasks with a cheap, reliable acceptance check (ALUCA gates!) and a high cheap-model success rate |
| **LLM-as-router** | A model reads the task and names the model/role to use | Flexible, handles novel tasks, no separate classifier to train | Extra call + latency; the router can be wrong/biased; non-deterministic; harder to govern; risks the agnostic seam if it emits model IDs | Open-ended/agentic surfaces where task classes aren't enumerable |
| **Cascade routing (unified)** | Adaptively picks the *next* model using quality + cost estimates; can skip, reorder, or stop early | Reported to **dominate both routing and cascading** on quality *and* cost (ICML/ICLR 2025) | Requires good per-model quality estimators (the hard part); more machinery | The general optimum once estimators are trustworthy |

**Cross-cutting finding (load-bearing):** across RouteLLM, FrugalGPT, and the unified
cascade-routing paper, the recurring conclusion is that **the quality/confidence estimator is
the critical success factor** — "good quality estimators are identified as the critical factor
for the success of model selection." ALUCA is unusually well-positioned here because its
acceptance check is **deterministic and already built** (Quality-Gate, `check_index.py
--strict`, the TMDL/PBIR PostToolUse hooks, KPI-catalog reference validation). That moves us
from "approximate a confidence score with a DistilBERT-style probe" (FrugalGPT) to "run the
real gate" — a far stronger signal.

Sources: RouteLLM [arXiv:2406.18665](https://arxiv.org/abs/2406.18665) (ICLR 2025); FrugalGPT
[arXiv:2305.05176](https://arxiv.org/abs/2305.05176); "A Unified Approach to Routing and
Cascading for LLMs" [arXiv:2410.10347](https://arxiv.org/abs/2410.10347) /
[SRI Lab, ETH Zürich](https://www.sri.inf.ethz.ch/publications/dekoninck2024cascaderouting)
(ICML 2025). Retrieved 2026-06-24.

---

## 2. Measuring "quality × reliability" per task class, across providers

The goal is a per-(task-class, provider-candidate) score that is **comparable across vendors**
and **resistant to provider bias**. Recommended layered method:

### Layer A — Deterministic gate (primary signal, provider-blind by construction)
Run the candidate's output through ALUCA's existing machinery and score pass/fail + repair cost:
- `python scripts/check_index.py --strict` (index completeness, dead links, placeholders)
- `tooling/quality/run_quality_gate.ps1` / `run_stage1_checks.ps1` and the Python suite
  (`pytest tooling/tests/ products/`)
- TMDL style hook (`validate_tmdl_style.sh`) and PBIR structure hook (`validate_pbir_structure.sh`)
- KPI-catalog / action-code reference integrity (Golden-Thread "reference, don't redefine")

These are **objective, deterministic, free of LLM-judge bias**, and identical regardless of
which provider produced the artifact — exactly what a cross-provider comparison needs. Metrics:
*first-pass gate-pass rate*, *number of repair iterations to green*, *token+$ cost to green*,
*wall-clock to green*.

### Layer B — Reference-based scoring (where ground truth exists)
For task classes with gold artifacts (e.g. a curated KPI draft, a known-good bracket), score
candidate output against the reference with exact/structural match or rubric checklist. This is
the most credible eval method and should be preferred wherever a gold set can be assembled.

### Layer C — LLM-as-judge (tie-breaker only, used with care)
Only for subjective qualities the gate can't capture (prose clarity of a Business Factsheet,
explanation quality). The 2026 judge literature is a **caution flag**:
- Judges show *reliability without validity*: even top judges flip preferences on a meaningful
  fraction of hard cases; "even the top-performing models … fail to maintain consistent
  preferences in nearly a quarter of difficult cases."
- Self-/provider-preference bias is real. Therefore:
  - **Blind the judge to provider/model identity.**
  - Use a **panel of judges from ≥2 providers** and require agreement (or report dispersion).
  - **Never let a single provider's model be sole judge of its own task class.**
  - Treat judge output as advisory, ranked below Layers A and B.

Sources: "Reliability without Validity: … LLM-as-a-Judge …"
[arXiv:2606.19544](https://arxiv.org/html/2606.19544); "Are We on the Right Way to Assessing
LLM-as-a-Judge?" [arXiv:2512.16041](https://arxiv.org/html/2512.16041); "Judge Reliability
Harness" [arXiv:2603.05399](https://arxiv.org/pdf/2603.05399). Retrieved 2026-06-24.

**Reliability dimension** (distinct from quality): per candidate track API error/refusal rate,
p95/p99 latency, timeout/`429` rate, and (for Anthropic) `stop_reason: "refusal"` frequency.
"Quality × reliability" = (gate-pass quality score) × (1 − failure rate), so a slightly
higher-quality model that refuses or times out often loses to a steady runner-up.

---

## 3. Task-class → capability-ROLE matrix (≥2 providers per role)

Task classes for an **analytics-framework authoring product** (ALUCA), each mapped to a
capability **role** (never a model ID) with ≥2 current provider candidates. Provider candidates
are listed for *capability adequacy*, not endorsement; the registry (§7) is what binds them.

| ALUCA task class | What it needs | Capability ROLE | Provider candidate A | Provider candidate B | Rationale |
|---|---|---|---|---|---|
| **KPI-draft extraction** (pull KPI candidates from source text into structured drafts) | Structured/JSON output, modest reasoning, high volume, cheap | `fast-cheap-structured` | Anthropic **Claude Haiku 4.5** ($1/$5 MTok, 200K ctx, structured outputs) | Google **Gemini 3.1 Flash-Lite** (~$0.25/$1.50 MTok `[secondary]`, 1M ctx) or OpenAI **GPT-5.4 Nano/Mini** (~$0.20/$1.25–$0.75/$4.50 `[secondary]`) | Extraction is high-throughput and schema-bounded; cheapest tier with reliable structured output wins. All three vendors offer a cheap, fast, JSON-capable tier → no lock-in. |
| **Bracket synthesis** (compose `UseCase_Bracket.yaml`: orchestration, action_code_ids, KPI refs — the hardest reasoning/consistency step) | Strong multi-constraint reasoning, long-horizon consistency, follows Golden-Thread rules | `strong-reasoning` | Anthropic **Claude Opus 4.8** ($5/$25 MTok, 1M ctx, adaptive thinking) — or **Fable 5** ($10/$50) for the very hardest | OpenAI **GPT-5.5** (~$5/$30 `[secondary]`) or Google **Gemini 3.1 Pro** (~$2/$12, rising to $4/$18 >200K ctx `[secondary]`) | Synthesis must respect cross-file invariants; this is where capability matters most and where escalation terminates. Each vendor has a flagship reasoning model → ≥2 candidates. |
| **Source discovery** (find/triage candidate sources, web research) | Web search/fetch, synthesis, current info | `research-web` | Anthropic Claude (server `web_search_20260209`/`web_fetch_20260209`, on Opus 4.8 / Sonnet 4.6) | Google Gemini (native grounding/search) or OpenAI (web/responses tooling) | Needs first-class web tooling + good synthesis. Provider tool-surfaces differ, so the adapter must normalise "search" — but ≥2 vendors offer it. |
| **Documentation** (prose Business Factsheets — Lean 2.0, prose-only; READMEs; `_INDEX.md` entries) | Clear long-form writing, instruction-following, mid cost | `balanced-writing` | Anthropic **Claude Sonnet 4.6** ($3/$15 MTok, 1M ctx) | Google **Gemini 3.5 Flash** (~$1.50/$9 `[secondary]`) or OpenAI **GPT-5.4** (~$2.50/$15 `[secondary]`) | Prose quality + steerability at moderate cost; mid-tier models are the sweet spot. Each vendor's mid tier qualifies → ≥2 candidates. |
| **Gate-repair** (read a failing gate/hook error, edit the artifact green) | Tight instruction-following, code/markup edits, deterministic-ish, fast loop | `fast-cheap-edit` → escalate to `strong-reasoning` | Tier 1: Claude Haiku 4.5 / Sonnet 4.6; Tier 2 (escalation): Claude Opus 4.8 | Tier 1: Gemini 3.1 Flash-Lite / 3.5 Flash or GPT-5.4 Mini; Tier 2: Gemini 3.1 Pro or GPT-5.5 | Most gate failures are mechanical (tab vs space in TMDL, missing `_INDEX.md` row) → cheap model fixes them; escalate only the few that need real reasoning. Natural cascade. |
| *(supporting)* **Long-context ingest** (whole-repo / large-doc reasoning) | ≥1M token context | `long-context` | Claude Opus 4.8 / Sonnet 4.6 / Fable 5 (1M ctx) | Gemini 3.1 Pro / 3.1 Flash-Lite (1M ctx) | Both Anthropic and Google offer 1M-token context; OpenAI GPT-5.4 also advertises 1M `[secondary]` → ≥2 candidates. |
| *(supporting)* **Vision** (read screenshots/diagrams of reports) | Image input | `vision` | Claude (all current models support vision input) | Gemini (native multimodal) or OpenAI GPT-5.x (vision) | Multiple vendors → no lock-in. |

**Verification of the Claude column (primary):** Opus 4.8 = $5/$25, 1M ctx, 128K out; Sonnet
4.6 = $3/$15, 1M ctx, 64K out; Haiku 4.5 = $1/$5, 200K ctx, 64K out; Fable 5 = $10/$50, 1M ctx,
128K out — all from the official models overview, retrieved 2026-06-24
([platform.claude.com](https://platform.claude.com/docs/en/about-claude/models/overview.md)).
The Google/OpenAI columns are `[secondary]` (see §8 Sources for the aggregator URLs and the
disagreements). The matrix's **load-bearing claim — that every role has ≥2 viable providers —
holds regardless of the exact cents**, because each vendor publicly ships a cheap tier, a mid
tier, a flagship-reasoning tier, web tooling, ≥1M context, and vision.

---

## 4. The recommended routing procedure (L0 universal-optimal default)

A **decidable, deterministic rule-plus-cascade** — no learned router at L0.

```
INPUT: task_class, payload, (optional) context_size, needs_vision, needs_web
OUTPUT: (role, then concrete model via the registry — §7)

# Step 1 — STATIC ROLE SELECTION (rule table, deterministic)
role = ROLE_TABLE[task_class]              # §3 matrix; the core's only "decision"
if context_size > LONG_CTX_THRESHOLD:  role = "long-context"
if needs_vision:                       role = compose(role, "vision")
if needs_web:                          role = compose(role, "research-web")

# Step 2 — RESOLVE role -> provider/model via the adapter registry (no IDs in core)
candidate = registry.resolve(role)         # primary candidate for this role
# registry already encodes ≥2 providers per role; it returns the active primary.

# Step 3 — RUN
output = candidate.run(payload)

# Step 4 — DETERMINISTIC ACCEPTANCE GATE (the quality estimator)
verdict = run_gate(task_class, output)     # check_index --strict / quality_gate / hooks / schema

# Step 5 — ESCALATION CASCADE (only for cascade-enabled task classes)
escalations = 0
while verdict != PASS and escalations < MAX_ESCALATIONS(task_class):
    role = ESCALATE(role)                  # e.g. fast-cheap-edit -> strong-reasoning
    candidate = registry.resolve(role)
    output = candidate.run(payload, prior=output, gate_feedback=verdict.errors)
    verdict = run_gate(task_class, output)
    escalations += 1

# Step 6 — TERMINATE
if verdict == PASS:        return output
else:                      return FAIL_TO_HUMAN(output, verdict.errors)   # never silently ship
```

**Explicit escalation criteria (decidable):**
- **Escalate** iff the deterministic gate returns a *fail* AND the task class is marked
  cascade-enabled AND `escalations < MAX_ESCALATIONS`. (Gate-repair: yes; bracket-synthesis:
  start strong, escalate at most once to Fable-tier; KPI extraction: escalate cheap→mid once;
  documentation: usually no escalation — a prose miss is human-reviewed, not auto-escalated.)
- **Do NOT escalate** when: the gate *passes*; the failure is a *human-judgment* failure the
  gate can't see (route to human, not to a bigger model); or escalation budget is exhausted.
- **Cross-provider failover (orthogonal to capability escalation):** if the primary candidate
  returns a hard provider error (`429`, timeout, refusal/`stop_reason:"refusal"`, 5xx after
  SDK retries), the registry transparently retries the **same role on provider B**. This is the
  no-lock-in guarantee in action and is separate from the cheap→strong escalation ladder.

**Why this is the universal-optimal default for ALUCA, not a learned router:** (a) the gate is a
*real* acceptance check, beating the approximate confidence scorers that learned cascades rely
on; (b) it's fully auditable/governable (repo rules > GOI); (c) zero training data or model
drift to manage; (d) it degrades to "pick the strong model directly" for any task class where
the cheap tier rarely passes (set `MAX_ESCALATIONS=0` and `ROLE_TABLE[class]="strong-reasoning"`).
Cascade-routing (the ICML-2025 optimum) remains a documented **L1 upgrade path** once we have
trustworthy per-model quality estimators beyond the binary gate.

---

## 5. When is a cheap→escalate cascade worth it vs. picking a strong model directly?

Let:
- `p` = first-pass acceptance rate of the cheap model for this task class (gate-pass)
- `C_cheap`, `C_strong` = cost (tokens·$ + latency) of one cheap / strong call
- `C_gate` = cost of running the acceptance check (≈ free for ALUCA's deterministic gates)

**Expected cost of the cascade** ≈ `C_cheap + C_gate + (1−p)·C_strong`.
**Cost of going strong directly** ≈ `C_strong` (+`C_gate` if you still verify).

**Cascade wins when:** `C_cheap + (1−p)·C_strong < C_strong`, i.e. roughly **`p > C_cheap / C_strong`**.
With Haiku-vs-Opus economics (~$1/$5 vs $5/$25, so `C_cheap/C_strong ≈ 0.2`), the cascade pays
off whenever the **cheap model succeeds more than ~20% of the time** — a low bar that mechanical
gate-repair and bounded extraction easily clear.

**Decision criteria (use the cascade when ALL hold):**
1. **Acceptance check is cheap and reliable.** ALUCA's deterministic gates satisfy this; if the
   only check were an unreliable LLM-judge, prefer going strong directly.
2. **Cheap-model first-pass success `p` clears the cost-ratio bar** (`p > C_cheap/C_strong`).
3. **Tail latency is acceptable.** Escalation adds the cheap call's latency to the hard cases;
   for interactive surfaces with strict SLAs, prefer direct-strong or run cheap+strong in
   parallel and take the first that passes (speculative, costs more).
4. **Escalation is bounded** (`MAX_ESCALATIONS` small) so a pathological input can't loop.

**Pick the strong model directly when:** the task is the hardest reasoning step and the cheap
model almost never passes (bracket synthesis — start strong); the acceptance check is
expensive/unreliable; or latency budget forbids a second hop. (FrugalGPT's headline ~98% cost
cut assumed a cheap, learned scorer and a high cheap-success regime — not universal; treat it as
an upper bound, not an expectation.)

Sources: FrugalGPT [arXiv:2305.05176](https://arxiv.org/abs/2305.05176); cascade trade-offs and
"start static, add cascading only where savings justify complexity" synthesised from the survey
"Dynamic Model Routing and Cascading for Efficient LLM Inference"
[arXiv:2603.04445](https://arxiv.org/html/2603.04445v2) and
[bigdataboutique LLM cost playbook](https://bigdataboutique.com/blog/llm-cost-optimization-techniques).
Retrieved 2026-06-24.

---

## 6. Current model line-ups & rough cost/capability tiers (verify live)

### Anthropic / Claude — PRIMARY-VERIFIED (official docs, 2026-06-24)
Source: [platform.claude.com models overview](https://platform.claude.com/docs/en/about-claude/models/overview.md).

| Model | API ID | Input $/MTok | Output $/MTok | Context | Max output | Tier |
|---|---|---|---|---|---|---|
| Claude Fable 5 | `claude-fable-5` | $10 | $50 | 1M | 128K | Top capability (GA 2026-06-09) |
| Claude Opus 4.8 | `claude-opus-4-8` | $5 | $25 | 1M | 128K | Flagship reasoning |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | $3 | $15 | 1M | 64K | Balanced |
| Claude Haiku 4.5 | `claude-haiku-4-5` | $1 | $5 | 200K | 64K | Fast/cheap |
| *(legacy active)* Opus 4.7 / 4.6 | `claude-opus-4-7` / `-4-6` | $5 | $25 | 1M | 128K | Prev-gen flagship |

### Google / Gemini — `[secondary]`, `[unverified-official]` (official page 403'd on 2026-06-24)
Aggregator-sourced; **numbers conflict across sources** — verify against
[ai.google.dev pricing](https://ai.google.dev/gemini-api/docs/pricing) before use.

| Model (per aggregators) | Input $/MTok | Output $/MTok | Context | Notes / disagreement |
|---|---|---|---|---|
| Gemini 3.1 Pro | $2 (≤200K) → $4 (>200K) | $12 → $18 | 1M | flagship reasoning, "preview" per one source |
| Gemini 3.5 Flash | $1.50 | $9 | (1M class) | launched ~2026-05-19 per [TokenMix](https://tokenmix.ai/blog/gemini-3-5-pro-release-date-google-io-2026) |
| Gemini 3.1 Flash-Lite | $0.25 | $1.50 | ~1.05M | one source says $0.10/$0.40 — **conflict, unresolved** |

Sources: [metacto Gemini guide](https://www.metacto.com/blogs/the-true-cost-of-google-gemini-a-guide-to-api-pricing-and-integration),
[aipricing.guru Google](https://www.aipricing.guru/google-ai-pricing/),
[Google blog: Gemini 3.1 Flash-Lite](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/),
[pricepertoken Flash-Lite](https://pricepertoken.com/pricing-page/model/google-gemini-3.1-flash-lite-preview). Retrieved 2026-06-24.

### OpenAI / GPT — `[secondary]`, `[unverified-official]` (official pages 403'd on 2026-06-24)
Aggregator-sourced; verify against [openai.com/api/pricing](https://openai.com/api/pricing/) before use.

| Model (per aggregators) | Input $/MTok | Output $/MTok | Context | Tier |
|---|---|---|---|---|
| GPT-5.5 | $5 | $30 | — | Newest flagship (~Apr 2026) |
| GPT-5.5 Pro | $30 | $180 | — | Max capability / research-grade |
| GPT-5.4 | $2.50 | $15 | 1M | Production workhorse |
| GPT-5.4 Mini | $0.75 | $4.50 | — | Budget mid |
| GPT-5.4 Nano | $0.20 | $1.25 | — | Cheapest reasoning-capable |
| GPT-4.1 Nano | $0.10 | $0.40 | 1M | Cheapest overall |
| o3 | $2 | $8 | — | Reasoning-focused |

Sources: [metacto OpenAI guide](https://www.metacto.com/blogs/unlocking-the-true-cost-of-openai-api-a-deep-dive-into-usage-integration-and-maintenance),
[aipricing.guru OpenAI](https://www.aipricing.guru/openai-pricing/),
[pecollective OpenAI pricing](https://pecollective.com/tools/openai-api-pricing/),
[cloudzero OpenAI pricing](https://www.cloudzero.com/blog/openai-pricing/). Retrieved 2026-06-24.

> **Capability-tier takeaway (provider-agnostic):** all three vendors expose the same *shape* of
> line-up — a sub-$1 cheap tier, a ~$1–3 input mid tier, a ~$5 input flagship-reasoning tier, and
> a premium/research tier — plus 1M-context options and vision. That structural symmetry is what
> makes the role abstraction in §3/§7 implementable without lock-in.

---

## 7. Agnostic check — the core knows NO model IDs

**Claim under test:** no core/business path ever names a provider or model ID; everything goes
through capability roles bound at the edge.

**Confirmation walk-through:** In §4's procedure, the core only ever (a) reads
`ROLE_TABLE[task_class]` → a *role string*, and (b) calls `registry.resolve(role)`. The strings
`"fast-cheap-structured"`, `"strong-reasoning"`, `"long-context"`, etc. carry no vendor
identity. The Golden-Thread rule ("reference, don't redefine") extends naturally: use-cases
reference governed roles, never model IDs, just as they reference KPI-catalog entries rather
than redefining KPIs.

### Provider-adapter seam (registry/contract pattern)

```
# ---- CONTRACT (stable, provider-neutral; this is all the core depends on) ----
interface ModelAdapter:
    run(payload, *, prior=None, gate_feedback=None) -> Output
    capabilities() -> set[Capability]          # {structured, vision, web, long_ctx, ...}
    health() -> {ok, p95_latency, error_rate, refusal_rate}

interface ModelRegistry:
    resolve(role: Role) -> ModelAdapter         # returns active primary for the role
    failover(role: Role, exclude: Provider) -> ModelAdapter   # next provider, same role
    register(role: Role, adapter: ModelAdapter, priority: int)

# ---- ROLE → CANDIDATES (config/data, NOT core code; ≥2 providers each) ----
ROLE_BINDINGS = {
  "fast-cheap-structured": [ (anthropic, "claude-haiku-4-5"),  (google, "<gemini-flash-lite>"), (openai, "<gpt-5.4-nano>") ],
  "strong-reasoning":      [ (anthropic, "claude-opus-4-8"),   (openai, "<gpt-5.5>"),           (google, "<gemini-3.1-pro>") ],
  "balanced-writing":      [ (anthropic, "claude-sonnet-4-6"), (google, "<gemini-3.5-flash>"),  (openai, "<gpt-5.4>") ],
  "long-context":          [ (anthropic, "claude-opus-4-8"),   (google, "<gemini-3.1-pro>"),    (openai, "<gpt-5.4>") ],
  "research-web":          [ (anthropic, "claude-opus-4-8+web"),(google, "<gemini+grounding>"), (openai, "<gpt+web>") ],
  # gate-repair uses fast-cheap-edit (tier1) then escalates to strong-reasoning (tier2)
}
```

Properties this seam guarantees:
- **LLM-agnostic:** swapping Anthropic→Google for a role is a *config edit to `ROLE_BINDINGS`*,
  zero core-code change. Model IDs live only inside concrete `ModelAdapter` implementations.
- **Customer-agnostic:** role→provider preference can be overridden per workspace/customer
  *in the registry config* (e.g. an EU-only customer pins providers/regions for DSGVO — see
  `compliance/_INDEX.md`) without the use-case/bracket logic knowing anything about it.
- **No lock-in:** `resolve` returns the priority-ordered primary; `failover` walks to the next
  provider for the *same role* on hard error. Because every role lists ≥2 providers (§3), every
  task class is servable without the primary vendor.
- **Governable:** the binding table is data, lintable like the rest of the repo (a check could
  assert "every role has ≥2 distinct providers" — analogous to `check_index.py`'s subtree rule).
- **Cache-safe:** keep the role→model binding stable within a session; switching providers
  mid-conversation invalidates prompt caches, so failover restarts the unit of work rather than
  mid-stream swapping.

**Provider quirks the adapter must absorb (so the core stays clean):** Anthropic adaptive-thinking
vs. budget tokens, `stop_reason:"refusal"` handling and server-side fallbacks, web-tool type
versions, structured-output parameter shape — these are exactly the kind of per-provider detail
that belongs *inside* the adapter, never in the routing core. (Anthropic specifics verified via
the bundled `claude-api` skill, 2026-06-24.)

---

## 8. Sources (URL + retrieval date 2026-06-24)

**Primary / official:**
- Claude models overview (IDs, pricing, context, max output) — https://platform.claude.com/docs/en/about-claude/models/overview.md
- Anthropic API behaviour (adaptive thinking, refusal/fallbacks, web tools, structured outputs) — bundled `claude-api` skill (Anthropic), 2026-06-24

**Routing / cascade research (primary papers, abstracts via search; full text 403'd to fetch tool):**
- RouteLLM (classifier router, ~2× cost cut) — https://arxiv.org/abs/2406.18665 (ICLR 2025)
- FrugalGPT (LLM cascade, confidence scorer, up-to-98% cost cut) — https://arxiv.org/abs/2305.05176
- A Unified Approach to Routing and Cascading for LLMs (cascade-routing dominates both) — https://arxiv.org/abs/2410.10347 ; https://www.sri.inf.ethz.ch/publications/dekoninck2024cascaderouting (ICML 2025)
- Survey: Dynamic Model Routing and Cascading for Efficient LLM Inference — https://arxiv.org/html/2603.04445v2
- LLM cost optimisation playbook (start-static-then-cascade guidance) — https://bigdataboutique.com/blog/llm-cost-optimization-techniques

**LLM-as-judge reliability (primary papers):**
- Reliability without Validity: LLM-as-a-Judge across agreement/consistency/bias — https://arxiv.org/html/2606.19544
- Are We on the Right Way to Assessing LLM-as-a-Judge? — https://arxiv.org/html/2512.16041
- Judge Reliability Harness — https://arxiv.org/pdf/2603.05399

**Secondary / aggregator (Google & OpenAI pricing — official pages 403'd; treat as unverified):**
- Gemini: https://www.metacto.com/blogs/the-true-cost-of-google-gemini-a-guide-to-api-pricing-and-integration ; https://www.aipricing.guru/google-ai-pricing/ ; https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/ ; https://pricepertoken.com/pricing-page/model/google-gemini-3.1-flash-lite-preview ; https://tokenmix.ai/blog/gemini-3-5-pro-release-date-google-io-2026
- OpenAI: https://www.metacto.com/blogs/unlocking-the-true-cost-of-openai-api-a-deep-dive-into-usage-integration-and-maintenance ; https://www.aipricing.guru/openai-pricing/ ; https://pecollective.com/tools/openai-api-pricing/ ; https://www.cloudzero.com/blog/openai-pricing/
- (Official pages that should be re-checked live: https://ai.google.dev/gemini-api/docs/pricing , https://openai.com/api/pricing/ , https://developers.openai.com/api/docs/pricing)

---

## 9. Open / unverified items (be honest)

- **Google & OpenAI pricing is NOT officially verified.** Both vendors' official pricing pages
  returned **HTTP 403** to the fetch tool on 2026-06-24; all Gemini/GPT cents above are from
  third-party aggregators and must be confirmed against the vendor pages before ADR-0008 commits
  to any number. The **architecture (roles + registry) does not depend on the exact prices** —
  only on each role having ≥2 viable providers, which holds.
- **Gemini Flash-Lite price conflict unresolved:** sources give both ~$0.25/$1.50 and $0.10/$0.40
  per MTok. Treat as a range pending official confirmation.
- **OpenAI model naming churn:** aggregators reference GPT-5.4/5.5 and o3 with varying exact IDs;
  the precise current API model strings should be pulled from OpenAI's live model list.
- **Routing-paper full texts not fetched:** arxiv HTML/PDF and the SRI Lab page 403'd; claims
  rest on the abstracts/search summaries (consistent across multiple sources) — directionally
  reliable, but quote-level figures (e.g. FrugalGPT's "98%") are benchmark-specific upper bounds,
  not guarantees for ALUCA.
- **Cross-provider benchmark numbers for ALUCA's specific task classes do not exist yet** — they
  must be *generated* by running Layer-A/B evals (§2) on a held-out ALUCA gold set; no public
  benchmark substitutes for that. This is the recommended first build step before ADR-0008 fixes
  default role bindings.
- **Provider web-tool parity** (`research-web` role): Anthropic web search/fetch is verified;
  Google grounding and OpenAI web tooling are assumed adequate but their exact surfaces/limits
  for ALUCA's source-discovery flow were not benchmarked here.
