---
title: "T5 — Layered Config Architecture (L0/L1/L2) for the AI Orchestration Layer"
theme: T5
charter: ALUCA I-6.6
date: 2026-06-24
status: research-draft
feeds: ADR-0008
owner: architecture
---

# T5 — Layered Config Architecture

> Grounded research + design synthesis. This is the **backbone** the other I-6.6 themes slot
> into: T5 fixes *where* every tunable lives, *who* owns it, *how* it resolves, and *how* a
> change is governed. Other themes (routing rules, token policy, eval thresholds, ROI/telemetry,
> provider policy) populate the field groups defined here; they do not re-invent the layering.

## Executive summary

The studio's model layer (`studio/src/lib/ai/orchestrator.ts`) today **hardcodes** model IDs in a
`DEFAULT_MODELS` map and a fixed provider priority (Google → Anthropic → OpenAI). That couples
*generally-optimal* engineering decisions (which capability-role to use, sane token defaults, eval
gates) to *customer-individual* decisions (budget caps, banned providers for compliance/region,
domain quality bars). T5 proposes to replace that with a **three-layer cascading config**, resolved
by a **pure, deterministic** merge function and validated against a **versioned JSON Schema** that
lives under the studio's declared schema SSOT `tooling/ai/schemas/` (see studio/CLAUDE.md).

Governing principle — **separate the universal from the individual, keep the core
LLM-agnostic and customer-agnostic**:

| Layer | Name | Owner | Holds (examples) | Mutable by customer? |
|---|---|---|---|---|
| **L0** | universal-optimal | **ALUCA** (shipped, versioned) | best default routing rule per task-role, token defaults, eval thresholds, telemetry defaults | No — only via ALUCA release |
| **L1** | customer | **Customer** (tenant admin) | budget caps, provider preference / ban (compliance/region), tenant risk appetite | Yes — under approval workflow |
| **L2** | domain | **Customer, per domain** | domain-specific business logic, stricter quality requirement, domain ROI weighting | Yes — under approval workflow |

**Precedence: L2 > L1 > L0** (most specific wins). Resolution is a deep merge with documented
per-field merge semantics (override vs. clamp vs. set-intersection). The resolved, *effective*
config is what `orchestrator.ts` reads — it never sees raw layers, never sees a model ID literal.
L1/L2 edits flow through the **existing Freigabe/approval workflow**
(`studio/src/lib/governance/approval-workflow.ts`), reusing its draft → review → approved lifecycle,
two-person rule (no self-approval), and append-only audit log.

Confidence: **high** on layering/merge/validation/versioning patterns (well-established, multiple
independent sources). **Medium** on the exact field taxonomy and clamp semantics — those are design
proposals to be ratified in ADR-0008 and refined as T-themes for routing/token/eval land.

---

## 1. Proven patterns for layered / overridable config

### 1.1 The layered model is standard practice

Layered (a.k.a. cascading) configuration — independent layers combined into one effective config —
is the mainstream answer for "shared defaults + environment/tenant-specific overrides." The
canonical shape is **base defaults → scoped overrides → most-specific overrides**, where a key
present in a higher-precedence layer wins ("last one wins" / "most specific wins"). This is exactly
the ASP.NET Core configuration stack (appsettings → env-specific → user secrets → env vars), the
12-factor ordering (`defaults < repo config < local overrides < process env`), and the
defaults→environment→user file pattern documented for JS apps. [S1][S3][S8]

Mapping to T5: **L0 = base defaults (ALUCA), L1 = tenant overrides, L2 = domain overrides.** Our
twist vs. the generic stack is *ownership and governance per layer*, not just file precedence: L0 is
read-only to the customer, L1/L2 are customer-writable but gated.

### 1.2 Deep merge vs. shallow merge — pick per field, document it

