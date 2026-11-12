---
title: "T2 — Token Optimization (grounded research)"
theme: T2
charter: ALUCA I-6.6
date: 2026-06-24
status: research-draft
feeds: ADR-0008
governing_principle: LLM-agnostic and customer-agnostic — techniques described per capability, marking provider-specific vs universal.
---

# T2 — Token Optimization

> **Grounding note.** Every pricing/discount number below carries a source URL and a
> retrieval date of **2026-06-24**. Numbers were verified against primary/official
> sources where reachable; where a primary source was blocked by the research proxy,
> the claim is corroborated by ≥2 secondary sources and **flagged**. No pricing or
> caching-discount number is stated from model memory. See *Sources* and
> *Open / Unverified* at the end.

---

## Executive summary

Token cost on an LLM-backed authoring product is driven by **input tokens far more than
output tokens** when prompts are system-prompt-heavy and schema-constrained — exactly
ALUCA's shape. The highest-leverage, **quality-neutral** lever is therefore **prompt /
context caching**: re-using a stable prefix (frozen system prompt + deterministic tool
list + governed schema) costs ~**0.1× input price** on a cache read across all three major
providers, i.e. up to a **90% input-token discount on the cached span** (Anthropic; Google
Gemini 2.5+; OpenAI's newest models — verified per provider below). It loses **no quality**
because the bytes are identical; the model sees exactly the same prompt.

The other quality-neutral levers, in rough priority for this product:

1. **Prompt / context caching** (L0 default) — biggest win for a heavy stable prefix.
2. **Constrained / structured JSON output** (L0 default) — already required by the schema;
   eliminates re-prompt/repair round-trips, which is where it saves tokens.
3. **Batch APIs** (L1, optional) — flat **50% discount** (Anthropic) on *non-latency-sensitive*
   work (bulk re-generation, evals, backfills). Not for interactive authoring.
4. **Just-in-time retrieval instead of full-context** (L1/L2) — fetch the smallest
   high-signal set rather than pre-loading whole catalogs; large input-token savings but
   carries a real quality risk (retrieval can miss relevant context).
5. **Context compaction / trimming** (L1, long-horizon only) — summarize or clear stale
   turns; lossy by construction, so it is a long-session tactic, not a default.

**Provider-specificity matters most for caching**: the *discount* is similar (~90%) but the
*semantics* differ — Anthropic requires explicit `cache_control` breakpoints and charges a
**cache-write premium (1.25×/2×)**; OpenAI and Gemini-2.5 cache **automatically with no write
premium**; Gemini also offers an *explicit* cache with storage cost. A caching layer must be
written behind a provider abstraction so the "where do I put the breakpoint / do I pay to
write" logic is swappable.

---

## RQ1 — Techniques that reduce tokens WITHOUT quality loss

"Without quality loss" = the model receives semantically equivalent (often byte-identical)
input and is asked for the same output. Ranked by fit to a system-prompt-heavy + JSON-output
authoring product.

### 1. Prompt / context caching — *quality-neutral by construction*

**What it saves.** Re-processing of a repeated prompt **prefix**. The cached span bills at a
deep discount instead of full input price.

| Provider | Cache-read price | = discount on cached span | Cache-write premium | Auto or manual |
|---|---|---|---|---|
| **Anthropic** | 0.1× base input | **~90%** | 1.25× (5-min TTL) / 2× (1-h TTL) | Manual breakpoints **or** top-level auto-cache |
| **OpenAI** (newest, e.g. GPT-5.x) | up to 0.1× input | **up to ~90%** (older 4o-family was 50%) | none | **Automatic**, no opt-in |
| **Google Gemini 2.5+** (implicit) | 0.1× input | **~90%** (Gemini 2.0 = 75%) | none (no storage cost for implicit) | **Automatic** by default |

Sources: Anthropic prompt-caching docs (verified live, 2026-06-24); Azure OpenAI prompt-caching
docs (verified live — mechanics; discount varies by model); Google Cloud / Gemini implicit-caching
docs (verified live).

**Why it's quality-neutral:** caching is a **prefix match on exact bytes** — the model's input
is unchanged, only the *billing* and *latency* change. There is no summarization, no dropping
of content.

**The one hard rule (all providers): the prefix must be byte-stable.** Any change anywhere in
the prefix invalidates everything after it. Render order is `tools → system → messages`
(Anthropic) / system-then-messages (OpenAI, Gemini). Silent cache-busters: `datetime.now()` in
the system prompt, unsorted `JSON.stringify`, a per-request UUID, a tool list that varies per
user. (Anthropic prompt-caching docs; corroborated by Azure OpenAI: *"A single character
difference in the first 1,024 tokens results in a cache miss."*)

### 2. Structured / constrained output (JSON Schema) — *quality-neutral, saves the retry*

**What it saves.** Not the first response — it saves the **repair round-trip**. With a
constrained decoder (`output_config.format` / `response_format: json_schema` / Gemini
`responseSchema`) the model is *guaranteed* to emit schema-valid JSON, so you don't spend a
second full request re-prompting "that wasn't valid JSON, try again." For a product that emits
schema-constrained JSON on every call, this is a recurring saved request, not a one-off.

**Quality risk:** essentially none for *validity*; minor watch-items — a hard `max_tokens`
truncates JSON mid-object (`stop_reason: max_tokens`), and a safety refusal can return
non-schema output. Constrained output is also **incompatible with citations** on Anthropic and
adds a one-time schema-compile latency on first use (24-h schema cache thereafter). (Anthropic
structured-outputs docs / skill reference.)

### 3. Batch APIs — *quality-neutral, 50% flat, async only*

**What it saves.** A flat **50% discount on all tokens** (input + output) for requests you can
afford to run asynchronously (most batches finish < 1 h; max 24 h). Same model, same prompt,
same output quality — you trade *latency* for *price*, not quality. **Batch + caching discounts
stack.** (Anthropic Message Batches docs, verified via official docs search 2026-06-24.)

Provider-specific: Anthropic Message Batches = 50%; OpenAI Batch API = 50% (widely documented;
not re-verified live here — flagged). Not available on Bedrock/Vertex for Anthropic models (see
platform-availability).

### 4. System-prompt reuse — *this IS caching, framed as discipline*

"System-prompt reuse" is not a separate API feature; it is the **design discipline that makes
caching hit**: keep one frozen system prompt + deterministic tool order so the prefix is shared
across every request and every user. The token saving is realised *through* the cache (above).
Quality-neutral. The product-level action is "never interpolate volatile data into the system
prompt" — inject per-request context *after* the cached prefix (Anthropic supports a
mid-conversation `role:"system"` message for exactly this, preserving the cached prefix).

### 5. Retrieval instead of full-context (just-in-time) — *large savings, real quality risk*

**What it saves.** Instead of pre-loading the entire KPI catalog / action-code library /
schema corpus into every prompt, retrieve only the high-signal subset the current task needs.
Anthropic's own context-engineering guidance frames this as fetching *"the smallest set of
high-signal tokens"* just-in-time rather than pre-loading. Savings scale with how much of the
corpus you were needlessly carrying.

**Quality risk: this is the one "quality-neutral" technique that ISN'T.** If retrieval omits a
relevant KPI definition or governed rule, the output degrades silently. It is quality-neutral
*only if* recall is high. Treat as an optimization with a measurable quality gate, not a free
default.

### 6. Context compaction / trimming — *long-horizon only, lossy*

Summarizing or clearing stale turns (Anthropic `compaction` / `context-editing`; provider
equivalents) keeps a long session under the window. **Lossy by construction** — compaction
*summarizes*, context-editing *deletes* old tool results. Only relevant for long multi-turn
sessions; for single-shot authoring calls it does not apply. Anthropic guidance notes tool
observations can consume 70–80% of the window in long agent loops, which is when this earns its
keep.

### Quantified, source-backed savings figures

- Cache read = **0.1× input** → **~90%** off the cached span (Anthropic, Gemini 2.5+, newest
  OpenAI). [verified]
- Batch = **−50%** on all tokens; **stacks** with caching. [verified — Anthropic]
- Programmatic tool calling (keep intermediate tool results out of context) reduced average
  token use **43,588 → 27,297 = ~37%** on complex research tasks. [Anthropic engineering,
  via official-domain search snippet — page body blocked, see Unverified]

---

## RQ2 — Provider-specific differences in caching semantics (verified 2026-06-24)

The discount converges (~90%) but the **mechanism** diverges. This is the part a portable
LLM layer must abstract.

| Dimension | **Anthropic (Claude)** | **OpenAI** | **Google (Gemini)** |
|---|---|---|---|
| Enablement | **Explicit** `cache_control:{type:"ephemeral"}` breakpoints, **or** top-level auto-cache | **Automatic**, no opt-in, no opt-out | **Implicit** = automatic (2.5+); **explicit** cache API also available |
| Cache-write cost | **Premium: 1.25× (5-min) / 2× (1-h)** | **None** | None for implicit; explicit has **storage cost** (per-token-hour) |
| Cache-read cost | 0.1× input (~90% off) | up to 0.1× input on newest models (50% on 4o-era) | 0.1× input on 2.5+ (~90%); 0.75× saving on 2.0 |
| Min cacheable prefix | **512** (Fable/Mythos 5) · **1024** (Opus 4.8, Sonnet 4.6) · **2048** (Opus 4.7) · **4096** (Opus 4.6/4.5, Haiku 4.5) | **1024 tokens**, then **128-token** increments | **1024** (2.5 Flash) / **2048** (2.5 Pro) for implicit eligibility |
| TTL / retention | 5-min default, 1-h optional (2× write) | ~5–10 min idle, ≤1 h; **extended 24 h** opt-in on newer models | implicit ephemeral; explicit = you set TTL (storage billed) |
| Breakpoints | **Max 4**, 20-block lookback window | prefix only (hash of first ~256 tokens routes) | prefix only / named explicit cache |
| Cache key scope | model-scoped; org-scoped | org-scoped; `prompt_cache_key` to steer routing | project-scoped |

Sources: Anthropic prompt-caching docs (live); Azure OpenAI prompt-caching docs (live);
Gemini implicit-caching docs / Google Cloud context-cache overview (live). OpenAI first-party
discount % varies by model and was confirmed via search (50% historical 4o-family; up to 90%
on GPT-5.x) — **the exact current per-model number must be read live from OpenAI pricing at
integration time** (their pricing page was proxy-blocked here).

**Practical implications for a portable layer**

- **Anthropic is the only one where you pay to write the cache.** A prefix used **once** is a
  net *loss* on Anthropic (1.25× write, no read). Break-even ≈ 2 requests (5-min) / ≈ 3
  requests (1-h). For OpenAI/Gemini there is no write premium, so caching is "free upside."
- **Anthropic needs explicit breakpoint placement**; OpenAI/Gemini-implicit need only that you
  *put the stable bytes first*. The portable rule that satisfies all three: **stable prefix
  first, byte-identical, volatile content last.**
- **Minimum-prefix thresholds differ** — a ~1.5K-token system prompt caches on Sonnet 4.6 and
  Gemini 2.5 Flash but is **below the 4096 floor** on Opus 4.6 / Haiku 4.5. The layer should
  know each model's floor and not bother marking sub-floor prefixes.

---

## RQ3 — Measurement and quality risk per technique

| Technique | How to measure it works | How to measure it didn't hurt quality | Trade-off |
|---|---|---|---|
| Caching | `cache_read_input_tokens` > 0 and rising across repeated calls (Anthropic `usage`); `prompt_tokens_details.cached_tokens` (OpenAI); cached-token field (Gemini). If read = 0 across identical prefixes → silent invalidator. | None needed — output is unchanged by construction. | Anthropic write premium; cache scoped to model/org; bursty fan-out all miss until first write streams. |
| Structured output | Schema-validation pass rate → 100%; count of repair retries → 0. | Spot-check that constraining didn't truncate (`stop_reason`) or force empty fields. | Incompatible w/ citations (Anthropic); first-use compile latency; `max_tokens` truncation. |
| Batch | Per-token invoice at 0.5×; batch completion < 24 h. | Compare batch vs sync outputs on a sample — should be identical-quality. | Latency (async only); results unordered (key by `custom_id`); not on all platforms. |
| JIT retrieval | Input tokens per call drop vs full-context baseline. | **Recall/coverage metric** on a labelled set: did the retrieved set contain every governed definition the answer needed? This is the gating metric. | Real quality risk: missing context degrades output silently. |
| Compaction / trim | Session stays under window; `input_tokens` low while history long. | Task-success / answer-consistency before vs after compaction. | Lossy — summary can drop a detail later needed. |
| System-prompt reuse | Same as caching (read-token field). | None. | Requires never interpolating volatile data into system prompt. |

**Universal measurement primitive:** `total_input = input_tokens + cache_creation_input_tokens
+ cache_read_input_tokens`. Logging the split per request is the single most useful
instrumentation to add — it tells you cache-hit rate, where tokens actually go, and catches
silent cache busting. Use the provider's **token-counting endpoint** (Anthropic
`count_tokens`; never `tiktoken` for Claude — it undercounts ~15–20%) to size prompts before
sending.

