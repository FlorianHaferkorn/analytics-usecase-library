# Framework Evolution (Internal Vision)

> This document describes a directional vision and an incremental path.  
> It is **not** a roadmap, timeline, or commitment. Only V1 is implemented and supported.

---

## Purpose

Define the long-term direction of the Analytics Framework and the smallest, pragmatic steps to reach it—without creating customer-facing promises or locking into specific tools.

---

## North Star

A standardized analytics system that can be:
- **Implemented repeatedly** across companies with different realities,
- **Operated with minimal manual effort**,
- **Consumed through reports and conversational interfaces**, and
- **Evolved safely** through deterministic guardrails.

Humans remain accountable for decisions; automation increases only when governance is strong enough to prevent drift.

---

## What Must Never Change (Invariants)

1. **Semantic Layer stays the single business interface**
   - KPIs and measures are defined once and referenced everywhere.
   - Reports and apps consume governed measures; they do not create business logic.

2. **Use Cases reference, they do not define**
   - Use cases link to KPIs, action codes, and templates.
   - KPI meaning, targets, lineage belong to the KPI catalog / governed artifacts.

3. **Governance before automation**
   - Automation is allowed only where definitions, ownership, and checks exist.

4. **Deterministic gates for hard rules**
   - Hard drift risks are blocked by Stage 1.
   - Soft issues are surfaced as guidance (Stage 2), not blockers.

5. **Tool-agnostic by design**
   - Artifacts are designed as contracts and templates first.
   - Implementations (Fabric/Power BI, etc.) are adapters, not the framework.

---

## End-State Capabilities (Final Vision)

### A) Provider-grade Repeatability
- Standardized packages (core domains/use cases) can be deployed repeatedly.
- Contracts + templates yield consistent results across customers.

### B) Closed Loop (Action-Ready Analytics)
- Insights connect to guided actions (action codes) with clear triggers, evidence, and ownership.
- Actions can be executed in target systems or workflows (later iterations).

### C) Assisted Creation and Operation
- AI assists in drafting artifacts, reviewing consistency, proposing improvements.
- Humans approve changes; AI does not invent definitions.

### D) Assisted Consumption
- Users can consume analytics via:
  - Report templates and curated pages
  - A conversational layer that queries the semantic layer and explains results
- AI highlights trends and suggests actions, but does not execute unapproved decisions.

---

## Versioned Path (How We Reach It Step by Step)

### V1 — Foundation (Current Baseline)
**Goal:** Repeatable, governed delivery without AI in the customer experience.

**Delivered / required outcomes**
- Core framework artifacts exist (strategy → KPIs → use cases → action codes → templates).
- Aurora Group reference implementation demonstrates:
  - core use cases end-to-end
  - report templates + layout standards
  - closed loop structure (without active AI)
- **Stage 1 Hard CI Gate** blocks drift:
  - schema validation, refs, ID integrity, SSOT marker rules, forbidden fields, duplicates
- Stage 2 is specified (non-blocking), but not required to run.

**Exit criteria**
- Aurora Group is demo-ready with core pages and consistent KPI definitions.
- Stage 1 is mandatory in CI and stable (low false positives).

---

### V2 — Assisted Quality (Soft Review + Authoring Assist)
**Goal:** Increase quality and consistency with minimal process overhead.

**What changes**
- Stage 2 Soft CI Report runs on PR diffs and posts guidance:
  - contradictions, ambiguous authority, red flags in prose
  - not blocking merges
- Optional authoring assistance:
  - draft improvements to wording, template alignment, documentation clarity
  - always reviewable and traceable

**Guardrails**
- Diff-only inputs.
- Max 10 findings per PR.
- No new artifact types introduced by AI.

**Exit criteria**
- Stage 2 reduces review effort and catches recurring issues.
- Teams accept it as helpful (low noise).

---

### V3 — Guided Automation (Template Instantiation + Partial Closed Loop)
**Goal:** Reduce manual build effort while keeping governance deterministic.

**What changes**
- Automated generation of customer-specific instantiations from governed templates:
  - use case package selection
  - data contract scaffolding
  - semantic model skeleton + measure dictionary scaffolds
  - report page scaffolds based on the 3-30-300 standard
- Closed loop becomes operationally useful:
  - action codes produce structured recommendations and evidence
  - execution remains human-orchestrated

**Guardrails**
- Generated artifacts must pass Stage 1.
- Changes are traceable and reviewable (PR-based).

**Exit criteria**
- Customer MVP packages can be produced faster with consistent quality.
- Drift stays controlled despite higher throughput.

---

### V4 — Assisted Operations (Observability + Recommendations at Scale)
**Goal:** Operate many deployments with consistent health and low effort.

**What changes**
- Standard operational telemetry:
  - data freshness, model health, report performance, usage signals
- AI-assisted triage:
  - identifies anomalies, suggests likely root causes, proposes fixes
- Governance-driven improvement loop:
  - recommended changes go through PR + Stage 1 gate

**Exit criteria**
- Reduced support workload per customer.
- Predictable quality across deployments.

---

### V5 — Assisted Consumption (Conversational Layer on Semantic)
**Goal:** Add a conversational consumer experience safely.

**What changes**
- AI consumes the semantic layer and produces:
  - explanations of KPIs and deltas
  - guided exploration (“why did margin drop?”) using governed measures only
  - suggested actions mapped to governed action codes
- Strict constraints:
  - no new measures defined at runtime
  - no hidden logic outside the semantic layer

**Exit criteria**
- Customers can explore insights conversationally without inconsistent definitions.
- “Explainability” remains aligned with governed artifacts.

---

### V6 — Orchestrated Autonomy (Vision)
**Goal:** AI proposes and orchestrates; humans approve.

**What changes**
- AI proposes:
  - trend detection
  - prioritized action queues
  - impact estimates based on historical outcomes
- Humans approve execution and remain accountable.
- Automation is constrained to:
  - what is explicitly allowed by governance and policies

**Exit criteria**
- Autonomy is limited, auditable, reversible, and governed.

---

## Practical “How We Get There” (Concrete Steps)

### Step 1 — Freeze V1 + Deliver Aurora Group
- Finish the Aurora Group reference as a tactile demo.
- Ensure Stage 1 is stable and mandatory.
- Keep documentation minimal and consistent.

### Step 2 — Introduce Stage 2 Soft Review as a Non-Blocker
- Start with “diff-only” and “max 10 findings”.
- Iterate until noise is low and signal is high.

### Step 3 — Automate Scaffolding, Not Decisions
- Generate skeletons (contracts, model scaffolds, page scaffolds).
- Keep decision logic (KPI meaning, triggers) governed and human-owned.

### Step 4 — Standardize Operations Before AI Consumption
- Add health/observability conventions first.
- Then use AI for triage and recommendations.

### Step 5 — Add Conversational Consumption Only After Semantic Maturity
- AI uses governed measures only.
- No “creative analytics” in production contexts.

---

## Success Metrics (Non-Technical)

- **Repeatability:** same package produces consistent outcomes across customers.
- **Speed:** faster MVP delivery without sacrificing quality.
- **Stability:** drift incidents decrease over time (Stage 1 + Stage 2 effectiveness).
- **Clarity:** fewer review debates about definitions and authority.
- **Adoption:** customers can understand and use the outputs without heavy enablement.

---

## Definition of Done for This Vision Document

- [x] Internal-only direction, no customer promises
- [x] Step-by-step evolution without timelines
- [x] Clear invariants (what must never change)
- [x] Separation of hard gates vs soft guidance
- [x] Tool-agnostic, implementation as adapter
