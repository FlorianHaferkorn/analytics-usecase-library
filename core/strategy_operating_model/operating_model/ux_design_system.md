# UX Design System

> **Canonical design principles:** [reporting_principles.md](../company/reporting_principles.md).  
> This document operationalizes the UX layer and must not redefine reporting principles.

The UX Design System defines binding standards for how analytics is presented and interacted with across the framework.

While the Golden Thread defines decision logic and the Operating Model governs its operation, the UX Design System ensures that analytical outputs are interpreted consistently and adopted by users.
It does not introduce analytical meaning.
It reinforces existing meaning through consistent interaction and presentation.

## 1. Role in the Framework

The UX Design System operationalizes the consumption layer of the Golden Thread.

- Strategy, KPIs, and Action Codes define what decisions matter.
- Semantic models and measures provide structured analytical meaning.
- UX standards ensure that this meaning is perceived, understood, and acted upon consistently.

UX consistency is a prerequisite for trust and adoption.

## 2. Design Scope

The UX Design System applies to all analytical products within the framework.

It defines:

- layout and visual hierarchy,
- interaction patterns,
- navigation structure,
- and decision-oriented presentation standards.

Customer-specific branding and tool-specific configuration are intentionally excluded.

## 3. UX Principles

UX standards follow a small set of binding principles.

Minimalism reduces noise and focuses attention on decision-relevant information.
Hierarchy guides users from KPIs to insights to exploration.
Consistency ensures recognizability across domains and products.
Clarity supports intuitive navigation and interpretation.
Predictability enables confident interaction without re-learning.

## 4. The 3-30-300 Design Model

The 3-30-300 model structures analytical consumption by decision horizon.

### 4.1. 3 Seconds

Immediate orientation and status awareness.
Typically represented by a small set of KPI cards with clear deltas and signals.

### 4.2. 30 Seconds

Understanding drivers, trends, and deviations.
Typically supported by rankings, trends, segmentation, and composition views.

### 4.3. 300 Seconds

Detailed analysis and validation.
Typically enabled through tables, drill-downs, exports, and advanced visualizations.

## 5. Normative UX Standards

The following standards are binding for all analytical interfaces.

### 5.1. Components

- A maximum of three slicers per page.
- Pie and donut charts are not used.
- 100% stacked bars replace split pie representations.
- Reference lines are used where targets or thresholds exist.

### 5.2. Layout and Density

- Clear spacing, padding, and alignment are mandatory.
- Visual density is controlled to avoid cognitive overload.

### 5.3. Navigation

- Pages follow a consistent structure from overview to insight to exploration.
- Navigation remains minimal and predictable.
- Active filters are always visible.

## 6. Usage and Adaptation

UX standards apply uniformly across domains and use cases.

Adaptation to customer branding occurs through separate, customer-specific design principles.
UX structure and interaction patterns remain unchanged.

## 7. Outcome

When applied consistently, the UX Design System ensures that:

- analytical insights are quickly understood,
- decisions are supported rather than obscured,
- and adoption remains high across users and domains.

The UX Design System enables action by reducing cognitive friction, not by adding visual complexity.

## 8. Sources & Grounding

The normative standards in this document draw on established design-system practice,
data-visualization research, and accessibility standards. The minimalism, hierarchy,
and consistency principles align with **Tufte/Few** data-visualization research and
**Munzner's** task-and-channel framework; the layout-token and component approach
aligns with mature **design systems** (Material Design, design tokens); the density,
contrast, and navigation standards align with **WCAG** accessibility requirements.
Grounded in:

- **Material Design 3 — design systems and design tokens** (platform-agnostic style
  tokens for color, typography, spacing; basis for layout, density, and component
  standardization) — Google Material Design: <https://m3.material.io/> · Design
  tokens overview: <https://m3.material.io/foundations/design-tokens/overview>
- **Data-visualization best practice — minimalism and visual hierarchy** (erase
  non-data ink; at-a-glance design; basis for the minimalism and hierarchy
  principles) — Edward Tufte, *The Visual Display of Quantitative Information*:
  <https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/> ·
  Stephen Few, Perceptual Edge: <https://www.perceptualedge.com/library.php>
- **Visualization Analysis and Design — task/channel framework** (matching visual
  encodings to analytical tasks; basis for choosing chart types and the no-pie /
  100% stacked-bar guardrails) — Tamara Munzner (UBC):
  <https://www.cs.ubc.ca/~tmm/vadbook/>
- **WCAG (Web Content Accessibility Guidelines) 2.2** (perceivable contrast, visible
  state, predictable navigation; basis for the accessibility and density standards) —
  W3C Web Accessibility Initiative: <https://www.w3.org/TR/WCAG22/> · WCAG 2 overview:
  <https://www.w3.org/WAI/standards-guidelines/wcag/>

> This document operationalizes — it does not redefine — the reporting principles in
> [reporting_principles.md](../company/reporting_principles.md), which carry their own
> grounding (IBCS, Tufte, Few). Customer branding and tool-specific configuration are
> intentionally out of scope (see §6).

