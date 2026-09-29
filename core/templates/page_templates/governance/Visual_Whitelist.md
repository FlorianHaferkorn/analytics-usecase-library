# Visual Whitelist

This document defines **which visual types are allowed**, **where**, and **for what purpose**.
It is intentionally restrictive to ensure clarity, consistency, and decision focus.

If a visual is not listed here, it is **not allowed**.

---

## Core Principles

- Visuals exist to support **decisions**, not decoration.
- Each visual must clearly support the **slot purpose**.
- Fewer visual types lead to higher user trust and faster adoption.

---

## Allowed Visuals by Category

### Header & Narrative

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Big Idea Textbox | `Header` (Zone 0, Overview/Summary pages only) | T1, T2, T3, T4 |
| Smart Narrative (chart-grounded) | `Smart_Narrative` (Detail pages) | All templates |

**Big Idea Textbox rules:**
- Mandatory on every Overview/Summary page — Zone 0, one line, plain text (`textbox` visual type)
- Text is exactly `UseCase_Bracket.yaml` → `ux_layout_rules.page_1_summary.big_idea` — never authored ad hoc in the report, never paraphrased
- Answers the "so what" before any chart is read (Knaflic *Big Idea*; Storytelling_Principles.md §2)
- Not a KPI value and not a slicer — decoration-free single sentence

**Smart Narrative rules:**
- Must be bound to a governed narrative measure (e.g. `Narrative Text (COM)`) — never left as an
  unconfigured native Smart Narrative visual, which falls back to generic auto-text disconnected
  from the use case's authored insight (docs/plans/UMSETZUNGSPLAN_REPORT_EXZELLENZ.md R1.2)
- Implemented as `cardVisual` bound to the measure via `queryState` (mirrors the `ActionPanel`
  slot's proven pattern in this same report) — this makes the narrative live/filter-context-aware.
  A native `smartNarrativeVisual` has no `queryState` at all (it auto-reads page data) and a static
  `textbox` cannot carry a live measure, so neither satisfies "chart-grounded" on its own.

### KPI & Targets

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| KPI Card | All overview slots | T1, T2, T3, T4 |
| KPI Card with Target / Delta | Trend, Variance | T1, T2 |
| Bullet Graph | `KPI_Cards` (optional variant) | T1, T2 |

**Bullet Graph rules (Few 2005, *Bullet Graph Design Specification*, Perceptual Edge):**
- Use as a space-efficient alternative to gauge/speedometer for KPIs with a defined target and performance bands
- Encodes: primary measure bar + target marker + qualitative performance bands (poor/satisfactory/good)
- Performance bands use **sequential single-hue shading** (light to dark) — NOT red/amber/green fills, to avoid conflating gauge aesthetics with RAG status semantics and to remain colorblind-safe
- Connector requirement: Power BI has no native bullet graph; implement via custom visual (`Enlighten Bullet Chart` or equivalent) or approximate with a `cardVisual` + `progress bar` combo with documented trade-off
- Use when: (1) space is constrained, (2) a KPI requires simultaneous display of actual value, target, and qualitative performance context

---

### Time & Development

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Line Chart | Trend | T1, T2, T3 |
| Area Chart | Trend | T1 (sparingly) |
| Small Multiples | Trend, Ranking | T1, T2, T3 |

Rules:

- Small multiples require identical scale and axis range across all panels — without this the comparison is invalid (Tufte, *The Visual Display of Quantitative Information*, p. 170)
- Use when comparing the same metric across 3–12 entities (regions, products, channels) simultaneously
- Each panel shows exactly one entity; the visual type within panels must be the same across all panels
- Maximum 12 panels per small-multiples visual; above this, use a ranked bar chart instead
- Not allowed on T4 pages — decision context requires focus on one entity, not comparison

---

### Comparison & Ranking

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Horizontal Bar Chart | Ranking, Variance | T1, T2, T3 |
| Column Chart | Ranking | T3 only |
| 100% Stacked Bar | Mix | T1, T2 |

---

### Diagnostics & Root Cause

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Scatter Plot | Root Cause, Prescriptive | T3, T4 |
| Waterfall | Variance | T2 |
| Decomposition Tree | Root Cause | T3 (limited use) |

Rules:

- Scatter plots in T3 require `needs_root_cause = true`
- Scatter plots in T4 require `needs_prescriptive = true`

---

### Prescriptive & Action

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Recommendation Table | Prescriptive | T4 |
| Action Panel | Prescriptive | T4 (optional but recommended) |

---

### Detail & Validation

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Table | Detail Matrix | All templates (Detail pages only) |
| Matrix | Detail Matrix | All templates (Detail pages only) |

Rules:

- Detail visuals are allowed **only on 300-layer pages**
- They must not be the primary insight driver

---

### Process Analysis

| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Funnel Chart | Funnel | T2 only |

Rules:

- Funnel charts are non-default and must be explicitly justified in the use case

---

## Explicitly Disallowed Visuals

The following visuals are **not allowed** under any circumstances:

- Pie / Donut charts
- Gauge / Speedometer charts
- Radar charts
- Tree maps (unless explicitly approved)
- Custom visuals without governance approval

---

## Slicer Rules

- **Standard maximum:** 3 slicers per page
  - Time
  - Organization
  - One domain-specific slicer
- **Optional 4th slicer:** allowed only as a **mode switch**
  - Scenario (Actual / Plan / Forecast)
  - Currency
  - Version

The 4th slicer must not increase analytical complexity.

---

## Key Principle

> **If a visual needs justification, it is usually the wrong visual.**

Visual consistency is a prerequisite for scalable analytics.
