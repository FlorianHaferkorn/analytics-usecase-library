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

### KPI & Targets
| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| KPI Card | All overview slots | T1, T2, T3, T4 |
| KPI Card with Target / Delta | Trend, Variance | T1, T2 |

---

### Time & Development
| Visual | Allowed Slots | Allowed Templates |
|------|---------------|-------------------|
| Line Chart | Trend | T1, T2, T3 |
| Area Chart | Trend | T1 (sparingly) |

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
