---
title: "T3 — Token/Cost Tracking & Observability (Local-First Telemetry for the Studio)"
theme: "T3 — Token/Cost Tracking & Observability"
charter: "ALUCA I-6.6"
date: 2026-06-24
status: research-draft
feeds: "ADR-0008; T4 (ROI)"
---

# T3 — Token/Cost Tracking & Observability

> Grounded web research for the I-6.6 charter. Governing principle: **LLM-agnostic,
> customer-agnostic, local-first**. The studio runs standalone (BYO-key, no mandatory
> cloud). Telemetry MUST NOT require a cloud SaaS; it must persist into the existing
> local SQLite store (`studio/data/studio.db`). Per-customer / per-domain attribution
> MUST work without customer-specific code.

## Executive summary

1. **Track per step, attribute provider-agnostically.** Every LLM call already runs
   through one chokepoint — the Vercel AI SDK `generateText`/`streamText` in
   `studio/src/lib/ai/orchestrator.ts`. That SDK normalizes token usage into one shape
   (`result.usage` → `inputTokens` / `outputTokens` / `totalTokens` plus
   `inputTokenDetails.{cacheReadTokens, cacheWriteTokens}` and
   `outputTokenDetails.reasoningTokens`) **across Anthropic, Google and OpenAI**. So the
   provider-agnostic capture point is "read `result.usage` at the call site and write
   one row." Attribution to use-case / domain / customer is just **context columns**
   (`use_case_id`, `domain`, `project_id`) passed in at the call site — no per-customer
   code.
2. **Standard to align field NAMES to, without adopting the runtime.** The OpenTelemetry
   **GenAI semantic conventions** (`gen_ai.*`) are the de-facto vocabulary: `gen_ai.provider.name`,
   `gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.response.model`,
   `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`,
   `gen_ai.usage.cache_read.input_tokens`, etc. We **borrow the names** so the local
   schema is OTel-portable later, but we do **not** require an OTel Collector or any
   exporter. Crucial finding: **OTel GenAI defines NO cost metric** — cost is explicitly
   out of scope and left to the consumer. So cost is *our* responsibility (derive from a
   local price table), which is exactly the T4 hand-off.
3. **Local-first tools exist but are not "embeddable."** Langfuse (MIT, self-host via
   Docker, Postgres + ClickHouse + Redis) and Arize Phoenix (ELv2, self-host, can use
   SQLite for trial) are both genuinely self-hostable and OTel-compatible. **But** both
   are *separate services* (extra containers / a server on ports 6006/4317). For a
   standalone BYO-key studio whose only persistence is one SQLite file, standing up
   ClickHouse or a Phoenix server violates "no mandatory infra." **Recommendation: own
   a tiny `llm_step_events` SQLite table now; keep an optional OTel export seam for
   teams that already run Langfuse/Phoenix.**
4. **A single `llm_step_events` table** (field list below) is enough to serve a health
   metric today (tokens/latency/error per step) AND ROI later (cost per use-case/domain/
   customer for T4). It mirrors the existing `audit_events` table style (same `id` /
   `project_id` / `created_at` conventions, WAL mode, `better-sqlite3`).

---

## 1. Per-step tracking and attribution, provider-agnostically (RQ1)

**The capture point.** The studio routes *all* model calls through the Vercel AI SDK
(`import { generateText } from 'ai'`, model built by
`createServerModel()` in `studio/src/lib/ai/orchestrator.ts`, providers
`@ai-sdk/anthropic | @ai-sdk/google | @ai-sdk/openai`). The SDK returns a normalized
usage object regardless of provider, so a single helper at the call site can record one
row per call — this is the provider-agnostic seam.

Normalized AI SDK usage shape (`LanguageModelUsage`):

| AI SDK field | Meaning |
|---|---|
| `usage.inputTokens` | prompt tokens (provider-normalized) |
| `usage.outputTokens` | completion tokens |
| `usage.totalTokens` | total |
| `usage.inputTokenDetails.cacheReadTokens` | tokens served from provider cache |
| `usage.inputTokenDetails.cacheWriteTokens` | tokens written to provider cache |
| `usage.inputTokenDetails.noCacheTokens` | non-cached input |
| `usage.outputTokenDetails.reasoningTokens` | reasoning/CoT output tokens |
| `usage.raw` | provider-specific raw usage (escape hatch) |

