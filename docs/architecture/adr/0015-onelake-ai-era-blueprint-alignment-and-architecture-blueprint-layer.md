# ADR-0015 — OneLake AI-Era Blueprint Alignment & a Stack-Agnostic Architecture-Blueprint Layer

- **Status:** Proposed
- **Date:** 2026-07-15
- **Scope:** ALUCA (this repo) + sibling `Freelancing`/Meridian (parallel doc:
  `meridian/docs/research/reporting-platform-blueprints/2026-07-15_onelake-ai-era-blueprint-alignment.md`)
- **Relates to:** ADR-0005 (Superversion home), ADR-0006 (Target-adapter contract),
  ADR-0002 (Official-First / GADW), ADR-0009 (Wirkungs-Loop),
  `core/strategy_operating_model/operating_model/lakehouse_architecture.md`,
  `core/strategy_operating_model/operating_model/data_layers_standard.md`,
  `core/strategy_operating_model/operating_model/ai_readiness.md`

> This ADR is a **plan** (Proposed). It records the comparison against Microsoft's
> current OneLake / AI-era architecture guidance, the gap analysis against ALUCA's
> approach, and the proposed direction. It does **not** yet mutate the operating-model
> standards or ship code — those are the ratification follow-ups in §Roadmap.

---

## 1. Context — the source and what it says

Trigger: the Fabric Updates blog **"OneLake architectural guidance: A practical
blueprint for the AI Era"** (community.fabric.microsoft.com, ba-p/5282667). The blog
consolidates Microsoft's **Cloud Adoption Framework (CAF)** guidance, which is the
authoritative, verbatim-fetchable backbone. The guidance reduces to **five
architectural patterns** plus an **AI-era consumption model**:

| # | Pattern | Core rule |
|---|---|---|
| P1 | **Data Access Unification** | Virtualize, don't duplicate. Integrate via **shortcuts** (virtual) or **mirroring** (replicated); copy only when performance/isolation/compliance demands it. |
| P2 | **Medallion Architecture** | **Bronze** = immutable, append-only *system of record* (raw, no enrichment). **Silver** = validated/cleansed *trusted view*. **Gold** = certified *business data products*. Every inbound dataset lands in bronze first; **shortcuts must not bypass the layers**. |
| P3 | **Data Mesh + Governance** | Fabric **domains** group **workspaces** (a workspace = the security/ownership/cost boundary). Publish gold as **data products** discoverable in the **OneLake Catalog** + **Purview**, with **endorsement** (Promoted/Certified), **metadata enrichment**, and a declared **intended audience**. |
| P4 | **Platform Simplification** | Fabric is the default managed estate on one copy in OneLake; enforce **platform ownership boundaries** (one platform owns each workload class) to prevent duplicate transformations. Databricks/other engines surface their **gold** into OneLake via shortcut/mirror. |
| P5 | **External Data Sharing** | External products are **separate, sanitized, labeled** (masked/reduced), in separate workspaces — never the internal operational data. |

**AI-era consumption model** (the "for the AI Era" half):

- A **unified, governed data platform is the prerequisite for AI agents.** Agents
  synthesize, they don't create — accuracy = quality of the grounding data.
- Agents consume **gold/silver data products** through **Fabric IQ**, **Foundry IQ**,
  **Fabric data agents**, and **Copilot Studio** — **never raw bronze.**
- **Retrieval strategy:** prefer **built-in retrieval** (Fabric IQ / Foundry IQ /
  OneLake indexers) first; use **MCP servers** only for live/action data.
- **Document retrieval decisions per data domain** (search vs API/MCP, which sources
  are certified, which need auth).
- **Adaptive Gold** (forward-looking): AI agents materialize frequently-requested gold
  datasets from Fabric/Power BI telemetry. Not out-of-the-box; needs a custom agent.

