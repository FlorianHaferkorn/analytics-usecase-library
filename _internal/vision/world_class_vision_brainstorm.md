# World-Class Vision — Conceptual, Domain & Content Brainstorm

> **Purpose:** Business, domain, and content ideas to evolve the framework from "solid" to "world-class."  
> Technical evolution remains in `framework_evolution.md`; this document focuses on *what* we offer and *how* companies succeed.

**Vision alignment:** The framework has **two roles** (procedure vs standardized reports product) and supports **customer choice** (framework only, framework + some/all pre-built reports). It also addresses **BI lifecycle** (strategy/report change, industry extensions, custom layouts), **platform architecture** ("analytics in a day"), and **governance/data security** (including country-specific rules). See `framework_evolution.md`: "Framework Roles and Product Layers" and "BI Lifecycle, Flexibility, and Intelligence" (including platform architecture and governance).

---

## 1. What "World-Class" Means Here

World-class is not "most features." It means:

- **Recognized** — The approach is cited, adopted, or used as a reference by other organizations or in industry discussions.
- **Complete** — Strategy → KPIs → use cases → actions is fully populated, consistent, and usable out of the box for core domains.
- **Proven** — There is evidence (cases, benchmarks, or repeatable outcomes) that adoption improves decision quality, speed, or efficiency.
- **Differentiated** — The combination of "one semantic interface + action-ready + decision-oriented" is explicit, governed, and reusable in a way that general BI tooling does not provide.
- **Extensible** — New domains, industries, or use cases can be added without breaking the Golden Thread; the pattern is clear and documented.

So the goal is: **the default reference for action-ready, strategy-aligned analytics** in the spaces we choose to cover.

---

## 2. Strategic & Conceptual Ideas

### 2.1 Strategy Patterns, Not Only One Strategy

- **Reference strategy patterns** — e.g. "Growth-first," "Margin-first," "Cash-first," "Customer-centric." Each pattern defines a small set of strategic KPIs, trade-offs, and priority order. Companies pick or blend patterns; the framework supplies the structure and the KPI/use-case mapping.
- **Why:** Companies struggle to go from "we want to be better" to "here are the 5 KPIs we steer on." Predefined patterns reduce blank-page syndrome and align analytics to strategy from day one.
- **Step:** Document 2–3 strategy patterns in the company layer (or a subfolder); link each to Strategic KPIs and to use-case clusters. No new artifact type—extend existing company/strategy content.

### 2.2 Decision Taxonomy, Not Only Use Cases

- **Explicit decision types** — e.g. "Steer," "Diagnose," "Allocate," "Forecast," "Intervene." Map use cases and action codes to these types. Clarifies *how* analytics supports decisions (not just *what* we report).
- **Why:** Helps companies and AI understand "this use case is for diagnosis, that one for allocation." Improves prioritization and UX (e.g. 3-30-300 can be tagged by decision type).
- **Step:** Add a short decision taxonomy to the operating model or glossary; add optional `decision_type` to use case metadata and templates.

### 2.3 Key Questions as First-Class Content

- **Key questions per use case (and per strategy pattern)** — Today key questions are conceptual in the Golden Thread; only partially filled in the inventory (e.g. "TBD"). Populate "Key Questions" for each core use case and link them to Strategic KPIs.
- **Why:** Key questions are the bridge from "KPI moved" to "what to do." Rich key questions improve adoption and make AI explanations more targeted.
- **Step:** Replace "TBD" in Use Case Inventory and factsheets with 3–5 key questions per use case; optionally add a `key_questions` section to Business Factsheet schema.

### 2.4 Maturity Model for Action-Ready Analytics

- **Staged maturity** — e.g. Level 1: Descriptive reporting; Level 2: Diagnostic with clear KPIs; Level 3: Decision-oriented use cases; Level 4: Action codes and closed loop; Level 5: Measured impact and learning. Publish as a one-pager or appendix.
- **Why:** Gives companies a shared language for "where we are" and "where we want to be." Supports scoping and roadmap discussions.
- **Step:** Add `_internal/vision/` or `framework/strategy_operating_model/` doc: maturity levels, criteria, and how they map to framework artifacts (use cases, action codes, semantic layer).

### 2.5 Ownership and RACI for the Golden Thread

- **Clear ownership** — Who owns strategy input? KPI definitions? Use case content? Action code logic? Semantic model? One RACI or ownership matrix tied to the Golden Thread.
- **Why:** "Governance before automation" and "first, pragmatic governance" only work if ownership is explicit. Reduces ambiguity in cross-team adoption.
- **Step:** Add an ownership/RACI section to the operating model or company layer; reference it from AGENTS.md and framework_evolution.md.