For multi-step (tool-calling) generations the SDK also exposes `result.totalUsage`
(cumulative across steps) in addition to `result.usage` (last step). For *per-step*
attribution, record per step — either one row per `generateText` call (current studio
usage), or one row per step using the SDK step callbacks for agentic flows.

**Attribution without customer-specific code.** Attribution is data, not code: the call
site passes a small context object (`use_case_id`, `domain`, `customer_id`/`project_id`,
`step`/`role`, `gate_result`) that gets written as columns. The studio already has
`project_id` as its tenant key everywhere (`audit_events`, `bracket_*`, default
`'default'`). So per-customer = `project_id`; per-use-case = `use_case_id` (the bracket
ID, regex `^[A-Z]{2,3}-\d{3}$`); per-domain = a free-text `domain` tag. None of this
needs branching per customer — same code path, different column values. This mirrors how
the existing audit repo takes `projectId` + `actor` as parameters
(`studio/src/lib/db/audit-repo.ts`).

---

## 2. Standards & local-first tooling (RQ2)

### 2a. OpenTelemetry GenAI semantic conventions (`gen_ai.*`)

These are the standard field NAMES to align to. Note: as of 2026 the GenAI conventions
moved out of the main `semantic-conventions` repo into a dedicated
`open-telemetry/semantic-conventions-genai` repo (the old paths now redirect).

Span attributes relevant to us (requirement level in parentheses):

| OTel attribute | Level | Notes |
|---|---|---|
| `gen_ai.operation.name` | Required | values incl. `chat`, `generate_content`, `text_completion`, `embeddings`, `execute_tool`, `invoke_agent` |
| `gen_ai.provider.name` | Required | values incl. `openai`, `anthropic`, `gcp.gemini`, `gcp.vertex_ai`, `azure.ai.openai`, `aws.bedrock`, `mistral_ai`, `cohere`, … |
| `gen_ai.request.model` | Conditionally Required | requested model id |
| `gen_ai.response.model` | Recommended | model that actually answered |
| `gen_ai.usage.input_tokens` | Recommended (int) | prompt tokens; *should include cached tokens* |
| `gen_ai.usage.output_tokens` | Recommended (int) | billed output count |
| `gen_ai.usage.cache_creation.input_tokens` | Recommended (int) | tokens written to provider cache |
| `gen_ai.usage.cache_read.input_tokens` | Recommended (int) | tokens read from provider cache |
| `gen_ai.usage.reasoning.output_tokens` | Recommended when applicable | reasoning/CoT tokens |
| `gen_ai.conversation.id` | Conditionally Required when available | session/thread id |
| `gen_ai.response.id` | Recommended | completion id |
| `gen_ai.response.finish_reasons` | Recommended (string[]) | |
| `gen_ai.request.temperature` / `top_p` / `max_tokens` | Recommended | request params |
| `gen_ai.request.stream` | Conditionally Required (bool) | streaming mode |
| `gen_ai.response.time_to_first_chunk` | Recommended if streaming (s) | |
| `error.type` | Conditionally Required if failed | error class |
| `gen_ai.input.messages` / `gen_ai.output.messages` / `gen_ai.system_instructions` | **Opt-In** | full prompt/response content — PII-bearing, off by default |

Metrics defined: `gen_ai.client.token.usage` (Histogram, `{token}`),
`gen_ai.client.operation.duration` (Histogram, `s`),
`gen_ai.client.operation.time_to_first_chunk`, plus server/workflow/agent durations.
Common dimensions: `gen_ai.operation.name`, `gen_ai.provider.name`,
`gen_ai.request.model`, `error.type`.

> **Adversarial check — cost:** The GenAI metrics spec defines **no cost metric** and
> contains no billing/monetary measurement; cost is outside the spec scope. Verified
> 2026-06-24. Implication: if we want cost (we do, for T4) we MUST compute it ourselves
> from token counts × a price table. OTel won't give it to us.

### 2b. Self-hostable observability tools (and why we don't *require* one)

