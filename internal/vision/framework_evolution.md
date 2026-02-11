# Framework Evolution (Internal Vision)

> This document describes a directional vision and an incremental path.  
> It is **not** a roadmap, timeline, or commitment. Only V1 is implemented and supported.

---

## Purpose

Define the long-term direction of the Analytics Framework and the smallest, pragmatic steps to reach it - without creating customer-facing promises or locking into specific tools.

---

## Product Vision: What We Deliver and Why

### Problems the framework solves for companies

- **KPIs exist but are debated, not trusted** — definitions and targets are reinterpreted per report or team.
- **Reports explain deviations but do not support decisions** — no clear link to actions or ownership.
- **Business and analytics work on different interpretations** of the same numbers.
- **New requirements lead to new logic** instead of reuse; drift and duplication grow.
- **AI and automation are discussed but not structurally prepared** — no single semantic interface for humans and AI.

The framework exists to make the path **strategy → KPIs → use cases → semantic models → actions** explicit, governed, and reusable so that analytics becomes a **reliable steering capability**, not a cost center.

### Benefits for companies

- **Fewer debates, faster decisions** — one KPI catalog and one measure system; reports and AI use the same definitions.
- **Decision-oriented analytics** — organized by use cases and actions (what question, what action), not by "another dashboard."
- **Reuse and speed** — new requirements extend existing KPIs and templates instead of reinventing logic.
- **Action-ready** — insights connect to governed action codes (triggers, evidence, ownership).
- **Automation- and AI-ready** — structured metadata and a single semantic layer enable both "AI helps build/maintain" and "AI consumes data reliably."

### Tool-agnostic concept, tool-specific implementation

- **Concept and design are tool-agnostic:** Strategy, KPIs, use cases, action codes, page types (3-30-300), data contracts, and governance live in YAML/Markdown and apply to any platform. They define *what* and *why*, not *how* in a specific tool.
- **Semantic models and measures are tool-specific:** When we *build* the semantic layer and reports, we choose a platform. For the first full product, that platform is **Microsoft Fabric / Power BI**. TMDL, PBIP, measures, and deployment are Fabric/Power BI-specific but *driven by* the tool-agnostic artifacts (factsheets, KPI catalog, action codes, templates). One concept; one concrete implementation that realizes it.

### First full product: Aurora Group on Fabric / Power BI

The **Aurora Group showcase** is the first fully functioning **Microsoft Fabric / Power BI** version of the framework. It delivers:

1. **Best-practice semantic modeling and reports** — 3-30-300, action codes, standardized report templates; semantic layer as single business interface.
2. **Best-practice architecture, code-driven** — workspace, dataset, lakehouse, and report structure that can be **set up and torn down by code** (e.g. Bicep, Fabric APIs), not only by clicking in the portal.
3. **Foundation for AI** — **AI as builder/maintainer:** metadata and structure enable AI to help create and maintain semantic models and reports in a governed way. **AI as consumer:** the semantic layer is the single, governed interface for querying and explaining data so AI and humans use the same definitions.
4. **Ease, efficiency, maintainability, scalability** — as **easy**, **time- and resource-saving**, and **maintenance-friendly** as possible; **scalable** to more use cases, workspaces, and customers.
5. **First, pragmatic governance** — lightweight but binding: ownership, change flow (e.g. KPI catalog → use cases → semantic model), and quality gates (e.g. Stage 1) without heavy process.

This vision should be reviewed and refined as we evolve; the rest of this document details invariants, end-state capabilities, and the versioned path.

---

## Framework Roles and Product Layers

The framework serves **two distinct roles**. Both are necessary; customers can use one or both.

### Role 1 — Structured Procedure (Methodology)

The framework provides a **repeatable, governed procedure** that we or customers follow to achieve meaningful, data-driven, world-class reporting. This is the "how to get there": strategy patterns, Golden Thread, use cases, KPI catalog, action codes, playbooks, and quality gates. Anyone can adopt the procedure and build their own reports and semantic layer on top of their data and tools. The procedure does not prescribe a specific UI or platform; it prescribes structure, ownership, and decision orientation.

**Deliverables:** Playbooks, strategy patterns, use case and action code definitions, templates, governance (RACI, change flow), validation (Stage 1, Fabric checks). Reference implementations (e.g. Aurora Group) demonstrate the procedure; they are not the only way to implement it.

### Role 2 — Standardized Reports Product

