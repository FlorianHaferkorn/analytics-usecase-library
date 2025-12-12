# Reporting Principles & Design Standards

Purpose:
This document defines the core principles that govern how reporting and analytics outputs are designed, structured, and consumed across the organization.

It ensures that reporting is **decision-oriented, consistent, and actionable**, independent of tools or technologies.

Scope:
- Defines *what good reporting looks like* from a business and user perspective.
- Defines non-negotiable design and usage principles.
- Defines how reporting supports decisions and actions.
- Does NOT define concrete page layouts or technical implementation details.

---

## 1. Reporting as a Decision Instrument

Reporting is not an end in itself.

The purpose of reporting is to:
- Support decisions
- Trigger actions
- Enable accountability
- Provide transparency

Dashboards that do not lead to decisions or actions are considered **incomplete**, regardless of visual quality.

Every report must answer at least one of the following:
- *What is happening?*
- *Why is it happening?*
- *What should we do about it?*

---

## 2. Principle: Actionability First

All reporting outputs must be **action-oriented**.

This means:
- KPIs are presented together with interpretation context.
- Thresholds, targets, or expectations are visible or clearly defined.
- Deviations are explicit, not implicit.
- Actions are either suggested, triggered, or traceable.

Actionability is operationalized through:
- Action Codes
- Use Case definitions
- Prescriptive views (where applicable)

A KPI without a possible action is considered **incomplete**.

---

## 3. Principle: Progressive Disclosure (3–30–300)

Reporting follows a structured information hierarchy known as **3–30–300**:

- **3 seconds**  
  Immediate orientation.  
  High-level status, trends, and critical signals.

- **30 seconds**  
  Structured explanation.  
  Key drivers, comparisons, and segmentation.

- **300 seconds**  
  Analytical depth.  
  Detailed breakdowns, root cause analysis, and drill paths.

Not every report must implement all three layers, but:
- Every report must clearly indicate *which layer it serves*.
- Mixing layers without intent is discouraged.

---

## 4. Principle: Cognitive Simplicity

Reports must minimize cognitive load.

This includes:
- Limited number of KPIs per page.
- Clear visual hierarchy.
- Consistent use of colors, scales, and formats.
- Avoidance of unnecessary visual decoration.

Clarity always has priority over completeness.

---

## 5. Principle: Consistency Across Domains

Users must be able to transfer understanding between reports.

Consistency applies to:
- KPI naming and definitions
- Time comparisons (YoY, MoM, YTD, etc.)
- Color semantics (e.g., good / neutral / bad)
- Layout logic and interaction patterns

Consistency is enforced through:
- KPI catalogs
- Measure system conventions
- Page template library

---

## 6. Principle: User-Centric Design

Reports are designed for **specific roles**, not generic audiences.

This implies:
- Clear definition of the target user per report or page.
- Alignment of content depth with user responsibility.
- Avoidance of “one-size-fits-all” dashboards.

Executive, tactical, and operational views must be clearly separated.

---

## 7. Principle: Transparency Over Perfection

Users must understand:
- What the numbers represent
- Where the data comes from
- What assumptions apply

Explicitly preferred:
- Clear definitions over hidden logic
- Documented limitations over silent inaccuracies
- Traceability over visual polish

---

## 8. Relationship to UX System & Templates

This document defines **principles**.

Concrete implementations are defined elsewhere:
- UX system and interaction standards:  
  `docs/operating_model/ux_design_system.md`
- Reusable page layouts and patterns:  
  `framework/templates/page_templates/`
- Visual whitelist and guardrails:  
  `framework/templates/page_templates/Visual_Whitelist.md`

Principles must always take precedence over templates.

---

## 9. What Good Looks Like

A report that follows these principles:
- Can be understood within seconds.
- Explains *why* something changed.
- Makes the next action obvious.
- Feels consistent with other reports.
- Builds trust instead of debate.

Reporting that does not meet these criteria should be challenged and improved.

---

## 10. Relationship to the Overall Framework

This document supports:
- **Company Strategy:**  
  `docs/company/company_strategy.md`
- **Analytics Operating Model:**  
  `docs/operating_model/`
- **Use Case Design:**  
  `usecases/`

Together, they ensure that reporting is not isolated, but embedded into a coherent analytics system.

---

This document defines the **non-negotiable reporting DNA** of the organization.
