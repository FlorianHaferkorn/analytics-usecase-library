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
- **Vision:** `internal/archive/framework_evolution.md` — Technical evolution (V1–V6) supports reaching and sustaining these levels.