**Similar / corroborating sources** (read for triangulation):
Microsoft Learn — *Understand medallion lakehouse architecture for Fabric with OneLake*;
*Data architecture for AI agents* (CAF); *Fabric governance and security baselines* (CAF);
*Data processing standards for AI and analytics* (CAF, the 5-pattern checklist);
*What is OneLake?* / *Lakehouse overview*; *Integrate Dataverse with Fabric using a
medallion architecture*. Practitioner echoes (revos.ai, exultglobal, conceptualise.de,
sqlyard) converge on the same layers + data-mesh-over-medallion framing, adding
concrete naming/workspace conventions but no divergence from the CAF spine.

**Net:** the source is not new information about medallion; its value is the
**AI-era framing** — *the architecture is the moat for agents*, gold/silver are the
grounding surface, and the five patterns are the standardization checklist that makes
an estate "AI-ready."

---

## 2. Where ALUCA stands today (gap analysis)

ALUCA already has strong, differentiated pieces — and some real gaps against the five
patterns. Honest scoring:

| Pattern | ALUCA today | Gap |
|---|---|---|
| **P2 Medallion** | `lakehouse_architecture.md` fully specifies Bronze→Silver→Gold (fixed Gold layout: `dim_*`/`fact_*`/`agg_*`, Delta, Direct Lake ≤300 cols). Strong. | `data_layers_standard.md` scopes **bronze/staging out** ("we define Silver via data contracts; deliver Gold+Semantics") and is **silver-first**. The blueprint mandates **bronze as immutable SoR** + a **no-layer-skipping** rule. → We need a *specified, optional* bronze contract and the layer-skip prohibition, even when a project outsources bronze. |
| **P1 Access Unification** | Shortcuts named for zero-copy Gold integration. | No **first-class shortcut-vs-mirroring decision** in the ingestion story; access mode isn't a governed, per-source field. |
| **P3 Data Mesh + publishing** | 5 domains → semantic-model-per-domain; Golden Thread governs meaning. | No **domain→workspace topology** standard; no **data-product publishing** standard (OneLake Catalog / Purview registration, **endorsement**, metadata-enrichment, intended-audience). Governance is meaning-level, not estate-level. |
| **P4 Platform Simplification** | Superversion already emits to N stacks (TMDL/PBIR/OSI/Databricks); Fabric is the default target. | No explicit **platform-ownership-boundary** statement; multi-target is a strength but the "one platform owns each workload" rule isn't recorded. |
| **P5 External Sharing** | — | **Absent.** No sanitized-external-data-product pattern. |
| **AI-era grounding** | **Strong.** GADW Stage 5 "Prep-for-AI" (`linguistic_schema.py` synonyms/Q&A + lineage → Copilot/data-agent readiness); `ai_readiness.md` doctrine ("retrieval preferred over generation, grounding mandatory"); ADR-0002 official-first. | No explicit **"agents ground on gold/silver, never bronze"** rule; no **Fabric IQ / Foundry IQ / MCP retrieval-strategy** decision record per domain; no **Adaptive Gold** concept (though ADR-0009 Wirkungs-Loop telemetry is the natural seed). |

**Structural observation.** ALUCA's `tooling/superversion/` is a genuinely reusable,
deterministic, stack-agnostic generator — but it operates at the **semantic-model /
report** layer (one CanonicalModel → N targets). There is **no equivalent one level up,
at the *platform-architecture* layer** (medallion topology, domain/workspace layout,
shortcut/mirroring plan, grounding surface). That missing layer is exactly what the
OneLake blueprint standardizes — and exactly the reusable standalone tool the request
asks for.

---

## 3. Decision (proposed) — a stack-agnostic **Architecture-Blueprint layer**

Introduce, one level **above** the existing Superversion CanonicalModel, a governed
**Architecture Blueprint IR**: a deterministic canonical description of the *platform
architecture* whose fields **are** the five patterns. It reuses ALUCA's proven pattern
(ADR-0005/0006: one canonical model → registry of target adapters → `render` dispatch)
so it "docks, doesn't rebuild."

