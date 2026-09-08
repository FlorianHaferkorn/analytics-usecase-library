# Page Templates

> **Canonical UX standards:** [ux_design_system.md](../../strategy_operating_model/operating_model/ux_design_system.md).
> These templates implement the UX system; they must not redefine layout or interaction principles.

This folder defines the **only allowed page types** for reports built with ALUCA (Analytics Library of Use Cases).

The goal is not design freedom, but **decision clarity, scalability, and reuse**.

---

## The 4 Golden Page Types (Mandatory)

| Template | Core Question | Primary Audience | Decision Type |
|---|---|---|---|
| **T1 — Strategic Overview** | *Are we on track?* | Executive, board | Directional |
| **T2 — Tactical Variance** | *Why are we off target?* | Management, domain leads | Diagnostic |
| **T3 — Operational Monitoring** | *Where is execution breaking now?* | Operations, process owners | Corrective |
| **T4 — Prescriptive Recommendation** | *What should we do next?* | Decision owners | Prescriptive |

Each use case is implemented as **exactly two pages**:
- one **Overview page** (3s + 30s layer)
- one **Detail page** (300s layer)

---

## Document Map

### Core Specs

| Document | Purpose |
|---|---|
| `Page_Spec_3_30_300.md` | Slot overview — where which visual goes and why |
| `Design_Spec_3_30_300.md` | **Authoritative** tool-agnostic layout spec (canvas, grid, zones, visual grammar, accessibility) |
| `Storytelling_Principles.md` | Narrative and content quality principles — Big Idea, Narrative Arc, pre-attentive attributes, color, typography |
| `Content_Quality_Guide.md` | Content standards — visual titles, KPI labels, Smart Narrative templates, Action Panel copy |
| `Visual_Delivery_System.md` | Shared visual contract for the dark Studio workbench and light consumer reports |
| `Connector_Spec.md` | Connector contract — what any tool connector must implement; compliance checklist |
| `Abstract_Visual_Types.md` | Tool-agnostic visual type vocabulary with cross-tool mapping table |

### Page Type Definitions

| Document | Template |
|---|---|
| `page_types/T1_Strategic_Overview.md` | T1 — including Narrative Arc |
| `page_types/T2_Tactical_Variance.md` | T2 — including Narrative Arc |
| `page_types/T3_Operational_Monitoring.md` | T3 — including Narrative Arc |
| `page_types/T4_Prescriptive_Recommendation.md` | T4 — including Narrative Arc |

### Governance

| Document | Purpose |
|---|---|
| `governance/Slot_Definitions.md` | Semantic slot definitions and allowed templates |
| `governance/Visual_Whitelist.md` | Allowed visual types by slot and template |
| `governance/Color_Semantics_Formatting.md` | Color roles, KPI card formatting, chart formatting rules (prose) |
| `governance/Layout_Grid_System.md` | 12×12 LU grid parameters and pixel formulae (prose) |
| `governance/Page_DoD.md` | Definition of Done — 8-point completion checklist |

### Design Tokens (Machine-Readable YAML)

| File | Contents |
|---|---|
| `tokens/layout_grid.yaml` | Grid parameters, canvas sizes, spacing values (canonical) |
| `tokens/color_semantics.yaml` | Semantic hex tokens, brand palette, surface/text/border colors |
| `tokens/typography.yaml` | Font scale — sizes, weights, color roles per typography role |
| `tokens/visual_slot_mapping.yaml` | Visual type → slot compatibility matrix with grid coordinates |

### Grid Templates (Machine-Readable)

| File | Layout |
|---|---|
| `grid_templates/pulse.json` | Overview layout (3s + 30s) |
| `grid_templates/action_matrix.json` | Detail layout (300s) |
| `grid_templates/investigator.json` | Alternative overview (focus-area layout) |

### Visual Templates (Machine-Readable)

| File | Component |
|---|---|
| `visual_templates/kpi_card_with_delta.json` | KPI Card |
| `visual_templates/trend_line.json` | Line chart (Trend slot) |
| `visual_templates/smart_narrative.json` | Smart Narrative |
| `visual_templates/slicer_top_bar.json` | Top-bar slicer (Zone 2) |
| `visual_templates/slicer_left_pane.json` | Left-pane slicer (300s pages) |
| `visual_templates/matrix_with_data_bars.json` | Detail Matrix |