---

## 3. Domain & Coverage Ideas

### 3.1 Cross-Domain Use Cases

- **Use cases that explicitly span domains** — e.g. "Margin bridge (Commercial + Finance + SCM)," "End-to-end service delivery (XD + OPS + SCM)," "Working capital (FIN + SCM)." Today domains are separate; cross-domain use cases make trade-offs and handoffs explicit.
- **Why:** Many decisions are cross-domain. Making them first-class prevents siloed reporting and clarifies ownership (e.g. one primary domain, others as contributors).
- **Step:** Define 2–3 cross-domain use cases in the inventory; document how they reference KPIs and action codes from multiple domains; keep one "primary" domain for ownership.

### 3.2 Industry Variants (Extended/Industry)

- **Industry-specific packs or overlays** — e.g. Manufacturing, Retail, Professional Services, Public Sector. Each adds industry KPIs (or aliases), use-case variants, and optional action codes without replacing the core.
- **Why:** "Implemented repeatedly across companies with different realities" requires industry relevance. Core stays tool-agnostic; industry adds context and naming.
- **Step:** Document "Industry extension" in the vision; add one industry as a pilot (e.g. Manufacturing): extra KPIs, 2–3 use-case variants, and a short "how we extended" playbook.

### 3.3 Executive and Board Layer

- **Executive/board use case** — XD-003 is a start. Expand to a small set of "C-level views": one page per strategic priority (e.g. growth, margin, cash, risk, people). Each view is 3-30-300 and links to underlying use cases and action codes.
- **Why:** Leadership adoption is critical. A dedicated, thin layer that aggregates only governed KPIs and links to drill-through keeps the Golden Thread visible at the top.
- **Step:** Treat XD-003 as the template; add 1–2 more "executive views" (e.g. cash & liquidity, risk & compliance) with clear KPI and use-case links.

### 3.4 Risk, Compliance, Sustainability (ESG)

- **Risk and compliance** — KPIs and use cases for operational risk, control effectiveness, audit readiness. Optional action codes (e.g. "Escalate," "Remediate").
- **Sustainability / ESG** — Carbon, energy, waste, or social metrics as first-class KPIs and one or two use cases (e.g. "Carbon footprint steering," "ESG reporting pack"). Many companies need this; keeping it in the same Golden Thread avoids a second, disconnected analytics stack.
- **Why:** Completeness and relevance. World-class coverage includes risk and ESG where the market demands it.
- **Step:** Add a domain or sub-domain (e.g. Risk & Compliance, Sustainability); add 1–2 use cases and a small KPI set; link to action codes where it makes sense.

### 3.5 People and Organization

- **People/HR analytics in the same thread** — Attrition risk, capacity, skills, adoption (e.g. digital adoption). XD-003 already references people KPIs; full use cases (e.g. "Workforce planning," "Attrition risk") would complete the picture.
- **Why:** Many strategies depend on people and culture. Aligning people metrics with the same governance and semantic layer avoids "HR analytics over there, rest here."
- **Step:** Add a small People/Org domain or extend XD; add 1–2 use cases and KPIs; link to strategy patterns (e.g. "Customer-centric" often includes people/experience).

---

## 4. Content & Substance Ideas

### 4.1 Reference KPI Set and Taxonomy

- **Canonical KPI taxonomy** — Hierarchical: Domain → Topic → Metric (already partially there). Publish a clean, readable taxonomy (e.g. one page per domain) with definition, unit, owner, and "used in use cases X, Y, Z."
- **Why:** Single source of truth is only world-class if it is also discoverable and understandable. A taxonomy speeds onboarding and AI grounding.
- **Step:** Generate or curate "KPI taxonomy" views from the catalog; add to framework docs or a simple catalog site; keep glossary aligned.

### 4.2 Action Code Library and Patterns

- **Action patterns** — Recurring action types: "Review and decide," "Escalate," "Replan," "Adjust price," "Schedule maintenance." Document as patterns; action codes implement them. Enables "which actions does the framework support?" and consistent naming.
- **Why:** Action codes are a differentiator. A clear library and pattern set makes the closed loop understandable and extendable.
- **Step:** Add a short "Action code patterns" doc in `framework/action_codes/` or operating model; optionally tag action codes with pattern; ensure UseCase_ActionCode_Map and Rationale stay the single source of truth.

### 4.3 Expected Impact and Success Criteria per Use Case