---

## RQ4 — What applies directly to ALUCA (system-prompt-heavy + schema-constrained JSON)

ALUCA's authoring prompts are: large frozen instruction + governed KPI/action-code/schema
context (stable) + a small per-use-case ask (volatile), producing **schema-constrained JSON**.
This is the *ideal* caching shape and the *ideal* structured-output shape.

**Direct fits (do these):**

1. **Cache the stable prefix.** Frozen system prompt + deterministic (sorted) tool list +
   governed schema/catalog context → one cached prefix shared across every authoring call and
   every customer. With a Sonnet/Opus-4.8-class model (1024-token floor) the system prefix
   easily clears the minimum. Expect ~90% off that span on repeat calls.
2. **Keep emitting constrained JSON**, but via the native structured-output path so you never
   pay a repair round-trip.
3. **Never interpolate volatile data (customer id, timestamp, the specific use-case ask) into
   the cached prefix.** Put it in the trailing user turn. This is the single highest-value
   discipline and it is free.
4. **Route bulk/regeneration/eval workloads to the Batch API** (50%, stacks with cache).
   Interactive authoring stays on the sync path.

**Conditional fits (measure first):**

5. **JIT retrieval of the catalog** instead of stuffing the entire KPI catalog + action codes
   into every prompt — only once the catalog is large enough that pre-loading dominates the
   prefix. Gate on a recall metric so a missing governed definition can't slip through.