Because of the structured approach, we can provide **standardized, pre-built reports** that nearly all companies need for their strategic goals — in an optimized, consistent form. These reports are the **next end product**: they implement the same use cases, KPIs, and 3-30-300 (or agreed variants) so that customers get best-practice content out of the box, not only the method to build it. Quality and consistency are high because every report is derived from the same framework artifacts.

**Deliverables:** Pre-built report packages (e.g. by domain or strategy pattern) that consume a governed semantic model; optional industry or layout variants. Customers can take all, some, or none of these reports and still use the framework as a procedure.

### Customer Choice

- **Framework only:** Customer uses the procedure (playbooks, use cases, governance) and builds or commissions their own reports and semantic layer. Full flexibility; more build effort.
- **Framework + standardized reports:** Customer uses the procedure and additionally adopts pre-built reports — all of them, or a subset (e.g. Commercial pack only, or only Executive view). Faster time to value; consistency with the framework’s definition of "done."
- **Hybrid:** Procedure plus some standardized reports; custom reports for the rest, as long as they consume the same semantic layer and do not redefine business logic.

The framework remains the single source of truth for meaning (KPIs, use cases, actions); the product layer is a **conformant implementation** of that meaning.

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

## BI Lifecycle, Flexibility, and Intelligence

Analytics is not one-time delivery. The framework must support the **full BI lifecycle** and stay smart and easy as strategies, reports, and requirements change.

### Lifecycle and Change

- **Strategy and reports evolve:** Company strategies adapt; reports and use-case priorities change. The framework supports change through governed artifacts (strategy patterns, KPI catalog, use cases): updates flow along the Golden Thread without ad-hoc rework. Versioning and impact awareness (e.g. "which reports use this KPI?") reduce risk.
- **Industry and gaps:** Industry-specific reports or use cases may be missing. The framework allows **extensions** (industry packs, additional use cases) that reference the same KPIs and governance; core remains stable; new content is additive.
- **Layout and UX flexibility:** Some customers do not want a strict 3-30-300 report; they want individual layouts or tools. The invariant is **consumption of the semantic layer** (governed measures only). Layout and visualization can vary (custom pages, different tools, embedded analytics) as long as business logic stays in the semantic layer and is not recreated in reports or apps. The framework supports "custom layout, governed meaning."

### Automation and AI

- **Framework maintenance:** AI assists in keeping the framework consistent: drafting artifact updates, checking refs, proposing alignment when strategy or KPIs change. Humans approve; automation reduces manual drift and speeds change.
- **AI as consumer:** The semantic layer is the single interface for querying and explaining data. AI can answer questions, explain deltas, and suggest actions using **only** governed measures and action codes — no ad-hoc logic. Use cases of "AI as consumer" extend the **coverage of domains and topics** that can be analysed conversationally, without building a new report for every question.
- **Coverage:** As domains and topics grow (e.g. risk, ESG, people), the framework and the standardized report product extend in a governed way; AI consumption benefits from the same extended semantics.