| Tool | License | Self-host | Local store | Verdict for studio |
|---|---|---|---|---|
| **Langfuse** | MIT | Docker Compose, "5 min" | Postgres **+ ClickHouse + Redis** (v3+) | Powerful, OTel-native (SDK v4 exports via OTel SpanExporter). But multi-container OLAP stack = heavy for a standalone BYO-key studio. Good as **optional** export target. |
| **Arize Phoenix** | Elastic License 2.0 (not OSI) | `phoenix serve` / Docker, ports 6006/4317 | **SQLite for trial** (loses data without a volume; limited concurrent writes), Postgres for prod | OTel + OpenInference transport. Closest to "local," but still a separate server process, and ELv2 forbids offering it as a hosted service to third parties. Optional. |
| **OpenLLMetry (Traceloop)** | Apache-2.0 (SDK) | instrumentation lib | sends to any OTel backend | A *library* that emits OTel spans; needs a backend to land in. Useful pattern, not a store. |

**Conclusion:** none of these is "embed in a single SQLite file." For local-first the
right move is to **own the table** and treat OTel-export to Langfuse/Phoenix as an
optional seam (Section 5). This keeps the standalone install at zero extra services.

> **AI SDK telemetry caveat (grounded, important for ADR-0008):** The AI SDK's
> `experimental_telemetry` *can* emit OTel `gen_ai.*` spans automatically, BUT
> vercel/ai issue #12801 documents that `generateText`/`generateObject` currently emit
> only the **deprecated** `ai.usage.promptTokens` / `ai.usage.completionTokens` span
> attributes and never the standardized `ai.usage.inputTokens|outputTokens|
> cachedInputTokens|reasoningTokens`. Therefore: **do not rely on auto-emitted spans for
> token accuracy.** Read `result.usage` directly at the call site and write our own row.
> The auto-span path can stay as an optional extra, not the source of truth.

---

## 3. Minimal local-first schema (RQ3) + persistence

One row per LLM step. Field list below; column names use OTel-portable semantics so a
later OTel exporter is a mechanical mapping. Persist with `better-sqlite3` in the
existing `studio/data/studio.db`, WAL mode, same conventions as `audit_events`
(`studio/src/lib/db/sqlite.ts`).

### Field list (per step)

| Column | Type | L0 / optional | OTel mapping | Purpose |
|---|---|---|---|---|
| `id` | TEXT PK | **L0** | (span id) | `evt-<base36>-<rand>`, same style as audit `aud-…` |
| `created_at` | TEXT (`datetime('now')`) | **L0** | span start | time bucketing for health |
| `project_id` | TEXT (default `'default'`) | **L0** | resource / `gen_ai.conversation.id` scope | **customer/tenant attribution** |
| `use_case_id` | TEXT (nullable) | **L0** | custom (`aluca.use_case.id`) | bracket id (`^[A-Z]{2,3}-\d{3}$`); ROI grain for T4 |
| `domain` | TEXT (nullable) | optional | custom (`aluca.domain`) | per-domain attribution |
| `step` | TEXT | **L0** | custom (`aluca.step`) | e.g. `wizard.kpi`, `factsheet-draft`, `chat`, `gate.golden-thread` |
| `role` | TEXT (nullable) | optional | custom | logical role of the call (drafter/reviewer/router) |
| `provider` | TEXT | **L0** | `gen_ai.provider.name` | `anthropic` / `gcp.gemini` / `openai` |
| `operation` | TEXT | optional | `gen_ai.operation.name` | `chat` / `generate_content` / `text_completion` |
| `request_model` | TEXT | **L0** | `gen_ai.request.model` | requested model id |
| `response_model` | TEXT (nullable) | optional | `gen_ai.response.model` | actual responder |
| `input_tokens` | INTEGER | **L0** | `gen_ai.usage.input_tokens` | from `usage.inputTokens` |
| `output_tokens` | INTEGER | **L0** | `gen_ai.usage.output_tokens` | from `usage.outputTokens` |
| `total_tokens` | INTEGER | optional (derivable) | — | `usage.totalTokens` |
| `cache_read_tokens` | INTEGER (default 0) | optional | `gen_ai.usage.cache_read.input_tokens` | `inputTokenDetails.cacheReadTokens` → **cache-hit** signal |
| `cache_write_tokens` | INTEGER (default 0) | optional | `gen_ai.usage.cache_creation.input_tokens` | `inputTokenDetails.cacheWriteTokens` |
| `reasoning_tokens` | INTEGER (default 0) | optional | `gen_ai.usage.reasoning.output_tokens` | `outputTokenDetails.reasoningTokens` |
| `cost_usd` | REAL (nullable) | optional | (none — OTel has no cost) | **derived** input×rate + output×rate − cache discounts; **the T4 cost side** |
| `price_table_version` | TEXT (nullable) | optional | custom | which price snapshot produced `cost_usd` (auditability) |
| `latency_ms` | INTEGER | **L0** | `gen_ai.client.operation.duration` (×1000) | wall-clock around the call |
| `gate_result` | TEXT (nullable) | optional | custom (`aluca.gate.result`) | `pass`/`fail`/`n_a` — ties a call to a Golden-Thread/E2E gate outcome |
| `cache_hit` | INTEGER (0/1) | optional (derivable) | — | convenience flag = `cache_read_tokens > 0` |
| `status` | TEXT (default `ok`) | **L0** | derived from `error.type` | `ok` / `error` |
| `error_type` | TEXT (nullable) | optional | `error.type` | error class when `status='error'` |
| `actor` | TEXT (default `system`) | optional | custom | who triggered (mirrors audit `actor`) |
| `raw_usage_json` | TEXT (nullable) | optional | — | `usage.raw` escape hatch for provider quirks/audit |