---

## Prioritized technique list — savings lever · quality risk · provider-specificity · Next.js dock-in

> Dock-in points assume a typical Next.js LLM layer: a thin **provider adapter**, an
> **orchestrator** (decides sync vs batch, multi-turn), a **context-builder** (assembles
> system/tools/messages), and **prompts** (the frozen templates).

| # | Technique | Savings lever | Quality risk | Provider-specific? | Dock-in point |
|---|---|---|---|---|---|
| 1 | **Prefix caching** | ~90% off cached span | None (byte-identical) | **Yes** — write premium + explicit breakpoints (Anthropic) vs auto (OpenAI/Gemini); per-model min-prefix floors | **context-builder** emits stable-first ordering + cache markers; **provider adapter** owns breakpoint syntax & write-premium math |
| 2 | **Structured/constrained JSON output** | Eliminates repair round-trip | Minimal (truncation/refusal edge) | Partly — `output_config.format` vs `response_format` vs `responseSchema` | **prompts** define the schema; **provider adapter** maps it to each API's constrained-decode param |
| 3 | **System-prompt reuse discipline** | Makes #1 hit cross-call/cross-customer | None | No (universal discipline) | **prompts** (frozen template) + **context-builder** (volatile data injected *after* prefix) |
| 4 | **Batch API** | −50% all tokens, stacks w/ cache | None (async only) | **Yes** — 1P only for Anthropic; not on Bedrock/Vertex | **orchestrator** routes non-interactive jobs to batch + polls by `custom_id` |
| 5 | **JIT retrieval vs full-context** | Cuts input by not pre-loading whole catalog | **High** — silent recall failures | No (RAG pattern is universal) | **context-builder** (retrieve top-k governed defs); needs a recall eval harness |
| 6 | **Compaction / context trimming** | Caps tokens in long sessions | Medium — lossy summarization | Partly — Anthropic compaction/context-editing betas; provider equivalents | **orchestrator** (long-running sessions only) |
| 7 | **Token counting before send** | Prevents over-budget calls / sizing surprises | None | Yes — Anthropic `count_tokens`; do not use `tiktoken` for Claude | **provider adapter** (pre-flight count) |

