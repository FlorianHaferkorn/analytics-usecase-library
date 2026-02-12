# Mockup / Layout Validation Checklist

Use this checklist before treating a page layout as done. Ensures analytics path clarity and UI/UX best practices (see [MOCKUP_DESIGN_SPEC.md](MOCKUP_DESIGN_SPEC.md)).

## Analytics path

- [ ] **3-30-300 flow** — Summary (KPIs) is visible first, then drivers (trend/variance/ranking/mix), then detail (matrix) if present. Order matches the narrative.
- [ ] **Decision question** — Primary decision question (or 1–2 key questions) is visible (e.g. in header/banner) and matches the use case.
- [ ] **Analytical path** — A user can answer "what should I do?" by following the layout top-to-bottom / left-to-right without confusion.

## UI/UX

- [ ] **Visual hierarchy** — KPI band is clearly distinct (e.g. background tint or grouping). Primary chart area is more prominent than secondary.
- [ ] **Readability** — Typography is clear (title vs labels vs dimensions). No cramped or overlapping text.
- [ ] **Consistency** — Spacing follows the grid (20px). Visual types use consistent slot colors (KPI, chart, table, slicer, action panel).
- [ ] **Reduced clutter** — Only necessary elements; no redundant labels or decorative noise.
- [ ] **Purpose-driven** — Layout supports the page type (T1 summary, T2 drivers, T3 monitoring, T4 prescriptive).

## Accessibility (design spec)

- [ ] **Contrast** — Text and borders meet WCAG 2.1 AA contrast against background.
- [ ] **Focus order** — Tab order follows visual hierarchy (KPIs → primary → secondary → detail → slicers → action panel).
- [ ] **Alt text / descriptions** — Visuals have descriptive titles or descriptions for screen readers.

## PBIP / scaffold

- [ ] **Speaking names** — Page folder and `page.json` use a human-readable name (e.g. `Page_COM001_Overview`). Visual folders and `visual.json` use names like `KPI_1`, `Trend`, `Slicer_Date` (no hex IDs).
- [ ] **Single layout engine** — Mockup and PBIP positions match (same layout calculator output).

## Sign-off

- [ ] **Stakeholder review** — Layout reviewed by product or business owner for analytics path and usability.
- [ ] **Design spec alignment** — Layout aligns with [MOCKUP_DESIGN_SPEC.md](MOCKUP_DESIGN_SPEC.md) (layout rules, typography, spacing, decision question).

---

*Run this checklist after generating or changing a page scaffold/mockup, and before building the real report.*
