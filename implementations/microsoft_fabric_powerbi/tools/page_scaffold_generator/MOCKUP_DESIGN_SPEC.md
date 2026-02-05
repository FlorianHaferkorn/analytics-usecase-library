# Mockup Design Spec — World-Class Page Layouts

Design specification for Power BI page scaffold mockups and PBIP output. Ensures analytics path clarity, UI/UX best practices, and a single layout engine for both PBIP and HTML mockups.

---

## 1. Non-negotiables

1. **Analytics path must stay as clear and self-explanatory as possible.** The 3-30-300 flow (summary → drivers → detail), the primary decision question, and the analytical path to answer it must remain obvious. Layout and hierarchy reinforce this—not obscure it. Adaptive resizing must preserve and support the narrative (e.g. KPIs first, then drivers, then detail; action panel prominent when present).

2. **UI/UX best practices are mandatory.** The goal is products users **want to use**. The design spec and implementation follow established UI/UX best practices: visual hierarchy, readability, consistency, accessibility, reduced clutter, purpose-driven layout. Any adaptive or flexible behaviour must still result in a clear, scannable, and desirable experience.

---

## 2. Research and authority sources

### Microsoft

- [Tips for designing a great Power BI dashboard](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips): most important information top-left, tell a story on one screen, accent the most important (e.g. cards), avoid clutter; consider audience and device.

### Reading patterns

- **Z-pattern:** Visual-first / landing-style layouts; user scans top-left → top-right → bottom-left → bottom-right. Dashboards with large charts often align with Z-pattern.
- **F-pattern:** Content-heavy layouts; users scan top then left. Use when text or tables dominate.

### Open-source references (layout and style only)