---

## Recommendation — L0 universal defaults vs L1/L2 overrides

**L0 — universal defaults (on for every customer, every model, no override needed):**

- **Prefix caching** of the frozen system prompt + deterministic tool list + governed context.
  Quality-neutral, provider-agnostic in *intent*; the adapter handles per-provider mechanics
  (and skips marking sub-floor prefixes / single-use Anthropic prefixes that wouldn't break
  even).
- **Native structured/constrained JSON output** — the product already requires schema-valid
  JSON; doing it via the constrained decoder removes repair retries.
- **System-prompt-reuse discipline** — frozen prefix, volatile data injected after it. This is
  what *makes* L0 caching pay off; it is a code-structure default, not a runtime flag.
- **Per-request token-split logging** (`input / cache_read / cache_creation`) — the
  measurement backbone for everything else.

**L1 — optional, domain/workload override:**

- **Batch API** for bulk regeneration, evals, library backfills — enabled per *job type*, not
  per customer. Default off for interactive authoring.
- **JIT catalog retrieval** — enable per customer/domain once their catalog is large enough
  that full-context pre-loading dominates the prefix; **gated on a recall metric**.

**L2 — customer/domain-specific, rarely:**

- **Context compaction / trimming** — only for customers running genuinely long multi-turn
  authoring sessions. Lossy; off by default.
