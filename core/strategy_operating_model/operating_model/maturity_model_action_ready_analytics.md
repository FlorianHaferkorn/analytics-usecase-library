# Maturity Model: Action-Ready Analytics

## 1. Purpose

This document defines **five maturity levels** for action-ready, strategy-aligned analytics. It gives organizations a shared language for "where we are" and "where we want to be," and supports scoping, roadmap, and investment discussions.

Levels are **cumulative**: each level assumes the previous one is in place.

---

## 2. Maturity Levels

### Level 1 — Descriptive Reporting

**What you have:** Reports that show what happened. KPIs may exist but are not consistently defined or owned; definitions can differ by report or team.

**Typical state:**

- Dashboards and spreadsheets with revenue, cost, or operational metrics.
- No single KPI catalog; no formal link from strategy to reports.
- Actions are ad hoc; no standardized response to deviations.

**Framework artifacts:** None or partial (e.g. some KPIs in a list). Use cases and action codes are not used.

---

### Level 2 — Diagnostic with Clear KPIs

**What you have:** A governed set of KPIs with single definitions and clear ownership. Reports use these KPIs; deviations can be explained by drivers (e.g. price, volume, mix).

**Typical state:**

- KPI catalog exists; definitions are documented and agreed.
- Reports consume the same definitions (e.g. via a semantic layer or shared measure set).
- "Why did this change?" can be answered with consistent logic. Actions are still decided case by case.

**Framework artifacts:** KPI Catalog; optional semantic model with measures aligned to catalog. Strategy and use cases may be implicit.

---

### Level 3 — Decision-Oriented Use Cases

**What you have:** Analytics is organized by use cases. Each use case links to Strategic KPIs, key questions, and a clear decision context. Reports are structured (e.g. 3-30-300) and mapped to use cases.

**Typical state:**

- Use Case Inventory, Business Factsheets, and UseCase_Bracket.yaml files exist.
- Key questions and required KPIs are explicit per use case.
- Reports are built from templates and consume governed measures. Prioritization is use-case-driven.

**Framework artifacts:** Use cases (factsheets, inventory); strategy patterns or strategic focus areas; page templates; semantic model and measures aligned to use cases.

---

### Level 4 — Action Codes and Closed Loop

**What you have:** When KPIs deviate, recommended actions are defined and owned. Action codes specify triggers, guardrails, and outcomes. Actions are tracked; the loop from signal → decision → action is visible.

**Typical state:**

- Action codes exist for material use cases; triggers (L1–L3) and ownership are clear.
- Reports or a separate action layer surface "what to do" in addition to "what happened."
- Execution and outcomes are logged (even if not fully automated). Governance is explicit (RACI, change flow).

**Framework artifacts:** Action codes; UseCase_Bracket.yaml (`orchestration.action_code_ids`); ownership/RACI; optional action execution and outcome tracking.

---

### Level 5 — Measured Impact and Learning

**What you have:** The impact of actions is measured. Outcomes are compared to expectations; the organization learns which actions work and refines thresholds and priorities. Analytics is a reliable steering capability.

**Typical state:**

- Action outcomes are evaluated (e.g. pre/post KPI, time to effect).
- Strategy, KPIs, use cases, and action codes are reviewed periodically; underperforming or redundant elements are deprecated or improved.
- New use cases or domains are added using the same Golden Thread; repeatability is high.

**Framework artifacts:** Outcome tracking; review cadence; deprecation and improvement process; optional benchmarks or norms.

---

## 3. Mapping to Framework Artifacts

