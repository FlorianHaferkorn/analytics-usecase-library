# ALUCA Report Design System (complementary design layer)

> **Provenance.** `generated_by: powerbi-report-design` · `contract_version: 2` · renderer-agnostic.
> **Scope.** The **visual-design layer** for the report set — identity, theme tokens, the title contract,
> the component/archetype grammar, and the chart guardrails, across all **21** governed reports. It decides
> *what a report looks like and why*; it does **not** write PBIR (that is `powerbi-report-authoring`).
> **Companion artifact:** a dashboard-styled render of this document (KPI cards, component gallery, per-report
> theses) is published as a private Artifact.
>
> **This layer does NOT own the narrative.** The per-visual *question → answer → so-what* ladder for every
> report is **generated deterministically** from the governed brackets into
> [`docs/architecture/use_case_storylines.md`](../../../../../docs/architecture/use_case_storylines.md)
> (`tooling/storyline/derive_storyline.py`). This spec **references** it and never duplicates it.
>
> **Aligns with** the report-quality roadmap (`KONZEPT_REPORT_QUALITAET.md` §8, K1 bar → K2 intent) and defers
> to the governed policies that landed with it:
> [`title_policy.py`](../../../../../tooling/reporting/title_policy.py) ·
> [`format_policy.py`](../../../../../tooling/reporting/format_policy.py) ·
> [`Boutique_Craft_Rubric.md`](../../../../../core/templates/page_templates/governance/Boutique_Craft_Rubric.md) ·
> [`color_semantics.yaml`](../../../../../core/templates/page_templates/tokens/color_semantics.yaml) ·
> [`typography.yaml`](../../../../../core/templates/page_templates/tokens/typography.yaml) ·
> [`Visual_Whitelist.md`](../../../../../core/templates/page_templates/governance/Visual_Whitelist.md).

---

## Part A — the design system

### A.1 Identity

- **Tone — *Boutique controlling brief*:** IBCS / ISO 24896-disciplined, editorial, calm-confident. It argues a thesis.
- **Signature:** a Big-Idea header band per page; a **variance anchor** (PVM / vs-plan bridge) as the 30-second centre of gravity; KPI cards that carry the hero value + comparison delta pills + a sparkline; **statement callouts at the mark** (not in titles). This is the look of the reference dashboards, realised in ALUCA's theme.

### A.2 Theme tokens (governed — do not invent)

Bound to `color_semantics.yaml` and `typography.yaml`:

| Token | Value | Use |
|---|---|---|
| Semantic positive / negative / warning / neutral | `#107C10` / `#A4262C` / `#C08000` / `#605E5C` | ISO 3864-1 / IEC 60073 variance — **never inverted**. Delta pills, arrows, deviation cells, annotations. |
| Brand primary / teal / coral | `#0078D4` / `#008575` / `#EF6950` | Data series (brand leads; teal + coral support). |
| Severity tints | `#E6F5E6` / `#FDE7E7` / `#FFF8E1` | Row/background highlight in T3/T4 tables. |
| Surface page / card / row-alt | `#F5F5F5` / `#FFFFFF` / `#F9F9F9` | — |
| Type — body / display / numerals | Segoe UI · DIN (hero value) · **tabular** | Hero KPI ≥ 2× body; tabular numerals for every column of digits. |
| IBCS scenario | AC solid · PL outlined · FC dashed · PY hatched | Scenarios share one hue; **pattern** distinguishes them — a second colour is a BC-COLOR-02 knock-out. |

### A.3 The storytelling contract (governed roles)

**Every report argues one thesis; every visual has one purpose and adds one sentence.** The three governed fields already live in each bracket's `ux_layout_rules` and are generated into `use_case_storylines.md`:

| Field | Role |
|---|---|
| `big_idea` | The report thesis — a claim with a consequence; passes the 5-second thesis test. |
| `question` | The one analytical question a visual answers (its honest default header). |
| `message` + `so_what` | The visual's finding and the clause it adds to the argument. |