The dominant nested-object strategy is **deep merge** so that an override of one nested key does not
discard sibling keys ("simple replacement can lose non-conflicting settings"). Renovate, for
example, deep-merges objects but treats specific fields as **additive** (concatenate + de-dupe via a
Set) rather than replace. [S1][S9]

T5 adopts **deep merge with explicit per-field merge semantics**. Three merge kinds cover our needs:

- **`override`** (scalar replace): higher layer's value wins outright. Used for booleans, enums,
  free scalars where "most specific wins" is correct (e.g. `roi.attributionMethod`).
- **`clamp` / `tighten`**: the effective value is the **more restrictive** of the layers, regardless
  of which layer set it. A customer or domain can only make a guardrail *stricter*, never looser
  than the L0 safety floor. Used for budgets, token ceilings, eval thresholds, risk. This is the
  "compliance always takes precedence / stricter wins" pattern from regulated-app flag resolution. [S10]
- **`intersect` (allow-list narrowing)**: provider allow-lists narrow as you go down — effective
  allowed providers = `L0.allowed ∩ (L1 not-banned) ∩ (L2 not-banned)`. A lower layer can *remove*
  a provider (ban it) but never *add* one the layer above forbade. This guarantees a compliance ban
  at L1 cannot be undone by an L2 domain config.

> Design rule: **the customer can only ever be more conservative than L0, never less.** `override`
> is reserved for fields with no safety dimension; everything with a cost/quality/compliance edge is
> `clamp` or `intersect`. This keeps L0 a genuine *floor*, not merely a *default that anyone can blow
> past*.

### 1.3 Precedence must be explicit and documented

Every source stresses the same operational lesson: **make precedence explicit, document it, and
optionally warn on unexpected overrides** — otherwise you lose hours debugging "why is this value
not what I set." [S1][S10] T5 encodes precedence and merge-kind **in the schema itself** (a
`x-merge` annotation per field, see §4) so the precedence is data, not tribal knowledge, and the
resolver reads it rather than hardcoding behavior.

### 1.4 Feature-flag layering is the closest analogue to provider policy

Modern flag platforms (PostHog "Layers", LaunchDarkly/Unleash group+user overrides) layer
*property targeting → rollout → variant* and resolve **deterministically** by hashing
`(flag key, distinct id)` so the same inputs always yield the same decision with no stored state.
[S6][S7] For regulated apps the resolution is lexicographic: **compliance status first, then
priority/rollout.** [S10] T5 borrows this: provider/region compliance (`providerPolicy`) is resolved
*before* preference ordering, and the whole resolution is a pure function of (layers, request
context) — no hidden state, no time-dependence (see §2).

---

## 2. Keeping resolution pure, deterministic, and testable

Pure functions — output depends only on inputs, no side effects — are deterministic and therefore
"simpler to unit test," needing no mocks. [S11][S12][S13] The testability recipe for config
specifically: **no package-level globals, deterministic fixtures, merge rules covered by unit
tests**, plus **golden files** to lock the resolved output. [S12][S14]

T5 resolution contract (proposed `studio/src/lib/ai/config/resolve.ts`):

```ts
// PURE. No fs, no env, no Date.now, no network. Inputs fully determine output.
export function resolveAiConfig(
  layers: { l0: AiConfigL0; l1?: AiConfigL1; l2?: AiConfigL2 },
  ctx: { taskRole: CapabilityRole; domainId?: string },
): EffectiveAiConfig { /* deep-merge per x-merge semantics, then validate */ }
```

Determinism rules:

- **Loading is separate from resolving.** A thin impure loader (uses `node:fs` / DB, mirrors the
  existing `src/lib/core/*-loader.ts` pattern) reads the three layers; `resolveAiConfig` is pure and
  receives them as arguments. Same split the codebase already uses for loaders vs. logic.
- **No clocks, no RNG, no env reads inside the resolver.** If a rollout percentage is ever needed,
  hash `(field key, tenantId|domainId)` — deterministic, like the flag platforms. [S6]
