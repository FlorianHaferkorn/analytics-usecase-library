# Page Templates

This folder defines the **only allowed page types** for reports built with the Analytics Use Case Library.

The goal is not design freedom, but **decision clarity, scalability, and reuse**.

If you follow these rules, every report:

- looks familiar to users,
- answers clear business questions,
- scales across domains and use cases,
- remains maintainable without consultants.

---

## What is a Page Template?

A page template is a **decision-oriented page type**, not a visual layout.

Each template answers a specific class of business questions and is designed
to support the **3–30–300 rule**:

- **3 seconds** → headline KPIs  
- **30 seconds** → patterns, deviations, rankings  
- **300 seconds** → detailed analysis and drill-down

---

## The 4 Golden Page Types (Mandatory)

Only the following page types are allowed.

| Template | Purpose | Core Question | Typical Use |
|--------|--------|--------------|-------------|
| **T1 – Strategic Overview** | Direction & performance | *Are we on track?* | Management, steering |
| **T2 – Tactical Variance** | Target vs. actual | *Where do we deviate and why?* | Performance management |
| **T3 – Operational Monitoring** | Process health | *Where are issues emerging right now?* | Operations, governance |
| **T4 – Prescriptive Recommendation** | Action & decision | *What should we do next?* | Action-driven analytics |

Each use case is implemented using **exactly two pages**:

- one **Overview** page (3 / 30 layer)
- one **Detail** page (300 layer)

---

## When NOT to use a Page Type

- Do **not** create custom layouts per report
- Do **not** mix multiple page purposes on one page
- Do **not** introduce new template types
- Do **not** redesign visuals outside the whitelist

If a question does not fit one of the four templates,
the **use case is not ready** or not well-defined.

---

## How Page Templates Are Used

### 1. Mapping (Single Source of Truth)

The assignment of use cases to page templates is defined in:

```yaml
mappings/UseCase_PageTemplate_Map.yaml
```

This file is the **authoritative source** for:

- which template a use case uses,
- which slots are required,
- whether an action panel is needed.

Markdown overview files are **read-only views**, not sources of truth.

---

### 2. Slots (What a Page May Contain)

Templates do not define concrete visuals.
They define **slots** (e.g. Trend, Variance, Ranking).

Slot rules and allowed visuals are defined in:

```yaml
governance/Slot_Definitions.md
```

---

### 3. Visual Governance

Which visuals are allowed (and where) is defined in:

```yaml
governance/Visual_Whitelist.md
```

Examples:

- Scatter plots are allowed only in **T3 and T4**
- Tables/matrices are allowed only on **Detail (300) pages**
- Funnel charts are non-default and explicitly flagged

---

### 4. Action Panel

Some pages require an **Action Panel** to support prescriptive analytics.

Rules and structure are defined in:

```yaml
components/ActionPanel_Spec.md
```

The Action Panel is **optional**, but if enabled, it must follow the spec.

---

## Definition of Done (DoD)

A page is considered complete only if:

- it follows one of the four page types,
- slot usage matches the mapping,
- only whitelisted visuals are used,
- slicer limits are respected,
- the page answers the template’s core question.

The formal checklist is defined in:

```yaml
governance/Page_DoD.md
```

---

## Deprecated Content

The following legacy templates are **no longer part of the Golden Path** and must not be used for new work:

- overview_page_template.md
- insights_page_template.md
- explorer_page_template.md

They are kept only for reference.

---

## Key Principle (Read This Twice)

> **Consistency beats creativity.**  
> The value of this framework comes from reuse, not customization.

If you feel the need to break these rules,
the problem is usually **upstream** (use case definition, KPIs, or actions),
not the page template.