> **Drafted contract:** the concrete IR — JSON Schema, architecture diagram, a worked
> Fabric example (render/audit/ground), and the cross-stack mapping — is spec'd in
> [`../research/architecture-blueprint-ir-spec.md`](../research/architecture-blueprint-ir-spec.md).
> Per the 2026-07-15 decision it is **field-identical and mirrored** with the sibling
> `Freelancing`/Meridian copy (ADR-0005 contract-mirror discipline): the schema is
> authored once, mirrored byte-identical, and parity-checked — not forked into two IRs.

### 3.1 The Architecture Blueprint IR (new canonical, schema in `tooling/generator/schemas/`)

```
ArchitectureBlueprint
  platform:      stack (fabric|databricks|snowflake|…) + ownership boundaries   # P4
  ingestion[]:   per source → access_mode (shortcut|mirror|copy) + rationale    # P1
  medallion:     bronze{immutable SoR, optional/outsourced flag} → silver{data
                 contracts} → gold{dim_/fact_/agg_ data products} ; no-skip rule # P2
  mesh:          domain → workspace(s) topology ; data_product registry ;
                 publishing{catalog, purview, endorsement, metadata, audience}   # P3
  sharing[]:     external data products (sanitized, labeled, separate workspace) # P5
  ai_grounding:  grounding_surface = {gold, silver} ;
                 retrieval_strategy per domain (built-in-first → MCP) ;
                 emits mcp_grounding manifest                                    # AI-era
```

The IR is **derived deterministically** from existing ALUCA truth — domains, the KPI
catalog, `UseCase_Bracket.yaml` (`overrides.data_contract_ref`), the data contracts —
so it stays inside the Golden Thread (references governed definitions, never redefines).

### 3.2 Three reusable capabilities (the standalone tool/workflow)

1. **`render`** — Blueprint IR → per-stack scaffolding, via the ADR-0006 target-adapter
   contract (`emit(blueprint) → {path: content}`):
   - **Fabric first** (`targets/arch_fabric`): lakehouse/workspace/domain layout +
     shortcut/mirroring plan + Direct-Lake semantic-model binding. This reuses the
     vendored Meridian `blueprint1` provisioning recipe.
   - **Databricks** (`arch_databricks`): Unity Catalog + medallion schemas.
   - **Snowflake** (`arch_snowflake`): database/schema + Semantic Views.
   Same IR, different renderers — the five patterns are stack-neutral; only native
   feature mapping differs. This is how "the same pattern is used for other stacks."
2. **`audit`** — score an existing/proposed architecture against the five patterns +
   AI-grounding, as a new **eval gate** in `tooling/superversion/eval/` (a
   `blueprint_conformance` gate alongside the value/compliance gates), emitting an
   honest pattern-by-pattern scorecard (green/amber/red + evidence).
3. **`ground`** — emit the **AI-grounding manifest** (`mcp_grounding.json` pointing
   agents at gold/silver data products) + a **per-domain retrieval-decision record**
   (built-in-first vs MCP, certified sources, auth). This operationalizes the AI-era
   half and extends GADW Stage 5 upward from the semantic model to the estate.

### 3.3 Standards changes proposed (ratification follow-ups, not done here)

- `data_layers_standard.md`: add a **specified, optional bronze contract** (immutable,
  append-only SoR) + the **no-layer-skipping-shortcut** rule, so that outsourcing
  bronze is a *documented* choice, not an unspecified gap.
- `lakehouse_architecture.md`: add **P1 access-unification** (shortcut/mirror decision
  matrix) and **P3 mesh/publishing** (domain→workspace topology + Catalog/Purview
  data-product publishing + endorsement + metadata) sections.
