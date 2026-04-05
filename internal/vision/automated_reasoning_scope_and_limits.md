# Automated reasoning: scope and limits

**Purpose:** Single place for what "automated reasoning" means in this framework, what is in scope, and what is explicitly out of scope or limited. Supports backlog planning (Strategy Pattern / AI urgency epic) and avoids scope creep.

**Audience:** Product, architecture, and anyone implementing or evaluating AI/automation around the framework.

**Status:** Scope and limits documented here; tooling and implementation are in backlog (see [phase2_backlog.md](phase2_backlog.md), [technical_backlog.md](../technical_backlog.md)).

---

## Scope (what we mean by automated reasoning)

Within this framework, **automated reasoning** refers to machine-assisted use of governed artifacts to derive conclusions or recommendations **without inventing new business logic**. In scope:

1. **Urgency derivation**  
   Using strategy patterns and bracket logic to infer *relative urgency* of actions or use cases (e.g. which deviation to address first). The strategy pattern is precise enough for tooling: urgency rules are in [strategy_patterns.md](../../core/strategy_operating_model/company/strategy_patterns.md) §8; tooling hook spec: [tooling/ir/urgency_derivation_spec.md](../../tooling/ir/urgency_derivation_spec.md).

2. **Action suggestion from governed logic**  
   Suggesting or surfacing actions that are already defined in action codes and wired in brackets. The "reasoning" is limited to: *given this KPI state and trigger level, which action codes apply?* No new trigger rules or action text are invented.

3. **Triage and recommendations for consumption**  
   A conversational or recommendation layer that explains deltas, highlights trends, or suggests next steps using **only** governed measures and action codes (semantic layer as single interface). Coverage grows with the framework (domains, KPIs, use cases); the system does not add ad-hoc logic.

4. **Assisted authoring and maintenance**  
   AI assists in drafting or updating artifacts (e.g. factsheets, brackets, refs) and in checking consistency. Output is proposed; humans approve. Automation reduces drift and speeds change but does not define KPI meaning, targets, or action logic.

---

## Limits (what we do not do)

- **AI does not invent definitions.**  
  KPI definitions, targets, lineage, and action trigger logic live in the catalog and action codes. They are not created or changed by AI without human approval.

- **No unapproved execution.**  
  AI may suggest actions or explain what to do; it does not execute decisions (e.g. change data, send commands) without explicit approval and governance.

- **No ad-hoc logic in consumption.**  
  Any conversational or recommendation layer must use the semantic layer and governed action codes only. Ad-hoc measures, new trigger rules, or one-off "explanations" that bypass the catalog are out of scope.

- **All changes pass Stage 1.**  
  Any artifact change (human- or AI-proposed) must satisfy the Stage 1 CI gate (schema, refs, SSOT, etc.). There is no bypass for "AI-generated" content.

- **Agentic / autonomous agents.**  
  Future agentic BI (e.g. agents that read/write metadata and suggest report or model changes) remains a later-stage consideration. If introduced, it stays under "humans approve, AI does not invent definitions" and must pass Stage 1. See [internal/archive/framework_evolution.md](../archive/framework_evolution.md) (Automation and AI, Future consideration).

---

## Related documents

| Document | Relevance |
|----------|-----------|
| [ACTIONREADY_HOLISTIC_MANIFESTO.md](ACTIONREADY_HOLISTIC_MANIFESTO.md) | Strategy pattern as basis for "Automated Reasoning"; payload integrity for AI/dashboard. |
| [phase2_backlog.md](phase2_backlog.md) | Strategy Pattern / KI-Dringlichkeit as Phase 2 backlog. |
| [internal/archive/framework_evolution.md](../archive/framework_evolution.md) | Automation and AI (assisted creation, consumption, limits, agentic future). |
| [core/strategy_operating_model/company/strategy_patterns.md](../../core/strategy_operating_model/company/strategy_patterns.md) | Authority for strategy patterns; §8 defines urgency rules for tooling. |
| [internal/technical_backlog.md](../technical_backlog.md) | Granular technical tasks: urgency tooling hook and implementation follow-ups. |