**L0 vs optional rationale.** L0 = the columns required to compute the *health metric
now* (tokens, latency, error, and the three attribution keys) and to be non-null on
every successful row. Everything else is optional because (a) it may be provider- or
mode-specific (cache/reasoning tokens, finish reasons), (b) it's PII-sensitive (we
deliberately exclude prompt/response content — OTel marks those Opt-In), or (c) it's
derivable (`total_tokens`, `cache_hit`).

> **Deliberately omitted (privacy / local-first):** full prompt/response text
> (`gen_ai.input.messages` / `gen_ai.output.messages`). OTel marks these Opt-In and
> PII-bearing. For a BYO-key, customer-agnostic studio the default is **token
> *counts*, never token *contents*.** A future opt-in flag could log content to a
> separate table if a customer explicitly enables it.

### Persistence (DDL — mirrors existing `studio/src/lib/db/sqlite.ts`)

```sql
CREATE TABLE IF NOT EXISTS llm_step_events (
  id                  TEXT PRIMARY KEY,
  project_id          TEXT NOT NULL DEFAULT 'default',
  use_case_id         TEXT,
  domain              TEXT,
  step                TEXT NOT NULL,
  role                TEXT,
  provider            TEXT NOT NULL,
  operation           TEXT,
  request_model       TEXT NOT NULL,
  response_model      TEXT,
  input_tokens        INTEGER NOT NULL DEFAULT 0,
  output_tokens       INTEGER NOT NULL DEFAULT 0,
  total_tokens        INTEGER NOT NULL DEFAULT 0,
  cache_read_tokens   INTEGER NOT NULL DEFAULT 0,
  cache_write_tokens  INTEGER NOT NULL DEFAULT 0,
  reasoning_tokens    INTEGER NOT NULL DEFAULT 0,
  cost_usd            REAL,
  price_table_version TEXT,
  latency_ms          INTEGER NOT NULL DEFAULT 0,
  gate_result         TEXT,
  cache_hit           INTEGER NOT NULL DEFAULT 0,
  status              TEXT NOT NULL DEFAULT 'ok',
  error_type          TEXT,
  actor               TEXT NOT NULL DEFAULT 'system',
  raw_usage_json      TEXT,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_llm_step_project_time ON llm_step_events(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_step_usecase ON llm_step_events(use_case_id);
```

This adds **one table** to the existing init block; no new dependency (better-sqlite3 is
already in use), no new service. A thin `llm-telemetry-repo.ts` (sibling of
`audit-repo.ts`) exposes `recordStepEvent(ctx, usage, timing)` called from the AI route
handlers (`studio/src/app/api/ai/{wizard,chat,factsheet-draft}/route.ts`).

---

## 4. Reliable token counts & cost across providers (RQ4)