The sentences chain: **Signal** (KPI band) → **Driver** (trend) → **Cause** (bridge/ranking) → **Consequence** (matrix) → **Decision** (ActionPanel). A visual with no distinct sentence is cut.

### A.4 The title contract (correction to draft v1 — defers to `title_policy.py`)

BC-NARR-01 ("say it in the title") is right for a **human-authored** report read *after* the data is known. A **generated, static** report is different: at build time the data is unknown and a classic BI title can't recompute, so a hard-coded conclusion **can contradict the chart** the moment the numbers move. The governed rule therefore splits three roles — and promotes the conclusion only where the tool can stand behind it:

| Slot | Content | Honest because |
|---|---|---|
| **title** | **descriptor** — *what* the visual shows ("OEE %, last 6 periods") | data-independent; can never lie |
| **subtitle** | the **question** the visual answers | true regardless of the data ("nothing unusual" is a valid read) |
| **verdict** (`message`) — rendered by capability | `statement_title` (verified + live + whole-subject scalar) → `annotation` (verified + live, Top-N/"where" claim) → `kpi_status` (verified, static: value + semantic delta) → `omit` (unverified: shown nowhere) | never asserts more than the tool can compute |

This is exactly what the reference dashboards do: the verdict lives in a **delta pill** (`kpi_status`) or a **mark annotation** ("Worst semester" / "Best semester"), not the chart title. Top-N / "concentrated in a few" claims stay in the question or the evidence area — a measure-driven title can't receive the visual's own Top-N filter and would silently miscompute.

### A.5 Page grammar & archetypes

Two pages (repo 3-30-300), whitelist visuals only. Governed page-type → archetype:

| page_type | Page role | Archetype | Overview intent |
|---|---|---|---|
| T1 Strategic Overview | Overview "Pulse" | Executive Summary · Portfolio | portfolio health at a glance |
| T2 Tactical Variance | Overview "Pulse" | Analytical · Driver-Bridge | variance vs plan → why off |
| T3 Operational Monitoring | Overview "Pulse" | Operational Monitor | exception queue → what's breaking |
| T4 Prescriptive Recommendation | Detail "Action Matrix" | Narrative + ActionPanel | evidence → owned next step |

**Overview "The Pulse":** KPI-card band (hero value + delta pills + sparkline) → trend (target ref-line, mark annotations) → variance bridge → driver ranking. **Detail "The Action Matrix":** Smart-Narrative → worst-first Top-N matrix at the use case's `evidence_grain` (deviation cells) → ActionPanel from the use case's action codes. Detail is the Overview's drill-through target.

### A.6 Component signatures (see the Artifact for rendered mockups)

`kpi_card` (hero DIN value · comparison delta pills · sparkline · optional dark **hero** variant) · `trend_line` (target reference line · verdict as mark annotation) · `waterfall` (IBCS PVM bridge, scenario patterns) · `bar_chart` / `ranking` (worst-first, one highlight) · `matrix` (worst-first Top-N, data-bar deviation cells, action-code column) · `smart_narrative` · `slicer`.

### A.7 Guardrails — the five knock-outs

| Knock-out | Applied |
|---|---|
| BC-CHART-01 | € and % never share an axis — split visuals or dual labelled axes. |
| BC-CHART-10 | Every evidence matrix sorted worst-first, curated to Top-N. |
| BC-NARR-01 | Titles follow the A.4 contract (descriptor / question / verified verdict). |
| BC-BRAND-01 | One composed theme (A.2); never the renderer default. |
| BC-COLOR-02 | Colour semantic only; one highlight per page; scenarios by pattern, not colour. |

### A.8 Composition principles & authoring process

The tokens (A.2), title contract (A.4), and knock-outs (A.7) govern the **hard, machine-checkable** layer. This section names the **compositional** layer above them — the human-design intent that lifts the *layout*, not just the correctness. Each principle is **enforced by** a governed artefact; the point is to build reports *against a named intent*, not only against tokens. (Provenance: reconciled from B. Dohmen's "smart practices" methodology, the BIBB grid system, and the Draft BI layout guide against ALUCA's own governance.)