### Samples (Annotated Reference Pages)

| File | What it Shows |
|---|---|
| `samples/page_pulse_full.md` | T2 Overview — full Pulse layout with annotations |
| `samples/page_action_matrix_full.md` | T1–T4 Detail — Action Matrix (with and without Action Panel) |
| `samples/page_investigator_full.md` | Investigator alternative overview |
| `samples/page_t1_strategic_hero.md` | **T1 Hero layout** — executive overview with Big Idea annotation |
| `samples/page_t3_operational_exception.md` | **T3 Exception dashboard** — F-pattern, severity-sorted exception list |
| `samples/page_t4_prescriptive_action.md` | **T4 Full action layout** — narrative arc + Action Panel copy standards |
| `samples/layer_3s_kpi_band.md` | KPI band detail — all variants |
| `samples/layer_30s_diagnostics.md` | 30s driver zone detail |
| `samples/layer_300s_detail.md` | 300s detail page detail |

### Connectors

| File | Purpose |
|---|---|
| `connectors/OSS_Connector_Guide.md` | Reference implementation for Superset, Grafana, Metabase |

### Components

| File | Purpose |
|---|---|
| `components/ActionPanel_Spec.md` | Action Panel — full specification |

### Archive

| Directory | Purpose |
|---|---|
| `_archive/` | Superseded documents kept for git history reference |

---

## How Page Templates Are Used

### Step 1 — Select Page Type

Choose exactly one page type (T1–T4) based on the use case's primary decision question.

```
Decision →  "Are we on track?"           → T1
            "Why are we off target?"     → T2
            "Where is execution off?"    → T3
            "What should we do?"         → T4
```

If the question maps to multiple types, the use case is probably two separate use cases.

### Step 2 — Define the Big Idea

Before building any visual, write the Big Idea sentence for each page:

```
T1: "[Domain] is [on/off] track — [KPI] is [Δ], [momentum direction]."
T2: "The [Δ] gap is driven by [factor] — intervention in [area] required."
T3: "[N] exceptions are outside threshold — [N_critical] need immediate action."
T4: "[Trigger]. Recommended: [action] by [owner] — [impact] by [deadline]."
```

See `Storytelling_Principles.md §2` for the full Big Idea framework.

### Step 3 — Activate Slots in UseCase_Bracket.yaml

Slots define what analytical content is present. Per-use-case configuration lives in:

```yaml
core/usecases/core/<ID>_*/UseCase_Bracket.yaml → ux_layout_rules
```

Only activate slots that answer a concrete question for this use case's audience.

### Step 4 — Select Visual Types

From the activated slots, select the appropriate visual type from `Abstract_Visual_Types.md`. The connector translates abstract types to tool-native components.

### Step 5 — Apply Content Quality Standards

Before any page is considered done, verify content quality per `Content_Quality_Guide.md`:
- Visual titles are question- or conclusion-form
- KPI labels ≤25 characters, Title Case
- Smart Narrative is quantified, ≤2 sentences
- Action Panel (T4) has all mandatory fields

### Step 6 — Run Definition of Done

`governance/Page_DoD.md` — 8-point completion checklist. A page is not done until all 8 checks pass.

---

## When NOT to Use a Page Type

- Do **not** create custom layouts per report
- Do **not** mix multiple page purposes on one page
- Do **not** introduce new template types
- Do **not** redesign visuals outside the whitelist

If a question does not fit one of the four templates, the **use case is not ready** or not well-defined.

---

## Key Principles (Read These)

> **Consistency beats creativity.**
> The value of this framework comes from reuse, not customization.

> **A page has one job: lead the reader to a decision within their time horizon.**
> If a page tries to do more, it does less.

> **The Big Idea first. Evidence second.**
> In analytical reports, the conclusion leads — the reader validates, not discovers.

If you feel the need to break these rules, the problem is usually **upstream** (use case definition, KPIs, or actions), not the page template.