- **1-hour cache TTL / extended retention** — only for customers with bursty traffic that has
  gaps longer than the default TTL; the 2× write premium (Anthropic) must be justified by
  read volume.

**Rationale:** L0 items are quality-neutral and universally beneficial; L1/L2 items either
trade latency (batch), carry a recall risk (retrieval), or are lossy (compaction) and so must
be opt-in behind a measured gate. Keep all provider-specific caching/batch logic inside the
**provider adapter** so the orchestrator and context-builder stay LLM-agnostic — this is the
load-bearing architectural requirement for ADR-0008.

---

## Sources (URL + retrieval date 2026-06-24)

**Primary / official — verified live this session:**

- Anthropic — Prompt caching docs (multipliers 1.25×/2×/0.1×, min-prefix per model, 4
  breakpoints, 20-block lookback, `usage` fields): https://platform.claude.com/docs/en/build-with-claude/prompt-caching — verified 2026-06-24.
- Azure OpenAI (Microsoft Learn) — Prompt caching (1024-token min, 128-token increments,
  ~256-token routing hash, automatic/no opt-out, in-memory 5–10 min/≤1 h, extended 24 h,
  `cached_tokens`): https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/prompt-caching — verified 2026-06-24.
- Google — Gemini implicit caching (default-on for 2.5+, ~90% discount on 2.5+, 75% on 2.0,
  no storage cost for implicit, min 1024 Flash / 2048 Pro): Google Developers Blog + Google
  Cloud context-cache overview — confirmed via official-domain search 2026-06-24.
- Anthropic — Message Batches (50% on all tokens, stacks with caching, <1 h typical / 24 h
  max, 29-day result retention): https://docs.anthropic.com/en/docs/build-with-claude/message-batches — confirmed via official docs search 2026-06-24.

**Primary — referenced but page body proxy-blocked (corroborated by ≥1 secondary):**

- OpenAI — Prompt caching announcement (50% original 4o-family discount; automatic):
  https://openai.com/index/api-prompt-caching/ — 403 via proxy; mechanics corroborated by the
  Azure OpenAI doc above (same engine).
- OpenAI — API pricing (current per-model cached-input ratio, e.g. GPT-5.2 ~90%):
  https://openai.com/api/pricing/ — 403 via proxy; **read live at integration time**.
- Gemini API caching docs: https://ai.google.dev/gemini-api/docs/caching — 403 via proxy;
  corroborated by Google Cloud context-cache overview + Developers Blog.
- Anthropic — Effective context engineering for AI agents (JIT retrieval, compaction,
  token-efficient tools; programmatic-tool-calling 43,588→27,297 ≈ 37%):
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — 403 via
  proxy; figures from official-domain search snippet.

**Skill-resident reference (Anthropic, bundled with this environment, treated as authoritative
for Claude API surface):** `claude-api` skill — `shared/prompt-caching.md`,
`shared/agent-design.md`, `shared/tool-use-concepts.md`, `python/claude-api/batches.md`.

---

## Open / unverified

- **OpenAI first-party cached-input discount is model-dependent and changes per release.**
  Verified that 4o-era was 50% and GPT-5.2 is ~90%, but the *exact current default for the
  model ALUCA targets* must be read live from `openai.com/api/pricing/` at integration time —
  that page was proxy-blocked here. Do not hard-code a single OpenAI cache % in ADR-0008.
- **OpenAI Batch API 50%** is widely documented but was **not** re-verified against an official
  OpenAI page this session (only Anthropic's 50% was verified live).
- **Gemini explicit-cache storage pricing** (per-token-hour) was confirmed to *exist* but the
  exact rate was not pulled from a live primary page (proxy block) — verify before relying on
  explicit (vs implicit) caching for cost modelling.
- **Anthropic context-engineering token figures (37% via programmatic tool calling)** come from
  a search snippet of the official engineering blog, not the rendered page (proxy-blocked).
  Treat the 37% as directional, not a contractual number.
- **Cross-provider min-prefix and TTL numbers** were each verified against one primary source;
  values drift with model releases — re-confirm the specific model IDs ALUCA pins before
  freezing them into the caching layer's per-model floor table.
- **Latency claims** (e.g. caching "up to 80% latency reduction") were seen in secondary
  sources only and are deliberately excluded from the body — this theme scopes *token* cost,
  not latency.