| Principle | Intent | Enforced by |
|---|---|---|
| **Hierarchy & scan path** | Primary KPI first (top-left / hero); size + colour + position agree; the eye reaches the thesis in ~5 s (Z-pattern). | T1/T2 archetype (A.5); hero value ≥ 2× body (A.2) |
| **One focal point per page** | Exactly one hero — a colour/dark hero card or a single highlighted mark — anchors the page; everything else recedes. This is the single most visible trait of the reference dashboards. | BC-COLOR-02 (one highlight/page); `kpi_card` dark-hero variant (A.6) |
| **Whitespace as grouping** | Tight spacing binds a group; air separates groups (spatial zones); no visual touches the canvas edge. | Master Grid 12×12, 32 px margin / 16 px gutter (`apply_page_layout.py`) |
| **Less is more** | Every decoration is cognitive load. Crowded page → cut a visual, never shrink the whitespace. | BC-COLOR-02 (no decorative colour); BC-BRAND-01 (composed theme) |
| **Cross-page consistency** | Card heights, chart widths, and slicer/filter positions match across both pages. | component signatures (A.6); grid |
| **Contrast floor** | Semantic colours + data series ≥ WCAG 2.2 AA (4.5:1 text / 3:1 non-text); colour is never the sole encoding — pair with icon/pattern. | `color_semantics.yaml` (AA-validated hexes); IBCS scenario patterns (A.2) |

**Authoring process** — B. Dohmen's four steps, mapped to ALUCA's governed inputs (the *how*, complementing the design *system*):

1. **Requirements** — the bracket's `decision_question` + `big_idea` (who reads it; which decision in 30 s).
2. **Structure** — page grammar & archetype (A.5) + the semantic model + the generated storyline ladder (`use_case_storylines.md`).
3. **Build visuals** — component signatures (A.6) against the whitelist; honest titles (A.4); the five knock-outs (A.7).
4. **Place** — the Master Grid, applying hierarchy, the single focal point, and whitespace zones (above).

**QA before "done"** (not visible in JSON): reload in Power BI Desktop → screenshot each page → review hierarchy, spacing, alignment, readability, and the focal point → one improvement pass → run the accessibility check. Structural validation (`powerbi-report-author validate` / Stage-1 / boutique scorecard) *precedes* the visual review and does not replace it.

---

## Part B — the 21 reports (design cards)

Each report's **thesis** (governed `big_idea`), its **archetype/variant**, and the **action codes** it lands on. The per-visual *question → answer → so-what* ladder is in
[`use_case_storylines.md`](../../../../../docs/architecture/use_case_storylines.md) — generated, not repeated here.

### Commercial
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **COM-001** Sales Performance vs Plan & LY | `margin.gm.pct` | T2 Driver-Bridge | Net Sales beats plan but GM% is below target — adverse DACH mix is the driver, and the lead is narrowing, so act on price/mix now, not volume. | C-M2.1, C-S1.1, C-S1.2 |
| **COM-002** Margin & Price Performance | `margin.gm.pct` | T2 Driver-Bridge | Gross margin is compressing on price concessions and adverse mix — the levers are commercial discipline, not demand. | C-M2.2, C-P4.1, C-S1.2 |
| **COM-003** Customer Value | `crm.clv.amount` | T1 Portfolio | CLV growth has stalled — mid-tier churn is eroding the base; targeted retention there stops the erosion before it compounds. | C-C3.1, C-C3.2 |
| **COM-004** Promotion Effectiveness | `sales.promo.roi.pct` | T1 Portfolio | Promo ROI misses — cannibalization on thin margin means the mechanics need redesign, not more spend. | C-P4.1, C-M2.1, C-M2.2 |
| **COM-005** Sales Pipeline Conversion | `sales.pipeline.coverage.ratio` | T3 Monitor | Pipeline coverage is below the safe threshold, and the gap is a win-rate problem, not a volume shortage. | (discovery) |
| **COM-IND-R001** Basket & Category Cross-Sell | `retail.category.crosssell_rate.pct` | T1 Portfolio | Cross-sell under-attaches in a few high-traffic categories — the lever is targeted bundling, not blanket promotion. | C-M3.1 |

