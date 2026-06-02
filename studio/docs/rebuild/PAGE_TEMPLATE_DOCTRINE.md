# Page Template Doctrine

> **Status:** Authoritative  
> **Governs:** All page template design decisions in the Analytics Use Case Library  
> **Feeds into:** `PAGE_TYPE_TAXONOMY.md` · `VISUAL_BAUKASTEN.md` · `REPORT_ENGINE_TARGET_ARCHITECTURE.md`  
> **Source authority:** See §2 — every rule carries a source tag.  
> **Do not edit** without updating the source tag and DoD check.

---

## 1. Doctrine Purpose

This document is the **canonical evidence base** for every structural and visual decision made in the Analytics Use Case Library's page template system.

It synthesizes:
- Peer-reviewed visualization and cognitive science research
- Internationally accepted business reporting standards (IBCS)
- Microsoft Power BI guidance for production constraints
- Internal core specs built on these sources

Every rule in this document carries one of four status labels:

| Status | Meaning |
|---|---|
| `evidence-backed` | Directly derived from a cited peer-reviewed source or internationally accepted standard |
| `meridian-inspired` | Derived from the Meridian reference layout; adopted because consistent with evidence |
| `project-specific` | Internal governance decision not contradicted by evidence |
| `⚠ aesthetic-only` | Not used. Rules without evidence basis are not admitted to this doctrine. |

---

## 2. Source Matrix

| ID | Source | Domain | Status |
|---|---|---|---|
| S1 | Shneiderman (1996), "The Eyes Have It", *IEEE Visual Languages* | Information architecture, progressive disclosure | evidence-backed |
| S2 | Cleveland & McGill (1984), "Graphical Perception", *JASA* | Visual encoding effectiveness hierarchy | evidence-backed |
| S3 | Munzner (2014), *Visualization Analysis & Design*, A K Peters/CRC Press | Nested model: task → data → encoding | evidence-backed |
| S4 | Sweller (1988), Cognitive Load Theory, *Cognitive Science* 12(3) | Limits on visual count, extraneous load reduction | evidence-backed |
| S5 | Miller (1956), "The Magical Number Seven", *Psychological Review* | Working memory chunks: basis for field limits | evidence-backed |
| S6 | Hick (1952) / Hyman (1953), choice reaction time law | Slicer count limits | evidence-backed |
| S7 | Few (2004), *Information Dashboard Design*, O'Reilly | Dashboard hierarchy, attention management | evidence-backed |
| S8 | Few (2005), *Bullet Graph Design Specification*, Perceptual Edge | Bullet graph rules | evidence-backed |
| S9 | IBCS — International Business Communication Standards (2021 edition) | Scenario notation, variance semantics, SUCCESS rules | evidence-backed |
| S10 | SQLBI (2022), "The 3-30-300 Rule" | Layer structure, zone order | evidence-backed |
| S11 | Tufte (1983), *The Visual Display of Quantitative Information* | Data-ink ratio, small multiples, axes | evidence-backed |
| S12 | Microsoft Power BI design guidance (2025) | Production layout, accessibility, performance | evidence-backed |
| S13 | Meridian Report Layout reference HTML | Depth-layer chrome, card system, navigation | meridian-inspired |
| S14 | WCAG 2.1 AA (W3C, 2018) | Accessibility: color contrast, focus, labels | evidence-backed |
| S15 | Bertin (1983), *Semiology of Graphics* | Retinal variables: position, size, shape, color, orientation, texture | evidence-backed |

---

## 3. Foundational Principles

### 3.1 Decision-First Design [S3, S1]

Every page exists to answer **one specific decision question**. Design serves that question; it does not compete with it.

Munzner's nested model (S3) is the primary design framework:
1. **Domain task** — what decision must be made? (T1–T4 page types)
2. **Data abstraction** — what information is required? (slot definitions)
3. **Visual encoding** — how is that information encoded? (visual baukasten)
4. **Algorithm** — how is the encoding rendered? (engine/generator)

A failure at any layer propagates down. No visual quality compensates for a wrong domain task or wrong data abstraction.

**Source:** Munzner (2014), ch. 4 "Nested Model Revised". The nested model is the most widely accepted framework in visualization research for evaluating design validity at each level independently.

### 3.2 Progressive Disclosure — 3-30-300 [S1, S10]

