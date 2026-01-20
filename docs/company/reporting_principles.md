# Reporting Principles

## 1. Purpose

This document defines the binding principles that govern how reporting and analytical outputs are designed and evaluated within the Action-Ready Analytics Framework.

While the Golden Thread defines decision logic, the Operating Model governs delivery, and the UX Design System defines interaction standards, this document defines the cognitive and decision-oriented quality criteria for reporting.

It does not define layouts, visual components, or technical implementation.
It defines what makes reporting effective for decision-making.

## 2. Scope

This document defines:

- what decision-oriented reporting looks like,
- non-negotiable principles for analytical consumption,
- and how reporting supports decisions and actions.

This document does not define:

- page layouts or visual components,
- tool-specific implementations,
- or domain-specific content.

## 3. Reporting as a Decision Instrument

Reporting is not an end in itself.

The purpose of reporting is to:

- support decisions,
- enable accountability,
- trigger actions,
- and provide transparency.

Dashboards that do not lead to decisions or actions are considered incomplete, regardless of visual quality.

Every report must answer at least one of the following questions:

- What is happening?
- Why is it happening?
- What should we do about it?

## 4. Principle: Actionability First

All reporting outputs are action-oriented by design.

This means:

- KPIs are presented together with interpretation context,
- expectations, targets, or thresholds are explicit,
- deviations are clearly visible,
- and potential actions are identifiable or traceable.

Actionability is enabled through:

- Action Codes,
- Use Case definitions,
- and prescriptive views where appropriate.

A KPI without a potential action is considered incomplete.

## 5. Principle: Progressive Disclosure (3EUR"30EUR"300)

Reporting follows a structured information hierarchy known as 3EUR"30EUR"300.

3 seconds:
Immediate orientation through high-level status and signals.

30 seconds:
Structured explanation through drivers, comparisons, and segmentation.

300 seconds:
Analytical depth through drill paths, detailed breakdowns, and validation.

Not every report must implement all three layers.
Each report must explicitly indicate which layer it primarily serves.

## 6. Principle: Cognitive Simplicity

Reports minimize cognitive load to support fast and confident interpretation.

This includes:

- a limited number of KPIs per page,
- clear visual hierarchy,
- consistent use of scales and formats,
- and avoidance of unnecessary visual decoration.

Clarity always takes precedence over completeness.

## 7. Principle: Consistency Across Domains

Users must be able to transfer understanding across reports and domains.

Consistency applies to:

- KPI naming and definitions,
- time comparisons,
- color semantics,
- and interaction logic.

Consistency is ensured through:

- KPI catalogs,
- the Measure System,
- and shared page templates.

## 8. Principle: User-Centric Design

Reports are designed for specific roles and decision responsibilities.

This implies:

- a clearly defined target user per report or page,
- alignment of analytical depth with responsibility,
- and explicit separation of executive, tactical, and operational views.

Generic one-size-fits-all dashboards are avoided.

## 9. Principle: Transparency Over Perfection

Users must understand what the numbers represent and what they do not.

Preferred practices include:

- explicit definitions over hidden logic,
- documented limitations over silent inaccuracies,
- and traceability over visual polish.

Trust is built through transparency, not perfection.

## 10. Relationship to UX System & Templates

This document defines principles.

Concrete implementations are defined in:

- UX standards and interaction patterns:
  `docs/operating_model/ux_design_system.md`
- Page templates and layout patterns:
  `framework/templates/page_templates/`
- Visual guardrails and whitelists:
  `framework/templates/page_templates/Visual_Whitelist.md`

Principles take precedence over templates.

## 11. Outcome

When applied consistently, these principles ensure that reporting:

- is understood within seconds,
- explains why changes occur,
- makes next actions clear,
- and feels consistent across domains and audiences.

These principles define the non-negotiable decision quality of reporting.