- **Quantified expected impact** — Inventory already has "Expected Impact" as prose. Tighten to "e.g. +0.5–1.5 pp GM," "fewer re-plans," "higher OTIF." Add optional "success criteria" (how we measure that the use case is working).
- **Why:** Helps prioritization and business cases. "What do we get if we implement this?" becomes answerable.
- **Step:** Refine Expected Impact in Use Case Inventory and Business Factsheets; add optional `success_criteria` or `expected_outcome` to schema/template; document in DoD.

### 4.4 Playbooks: From Strategy to Go-Live

- **Implementation playbooks** — Step-by-step: "Define or choose strategy pattern" → "Select use-case pack" → "Map to data contracts" → "Build semantic model" → "Deploy reports and actions." One playbook per entry path (e.g. "Greenfield," "Existing BI migration").
- **Why:** Repeatability and speed. World-class means a new team can follow a playbook and reach a consistent outcome.
- **Step:** Add `framework/implementation_guides/` or extend existing guide with 1–2 playbooks; link to Golden Thread, use cases, and implementation docs.

### 4.5 Benchmarks and Norms (Optional)

- **Benchmark or norm ranges** — Where sensible, document "typical" or "target" ranges for KPIs (e.g. OEE, CCC, OTIF) by industry or context. Clearly label as reference, not contractual.
- **Why:** Supports "are we in range?" and prioritization. Use with care to avoid gaming or over-reliance.
- **Step:** Optional appendix or separate "norms" artifact; link to KPI catalog as reference only; keep targets company-specific in strategy.

### 4.6 Case Studies and Outcome Stories

- **Lightweight case studies** — 1–2 pages per story: situation, what was implemented (strategy pattern, use cases, actions), outcome (speed, quality, alignment). Aurora Group can be the first "reference implementation story."
- **Why:** Proof and adoption. "Others achieved X with this approach" supports internal and external adoption.
- **Step:** Add a "Cases" or "Stories" area (e.g. `showcases/` or `_internal/vision/`); start with Aurora as the first written case; template for future cases.

---

## 5. Company Success Levers (How We Help Companies Win)

### 5.1 Faster Time to Value

- **Pack-based deployment** — Deploy by use-case pack (e.g. Commercial pack, Finance pack) instead of one-off projects. Reduces time from "we want margin steering" to "we have it" with consistent quality.
- **Step:** Already in vision (packages). Implement as versioned packs and document "how to deploy pack X" in playbooks.

### 5.2 Fewer Debates, One Truth

- **Single semantic interface** — Already an invariant. Emphasize in positioning: "One definition of margin, one definition of OTIF; reports and AI use the same."
- **Step:** Make this explicit in README, vision, and any customer-facing summary; link to KPI catalog and measure system.

### 5.3 Decision Quality and Traceability

- **Traceability** — From a number on a report back to: measure → KPI → use case → key question → strategy. Document how this works and, where tooling exists, expose it (e.g. lineage, impact).
- **Step:** Conceptual description in Golden Thread; technical lineage/impact in framework_evolution (as previously brainstormed).

### 5.4 Change Management and Adoption

- **Adoption path** — Glossary → Strategy (or pattern) → KPI catalog → Use cases → Reports → Actions. Publish as "how to adopt" and "how to onboard new users."
- **Step:** Add to operating model or implementation guide; optional "adoption checklist" per use case or pack.

### 5.5 Measured Framework Success

- **Framework success metrics** — e.g. "Time to first governed report," "Number of use cases in production," "Action code usage (views/triggers)." Define a small set and, where possible, measure in showcases or pilots.
- **Step:** Add to framework_evolution "Success metrics" or world-class doc; keep simple and avoid vanity metrics.

---

## 6. Step-by-Step Path to World-Class

A phased path keeps the vision actionable without committing to dates. Each phase builds on the previous.

### Phase A — Solid Foundation (Align with V1)

**Goal:** Framework is internally consistent, demo-ready, and governance is clear.

- [x] Golden Thread fully documented and linked (strategy → KPIs → use cases → actions).
- [x] Core use cases (current 15) with complete factsheets, key questions no longer "TBD," and expected impact stated (Key Questions column and full list in Use Case Inventory).
- [x] Stage 1 mandatory; Fabric/Power BI reference (Aurora) stable and reproducible.
- [x] Ownership/RACI for framework artifacts documented: `operating_model/ownership_raci_golden_thread.md`.

**Exit:** A new team can understand the Golden Thread, run the showcase, and know who owns what. **Done.**

---

### Phase B — Reference Content and Patterns

**Goal:** Strategy and domain content are rich enough to be reused, not just structure.