### Finance
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **FIN-001** Cash & Liquidity Performance | `wc.ccc.days` | T1 Trend | Cash conversion is deteriorating — DSO extension squeezes headroom; the fix is receivables and inventory days, not stretching payables. | F-C1.1, F-C1.2, F-C1.4, S-I1.2 |
| **FIN-002** Cost Performance | `cost.unit.amount` | T1 Portfolio | Input inflation is outrunning pricing — COGS% is expanding and erodes margin within ~2 quarters unless productivity or price responds. | F-K2.1–F-K2.4 |
| **FIN-003** Earnings Performance vs Plan | `margin.ebitda.pct` | T3 Monitor | EBITDA margin trails plan and the gap is opex-led, while revenue and gross margin hold. | (discovery) |

### Operations
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **OPS-001** Operations Performance | `ops.oee.pct` | T3 Exception Queue | OEE is below target and widening — availability losses are ~70% of the gap, so maintenance moves the needle fastest. | O-O1.1–O-O1.4 |
| **OPS-002** Asset Performance | `ops.mtbf.hours` | T1 Portfolio | Availability is declining — backlog accumulates faster than it clears, trending below the level the plan needs. | O-A2.1–O-A2.5 |
| **OPS-003** Quality & Yield | `quality.fpy.pct` | T3 Process Control | Scrap is above target — yield loss concentrates on two lines, so line-level containment beats a plant-wide program. | O-Q3.1–O-Q3.5 |

### Supply Chain
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **SCM-001** Inventory Performance | `inv.dio.days` | T1 Portfolio | Turnover is falling — dead stock in three SKU clusters ties up capital; the root cause is forecast accuracy, not capacity. | S-I1.1–S-I1.5 |
| **SCM-002** Supply Reliability & OTIF | `supply.otif.pct` | T3 Process Control | OTIF is down — on-time is the drag, not in-full; failures concentrate in two categories, so carrier/lane fixes beat stock buffers. | S-R2.1–S-R2.5 |
| **SCM-003** Forecast vs Actual | `plan.forecast.accuracy.pct` | T2 Comparative | Forecast error is systematic bias — not noise — in the mid-range cluster, so recalibration beats manual overrides. | S-F3.1–S-F3.4 |
| **SCM-004** Procurement & Supplier Performance | `procurement.savings.realized.pct` | T3 Monitor | Savings realisation is behind target — the leak is off-contract spend concentrated in a few categories. | (discovery) |

### Experience & Executive
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **XD-001** Service Level Performance | `svc.sla.attainment.pct` | T3 Process Control | Backlog is building toward SLA breaches — falling FCR and rising escalations point to a capability gap; fix FCR to cut both. | X-S1.1–X-S1.4 |
| **XD-002** Resource Utilization | `res.utilization.pct` | T1 Portfolio | Utilization is above sustainable levels — two teams are overloaded and overtime is masking the coming capacity shortfall. | X-R2.1–X-R2.4 |
| **XD-003** Executive KPI Overview | `enterprise.value_at_risk.index` | T1 Portfolio | Growth is on track but GM% and OTIF flash execution risk — two units below threshold on both need escalation. | X-E3.2 |
| **XD-004** Executive Action Governance | `enterprise.action_outcome_rate.pct` | T1 Portfolio | Governance is judged by verified outcomes, not actions closed — value-at-risk concentrates where follow-through is weakest. | Impactful-15 |

### People
| Report | KPI | Archetype | Thesis | Actions |
|---|---|---|---|---|
| **HR-001** Workforce Performance & Retention | `people.attrition.pct` | T3 Monitor | Attrition is rising in the lowest-engagement segments — a concentrated retention problem, not a broad one. | (discovery) |

---

## Part C — consistency & handoff

