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
| S7 | Few (**2006**), *Information Dashboard Design*, O'Reilly | Dashboard hierarchy, attention management | evidence-backed |
| S8 | Few (2005), *Bullet Graph Design Specification*, Perceptual Edge | Bullet graph rules | evidence-backed |
| S9 | IBCS Standards Version 2.0 (IBCS Association 2026, CC BY-SA 4.0) / ISO 24896 *Notation for business reporting* (UNIFY follows ISO 24896 Clause 4, IBCS 2.0 p. 25); rules as catalogued in `docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml` | Scenario notation, variance semantics, SUCCESS rules | evidence-backed |
| S10 | SQLBI / Buhler (2024), "The 3-30-300 Rule" | Layer structure, zone order | **heuristic** — see note |
| S11 | Tufte (1983), *The Visual Display of Quantitative Information* | Data-ink ratio, small multiples, axes | evidence-backed |
| S12 | Microsoft Power BI design guidance (2025) | Production layout, accessibility, performance | evidence-backed |
| S13 | Meridian Report Layout reference HTML | Depth-layer chrome, card system, navigation | meridian-inspired |
| S14 | WCAG 2.1 AA (W3C, 2018) | Accessibility: color contrast, focus, labels | evidence-backed |
| S15 | Bertin (1983), *Semiology of Graphics* | Retinal variables: position, size, shape, color, orientation, texture | evidence-backed |

### Korrekturen an dieser Tafel (02.08.2026, Recherche gegen den eigenen Stand)

Drei Befunde aus einer Recherche mit dem ausdrücklichen Auftrag, diese Tafel zu
**widerlegen**:

1. **S7 war falsch datiert.** *Information Dashboard Design* erschien **2006** bei
   O'Reilly, nicht 2004. Der 2004er Beitrag ist „Dashboard Confusion" (Intelligent
   Enterprise) — ein anderer Text. Verifiziert über Open Library, ACM DL, InfoVis-Wiki.
2. **S10 ist keine „evidence-backed" Quelle, sondern eine Heuristik.** Die 3-30-300-Regel
   ist eine ausdrückliche **Paraphrase** von Shneidermans Visual-Information-Seeking-Mantra
   (S1). Für die konkreten Schwellen 3 / 30 / 300 Sekunden ließ sich **keine** Studie
   finden, die sie misst oder validiert. Die Regel bleibt nützlich — als Merkhilfe mit
   echter Ahnenreihe, nicht als gemessene Zeitschwelle. Sie als belegt zu führen war eine
   Überhöhung.