- [x] 2–3 **strategy patterns** (Margin-first, Cash-first, Growth-first) with linked KPIs and use-case clusters: `company/strategy_patterns.md`.
- [x] **Key questions** populated for all core use cases (inventory + factsheets); strategy patterns include example key questions.
- [x] **Decision taxonomy** (Steer, Diagnose, Allocate, Forecast, Intervene) defined and mapped to use cases/action codes: `operating_model/decision_taxonomy.md`.
- [x] **KPI taxonomy** (`kpi_catalog/KPI_Taxonomy.md`) and **action code patterns** (`action_codes/Action_Code_Patterns.md`) documented.
- [x] **Maturity model** (five levels, mapping to artifacts): `operating_model/maturity_model_action_ready_analytics.md`.
- [x] **One implementation playbook** ("From strategy to first report"): `framework/implementation_guides/playbook_strategy_to_first_report.md`.

**Exit:** A company can choose a strategy pattern, see which use cases and KPIs apply, and follow a playbook to implement. **Done.**

---

### Phase C — Breadth and Relevance

**Goal:** Coverage and relevance sufficient for "default reference" in chosen domains/industries.

- [ ] **Cross-domain use cases** (2–3): e.g. margin bridge, working capital, end-to-end service; documented in inventory and linked to multiple domains.
- [ ] **Executive/board layer** explicit: XD-003 plus 1–2 more C-level views (e.g. cash, risk) with 3-30-300 and links to underlying use cases.
- [ ] **One industry variant** (e.g. Manufacturing): extra KPIs, 2–3 use-case variants, "how we extended" doc.
- [ ] **Risk or ESG**: 1 domain or sub-domain, 1–2 use cases, small KPI set; optional action codes.
- [ ] **People/org**: 1–2 use cases (e.g. workforce planning, attrition risk) and KPIs linked to strategy and XD.

**Exit:** The framework covers strategy, operations, finance, commercial, supply chain, experience, and at least one of risk/ESG/people in a coherent way; one industry is shown as an extension.

---

### Phase D — Proof and Recognition

**Goal:** Evidence and visibility that the approach works and is reusable.

- [ ] **Aurora Group case study** (1–2 pages): situation, what was implemented, outcomes (speed, consistency, alignment).
- [ ] **Framework success metrics** defined and, where possible, measured (e.g. time to first report, use cases in production).
- [ ] **Benchmarks/norms** (optional): reference ranges for selected KPIs, clearly labeled; or "how to add benchmarks" guide.
- [ ] **External or partner use**: at least one other deployment or partner reference (internal or external) that follows the same Golden Thread and packs.

**Exit:** There is a written case, measurable success criteria, and at least one additional proof point beyond Aurora.

---

### Phase E — World-Class Standard (Ongoing)

**Goal:** The framework is the go-to reference for action-ready, strategy-aligned analytics in its scope.

- [ ] **Second industry** (or second implementation stack) documented as extension/adapter; compatibility and gaps clear.
- [ ] **Community or ecosystem**: contributions, feedback loop, or adoption by more teams/customers; lightweight governance for contributions.
- [ ] **Thought leadership**: maturity model, playbooks, and taxonomy are stable and cited; optional certification or training path.
- [ ] **Continuous refresh**: strategy patterns, use cases, and KPIs reviewed periodically; deprecation and sunset process in place.

**Exit:** The framework is recognized, complete in scope, proven with cases, and extended in a governed way.

---

## 7. How This Ties to framework_evolution.md

- **V1 (Foundation)** ↔ **Phase A** — Same baseline: governance, Stage 1, Aurora, ownership.
- **V2–V3 (Assisted quality, scaffolding)** ↔ **Phase B–C** — Technical enablement (Stage 2, generation) supports richer content and packs; content work (strategy patterns, playbooks) is independent but parallel.
- **V4–V6 (Operations, consumption, autonomy)** ↔ **Phase D–E** — Observability and AI consumption support proof (metrics, usage) and recognition (conversational layer, automation within guardrails).

Recommendation: Keep **framework_evolution.md** as the technical and product-version path; add a **"World-class direction"** section (or link to this brainstorm) that summarizes Phases A–E and the main conceptual/domain/content ideas. Optionally move this brainstorm into `_internal/vision/` as a living doc and trim the vision to a short "strategic direction" that points to it.

---

## 8. Definition of Done for This Brainstorm

- [x] Conceptual, domain, and content ideas captured (not only technical).
- [x] Step-by-step path (Phases A–E) from solid foundation to world-class.
- [x] Each idea has a "why" and a concrete "step."
- [ ] Prioritization: which phases and ideas to adopt first (to be decided).
- [ ] Integration: which parts go into framework_evolution.md vs a separate world-class vision doc (to be decided).