- **Resolution order is fixed and total:** start from L0 (which is *complete* — every field has a
  value), fold in L1, then L2, applying each field's `x-merge` kind. Because L0 is complete, the
  effective config is **never partial** → `orchestrator.ts` never hits an undefined tunable.
- **Validate after merge**, not only per-layer (a legal L1 + legal L2 could still produce an
  out-of-range effective value if merge logic regresses — the post-merge validation is the
  backstop).

Test strategy:

- **Unit tests per merge kind** (`override`/`clamp`/`intersect`) with hand-written fixtures.
- **Golden fixtures**: `(l0, l1, l2, ctx) → effective.json` checked in; the resolver output is
  diffed against the golden file. Locks intended precedence and catches accidental semantic drift. [S14]
- **Property tests**: e.g. "effective budget ≤ L0 budget for any L1/L2" (clamp invariant); "effective
  allowed-providers ⊆ L0 allowed" (intersect invariant). These encode the §1.2 safety rule as
  executable invariants.

---

## 3. Governance: who may change L1/L2, and how it ties to approval

### 3.1 Reuse the existing Freigabe workflow — do not build a parallel one

`studio/src/lib/governance/approval-workflow.ts` already implements exactly the lifecycle we need:

- States `draft → review → approved/rejected → deprecated` (+ `reopen`), with `VALID_TRANSITIONS`
  enforced (`approval-types.ts`).
- **Two-person rule**: `transition()` throws on self-approval (`current.submitted_by === actor`).
- **Append-only audit**: every transition calls `logAuditEvent('governance', id, action, {before, after, justification}, ...)`.

T5 generalizes the keyed entity from `bracketId` to a config-change record. Concretely: introduce an
`aiConfigChangeId` lifecycle row reusing the same `transition()` machinery (or a sibling table with
identical state machine). A proposed L1/L2 edit becomes a **draft change-set** (a diff against the
currently-approved layer), is `submit`ted for review, and only the **approved** version is what the
loader serves to `resolveAiConfig`. Pending drafts never reach the orchestrator.

### 3.2 Who may change what

| Layer | Propose (draft/submit) | Approve | Notes |
|---|---|---|---|
| **L0** | ALUCA engineering only | ALUCA release process | Ships with the product, versioned (§4.3). Customers cannot edit; they can only *tighten* it via L1/L2. |
| **L1** (tenant) | Tenant admin role | A *different* tenant approver (two-person rule) | Budget caps, provider ban/preference, risk appetite. RBAC via `src/lib/auth/require-role.ts` / `rbac-types.ts`. |
| **L2** (domain) | Domain owner / steward | Tenant or domain approver ≠ proposer | Mirrors the action-code `owner_role` / `steward_role` separation already in the schemas. |

This maps cleanly onto the action-code governance convention already in the repo (distinct
`owner_role` and `steward_role`, "must differ"), so the segregation-of-duties model is consistent
platform-wide.

### 3.3 What gets recorded

Every L1/L2 change records, via the existing audit chain (`src/lib/db/audit-repo.ts`,
`audit-chain.ts`): actor, justification, before/after **diff of the layer**, the **schema version**
the change was authored against, and the resulting **effective-config hash** for the affected
task-roles. The hash lets you prove later exactly which effective config a given orchestration run
used (ties to telemetry — T-theme for telemetry/ROI).

---

## 4. Concrete L0/L1/L2 schema proposal

Target file (declared SSOT per studio/CLAUDE.md): `tooling/ai/schemas/ai_config.schema.json`,
draft-07, `additionalProperties: false`, `schema_version` `const` — **matching the house style** of
the existing schemas (e.g. `action_code.schema.json`). TS types regenerate via
`npm run generate:types` into `src/lib/schemas/`.

### 4.1 Field groups (shared shape across layers)