Information depth is structured by the time a user has available:

| Layer | Time | Primary Question | Design Imperative |
|---|---|---|---|
| **3 seconds** | Glance | Am I on track? | Immediate orientation — status and signal |
| **30 seconds** | Scan | Why am I off track? | Driver explanation — trends, variance, ranking |
| **300 seconds** | Analyse | What exactly happened / what do I do? | Validation and action |

This layering is grounded in Shneiderman (S1): *"overview first, zoom and filter, then details on demand"* — the foundational UX principle for information systems.

SQLBI (S10) provides the BI-specific adaptation: the 3-30-300 rule as a practical zone model for report pages.

**Not every page implements all three layers.** Each use case explicitly declares its primary layer(s) in `UseCase_Bracket.yaml (ux_layout_rules)`.

### 3.3 Perceptual Accuracy Hierarchy [S2, S15]

Visual encodings are not equally effective. Cleveland & McGill (1984) established an empirically tested hierarchy (ordered from most to least perceptually accurate):

1. Position on a common scale
2. Position on non-aligned scales
3. Length
4. Direction / angle
5. Area
6. Volume
7. Color saturation / density
8. Color hue

**Implication for visual selection:** Prefer position-based encodings (line charts, bar charts with shared axis) over area- or angle-based encodings (pie, area, bubble). This is not an aesthetic preference — it is an empirically validated perceptual fact.

Bertin (S15) adds: position (x, y) is the most powerful retinal variable for quantitative data. Color hue is unsuitable for quantitative magnitude; use it only for categorical distinctions.

### 3.4 Cognitive Load Limits [S4, S5, S6]

| Limit | Value | Source |
|---|---|---|
| Max visible visuals per page | 20 | S4 — extraneous cognitive load from visual search overhead |
| Max data fields per visual | 6 | S5 — Miller's 7±2 working memory chunks |
| Max slicers per page | 3 (4th allowed as mode switch only) | S6 — Hick/Hyman: choice RT grows as log₂(n+1) |
| No vertical scroll on report pages | Hard rule | S4 — navigation competes with analytical load |

### 3.5 Variance Semantics — IBCS Rules [S9]

Any page showing variances or comparisons must follow IBCS scenario notation:

| Abbreviation | Meaning |
|---|---|
| AC | Actual (current period, realized) |
| PY | Prior Year |
| PL | Plan / Budget |
| FC | Forecast |
| Δ | Absolute variance |
| Δ% | Relative variance |

Rules:
- Favorable variances: **positive Δ** (blue or dark) — never "green" in isolation (colorblind safety, S14)
- Unfavorable variances: **negative Δ** (orange or highlighted) — never raw red
- Both absolute and relative variance must be shown simultaneously on variance visuals
- Reference scenario must always be visible (Plan bar or line as reference, not hidden)

**Source:** IBCS SUCCESS rules (2021), specifically UNIFY U4 (consistent scenario notation) and EXPRESS E3 (show absolute + relative variance).

### 3.6 Reading Patterns [S7, S12]

| Pattern | Applies to | Implication |
|---|---|---|
| **Z-pattern** | T1 overview, T2 overview | Top-left → top-right → diagonal → bottom-right. Hero KPI top-left, primary chart spans top. |
| **F-pattern** | T3 detail, T4 detail | Scan top, then down left column. Exception list or action panel anchors left; slicer pane on left. |

Use Z-pattern for pages where the page state itself is the primary communication (T1, T2 overview). Use F-pattern for pages that are tool-like — frequently used, operationally focused (T3, T4 detail).

**Sources:** Few (2004) ch. 4 on attention management; Microsoft design guidance (S12) on top-left visual priority.

### 3.7 Accessibility [S14]

All pages must meet WCAG 2.1 AA at minimum:
- Contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI components
- No meaning conveyed by color alone — always add shape, label, or pattern
- All visuals must have alt-text or title descriptions for screen readers
- Keyboard navigation support where the tool allows

Power BI Fabric specifics: use the built-in Accessibility Checker; set alt text on all visuals; ensure tab order matches the reading direction.

---

## 4. Design Canvas and Grid

### 4.1 Canonical Canvases