| Level | Strategy | KPIs | Key questions | Use cases | Action codes | Semantic model | Reports | Ownership / governance |
|-------|----------|------|---------------|-----------|--------------|----------------|---------|------------------------|
| 1 | Implicit | Ad hoc | No | No | No | Partial / none | Ad hoc | Unclear |
| 2 | Implicit or partial | Catalog, single definition | Partial | No | No | Yes (measures) | Use same measures | KPI owner |
| 3 | Explicit (patterns or focus areas) | Catalog | Yes (per use case) | Yes (inventory, factsheets) | No or pilot | Yes, aligned to use cases | 3-30-300, templates | Domain owner, use case owner |
| 4 | Explicit | Catalog | Yes | Yes | Yes (triggers, ownership) | Yes | Yes + action layer | RACI, change flow |
| 5 | Reviewed | Reviewed | Reviewed | Reviewed | Reviewed + outcomes | Yes | Yes | Full governance, learning loop |

---

## 4. How to Use This Model

1. **Assess:** Score the organization (or a domain) against each level. Most organizations are between Level 1 and 3.
2. **Scope:** Choose a target level and the next 1–2 steps (e.g. "We are L2; we want L3 in Commercial and Finance within 12 months").
3. **Roadmap:** Use the framework artifacts in the table to plan work (e.g. introduce use cases, then action codes, then outcome tracking).
4. **Avoid skip:** Reaching Level 4 without Level 3 (use cases) usually fails—action codes need a clear use-case and KPI anchor.

---

## 5. Relationship to Other Documents

- **Golden Thread:** `golden_thread_strategy_to_action.md` — Levels 3–5 assume the full thread is in place or in progress.
- **Ownership:** `ownership_raci_golden_thread.md` — Level 4+ requires explicit RACI.
- **Strategy patterns:** `company/strategy_patterns.md` — Level 3+ benefits from choosing or defining a strategy pattern.
- **Framework Health Metrics:** `framework_health_metrics.md` — H1–H5 metrics measure the framework's own completeness and support Level 4–5 governance.
- **Vision:** `internal/archive/framework_evolution.md` — Technical evolution (V1–V6) supports reaching and sustaining these levels.

---

## 6. Self-Assessment Rubric

Use this rubric to score an organization or a specific domain objectively.
Score each dimension (A–E) independently, then compute the overall level.

### How to score

- Score each dimension 1–5 using the criteria table below
- **Overall level = the lowest-scoring dimension** (weakest link)
- Dimensions where you score ≥4 but are blocked by another dimension at 2 are advancement opportunities

### Scoring Criteria

#### Dimension A — KPI Governance

| Score | Criteria |
|-------|----------|
| 1 | KPIs are ad hoc; definitions vary by report |
| 2 | KPI catalog exists; ≥50% of KPIs have single owner and definition |
| 3 | KPI catalog governs ≥80% of reported KPIs; measures aligned to catalog in semantic layer |
| 4 | KPI catalog covers 100% of strategic KPIs; all linked to use cases; aggregation methods documented |
| 5 | KPIs reviewed quarterly; obsolete KPIs deprecated; Golden Thread coverage ≥90% (H1 metric) |

#### Dimension B — Use Case Completeness

| Score | Criteria |
|-------|----------|
| 1 | No formal use cases; reports are ad hoc or project-based |
| 2 | Informal use case list exists; no Bracket schema; no consistent structure |
| 3 | ≥50% of core use cases have Business_Factsheet.md + UseCase_Bracket.yaml (v2.0 schema) |
| 4 | ≥80% of core use cases are build-ready (pass Core DoD); page types declared; fact tables in data contracts |
| 5 | 100% core use cases build-ready; ≥1 extended use case per domain; use case inventory maintained |

#### Dimension C — Action Code Coverage

| Score | Criteria |
|-------|----------|
| 1 | No action codes; responses are ad hoc per manager judgment |
| 2 | Some response patterns documented informally; not linked to KPI triggers |
| 3 | ≥50% of core use cases have ≥1 action code with L1 trigger and KPI linkage |
| 4 | ≥80% of action codes have complete execution_bridge + impact_valuation; linked to decision spines |
| 5 | All action codes complete; outcome tracking in place; false positive rate <5% (H4 metric ≥80%) |

#### Dimension D — Semantic Model & Data Contract Maturity