All three providers return usage **in the response body** (no separate count call
needed for actuals). The AI SDK normalizes them; the table maps the raw fields:

| Provider | Raw usage fields (in response) | → AI SDK / our column |
|---|---|---|
| **Anthropic** (Messages API) | `usage.input_tokens`, `usage.output_tokens`, `usage.cache_creation_input_tokens`, `usage.cache_read_input_tokens` (cache_creation can break out `ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`) | `inputTokens` / `outputTokens` / `cacheWriteTokens` / `cacheReadTokens` |
| **Google Gemini** (`generateContent`) | `usageMetadata.promptTokenCount`, `usageMetadata.candidatesTokenCount`, `usageMetadata.totalTokenCount`, plus `*TokensDetails` modality breakdowns (cached-content reflected inside `promptTokenCount`) | `inputTokens` / `outputTokens` / `totalTokens` |
| **OpenAI** (Chat Completions / Responses) | `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`, `usage.prompt_tokens_details.cached_tokens`, `usage.completion_tokens_details.reasoning_tokens` | `inputTokens` / `outputTokens` / `cacheReadTokens` / `reasoningTokens` |

**Reliability caveats (honest):**
- **Streaming:** providers emit usage only at the end of the stream; some OpenAI
  streaming paths require opting in to a final usage chunk, and there are documented
  cases of zeroed usage. For `streamText` paths, read usage from the resolved
  `result.usage` promise after the stream completes, and write the row then (or mark
  `status='error'`/usage unknown if absent). The studio's current calls use
  `generateText` (non-streaming), where usage is reliably present.
- **AI SDK accuracy:** vercel/ai issue #8349 reports cases of inaccurate Anthropic usage
  mapping in some SDK versions; keep `raw_usage_json` so we can reconcile against the
  provider's own numbers and pin a tested SDK version.
- **Counts ≠ cost.** Providers return *counts*, not *money*. There is no cross-provider
  cost field and (per Section 2a) OTel defines none. **Cost = counts × local price
  table**, with cache-read/write and reasoning priced at their own multipliers (e.g.
  Anthropic cache write ≈ 1.25× base input, cache read ≈ 0.1×). Cost therefore must be
  computed in our code, versioned (`price_table_version`), and is intrinsically the
  thing T4 consumes.

---

## 5. How this feeds T4 (ROI — the cost side)

T4 turns "what did it cost" into "was it worth it." This schema is the **cost
ledger** T4 reads:

- **Cost grain = the attribution columns.** `SUM(cost_usd) GROUP BY use_case_id` →
  cost per use case; `GROUP BY project_id` → cost per customer; `GROUP BY domain` →
  cost per domain. T4 joins those sums against the value/benefit side it owns.
- **Health now, ROI later from the same rows.** Health = tokens/latency/error rate/
  cache-hit rate per step over `created_at` windows (no cost needed → works even before
  a price table exists). ROI = the same rows once `cost_usd` is populated. One write
  path, two readers.