| Context | Canvas | Notes |
|---|---|---|
| Design base (all specifications) | **1280 × 720 px** | All coordinates in this library use this base |
| Power BI / Fabric production | **1920 × 1080 px** | Scale 1.5× from base; font compensation required |
| Web / browser | Fluid viewport | Use `clamp()` rem units |
| PDF / print export | 1920 × 1080 px | +2pt on all text roles for print legibility |

The 1280×720 design base was chosen because it matches the most common BI tool default canvas and is 16:9 (TV/screen standard), making it cognitively predictable and layout-consistent across tools. [S12, project-specific]

### 4.2 Grid System

All layouts use a **12-column × 12-row logical unit (LU) grid** (canonical: `tokens/layout_grid.yaml`).

| Parameter | Value |
|---|---|
| Grid | 12 × 12 LU |
| Outer margin | 32 px (design base) |
| Gutter | 16 px |
| Internal padding | 8 px |
| Zone gap | 40 px |

Spacing hierarchy: Zone gap (40) > Gutter (16) > Internal padding (8). [meridian-inspired, consistent with S11]

---

## 5. What This Doctrine Prohibits

The following are **never permitted**, regardless of use case:

| Prohibition | Evidence |
|---|---|
| Pie / donut charts | S2 — angle encoding is 5th in accuracy hierarchy; misleading for comparison |
| Gauge / speedometer | S7 — Few (2004): gauges waste 90% of ink on non-data elements; use KPI card |
| Radar / spider charts | S2 — area and angle encoding; comparisons across axes are perceptually invalid |
| Vertical scroll on report pages | S4 — navigation competes with analytical load |
| Color as the sole variance indicator | S9 — IBCS requires notation, not just color; S14 — WCAG colorblind safety |
| Exploratory controls on T1/T2/T4 | S3 — wrong domain task; exploration ≠ decision orientation |
| Custom visuals without governance approval | S12 — performance, accessibility, rendering stability |
| More than 8 driver bars in a waterfall | S5 — exceeds working memory; group smaller items as "Other" |

---

## 6. Meridian Reference Evaluation

The Meridian HTML reference layout was evaluated as a *design reference artifact*, not as a scientific source.

Elements adopted (tagged `meridian-inspired` where used):
- Depth-layer chrome: color-coded strip at top-left indicating 3s / 30s / 300s layer — consistent with S1 progressive disclosure
- Card system and spacing — consistent with S11 data-ink principles
- Navigation breadcrumb with `domain · function · page type` pattern — project-specific, retained

Elements **not adopted**:
- Decorative gradients on chart backgrounds — contradict S11 data-ink ratio principle
- Animated transitions between states — increase extraneous cognitive load (S4)
- Free-form filter panels — contradict max-3-slicer rule (S6)

---

## 7. Rule Status Summary

| Rule | Status | Source(s) |
|---|---|---|
| Decision-first page design | evidence-backed | S3 |
| 3-30-300 layering | evidence-backed | S1, S10 |
| Position-first encoding | evidence-backed | S2, S15 |
| Max 20 visuals | evidence-backed | S4 |
| Max 6 fields per visual | evidence-backed | S5 |
| Max 3 slicers | evidence-backed | S6 |
| No vertical scroll | evidence-backed | S4 |
| IBCS variance notation | evidence-backed | S9 |
| Z/F reading patterns | evidence-backed | S7, S12 |
| 1280×720 design base | project-specific | S12 (PBI default) |
| 12×12 LU grid | meridian-inspired | S11 (data-ink) |
| Outer margin 32px | meridian-inspired | S11 |
| No pie/donut | evidence-backed | S2 |
| No gauge | evidence-backed | S7 |
| No vertical scroll | evidence-backed | S4 |
| WCAG 2.1 AA | evidence-backed | S14 |
| Breadcrumb nav pattern | meridian-inspired | project-specific |

---

## 8. Definition of Done

This doctrine is complete when:
- [ ] Every rule has a source tag (evidence-backed, meridian-inspired, or project-specific)
- [ ] No rule is marked aesthetic-only
- [ ] Source conflicts are explicitly noted (none identified at time of writing)
- [ ] `PAGE_TYPE_TAXONOMY.md` references this document as its authority
- [ ] `VISUAL_BAUKASTEN.md` references this document for encoding decisions
- [ ] `REPORT_ENGINE_TARGET_ARCHITECTURE.md` references this document for validation gate definitions