| Score | Criteria |
|-------|----------|
| 1 | No semantic layer; measures defined in individual reports |
| 2 | Semantic model exists; ≥50% of KPI measures defined and reused across reports |
| 3 | Domain measure dictionaries exist; ≥80% of measures have aggregation_method; data contracts for ≥3 domains |
| 4 | Semantic model stability ≥80% (H2 metric); data contract coverage ≥90% (H3 metric); quality_rules defined |
| 5 | All domains have active-status measures; ESG/Risk/Efficiency/Growth contracts active; Silver→Gold lineage complete |

#### Dimension E — Governance & Learning Loop

| Score | Criteria |
|-------|----------|
| 1 | No formal ownership; no review cadence |
| 2 | KPI and use case owners named; ad hoc review when issues arise |
| 3 | RACI documented; monthly review cadence for tactical domains; Stage 1 CI gate in place |
| 4 | Decision spine governance active; action outcomes tracked; quarterly framework health review |
| 5 | Full learning loop: outcomes measured, thresholds refined, underperforming use cases deprecated; framework health ≥80% on all H1–H5 metrics |

---

### Quick Self-Assessment Template

Copy and fill in for your organization or a specific domain:

```
Domain/Organization: _______________
Assessment date:     _______________
Assessor:            _______________

A — KPI Governance:            [ 1 / 2 / 3 / 4 / 5 ]  Notes: ___
B — Use Case Completeness:     [ 1 / 2 / 3 / 4 / 5 ]  Notes: ___
C — Action Code Coverage:      [ 1 / 2 / 3 / 4 / 5 ]  Notes: ___
D — Semantic Model & Contracts:[ 1 / 2 / 3 / 4 / 5 ]  Notes: ___
E — Governance & Learning:     [ 1 / 2 / 3 / 4 / 5 ]  Notes: ___

Overall Level (lowest dimension): [ 1 / 2 / 3 / 4 / 5 ]
Blocking dimension(s):            _______________
Next milestone:                   _______________
```

---

### Effort Estimates

These are orientation estimates for teams starting from zero in a domain.
Actual effort depends on data availability and team capacity.

| Transition | Typical Effort | Key Accelerators |
|------------|---------------|-----------------|
| Level 1 → 2 | 2–4 weeks | Existing KPI list; domain SME available |
| Level 2 → 3 | 6–10 weeks | Templates in place; use cases from framework (not greenfield) |
| Level 3 → 4 | 8–12 weeks | Action code templates; decision spine for the domain |
| Level 4 → 5 | 3–6 months | Reporting infrastructure for outcome tracking; review cadence established |
| Full Level 1 → 4 (single domain) | ~4–6 months | Framework adoption (vs. custom build: 12–18 months) |
| Full Level 1 → 5 (enterprise) | 12–24 months | Phased rollout; domain by domain |

**Critical path bottlenecks (most common causes of stall):**
- L2 → L3: KPI definitions not agreed across Finance and Commercial
- L3 → L4: Action code ownership unclear (no single decision owner per domain)
- L4 → L5: No outcome tracking infrastructure; actions not logged in a system of record

---

### Milestone Checklist: Level 3 → Level 4 (Single Domain)

Use this checklist to confirm a domain is ready for Level 4 transition:

- [ ] All core use cases for the domain have v2.0 `UseCase_Bracket.yaml`
- [ ] Each use case has ≥1 action code with `l1_trigger` defined
- [ ] Action code KPI trigger IDs exist in `core/kpi_catalog/`
- [ ] Decision spine for the domain is active (not placeholder)
- [ ] `when_not_to_act` conditions defined in the decision spine
- [ ] Execution bridge type declared for each action code (not "TBD")
- [ ] Stage 1 CI passes without errors for the domain's files
- [ ] Domain Lead and Business Owner named in use case metadata
- [ ] RACI for the domain exists in `ownership_raci_golden_thread.md`
- [ ] Action codes presented to and accepted by domain leadership