All three layers share the **same five field groups**; what differs is which fields each layer is
*allowed* to set and the per-field merge kind. (`x-merge` is a custom annotation the resolver reads;
JSON-Schema validators ignore unknown keywords, so it is safe.)

| Group | Field (illustrative) | x-merge | L0 | L1 | L2 | Meaning |
|---|---|---|---|---|---|---|
| **routing** | `roles[].capabilityRole` | override | ✔ set | (✔) | (✔) | Maps a **task-role** (e.g. `discovery`, `field-fill`, `judge`) to an abstract **capability-role** (e.g. `fast-cheap`, `deep-reasoner`, `long-context`). Never a model ID. |
| | `roles[].minCapabilityTier` | clamp(↑) | ✔ | ✔ | ✔ | A domain may *require* a stronger tier; cannot drop below L0. |
| **tokenPolicy** | `maxOutputTokens` | clamp(↓) | ✔ | ✔ | ✔ | Effective = min across layers (cost/latency floor). |
| | `maxContextTokens` | clamp(↓) | ✔ | ✔ | ✔ | |
| | `temperatureDefault` | override | ✔ | ✔ | ✔ | |
| **providerPolicy** | `allowedProviders[]` | intersect | ✔ | ✔(narrow) | ✔(narrow) | Effective = intersection; lower layers can ban, never add. Compliance/region bans live at L1. |
| | `preferenceOrder[]` | override | ✔ | ✔ | ✔ | Tie-break order among *still-allowed* providers. Resolved **after** allow-list. |
| | `dataResidency` | clamp(strict) | ✔ | ✔ | — | e.g. `eu-only`; only tightenable (DSGVO). |
| **eval / quality** | `evalThresholds.*` | clamp(↑) | ✔ | (✔) | ✔ | Min quality gates; a domain can demand higher, never lower than L0 floor. |
| | `requireHumanReview` | override→true-sticky | ✔ | ✔ | ✔ | Once any layer sets `true`, stays `true` (OR semantics). |
| **telemetry** | `sampleRate` | clamp(↑) | ✔ | ✔ | ✔ | More observability allowed, not less than L0 minimum. |
| | `redactPII` | override→true-sticky | ✔ | ✔ | ✔ | Sticky-true like review. |
| **roi** | `attributionMethod` | override | ✔ | — | ✔ | Domain ROI logic (ties to action-code `impact_valuation`). |
| | `weighting.*` | override | ✔ | (✔) | ✔ | Per-domain ROI weighting = customer-individual business logic. |

`(✔)` = settable but uncommon; `—` = layer must not set this field (schema forbids via that layer's
variant). "clamp(↓)" = effective is the minimum; "clamp(↑)" = effective is the maximum; "clamp(strict)"
= most-restrictive enum wins; "intersect" = set intersection; "true-sticky" = boolean OR.