- **Tremor** ([tremor.so](https://www.tremor.so/), [template-dashboard-oss](https://github.com/tremorlabs/template-dashboard-oss)): Analytics-focused; KPI cards, charts, tables, filters; clear hierarchy and spacing; Apache-2.0. Use as **layout and visual hierarchy reference** (we keep static HTML/CSS, no React).
- **Tabler** ([preview.tabler.io](https://preview.tabler.io/layout-fluid.html)): Fluid grid, clean dashboard layouts.
- **Flowbite / Tailwind admin templates:** Grid-based analytics layouts; useful for spacing and card treatment.

---

## 3. Design principles

- **Visual hierarchy:** Size and position so "3-second" KPIs dominate (top-left or top band), then "30-second" drivers, then "300-second" detail.
- **One screen story:** Tell the story on one screen; avoid unnecessary scrolling for the primary narrative.
- **Accent the important:** Cards and primary visuals get prominence; supporting context is secondary.
- **Audience-aware:** Layout and density should match decision level (strategic vs tactical vs operational vs prescriptive).

---

## 4. Layout rules per page type (T1–T4)

Layout rules define **hierarchy and emphasis only**, not a fixed grid. Positions and sizes are derived from the **actual list of visuals** for the use case (adaptive layout: resize and reflow based on content).

| Page type | Analytics layer | Emphasis |
|-----------|-----------------|----------|
| **T1** | Strategic summary (3-second) | Hero summary; fewer visuals; large KPI band; optional single primary chart. |
| **T2** | Tactical drivers (30-second) | Variance/drivers prominent; KPI band + trend/variance + ranking/mix/funnel; detail matrix on detail pages. |
| **T3** | Operational monitoring | Exceptions and alerts prominent; higher density; monitoring/alert feel. |
| **T4** | Prescriptive recommendation | Action panel and prescriptive block clear; recommendation + evidence + optional detail. |

**Adaptive layout:** Given page type and the actual set of visuals (slots) for the use case, the layout engine computes positions and sizes that:

- Reserve a **KPI band** (height depends on KPI count; min 1 row, max 2 rows).
- Allocate **primary zone** (trend, variance, exceptions, or prescriptive) with priority by page type.
- Allocate **secondary zone** (ranking, mix, root cause, funnel) with remaining space.
- Allocate **detail zone** (detail matrix) when present; height can grow with content.
- Reserve **slicer area** (top bar or side strip) and **action panel** (right side) when present.

Row boundaries and heights are **computed** from the count and type of visuals, not fixed.

---

## 5. Typography

- **Font stack:** System UI first (e.g. `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`). Optional second font for headings only (e.g. a stronger sans for page title).
- **Page title:** 1.25rem, font-weight 600; primary text color.
- **Slot / section labels:** 0.75rem, muted color (e.g. #6E6D6B).
- **Dimension / dev labels (mockups):** 0.65rem, monospace (`'Courier New', monospace`), muted.
- **Visual titles:** Every visual has a speaking, question-oriented title (not "Chart" or "Table"); scaffold and mockup support this.

---

## 6. Spacing

- **Grid unit:** 20px. All padding and gaps are multiples of 20px where possible.
- **Page padding:** 20px from canvas edges.
- **Gap between visuals:** 20px (horizontal and vertical).
- **Gap between groups:** 40px (e.g. between KPI band and primary chart area).
- **Zones:** Flexible zones (KPI band, primary, secondary, detail) whose **sizes depend on content**; within each zone, 20px spacing.

---

## 7. Color and accessibility

- **Slot-based colors (mockups):** KPI band/charts/tables/slicers/action panel use distinct, semantic tints (see existing mockup generator). Refine for **contrast and accessibility (WCAG 2.1 AA)** where possible.
- **Avoid red-green pairing** for critical distinctions; use patterns or red/blue, green/blue.
- **Contrast:** Text and borders must meet WCAG contrast requirements against background.

---

## 8. Decision question

- The **primary decision question** (or 1–2 key questions) from the use case must be visible on the page (e.g. in the header or a small banner) so the analytics path is self-explanatory.
- **Source:** Use case factsheet (e.g. Business Factsheet primary question or page-level question).
- **Placement:** Page title area or subtitle; design spec and mockup/scaffold support a dedicated line or banner for this.

---

## 9. Visual titles and labels

- Every visual has a **clear, question-oriented title/label**, not generic "Chart" or "Table".
- Scaffold can emit placeholder titles (e.g. from slot or KPI name); mockup shows the slot or a speaking label.
- Convention: prefix by type (KPI_, Trend_, Slicer_, Table_, etc.) and a concise descriptor for PBIP naming.

---

## 10. Accessibility

- **Contrast (WCAG):** All text and interactive elements meet minimum contrast ratios.
- **Focus order:** Tab order follows visual hierarchy (KPIs → primary → secondary → detail → slicers → action panel).
- **Alt text / descriptions:** Visuals have descriptive alt text or descriptions so reports are usable by as many people as possible; scaffold and mockup support this (e.g. title/description field).

---

## 11. Single layout engine

- The **same layout logic** drives both the **PBIP scaffold** (Power BI page/visual JSON) and the **HTML mockup**.
- One source of truth (e.g. `layout_calculator` or a dedicated adaptive-layout module) so mockup and scaffold stay in sync. Page type (T1/T2/T3/T4) and the actual list of visuals are inputs; output is positions and sizes for each visual.

---

## 12. Design references (links)

- [Tremor template-dashboard-oss](https://github.com/tremorlabs/template-dashboard-oss) — layout and visual hierarchy.
- [Tabler layout fluid](https://preview.tabler.io/layout-fluid.html) — fluid grid, dashboard layouts.
- [Microsoft Power BI design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips) — authority guidance.

---

## 13. Validation

- **Analytics path:** Checklist or stakeholder review confirms that 3-30-300 flow and decision question are obvious.
- **UI/UX:** Checklist confirms visual hierarchy (KPI band → primary → secondary), readability, consistency, and accessibility before treating a layout as done. See validation checklist in repo (e.g. `VALIDATION_CHECKLIST.md` or equivalent).