3. **Die IBCS-Zuschreibung „M–A–K–T" ist nicht verifizierbar.** `PAGE_TYPE_TAXONOMY.md`
   begründet die vier Familien u. a. mit *„IBCS uses 4: M–Message, A–Analysis, K–KPI,
   T–Table"*. Diese Kategorisierung war weder auf ibcs.com noch in Sekundärquellen
   auffindbar (ibcs.com liefert aus dieser Umgebung 403 — „nicht auffindbar" ist also
   nicht „falsch", aber es ist auch kein Beleg).

**Die Schlussfolgerung überlebt trotzdem — und zwar besser belegt als vorher.** Die
Obergrenze von 4–5 Archetypen stützt sich jetzt auf drei unabhängige, prüfbare Quellen
statt auf eine unauffindbare: Few (2006) 3 Typen, Eckerson (*Performance Dashboards*,
Wiley, 2. Aufl. 2010) 3 Top-Level-Typen, und **Microsofts eigener `powerbi-report-design`-
Skill (2026) mit 5 Archetypen** (S16).

| ID | Source | Domain | Status |
|---|---|---|---|
| S16 | `microsoft/skills-for-fabric`, Skill `powerbi-report-design` (2026) | 5 Report-Archetypen, 12-Spalten-Raster, **Zonen als „advisory, not mandatory"** | evidence-backed (offizielles MS-Artefakt) |
| S17 | Eckerson, *Performance Dashboards*, Wiley, 2. Aufl. (2010) | 3 Top-Level-Dashboard-Typen | evidence-backed |
| S18 | Wang et al. (2019), *DataShot*, IEEE VIS | korpusgetriebene Templates (245 Infografiken), In-Lab-Studie | evidence-backed |

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

**Source:** IBCS Version 2.0 (2026) / ISO 24896 — UN 3.2 *Unify scenarios* (p. 44, scenario notation), UN 4.1 *Unify scenario analyses* (p. 51, variance notation) and EX 4.2 *Add variances* (p. 141). Rule ids before 2.0 (2021 edition: U4, E3) are superseded.

> **Deviation from IBCS 2.0 (open, 02.10.2026):** the two colour bullets above predate 2.0.
> UN 4.1 (p. 51) colours variances by rating: desirable bright green, undesirable dark red,
> not rated blue; colour-vision fallback blue-green for desirable, black/white fallback in
> greys. The Visual Library profile `ibcs` (`_notation_profiles.yaml`) already follows UN 4.1.
> Aligning this table is a separate decision (it touches Studio CSS and template tokens).

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

### 3.8 Verbindlichkeit ist deklariert, nicht abgeleitet [S16]

S16 sagt wörtlich: *„Treat archetype zones as advisory, not mandatory. A variant is a
layout starting point, not a required component checklist."* Das steht in offenem
Widerspruch zu einem Gate, das einen fehlenden Slot rot werden lässt — und der
Widerspruch wird hier aufgelöst, nicht überlesen.

Es sind **zwei** Fragen, nicht eine abgestufte:

1. **Muss der Slot existieren?** Das ist S16s Punkt: jede Zone muss ihren Platz
   verdienen, indem sie eine eigene analytische Frage beantwortet. Im Manifest ist das
   `mandatory: true|false`.
2. **Wie hart wird eine bereits zugesagte Pflicht eingefordert?** Das ist eine Frage an
   das Gate, nicht an das Design. Im Manifest ist das `severity: error|warning`.

Für (2) gilt: die Härte richtet sich nach der **Datenlage der Regel**, nie nach der Art
des Slots. Das folgt der Praxis von ESLint (`off/warn/error`), HashiCorp Sentinel
(`advisory/soft-mandatory/hard-mandatory`), OPA Gatekeeper (`dryrun/warn/deny`) und
Kubernetes Pod Security (`enforce/audit/warn`) — alle vier trennen Regel von Härte, und
in keinem ist die Achse der Objekttyp. Eine zwischenzeitlich erwogene Staffelung
„Chrome hart, Inhalt weich" ist als Eigenerfindung verworfen; sie liess sich in keinem
geprüften System belegen (Grafana Foundation SDK, LookML, Superset, Evidence.dev).

Praktische Regel: ein Pflicht-Slot startet auf `warning` und steigt auf `error`, sobald
echte Läufe das tragen. Herleitung und Messstand in
[`docs/plans/KONZEPT_LAYOUT_SYSTEM.md` §15](../../../docs/plans/KONZEPT_LAYOUT_SYSTEM.md).

### 3.9 Titles and Key Message — IBCS UN 2.1 / UN 2.2 [S9]

Decided 08.10.2026 (ALUCA ledger A-34, mirror of Freelancing D-641). A title **describes**, it
never judges; the conclusion has its own slot.

| Element | Rule | Field / code |
|---|---|---|
| Page title | Three lines: **who** (reporting unit), **what** (measure bold, unit normal: "Gross margin in %"), **when** (period, scenarios, variances: "Jan..Dec 2026, AC and PL"). No evaluative words. | `page_1_summary.title_lines {who, what, unit, when}`; `title_policy.TitleLines` |
| Key message | Own slot at one fixed position, above the page title (`above_title`, the default; `right_of_title` allowed by the standard, not rendered in PBIR). Unverified it is always framed "Expected finding —". The block grows with the wrapped key message, the grid moves below it. | `big_idea` → first paragraph of the Zone-0 title block (`page_scaffold_generator/title_block.py`); position `page_1_summary.key_message_position`; `title_policy.frame_key_message` |
| Visual header | The governed question leads; the exhibit message follows as subtitle (framed "Expected finding —" until value-verified). The message is **never** the visual title — checked on the committed PBIR. | `title_policy.resolve_header`; `tooling/validation/check_exhibit_message.py` |
| Tool-neutral contract | Title = descriptor (or line 2), verdict rendered as `key_message` / `annotation` / `kpi_status` / `omit`. `statement_title` is locked. | `title_policy.title_contract`, `LOCKED_VERDICT_RENDERS` |
| Small screens | The three lines joined with " \| " in one line. | `title_policy.single_line` |

Presentation per variant: IBCS and the PBIR output render three lines with the key message above;
Story and Brand render one line with the measure bold and the subtitle "who · when"
(`title_policy.hybrid`). The content (who, what, when, key message) is held once.

**Superseded:** "say it in the title" (BC-NARR-01 until 08.10.2026, `assert_statement_titles=True` as
the `PageBuilder` default). A static title that carries a statement can contradict the chart below
it, and UN 2.2 sets `evaluative_words_allowed: false`.

**Source:** IBCS Version 2.0 (2026) / ISO 24896 — UN 2.1 *Unify key messages* (p. 28), UN 2.2 *Unify
titles and subtitles* (p. 29), UN 1.2 units (p. 26), as catalogued in
`docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml`.

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
| A title that carries a statement or an evaluative word | S9 — IBCS 2.0 UN 2.2; the conclusion belongs in the key-message slot (UN 2.1, §3.9) |

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
| Descriptive three-line title, key message above (§3.9) | evidence-backed | S9 |
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