### 4.2 Schema skeleton (illustrative — ratify in ADR-0008)

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://aluca.dev/schemas/ai_config/1.0.0/ai_config.schema.json",
  "title": "AI Config Layer v1.0.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "layer"],
  "properties": {
    "schema_version": { "type": "string", "const": "1.0.0" },
    "layer": { "type": "string", "enum": ["L0", "L1", "L2"] },
    "scope": {                         // identifies what this layer instance applies to
      "type": "object", "additionalProperties": false,
      "properties": {
        "tenantId": { "type": ["string", "null"] },  // required for L1/L2
        "domainId": { "type": ["string", "null"] }   // required for L2
      }
    },
    "routing": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "roles": {
          "type": "array",
          "items": {
            "type": "object", "additionalProperties": false,
            "required": ["taskRole", "capabilityRole"],
            "properties": {
              "taskRole":       { "type": "string" },
              "capabilityRole": { "type": "string", "enum": ["fast-cheap","balanced","deep-reasoner","long-context"] },
              "minCapabilityTier": { "type": "integer", "minimum": 0, "x-merge": "clamp-max" }
            }
          }
        }
      }
    },
    "tokenPolicy": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "maxOutputTokens":  { "type": "integer", "minimum": 1, "x-merge": "clamp-min" },
        "maxContextTokens": { "type": "integer", "minimum": 1, "x-merge": "clamp-min" },
        "temperatureDefault": { "type": "number", "minimum": 0, "maximum": 2, "x-merge": "override" }
      }
    },
    "providerPolicy": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "allowedProviders": { "type": "array", "items": { "type": "string" }, "x-merge": "intersect" },
        "preferenceOrder":  { "type": "array", "items": { "type": "string" }, "x-merge": "override" },
        "dataResidency":    { "type": "string", "enum": ["any","eu-only","us-only"], "x-merge": "clamp-strict" }
      }
    },
    "eval": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "thresholds":         { "type": "object", "x-merge": "clamp-max-per-key" },
        "requireHumanReview": { "type": "boolean", "x-merge": "or" }
      }
    },
    "telemetry": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "sampleRate": { "type": "number", "minimum": 0, "maximum": 1, "x-merge": "clamp-max" },
        "redactPII":  { "type": "boolean", "x-merge": "or" }
      }
    },
    "roi": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "attributionMethod": { "type": "string", "enum": ["before_after","diff_in_diff","holdout"], "x-merge": "override" },
        "weighting":         { "type": "object", "x-merge": "override" }
      }
    }
  }
}
```

> One schema, a `layer` discriminator, and per-layer `required`/`forbidden` constraints (expressible
> with draft-07 `allOf`/`if`-`then`) keep all three layers in a single SSOT file. L0 additionally
> requires *completeness* (every group present) — enforced either in-schema or by a "L0-completeness"
> unit test, so the merge always starts from a total config.

### 4.3 Docking into `orchestrator.ts`

Today (`studio/src/lib/ai/orchestrator.ts`): `DEFAULT_MODELS` hardcodes `gemini-2.0-flash`,
`claude-sonnet-4-20250514`, `gpt-4o`, and `detectServerProvider()` hardcodes the Google→Anthropic→OpenAI
priority. T5 replaces both with config-driven resolution. Proposed flow:

```
request(taskRole, domainId?)
   │
   ├─ load layers  (impure loader: L0 from package, L1/L2 = latest *approved* from DB)
   ├─ resolveAiConfig(layers, {taskRole, domainId})  → EffectiveAiConfig   // PURE (§2)
   │
   ├─ pick capabilityRole          = effective.routing.roles[taskRole].capabilityRole
   ├─ pick provider                = first of effective.providerPolicy.preferenceOrder
   │                                   that is ∈ allowedProviders AND has a configured secret
   │                                   AND satisfies dataResidency
   ├─ map (capabilityRole, provider) → concrete modelId   // via a capability→model MAP, also config,
   │                                                       // NOT a literal in orchestrator.ts
   └─ createModel({ provider, apiKey, model: modelId, /* maxTokens, temperature from tokenPolicy */ })
