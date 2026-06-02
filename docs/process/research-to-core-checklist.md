# Research-to-Core Checklist

> **Purpose:** Step-by-step execution checklist for agents and humans.  
> **Standard:** `docs/process/research-to-core-standard.md`  
> **Applies to:** Every new or substantially revised standard use case.

---

## How to Use

Work through each section in order. All mandatory items must be checked before moving to the next phase.
Optional items are marked `(opt)`.

---

## Phase 1 — Domain Scoping

- [ ] Business process named and bounded (what is in scope, what is explicitly out of scope)
- [ ] Industry segment and company context defined (discrete mfg, process mfg, B2B services, etc.)
- [ ] Applicable domain frameworks identified (SCOR, APQC PCF, ISO 22400, IFRS, etc.)
- [ ] Target decision frequency confirmed (daily, weekly, monthly)
- [ ] (opt) Cross-use-case dependencies noted

---

## Phase 2 — Source Inventory

- [ ] At least 10 sources identified (target 15)
- [ ] At least 5 of 6 source categories covered (STD + BNK mandatory)
- [ ] Every source scored ≥ 8/15
- [ ] Portfolio score ≥ 10/15
- [ ] Every source has: URL or DOI, publication date, and list of extraction fields it supports
- [ ] Conflicting sources documented with chosen position justified

Source category coverage:

| Category | ID | Covered? |
|----------|----|----------|
| Standards & Frameworks | STD | [ ] |
| Academic / Systematic | ACA | [ ] |
| Professional Bodies | PRO | [ ] |
| Benchmark / Targets | BNK | [ ] |
| Practitioner / Implementation | IMP | [ ] |
| Anti-Pattern / Risk | RSK | [ ] |

---

## Phase 3 — Extraction Completeness

Mandatory fields extracted:

- [ ] `process_scope` — business process scope statement
- [ ] `outcome_kpis` — top-level success/failure KPIs with definitions
- [ ] `driver_kpis` — causal second-level KPIs
- [ ] `diagnostic_kpis` — third-level root-cause KPIs
- [ ] `guardrails` — conditions where action must NOT be triggered
- [ ] `required_dimensions` — full dimension list needed for meaningful slicing
- [ ] `required_grain` — minimum and preferred data grain
- [ ] `actions_by_root_cause` — action logic seeds per driver/diagnostic combination
- [ ] `wrong_interpretations` — at least 3 documented anti-patterns
- [ ] `benchmark_targets` — at least 1 quantified industry benchmark per outcome KPI
- [ ] `evidence_sources` — complete scored source inventory

Optional (check if applicable):

- [ ] (opt) `causal_chain` documented
- [ ] (opt) `seasonality_patterns` noted
- [ ] (opt) `leading_indicators` identified
- [ ] (opt) `cross_use_case_links` declared

---

## Phase 4 — Canonical Domain Model

- [ ] Driver tree produced (outcome → driver → diagnostic, with causal direction)
- [ ] Required grain and dimension set summarised
- [ ] Top 3–5 action patterns with trigger conditions written
- [ ] Top 3 wrong interpretations / guardrails documented
- [ ] One-page domain model review-ready

---

## Phase 5 — Core Mapping

For each evidence item:

- [ ] KPI Catalog checked — does an entry already exist or is one needed?
- [ ] Business Factsheet checked — are all core business questions covered?
- [ ] UseCase Bracket checked — does it support required visuals, evidence columns, and slicers?
- [ ] Semantic model checked — do required facts, dimensions, grain, and measures exist?
- [ ] Action Codes checked — are trigger conditions, guardrails, and outcomes expressible?

---

## Phase 6 — Gap Classification

Every mismatch classified as one of:

| Gap Type | Description | Next Step |
|----------|-------------|-----------|
| `content_gap` | Schema can express it; content is missing | Add content directly |
| `mapping_gap` | Content exists but is wired to wrong KPI/visual/action/grain | Rewire in bracket/factsheet |
| `schema_gap` | Core schema cannot express required semantics | **Stop — produce Schema Gap Report** |
| `generator_gap` | Schema/content sufficient; generator ignores it | Fix generator |
| `model_gap` | Semantic model lacks required table/measure/grain | Add to semantic model or data contract |

- [ ] All gaps classified
- [ ] Zero unresolved `schema_gap` items (each must have an approved Schema Gap Report or be resolved)

---

## Phase 7 — Core Content Update

- [ ] Only content/mapping/generator/model gaps addressed (no unilateral schema changes)
- [ ] Domain Evidence Pack referenced in Bracket `documentation` field
- [ ] Factsheet Business Summary, Core Questions, Risks, and Success Criteria updated if gaps found
- [ ] KPI Catalog entries added or updated where `content_gap` found
- [ ] Action Codes added or updated where `content_gap` found
- [ ] Semantic model requirements documented in data contract

---

## Phase 8 — Validation

- [ ] Stage 1 checks pass
- [ ] Fabric / PBIR checks pass (if report generated)
- [ ] Semantic Quality Gate score computed
- [ ] Source coverage threshold met (≥ 10 scored sources)
- [ ] Gap report produced and attached
- [ ] (Showcase use cases) Aurora Proof Dossier entry completed

---

## Sign-Off

| Role | Name / Agent ID | Date |
|------|----------------|------|
| Use Case Author | | |
| Reviewer | | |
| Framework Architect (if schema gap) | | |