- `ai_readiness.md`: add the explicit **"agents ground on gold/silver, never bronze"**
  rule + the **retrieval-first-then-MCP** strategy; note **Adaptive Gold** as a
  forward-looking use of the ADR-0009 Wirkungs-Loop telemetry.
- New **P5 external-data-sharing** stub in the operating model.

---

## 4. Consequences

**Positive**
- Turns Microsoft's AI-era guidance into an **executable, audited standard**, not prose.
- The reusable Architecture-Blueprint tool fills the one real structural gap (no
  architecture-layer generator) using the already-ratified ADR-0005/0006 pattern — low
  conceptual risk, high leverage.
- Cross-stack falls out for free: the IR is stack-neutral; Fabric/Databricks/Snowflake
  are renderers. Matches the request's "same pattern for other stacks."
- Sharpens the ALUCA moat exactly where the market is converging (grounding is becoming
  vendor-native; **determinism + auditability + portability + tool-free** is the
  differentiator — mirrors the sibling repo's MS-2606-2 finding).

**Costs / risks**
- New IR + schema + 3 renderers + a gate is real work; must respect Tool-Reuse (extend
  Superversion + eval, do **not** fork a parallel generator).
- Bronze-as-SoR partially reverses the deliberate silver-first scope of
  `data_layers_standard.md`; it must stay **optional/specified**, not mandatory, to
  keep the "we deliver Gold+Semantics" delivery posture.
- Fabric-native features (Fabric IQ, Foundry IQ, Adaptive Gold, materialized lake views)
  are **not fully reproducible in this sandbox** (no live tenant) — audit/ground stay
  deterministic + tool-free; live provisioning is Windows/tenant-gated, like the
  existing Premium-floor F1/F6 honesty caveats.

**Honesty caveats**
- The source blog itself returned HTTP 403 to automated fetch; its content is
  reconstructed from the **verbatim CAF pages it consolidates** (Microsoft Learn MCP) +
  corroborating search summaries. The five patterns and AI-era model are quoted from
  those first-party pages, not the blog HTML.

---

## 5. Roadmap (ratification → build)

| Step | What | Gate |
|---|---|---|
| R-1 | Ratify this ADR (Accepted) | Maintainer (Flo) |
| R-2 | Land the standards deltas (§3.3) in the operating model | Drift-gate + review |
| R-3 | `ArchitectureBlueprint` schema (per drafted spec) + deterministic derivation from ALUCA truth; **field-identical mirror** with Meridian + parity check | Schema + parity tests |
| R-4 | `targets/arch_fabric` renderer (reuse Meridian `blueprint1`) | Cross-target test |
| R-5 | `blueprint_conformance` eval gate (5 patterns + grounding scorecard) | pytest |
| R-6 | `ground` = `mcp_grounding.json` + per-domain retrieval-decision record | GADW Stage 5 seam |
| R-7 | `arch_databricks` / `arch_snowflake` renderers (cross-stack) | Cross-target test |

Coordinate R-3…R-7 with the sibling `Freelancing`/Meridian build of the same layer
(its long-planned Prompt-N / D-142 architecture generator), so ALUCA and Meridian keep
a **field-identical Architecture Blueprint IR** — same contract-mirror discipline as
ADR-0005.

---

## 6. Sources

- Microsoft Fabric Updates Blog — *OneLake architectural guidance: A practical blueprint
  for the AI Era* (community.fabric.microsoft.com/t5/Fabric-Updates-Blog/…/ba-p/5282667).
- Microsoft Learn / CAF — *Data processing standards for AI and analytics*;
  *Data architecture for AI agents*; *Fabric governance and security baselines*;
  *Understand medallion lakehouse architecture for Fabric with OneLake*;
  *What is OneLake?*; *Integrate Dataverse with Fabric using a medallion architecture*.
- Retrieved 2026-07-15 via Microsoft Learn MCP + web search (blog HTML itself 403 to
  automated fetch — see §4 honesty caveat).