```

Key points:
- `createModel(...)` stays as the **provider-adapter boundary** — unchanged signature, still
  LLM-agnostic. What changes is that `provider`/`model`/token params arrive from the *resolved
  config*, not constants.
- The **capability-role → concrete model** mapping is itself part of L0 (versioned by ALUCA), so
  swapping `claude-sonnet-4-*` for a newer model is an L0 release, not a code edit — and it is the
  single place a model ID literal may appear.
- Secret presence check (`detectServerProvider`'s real job) is preserved but becomes a *filter* over
  `allowedProviders`, not the source of priority. Priority comes from `preferenceOrder`.
- If no allowed+configured provider satisfies residency → explicit typed error (no silent fallback),
  surfaced like other `src/lib/api/error-codes.ts` errors.

---

## 5. Validation + versioning approach

### 5.1 Validation

- **Authoring-time / per-layer**: validate each L0/L1/L2 instance against `ai_config.schema.json`
  (with its `layer` discriminator) using the studio's existing **Ajv** validator
  (`src/lib/validation/schema-validator.ts`). Reject on save (the house rule: "never trust user
  input — validate before persisting").
- **Post-merge / effective**: after `resolveAiConfig`, validate the **effective** object against an
  *effective* schema variant (no `layer` discriminator, all groups required, all ranges enforced).
  This catches merge-logic regressions and is the runtime backstop (§2).
- **Invariant tests** (CI): clamp/intersect invariants as property tests (§2) so the safety rule
  "customer can only tighten" is machine-checked, not just documented.

### 5.2 Versioning — version the L0 schema with SemVer, version *instances* with a stamped field

Following the consensus pattern [S2][S4][S5][S7]:

- **`$id` carries the version** (`.../ai_config/1.0.0/...`) and `schema_version` `const` mirrors it
  inside instances — same dual signal the sources recommend (`$id` for the schema, a `schemaVersion`
  property inside documents). [S2][S4]
- **SemVer for the schema**, because it is product-facing (customers author L1/L2 against it):
  **major** = breaking (field removed/retyped/semantics changed) → requires migration; **minor** =
  backward-compatible addition (new optional field older readers ignore) → no migration needed;
  **patch** = doc/clarification, non-structural. [S2][S4] (Plain integers are fine for purely
  internal config [S2]; we choose SemVer here precisely because L1/L2 are customer-authored.)
- **Loader = migration pipeline** [S2]: `parse → read schema_version → validate against that version
  → migrate one step at a time to latest → hand normalized object to resolver`. Migrations are pure
  functions `vN → vN+1`, unit-tested with golden before/after fixtures. Because L1/L2 are stored
  per-tenant, migrations run lazily on load (and may be persisted back as an approved, audited
  change).
- **Adding an optional field needs no major bump** if older readers ignore unknowns and behavior is
  unchanged. [S2][S5] Our resolver tolerates unknown `x-merge`-less fields by treating them as
  `override` only when explicitly opted in; otherwise unknown fields are rejected at validation
  (`additionalProperties: false`) — so additions are *deliberate schema minor bumps*, not silent.
- **Audit captures the authored schema version** per change (§3.3), so a tenant's L1/L2 always
  records which version it was written against — essential for replaying/migrating.

---

## Sources

Retrieved 2026-06-24.

- [S1] DEV Community — *A Practical Guide to Layered Configuration for Modern JavaScript Applications.* https://dev.to/raulfdm/a-practical-guide-to-layered-configuration-for-modern-javascript-applications-5709
- [S3] codewithmukesh — *ASP.NET Core Configuration: appsettings, Env Vars & User Secrets.* https://codewithmukesh.com/blog/environment-based-configuration-aspnet-core/
- [S8] DeepWiki — *Settings and Configuration | astral-sh/uv.* https://deepwiki.com/astral-sh/uv/2.2-settings-and-configuration
- [S9] DeepWiki — *Configuration Inheritance and Merging | renovate-config-validator-workflow.* https://deepwiki.com/suzuki-shunsuke/renovate-config-validator-workflow/3.2-configuration-inheritance-and-merging
- [S2] offlinetools.org — *Schema Versioning for JSON Configuration Files.* https://offlinetools.org/a/json-formatter/schema-versioning-for-json-configuration-files (search-snippet only; HTTP 403 on direct fetch 2026-06-24 — see Open/unverified)
- [S4] Liquid Technologies — *JSON Schema Tutorial Part 3: Design and Structure (reusability, $id, versioning).* https://blog.liquid-technologies.com/json-schema-tutorial-part-3-design-and-structure
- [S5] dataexpert.io — *Backward Compatibility in Schema Evolution: Guide.* https://www.dataexpert.io/blog/backward-compatibility-schema-evolution-guide
- [S7] GitHub — UlisesGascon/POC-semver-and-json-schemas (*SemVer + JSON Schemas*). https://github.com/UlisesGascon/POC-semver-and-json-schemas
- [S6] PostHog — *Best practices for production-ready feature flags* (deterministic hash, Layers). https://posthog.com/docs/feature-flags/best-practices
- [S10] MDPI — *Dynamic Frontend Architecture for Runtime Component Versioning and Feature Flag Resolution in Regulated Applications* (lexicographic compliance-first resolution). https://www.mdpi.com/2674-113X/4/4/32
- [S11] Wikipedia — *Pure function.* https://en.wikipedia.org/wiki/Pure_function
- [S12] Mark Heath — *Testable Code with Pure Functions.* https://markheath.net/post/testable-code-with-pure-functions
- [S13] OxRSE Training — *Testable Code and Fixtures.* https://train.rse.ox.ac.uk/material/HPCu/technology_and_tooling/testing/testable_code_fixtures
- [S14] Medium (Hash Block) — *10 Ways to Test ML Code: Fixtures, Seeds, Golden Files.* https://medium.com/@connect.hashblock/10-ways-to-test-ml-code-fixtures-seeds-golden-files-811310517cae

Repo grounding (read-only, this session): `studio/src/lib/ai/orchestrator.ts` (hardcoded
`DEFAULT_MODELS`, fixed provider priority); `studio/src/lib/governance/approval-workflow.ts` +
`approval-types.ts` (lifecycle, two-person rule, audit); `studio/src/lib/db/audit-repo.ts`,
`audit-chain.ts`; `studio/src/lib/validation/schema-validator.ts` (Ajv); `studio/src/lib/auth/*`
(RBAC); `tooling/generator/schemas/action_code.schema.json` (house schema style: draft-07,
`additionalProperties:false`, `schema_version` const, `owner_role`/`steward_role` split);
`studio/CLAUDE.md` (declares `tooling/ai/schemas/` as schema SSOT + `npm run generate:types`).

## Open / unverified

- **[S2] not directly fetched.** offlinetools.org returned HTTP 403 to WebFetch on 2026-06-24; its
  claims (loader pipeline: parse→detect version→validate→migrate; integer-vs-SemVer guidance;
  optional-field/backward-compat rule) are taken from the search-result snippet and are independently
  corroborated by [S4][S5][S7]. Verify the primary before citing verbatim in ADR-0008.
- **`tooling/ai/schemas/` does not physically exist yet.** studio/CLAUDE.md declares it as the schema
  SSOT and the regeneration command points at it, but the actual schemas currently live in
  `tooling/generator/schemas/`. ADR-0008 must decide: create `tooling/ai/schemas/` (as documented) vs.
  place `ai_config.schema.json` under the existing `tooling/generator/schemas/`. This doc assumes the
  documented path; confirm with the maintainer.
- **Field taxonomy is a proposal.** The exact field names/ranges in §4 (esp. `capabilityRole` enum,
  eval threshold keys, ROI weighting shape) are placeholders to be filled by the routing/token/eval/ROI
  T-themes. Treat §4.1/§4.2 as the *shape contract*, not the final field list.
- **`x-merge` annotation approach** (merge semantics encoded in-schema, read by the resolver) is a
  design choice, not an external standard. Alternative: keep merge semantics in a separate resolver
  table. In-schema keeps it as one SSOT but means the resolver and schema are coupled; decide in ADR-0008.
- **L0 release/versioning mechanics** (how an L0 schema bump + capability→model map update is shipped
  to existing tenants, and whether tenant L1/L2 auto-migrate or require re-approval on major bumps)
  needs a concrete migration runbook — out of scope for T5 research, flagged for ADR-0008.
- **Reusing `bracket_lifecycle` vs. a new table** for config-change governance is left open; both
  reuse the same `transition()` state machine. Schema/DB impact to be decided with the DB owner.
