# Golden Thread – From Strategy to Action

Most analytics landscapes implicitly assume a link between strategy, KPIs, insights, and actions.

In reality, this link is often fragmented:

- Strategy is defined, but not operationalized
- KPIs exist, but are not action-oriented
- Insights are generated, but not executed
- Actions happen, but are not measured

The purpose of the Golden Thread is to make this connection explicit, traceable, and operational across the entire analytics lifecycle.

---

## 1. Business Strategy (WHY)

Business strategy defines *what matters* for the company.

Artifacts:

- Company Strategy
- Strategic KPIs
- Strategic Domains

Outcome:

- A small, stable set of **Strategic KPIs** that express success (e.g. Revenue Growth %, Gross Margin %, Cash Conversion Cycle).

Reference:

- docs/company/company_strategy.md

---

## 2. Strategic KPIs → Key Questions

Strategic KPIs are operationalized through concrete business questions.

Examples:

- Why is Gross Margin declining?
- Which levers influence Cash Conversion Cycle?
- Where do we lose customers or value?

Outcome:

- Clear **Key Questions** that analytics must answer.
- Avoids tool-driven or ad-hoc reporting.

Reference:

- docs/company/reporting_principles.md

---

## 3. Key Questions → Use Cases (WHAT)

Each key question is addressed by one or more **Analytics Use Cases**.

A Use Case defines:

- Business intent and decision context
- Required KPIs
- Expected business impact
- Action Codes (what to do when something deviates)

Outcome:

- Analytics is framed around **decisions and actions**, not dashboards.

Reference:

- usecases/UseCase_Inventory.md
- usecases/core/

---

## 4. Use Cases → Semantic Model (HOW)

Use Cases drive the design of the **Action-Ready Semantic Model**.

Principles:

- Star schema
- KPI-driven aggregates
- Action-specific calculation logic
- Stable measure definitions

Outcome:

- One consistent semantic layer usable across reports, automation, and AI.

Reference:

- docs/operating_model/semantic_layer.md
- docs/operating_model/ActionReady_SemanticModel_Blueprint.md

---

## 5. Semantic Model → Measures & KPIs

KPIs are implemented as governed measures.

Rules:

- KPI definitions live in the KPI Catalog
- Measures follow naming, formatting, and folder standards
- Supporting measures are explicit and reusable

Outcome:

- Single Source of Truth for all metrics.
- High trust and explainability.

Reference:

- framework/kpi_catalog/
- docs/operating_model/measure_system.md
- docs/operating_model/single_source_of_truth.md

---

## 6. Measures → Reports (3–30–300)

Measures are exposed through standardized reporting patterns.

Levels:

- 3s: Strategic overview
- 30s: Tactical drivers
- 300s: Operational detail and analysis

Outcome:

- Consistent user experience
- Fast orientation and decision support

Reference:

- framework/templates/page_templates/
- docs/operating_model/ux_design_system.md

---

## 7. Reports → Actions

Analytics becomes valuable only when it leads to action.

Mechanism:

- KPI thresholds trigger Action Codes
- Actions are documented, executed, and measurable
- Optional tracking of action effectiveness

Outcome:

- Closed loop: insight → action → impact

Reference:

- framework/action_codes/
- docs/operating_model/usecase_DoD_Core.md

---

## 8. Automation & AI Readiness

Because all elements are structured and linked:

- Use Cases
- KPIs
- Semantic Models
- Actions

The framework is:

- Automation-ready
- Copilot / AI-agent ready
- Scalable across domains and platforms

Reference:

- docs/operating_model/ai_readiness.md

---

## Summary

Strategy defines *what matters*.  
Use Cases define *what to analyze*.  
Semantic Models define *how it is calculated*.  
Reports define *how it is consumed*.  
Actions define *what changes*.

This is the Golden Thread.