- **One theme, one identity** (BC-BRAND-01/02): all 21 share A.2's tokens, the Big-Idea band, hero-value type, tabular numerals, and IBCS scenario patterns.
- **Honest titles** (BC-NARR-01 via `title_policy.py`): descriptor title · question subtitle · verdict only where verified/live (A.4).
- **Evidence discipline** (BC-CHART-10) and **scale discipline** (BC-CHART-01) on every page.
- **Grounding** (K4): hero KPIs carry a benchmark reference-label once `benchmark_catalog` lands, so the thesis reads expert, not templated.
- **Handoff:** this design layer → `powerbi-report-authoring` for page/visual/theme mechanics and PBIR emission → validate (Stage-1 + boutique scorecard + `check_storyline` / `check_visual_format`) → Desktop check.

---

## Part D — the visual idiom catalog

Per visual: the analytical **question** it answers, the **best-perceived form** for it (Cleveland-McGill / IBCS, governed by [`pbi-design/references/charts.md`](../../../../../.claude/skills/pbi-design/references/charts.md)), the **anti-patterns** to avoid, and the realisation across four tool tracks — **Power BI native · SVG-DAX · Deneb/Vega-Lite · Web (D3/Recharts/ECharts)**. A rendered companion grows alongside as a private Artifact. Renderer-agnostic (`contract_version: 2`): the *form* is governed; the *tool* is a realisation.

**Encoding rule (governed).** Magnitude → **length/position** (perceptual rank 1–3), never the colour of a number (rank 9–10). Direction → colour **and** sign/arrow, never colour alone. **Size is the only highlight attribute** (`cookbook.md`). Every element serves one purpose or it is cut.

### D.1 `kpi_card` — a metric, its verdict, its trajectory
- **Question:** how are we doing on X vs plan/target, and where is it heading?
- **Structure:** label · hero value (a number — best for a precise single value) · deviation · **chart full-width below**.
- **Best form, by sub-question:** deviation bar (Δ vs plan, zero line) · bullet graph (vs target + ranges — Few, the governed gauge replacement) · trend + target reference (trajectory) · variance sparkline (gap over time — a *different sentence* than the level-trend) · IBCS overlapped AC/PL bars (true scale, scenario by pattern) · dark hero (the one focal point per page).
- **Avoid:** the tinted delta pill (magnitude on colour + decorative fill); gauge/speedometer.
- **Tools:** native `cardVisual` value + a companion slim `clusteredBarChart` for Δ (native can't colour one callout by sign) · SVG-DAX one `ImageUrl` measure (`<rect>` bar from the plan line, width = normalised Δ, fill by `SIGN`) · Vega-Lite `mark:bar` + `rule@0` + layered `text` · Web Recharts `BarChart` + `ReferenceLine x=0`.

### D.2 `trend_line` — development over time, against plan
- **Question:** how is X developing, and is the gap to plan closing or widening?
- **Best form:** a line (the eye reads the curve as trajectory — `charts.md` „Entwicklung über Zeit → Liniendiagramm"); honest **labelled** axis; plan as a **dashed reference line**; one **emphasized endpoint** carrying the verdict; direct end-label, no legend.
- **Avoid:** bars/pie for a time series; an auto-scaled sparkline with no reference (graphical integrity — Tufte); a dual Y-axis without a stated semantic reason.
- **Tools:** native `lineChart` + analytics-pane `y1AxisReferenceLine` (target measure) + last-point data label · SVG-DAX `CONCATENATEX` → `<polyline>` + plan `<line>` + endpoint `<circle>` · Vega-Lite `layer[ line, rule@plan, point(last), text ]` (`x:temporal`, `y:quantitative` honest domain) · Web Recharts `LineChart` + `ReferenceLine y=plan` + last `Label`, or D3 `d3.line()` + annotation.

### Roadmap — one visual per increment
`kpi_card` ✅ · `trend_line` ✅ · **`bar_chart` / ranking** (next — sorted worst-first Top-N, one highlight) · `waterfall` / PVM bridge · evidence `matrix` · `smart_narrative` · `slicer`. Each increment updates this section **and** the Artifact together (both synchron).