- **`cost_usd` is the single hand-off field**, `price_table_version` makes historical
  cost reproducible (re-pricing won't silently rewrite history), and `gate_result`
  lets T4 separate "cost of work that passed the gate" from "cost of rework" — a real
  ROI denominator.
- **Optional OTel export seam** (for teams already running Langfuse/Phoenix): the same
  rows map mechanically to `gen_ai.*` spans + the `gen_ai.client.token.usage` metric;
  cost ships as a custom attribute since OTel has no cost metric. Off by default to
  preserve local-first.

---

## Sources (URL + retrieval date 2026-06-24)

OpenTelemetry GenAI semantic conventions (names borrowed; cost confirmed out-of-scope):
- OTel GenAI spans (current, in `semantic-conventions-genai` repo): https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-spans.md — 2026-06-24
- OTel GenAI metrics (no cost metric defined): https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-metrics.md — 2026-06-24
- OTel GenAI relocation notice (old paths redirect): https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/ — 2026-06-24 (returned move notice / 403 on rendered site)
- OTel GenAI attribute registry: https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ — 2026-06-24 (via search index)

Provider usage metadata (token counts in responses):
- Anthropic prompt caching / usage fields: https://platform.claude.com/docs/en/build-with-claude/prompt-caching — 2026-06-24
- Anthropic Messages API usage: https://platform.claude.com/docs/en/build-with-claude/working-with-messages — 2026-06-24
- Google Gemini generateContent / usageMetadata (AI for Developers): https://ai.google.dev/api/generate-content — 2026-06-24
- Google Gemini token counting / cached content: https://ai.google.dev/gemini-api/docs/generate-content/tokens — 2026-06-24
- Vertex AI GenerateContentResponse.UsageMetadata: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse — 2026-06-24
- OpenAI Completions / usage object (prompt_tokens_details.cached_tokens, completion_tokens_details.reasoning_tokens): https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create — 2026-06-24

Vercel AI SDK (the actual studio capture point):
- AI SDK Core generateText reference (usage / totalUsage): https://ai-sdk.dev/docs/reference/ai-sdk-core/generate-text — 2026-06-24
- AI SDK Core telemetry (experimental_telemetry, recordInputs/recordOutputs): https://ai-sdk.dev/docs/ai-sdk-core/telemetry — 2026-06-24
- vercel/ai #12801 (generateText/generateObject emit only deprecated token attrs): https://github.com/vercel/ai/issues/12801 — 2026-06-24
- vercel/ai #8349 (inaccurate Anthropic usage counts): https://github.com/vercel/ai/issues/8349 — 2026-06-24

Local-first observability tools:
- Langfuse self-hosting (MIT; Docker; Postgres+ClickHouse+Redis; OTel SpanExporter): https://langfuse.com/self-hosting — 2026-06-24
- Langfuse repo: https://github.com/langfuse/langfuse — 2026-06-24
- Arize Phoenix (self-host; SQLite trial / Postgres prod; OTel+OpenInference; ELv2): https://github.com/Arize-ai/phoenix — 2026-06-24
- Arize Phoenix product page: https://phoenix.arize.com/ — 2026-06-24
- OpenInference (OTel instrumentation for AI): https://github.com/Arize-ai/openinference — 2026-06-24

Repo grounding (existing studio, not web):
- `studio/src/lib/ai/orchestrator.ts` — single provider router (Google→Anthropic→OpenAI), AI SDK models.
- `studio/src/lib/db/sqlite.ts` — better-sqlite3, WAL, `audit_events` schema this table mirrors.
- `studio/src/lib/db/audit-repo.ts` — `projectId`/`actor` parameterized write pattern reused for telemetry.
- `studio/src/app/api/ai/{wizard,chat,factsheet-draft}/route.ts` — the call sites where `recordStepEvent` hooks in.
- `docs/architecture/studio-capability-inventory.md` — I-6.6 health item; "heute kein Budget-Tracking im Studio sichtbar."

## Open / unverified

- **OTel GenAI is evolving and recently relocated.** Field names verified against the
  `main` branch of `semantic-conventions-genai` on 2026-06-24, but these conventions
  are still maturing; pin the field-name mapping to a spec version in ADR-0008 and
  re-check before GA. Some attributes (e.g. `gen_ai.conversation.compacted`,
  reasoning-level) are newer and may churn.
- **Exact `usage.raw` shape per provider in the current pinned AI SDK version** was not
  byte-verified here (read from docs/issues, not from a live SDK run). Confirm against
  the installed `ai` / `@ai-sdk/*` versions in `studio/package.json` before relying on
  `cacheWriteTokens`/`reasoningTokens` field names.
- **Gemini cache token reporting:** `cachedContentTokenCount` did not appear as a
  top-level field in the rendered AI-for-Developers reference; caching is reflected
  *inside* `promptTokenCount`. If explicit cache attribution is needed for Gemini,
  verify whether a separate field is exposed (Vertex vs AI Studio surfaces may differ).
- **Streaming usage availability** varies by provider/SDK path and can be zero/absent;
  the row-write timing for `streamText` paths must be validated live (current studio
  uses non-streaming `generateText`, so this is a future concern).
- **Price tables are not standardized** anywhere; the local price table is a
  hand-maintained artifact that must be versioned and refreshed — a known operational
  cost, flagged for T4/ADR-0008.
- **OTel auto-span token bug (#12801)** was read from the issue tracker, not reproduced;
  treat "read `result.usage` directly" as the safe default regardless of its current
  status.