**Future consideration (later stage): agentic BI development.** For a later stage, consider the building blocks and scenarios in [SQLBI: Introducing AI and agentic development for Business Intelligence](https://www.sqlbi.com/articles/introducing-ai-and-agentic-development-for-business-intelligence/): (1) chatbot tools with basic context, (2) augmented chatbot with MCP servers and curated context (PBIP + remote repos), (3) agentic development—agents that read/write metadata and assist report/model build with orchestration and validation, (4) asynchronous agents (delegated tasks, PR-based review). Our setup (PBIP/TMDL, MCP tooling, governed context in KPI catalog and use cases) aligns with the article’s emphasis on context, tools, and environment; any agentic use should remain under “humans approve, AI does not invent definitions” and pass Stage 1.

### Platform Architecture and "Analytics in a Day"

- **Best-practice architecture per platform:** The vision includes **reference architectures** for different data platforms and visualization tools (e.g. Microsoft Fabric, other cloud analytics stacks). These are not only "how to model" but **deployable, code-driven setups** (workspaces, datasets, pipelines, lakehouse, report structure) so that analytics can be **set up in a day** — or at least in a predictable, repeatable way — instead of weeks of manual configuration. First full reference: Fabric / Power BI (Aurora); additional platforms follow as adapters to the same framework.
- **Out of the box:** Standardized reports plus platform architecture mean a customer can choose "framework + product + platform X" and get a running, governed analytics environment with minimal customisation, then refine.

### Governance and Data Security (Including Country-Specific Rules)

- **Governance** remains explicit: ownership, change flow, quality gates (Stage 1, Stage 2). As the framework and product are used across customers and regions, **data security and compliance** become part of the design: access control, sensitivity classification, auditability.
- **Country- and region-specific rules:** Data residency, sector regulations (e.g. financial, health), and local data-protection rules (e.g. GDPR and equivalents) must be supported. The framework and platform architectures should allow **configurable governance and security** (e.g. where data lives, who can see what, how long it is retained) so that one procedure and one product can be deployed in a compliant way in different jurisdictions. This is a design goal for governance and platform blueprints, not a single implementation detail.

---

## Versioned Path (How We Reach It Step by Step)

### V1 - Foundation (Current Baseline)
**Goal:** Repeatable, governed delivery without AI in the customer experience. First **fully functioning Microsoft Fabric / Power BI** version (Aurora Group).

**Delivered / required outcomes**
- Core framework artifacts exist (strategy -> KPIs -> use cases -> action codes -> templates).
- Aurora Group reference implementation demonstrates:
  - core use cases end-to-end
  - best-practice semantic modeling and reports (3-30-300, action codes, standardized report templates)
  - closed loop structure (without active AI)
  - foundation for code-driven architecture (setup/teardown by code where applicable)
- **Fabric / Power BI development** includes:
  - semantic model generation (TMDL, PBIP), report templates, action code integration
  - **Power BI Theme Generator** (`products/fabric_powerbi/tooling/theme_generator/`) — generates/standardizes report themes from framework conventions; documented in `products/fabric_powerbi/docs/fabric_powerbi.md` (section 9.4) and tool README
  - alignment with `products/fabric_powerbi/docs/fabric_powerbi.md` and `tooling/` (validation, generation, Power BI MCP)
- **Stage 1 Hard CI Gate** blocks drift:
  - schema validation, refs, ID integrity, SSOT marker rules, forbidden fields, duplicates
- Stage 2 is specified (non-blocking), but not required to run.
- **First, pragmatic governance** — ownership, change flow, Stage 1 as gate; minimal process.

**Exit criteria**
- Aurora Group is demo-ready with core pages and consistent KPI definitions.
- Stage 1 is mandatory in CI and stable (low false positives).
- Fabric/Power BI tooling (including Theme Generator) is documented and part of the implementation guide.

**V1 completion checklist (internal)**

| Criterion | Status | Notes |
|-----------|--------|--------|
| Aurora demo-ready: data, semantic model, "To reproduce" steps | Done | `showcases/aurora_group/`: data/gold, semantic_models, README "To reproduce" with explicit commands (Stage 1, generate_tmdl_measures, run_fabric_checks) |
| Aurora: core use cases represented | Done | COM-001–003, OPS-001, SCM-001, FIN-001 in scope; TMDL generierbar für alle |
| Stage 1 mandatory in CI, documented | Done | README "When to use which"; VSCode task "Run Stage 1 checks (CI gate)"; AGENTS.md |
| Stage 1 stable (low false positives) | Verify | Run `.\tooling\run_stage1_checks.ps1` from repo root before closing V1 |
| Fabric tooling documented in guide | Done | fabric_powerbi.md (entry points, section 11 best practices, section 9.4 Theme Generator); run_fabric_checks, test_tmdl, TMDL_Testing_Guide in tools/README |
| Theme Generator in implementation guide | Done | fabric_powerbi.md §9.4; tools/theme_generator/README; guide/README references theme_generator |

**V1 Finalization (required before V1 is fully closed)**  
V1 is considered complete only when the following are in place for **one tool (Fabric/Power BI)** end-to-end:

1. **Finalized PBI reports** — For each **core use case** in scope (e.g. COM-001, COM-002, COM-003, OPS-001, SCM-001, FIN-001, and optionally XD-003), the Aurora showcase (or equivalent) contains:
   - **Finalized report pages** — One or more pages per use case following 3-30-300 and `core/templates/page_templates/` / `UseCase_PageTemplate_Map.yaml`.
   - **Finalized visuals** — Visuals bound to governed measures only; layout and visual types aligned with page templates and `Visual_Whitelist.md`.
   - **Theme** — Report theme applied consistently (Power BI Theme Generator output or equivalent); theme documented and repeatable.
2. **Report Documentation Generator** — A tool or script that produces **report documentation** from the PBIP/report (e.g. list of pages, visuals per page, theme used, link to use case and action codes). Output is human-readable (e.g. Markdown) and can be stored in the repo or delivered with the report. Purpose: traceability, onboarding, and governance (what this report contains and why).

**V1 Finalization checklist (internal)**

| Criterion | Status | Notes |
|-----------|--------|--------|
| Finalized pages per core use case | Open | COM-001, COM-002 scaffolds (overview + detail) in Aurora; COM-003, OPS-001, SCM-001, FIN-001 to be added. Pages follow 3-30-300 and UseCase_PageTemplate_Map. |
| Finalized visuals bound to measures only | Open | No ad-hoc calculations in report; visuals use semantic model measures (binding in PBI pending for finalized reports) |
| Theme applied and documented | Done | Theme Generator in tools/theme_generator/; apply_report_theme.py; fabric_powerbi.md §9.4 and §9.4 theme-applied doc |
| Report Documentation Generator | Done | Tool: `tools/report_documentation_generator/generate_report_documentation.py`; PBIP → Markdown (metadata, questions, pages, visuals, traceability); run for COM-001; output in showcases/aurora_group/reporting/Report_Documentation_COM-001.md; doc in fabric_powerbi.md §9.5 |

**After V1 Finalization: Fabric/Power BI Best Practice Architecture**  
Once finalized PBI reports and Report Documentation Generator are done, the **next step** is to document and, where possible, automate the **Best Practice Architecture for Fabric/Power BI** so that all core use cases are delivered **end-to-end for one tool**, including action codes (closed loop). This includes:

- **Workspaces** — Structure (e.g. Dev/Test/Prod), naming, and assignment.
- **Pipelines and OneLake** — Data flow from source/lakehouse to semantic model; parameterized paths; deployment.
- **Deployment** — Code-driven setup/teardown (e.g. Bicep, Fabric APIs) so that workspace, semantic model, and report can be provisioned in a repeatable way.
- **Closed loop** — Reports and, where applicable, an action layer or drill-through clearly reference action codes; action code definitions remain in `core/action_codes/`; traceability from KPI deviation → use case → action code is documented and visible.

**V1 closed (full):** Stage 1 and Fabric checks green; finalized PBI reports (pages, visuals, theme) for core use cases; Report Documentation Generator available; Fabric/Power BI Best Practice Architecture section in guide (workspaces, pipelines, OneLake, deployment, closed loop). Then: V2 (Stage 2 Soft Review) or further platform expansion as needed.

---

### V2 - Assisted Quality (Soft Review + Authoring Assist)
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

### V3 - Guided Automation (Template Instantiation + Partial Closed Loop)
**Goal:** Reduce manual build effort while keeping governance deterministic.

**What changes**
- **Generators** for full artifact coverage (vision: no manual TMDL/PBIP for standard patterns):
  - **Semantic model:** tables (columns, data types), relationships (unique IDs, cardinality), partitions (M with parameterized paths, e.g. GoldDataPath), RLS (security tables, `securityFilteringBehavior: oneDirection`), measures (already: `generate_tmdl_measures.ps1`).
  - **Reports:** report pages, visuals, layouts from 3-30-300 templates and layout_330300.
  - All generators emit artifacts that conform to validation (Stage 1, Fabric checks, PBIP readiness).
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

### V4 - Assisted Operations (Observability + Recommendations at Scale)
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

### V5 - Assisted Consumption (Conversational Layer on Semantic)
**Goal:** Add a conversational consumer experience safely.

**What changes**
- AI consumes the semantic layer and produces:
  - explanations of KPIs and deltas
  - guided exploration ("why did margin drop?") using governed measures only
  - suggested actions mapped to governed action codes
- Strict constraints:
  - no new measures defined at runtime
  - no hidden logic outside the semantic layer

**Exit criteria**
- Customers can explore insights conversationally without inconsistent definitions.
- "Explainability" remains aligned with governed artifacts.

---

### V6 - Orchestrated Autonomy (Vision)
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

## Continuous Learning and Self-Correction

**Principle:** The framework should **learn from every failure** and **prevent recurrence** without relying on human memory. Over time, the system becomes more robust by encoding past fixes into rules and, where feasible, into automatic correction.

### How it works today (V1)

1. **Failure → validation rule:** When a defect is fixed (e.g. duplicate relationship ID, hardcoded partition path, RLS `bothDirections`, duplicate measure name), a **validation check** is added (e.g. `check_tmdl_pbip_readiness.ps1`) so the same pattern fails CI and cannot be reintroduced.
2. **Documentation:** The fix and the rule are documented (e.g. `tmdl_best_practices.md` §5.4 and §9.4) so generators and humans follow the same constraints.
3. **Single source of truth:** Measure dictionaries, KPI catalog, and action codes remain the authority; generators and validation reference them.

### Target state: self-correcting loop

- **Generate** artifacts from governed sources (templates, KPI catalog, data contracts).
- **Validate** with Stage 1 and Fabric checks (including PBIP readiness).
- **On failure:**
  - **Classify** the failure (e.g. known pattern: hardcoded path, duplicate ID).
  - **Correct** where a safe, deterministic fix exists (e.g. replace path with `GoldDataPath`; deduplicate measure definitions; set RLS to `oneDirection`).
  - **Re-validate** until green or until no automatic fix applies (then fail and report).
- **Learn:** New failure patterns are turned into new validation rules and, where possible, into corrective steps or generator constraints for the next release.

This does **not** mean AI invents new logic: corrections are limited to **structural and syntactic** fixes that are defined in code (validation scripts, fix scripts, generator defaults). Business logic (KPI definitions, measure formulas, action triggers) remains governed and human-approved.

### Generators (vision)

To minimize manual TMDL/PBIP and report authoring, the following **generators** are in scope (current state → target):

| Artifact | Current | Target |
|----------|--------|--------|
| Measures | `generate_tmdl_measures.ps1` | Extended; no duplicate names; displayFolder from use case. |
| Tables | Manual / MCP | Generator: columns, data types, lineage from data contract; no `description` on columns. |
| Relationships | Manual / MCP | Generator: unique GUIDs, cardinality from model; RLS relationships `oneDirection`. |
| Partitions | Manual | Generator: M from template; **parameterized path only** (e.g. GoldDataPath). |
| RLS | Manual | Generator: security table + relationship from model; `securityFilteringBehavior: oneDirection`. |
| Report pages / visuals | Manual / Theme Generator | Generator: pages and visuals from layout_330300 and page templates. |

All generated output must pass Stage 1 and Fabric checks (including PBIP readiness). New validation rules are added whenever a new failure pattern is fixed.

---

## Practical "How We Get There" (Concrete Steps)

### Step 1 - Finalize V1 (Reports, Theme, Report Doc Generator)
- Finish the Aurora Group reference as a tactile demo (Fabric / Power BI). **Done:** Aurora README "To reproduce", data/gold, semantic_models; scope COM-001–003, OPS-001, SCM-001, FIN-001.
- Ensure Stage 1 is stable and mandatory. **Done:** README, AGENTS.md, VSCode task; run once to verify green before closing V1.
- Include **Power BI Theme Generator** in Fabric/Power BI development: document in implementation guide, refine as needed, align with report templates and BaseThemes. **Done:** Theme Generator in `products/fabric_powerbi/tooling/theme_generator/`; documented in fabric_powerbi.md §9.4; BaseThemes example in `showcases/sample_pbip_report/` (StaticResources/SharedResources/BaseThemes/).
- **V1 Finalization (to do):** Deliver **finalized PBI reports** for core use cases (COM-001, COM-002, COM-003, OPS-001, SCM-001, FIN-001, optionally XD-003) with finalized **pages and visuals** (3-30-300, governed measures only), **theme** applied and documented, and a **Report Documentation Generator** (PBIP/report → human-readable report doc: pages, visuals, theme, use case/action code refs).
- Keep documentation minimal and consistent. **Done:** Evaluation 2026-02 recommendations implemented; outdated working docs removed.

### Step 1b - Fabric/Power BI Best Practice Architecture (after V1 Finalization)
- Document and, where possible, automate **Best Practice Architecture for Fabric/Power BI**: workspaces (e.g. Dev/Test/Prod), pipelines, OneLake, code-driven deployment (e.g. Bicep, Fabric APIs).
- Ensure **closed loop** for one tool: core use cases end-to-end including **action codes** (reports and/or action layer reference action codes; traceability from KPI → use case → action code is documented).
- Outcome: All core use cases for Fabric/Power BI are finalized end-to-end with action codes; new environments can be set up in a repeatable way.

### Step 2 - Introduce Stage 2 Soft Review as a Non-Blocker
- Start with "diff-only" and "max 10 findings".
- Iterate until noise is low and signal is high.

### Step 3 - Automate Scaffolding, Not Decisions
- Generate skeletons (contracts, model scaffolds, page scaffolds).
- Keep decision logic (KPI meaning, triggers) governed and human-owned.

### Step 4 - Standardize Operations Before AI Consumption
- Add health/observability conventions first.
- Then use AI for triage and recommendations.

### Step 5 - Add Conversational Consumption Only After Semantic Maturity
- AI uses governed measures only.
- No "creative analytics" in production contexts.

---

## World-Class Foundation (Phase A & B)

To set the foundation for a world-class framework, the following conceptual and content artifacts are in place. They support repeatability, clarity, and adoption without changing technical evolution (V1–V6).

**Phase A — Solid foundation**

- **Ownership/RACI for the Golden Thread:** `core/strategy_operating_model/operating_model/ownership_raci_golden_thread.md` — Who is accountable and responsible for strategy, KPIs, use cases, action codes, semantic model, reports.
- **Key questions:** Use Case Inventory no longer uses "TBD" for key questions; column "Key Questions (summary)" is populated for all 15 core use cases; full list in section "Key Questions by Use Case" in `core/usecases/UseCase_Inventory.md`. Business Factsheets already contain "Core Business Questions" (section 2).

**Phase B — Reference content and patterns**

- **Strategy patterns:** `core/strategy_operating_model/company/strategy_patterns.md` — Margin-First, Cash-First, Growth-First with linked Strategic KPIs and use-case clusters.
- **Decision taxonomy:** `core/strategy_operating_model/operating_model/decision_taxonomy.md` — Decision types (Steer, Diagnose, Allocate, Forecast, Intervene) and mapping to use cases and action codes.
- **KPI taxonomy:** `core/kpi_catalog/KPI_Taxonomy.md` — Readable, domain-oriented summary of the KPI catalog for discovery and onboarding.
- **Action code patterns:** `core/action_codes/Action_Code_Patterns.md` — Recurring action types (Governance, Control, Allocate, Escalate) and mapping to action code groups.
- **Maturity model:** `core/strategy_operating_model/operating_model/maturity_model_action_ready_analytics.md` — Five levels from descriptive reporting to measured impact and learning; mapping to framework artifacts.
- **Implementation playbook:** `core/implementation_guides/playbook_strategy_to_first_report.md` — Step-by-step from strategy pattern to first report (Greenfield path); references Fabric/Power BI where applicable.

**Broader vision (conceptual, domain, content):** `internal/vision/world_class_vision_brainstorm.md` — Phases C–E (breadth, proof, world-class standard) and further ideas for strategy, domains, and content.

---

## Success Metrics (Non-Technical)

- **Repeatability:** same package produces consistent outcomes across customers.
- **Speed:** faster MVP delivery without sacrificing quality.
- **Stability:** drift incidents decrease over time (Stage 1 + Stage 2 effectiveness).
- **Clarity:** fewer review debates about definitions and authority.
- **Adoption:** customers can understand and use the outputs without heavy enablement.

---

## Out of Scope (What We Do Not Pursue Here)

To keep the vision focused and avoid scope creep:

- **Real-time or streaming analytics** — The framework targets batch/refresh semantic models and reports; event-driven or sub-second streaming is out of scope unless explicitly added later as an extension.
- **Replacement of operational system reporting** — We do not aim to replicate or replace ERP, CRM, or operational tool reporting; we provide a governed, strategy-aligned layer that may consume data from those systems.
- **Full data platform or ERP implementation** — We define contracts, semantics, and report structure; we do not build or own the underlying transactional systems or data engineering beyond what is needed for the semantic layer and pipelines.
- **Generic "data lake" or "data mesh" design** — Data architecture is in scope only where it directly supports the semantic layer, deployment, and governance (e.g. workspace, lakehouse, pipelines for the framework). Broader data strategy is for the customer.
- **Custom commercial or licensing model** — How the procedure or standardized reports are offered (internal use, license, SaaS) is a business decision; the vision describes *what* we build, not the commercial wrapper.

---

## Risks and Assumptions

**Risks we accept or mitigate**

- **Platform dependency:** First full product is Fabric/Power BI; a **second platform adapter** (same framework, different stack) is an explicit goal to prove tool-agnostic design and reduce lock-in. Until then, platform roadmap and API stability affect us.
- **Governance under pressure:** "Governance before automation" can be weakened when delivery pressure is high. Mitigation: Stage 1 as hard gate; ownership and RACI documented; no bypass of quality checks for speed.
- **AI and drift:** AI-assisted authoring or consumption can introduce subtle drift if guardrails are skipped. Mitigation: AI does not invent definitions; all changes pass Stage 1; conversational layer uses only governed measures.

**Assumptions we rely on**

- **Customer willingness to adopt the change flow** — Strategy → KPIs → use cases → semantic model works only if the organization accepts ownership and the Golden Thread. We assume sponsors and domain owners engage.
- **Stable core, extensible edges** — Core framework (KPIs, use cases, action codes) stays relatively stable; industry packs, custom layouts, and new domains extend at the edges without breaking the core.
- **One semantic layer per deployment** — We assume one governed semantic interface per customer or deployment; we do not design for multiple competing semantic layers in the same scope.

---

## Adoption and Feedback

**How adoption is expected to work**

- **Procedure first:** Teams adopt the framework as a procedure (playbooks, use cases, governance) before or alongside any standardized reports. This ensures shared language and ownership; the product layer then lands on a ready base.
- **Pilot then scale:** A single domain or use-case pack is piloted (e.g. Commercial or Finance); success criteria and feedback are collected; then additional domains or the full product are rolled out.
- **Maturity as a guide:** The maturity model helps position "where we are" and "where we want to be"; it supports scoping and avoids overreaching (e.g. Level 4 action codes before Level 3 use cases).

**How feedback flows back into the framework**

- **Missing industry or topic:** Requests for industry-specific or new-domain content are captured; they drive extensions (industry packs, new use cases) that reference the same governance. Core artifacts are updated only when the change benefits all or most customers.
- **Layout or UX preference:** Custom layout needs are supported within "custom layout, governed meaning"; repeated patterns can be turned into optional templates or variants (e.g. alternative to 3-30-300) without changing the invariant that reports consume the semantic layer only.
- **Failure and validation:** Defects and near-misses are turned into validation rules (Stage 1, Fabric checks) and, where applicable, into generator constraints or documentation so the same issue does not recur. (See "Continuous Learning and Self-Correction.")

---

## Recommended Sequence (When Resources Are Limited)

A pragmatic order to develop and deliver the vision without doing everything at once:

1. **Procedure and one platform** — Lock the procedure (playbooks, use cases, governance, Stage 1) and one full platform reference (Fabric/Power BI). This is V1 + Phase A/B. Everything else builds on this.
2. **V1 Finalization (one tool, end-to-end)** — Finalized PBI reports for core use cases (pages, visuals, theme) and Report Documentation Generator; then **Fabric/Power BI Best Practice Architecture** (workspaces, pipelines, OneLake, deployment, closed loop with action codes). Outcome: all core use cases for Fabric/Power BI are deliverable end-to-end.
3. **Standardized reports product** — Package pre-built reports (by domain or strategy pattern) that conform to the framework. Enables "framework + product" and faster time to value.
4. **Platform architecture and "analytics in a day"** — Extend deployable setup so new environments can be provisioned in a day. Extend to a **second platform** when the first is stable.
5. **Lifecycle and flexibility** — Impact awareness, versioning, industry extensions, custom layout support. Keeps the framework relevant as strategies and requirements change.
6. **Automation and AI** — Stage 2, generators, AI-assisted maintenance, conversational consumption. Only after semantic and governance maturity.
7. **Governance depth and country-specific rules** — Configurable security, residency, and compliance as the framework and product are used across regions and regulated sectors.

This order is a guideline, not a contract; steps can overlap or be reordered where it makes sense (e.g. early scoping of country rules if a specific market is in focus).

---

## Definition of Done for This Vision Document

- [x] Internal-only direction, no customer promises
- [x] Step-by-step evolution without timelines
- [x] Clear invariants (what must never change)
- [x] Separation of hard gates vs soft guidance
- [x] Tool-agnostic, implementation as adapter
- [x] Framework roles (procedure vs standardized product) and customer choice articulated
- [x] BI lifecycle, flexibility (strategy change, industry, custom layout), and AI (maintenance, consumer, coverage) described
- [x] Platform architecture ("analytics in a day") and governance/data security (including country-specific rules) as design goals
- [x] Out of scope, risks/assumptions, adoption/feedback, and recommended sequence documented
