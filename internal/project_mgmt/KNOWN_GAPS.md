# Known Gaps & Deferred Items

This document tracks known limitations, placeholder content, and deferred activation steps for the Analytics Usecase Library (Spur 1 — Fabric Showcase).

> ⚠️ **Last full audit:** 2026-03-27. Items below may have been resolved since — **always verify against the current codebase before assuming an item is still open**:
> - For a file mentioned by an item, check `git log -p -- <path>` since 2026-03-27.
> - For a feature, run the relevant validation gate ([`CONTRIBUTING.md`](CONTRIBUTING.md) § "Validation gates").
> - For a "Resolved" entry at the bottom: trust it (those are append-only history).
>
> If you confirm an item is now resolved, move it to the **Resolved Items** table at the bottom and link the commit.

## How to read this file

- **Section 1a** — missing data / pending model integrations.
- **Sections 2–7** — activation steps and deferred epics that need an external action or deliberate authoring (theme save, design tool setup, industry-variant tier).
- **Resolved Items** — append-only changelog of past gaps. Useful as evidence when an audit asks "what was deferred and when did it ship?"

---

## 1a. Pending Measures — Require ML/Predictive Models (Deferred)

Two XD-003 measures are explicitly deferred — they require predictive model outputs not yet in any data contract:

| Measure | KPI ID | Requirement |
|---|---|---|
| `[Digital Adoption Rate %]` | `people.digital_adoption.pct` | `fact_it` digital users + `fact_hr` total headcount |
| `[Attrition Risk %]` | `people.attrition_risk.pct` | Predictive attrition model output table |

These return `BLANK()` by design until the source systems are connected.

---

## 2. Custom Aurora Theme — Report-Level Application

The Aurora theme (`Aurora_Group__Monochromatic__Light__#2ECDE7`) is referenced in `report.json` for all 15 reports and the JSON file is included in each `StaticResources/RegisteredResources/` folder.

**Important:** Power BI Desktop currently requires the theme to be opened and saved once via the Desktop UI before it becomes fully active in a published Fabric workspace. The programmatic `themeCollection.customTheme` entry is correct and will be applied on first open.

**Steps when deploying to Fabric:**
1. Open any `.pbip` file in Power BI Desktop.
2. Go to **View → Themes → Browse for themes** — the Aurora theme is already pre-loaded; just click it to confirm.
3. Save and re-publish to the Fabric workspace.

---

## 3. Penpot Layout Integration — Activation Steps

Absolute-position layouts sourced from Penpot are supported via `PenpotLayoutBridge`. The bridge code is in place but requires a Penpot project to be created before it can be used.

**To activate Penpot layouts for a use case:**

1. **Create a free Penpot account** at [penpot.app](https://penpot.app) (no cost, self-hostable).
2. **Create a new project** and add a page per layout variant (e.g. `Pulse_Overview`, `Action_Matrix_Detail`).
3. **Name child frames** using the canonical slot IDs (`KPI_Cards`, `Main_1`, `Main_2`, `Main_3`, `Slicer_Date`, `Slicer_Entity`, `Smart_Narrative`, `Detail_Matrix`, `ActionPanel`). Add visual type annotations in brackets: `Main_1 [lineChart]`.
4. **Export as JSON** from Penpot: File → Export → Penpot format (`.penpot` file = ZIP containing JSON).
5. **Reference in `UseCase_Bracket.yaml`:**
   ```yaml
   ux_layout_rules:
     layout_source: "penpot://FILE_ID/PAGE_ID/FRAME_ID"
     page_template: pulse   # fallback if Penpot unreachable
   ```
6. Regenerate with `generate_full_report.py --force-full`.

Full design guide: [`docs/penpot_layout_design_guide.md`](docs/penpot_layout_design_guide.md)

Similarly, Figma layouts are supported via `FigmaLayoutBridge` (requires Figma MCP `mcp__d9301186-5d57-4267-8b50-777fd092c841`). Reference via `figma://FILE_ID/NODE_ID` in `layout_source`.

---

## 4. Slicer Hierarchy — CalendarYearMonth (Implemented)

~~All date slicers used `dim_date.Date` (flat date picker), which rendered as a calendar widget without month grouping.~~

**Resolved 2026-03-27:** All reports now use `dim_date.CalendarYearMonth` (format: `YYYY-MM`) as the default slicer field. The calculated column is defined in all 5 semantic model `dim_date.tmdl` files. Slicers render as a sortable dropdown grouped by month.

---

## 6. Layout Templates — Figma / Penpot Design Files Not Yet Created

Three new absolute-position layout templates are defined as JSON:
- `pulse_asymmetric.json` — 52% dominant + 2× stacked 22.5% charts
- `investigator_focus.json` — 64% focus + 34% stacked support
- `executive_kpi.json` — 240px KPI strip + large trend + compact side panels

These JSON templates work standalone (grid layouts). To use them with Penpot/Figma pixel-perfect designs, the corresponding design files need to be created in Penpot (see section 3 above) and the `penpot://` URIs added to each `UseCase_Bracket.yaml`.

---

## 7. Industry-Variant Use-Case Tier — Deferred Epic (from branch `enhance-factsheets-quality`)

The closed branch `claude/enhance-factsheets-quality-7YkI9` proposed a brand-new
**industry-variant tier** of the use-case library. The *clean, self-contained*
parts of that branch were salvaged (scorecard H9 cross-UC coverage, `use_case_links`
+ `security.rls` schema/bracket support, GDPR §7.4 prose for COM-003/XD-001, three
domain-agnostic decision spines). The tier itself is **deferred** because it
*defines net-new governance* (new ID taxonomy, new KPI namespaces, new action
codes) and must be authored deliberately, not auto-generated off an abandoned
branch.

**What the tier introduces (all NOT yet in the catalog):**

- **New ID taxonomy** `XXX-EXT-NNN` / `XXX-IND-<R|L|M>NNN` alongside the governed
  `XXX-NNN` set, and a **new directory tree** `core/usecases/industry/<sector>/`.
- **Six use cases**, only one of which (`COM-IND-R001`) has a draft bracket on the
  branch — and even it is missing its `Business_Factsheet.md`:

  | Spine (already salvaged) | Target UC (to author) | Sector |
  |---|---|---|
  | `DEC-SPINE-COM-BASKET_CROSSSELL` | `COM-IND-R001` Basket & Category Cross-Sell | Retail |
  | `DEC-SPINE-COM-SEGMENTATION` | `COM-EXT-001` Customer Segmentation / RFM | Commercial |
  | `DEC-SPINE-FIN-BUDGET_VARIANCE` | `FIN-EXT-001` Budget Variance / P&L Bridge | Finance |
  | `DEC-SPINE-SCM-SUPPLIER_RISK` | `SCM-EXT-001` Supplier Risk | Supply Chain |
  | `DEC-SPINE-SCM-LAST_MILE` | `SCM-IND-L001` Last-Mile Delivery | Logistics |
  | `DEC-SPINE-OPS-OEE` | `OPS-IND-M001` OEE | Manufacturing |

  > The three spines `DEC-SPINE-OPS-OEE`, `DEC-SPINE-SCM-LAST_MILE`,
  > `DEC-SPINE-SCM-SUPPLIER_RISK` were **NOT** salvaged: their escalation paths cite
  > action codes (`O-P2.1`, `S-L1.1/.2`, `S-P3.1/.2`) that don't exist yet.

**Prerequisites before any of these UCs can pass the Golden Thread gates:**

1. **KPIs** — `COM-IND-R001` alone references five KPIs absent from
   `core/kpi_catalog/`, in two **new namespaces**:
   `retail.basket.items_per_transaction`, `retail.category.crosssell_rate.pct`,
   `retail.basket.value.average`, `retail.promotion.attachment_rate.pct`,
   `customer.rfm.frequency_score`. The other five UCs will need their own.
2. **Action codes** — author `O-P2.1`, `S-L1.1`, `S-L1.2`, `S-P3.1`, `S-P3.2` in
   `core/action_codes/` before salvaging their spines.
3. **Map wiring** — `DecisionSpine_UseCase_Map.yaml` entries for the six spines were
   **intentionally left out** of this salvage (they pointed at non-existent UC IDs).
   Add each entry only once its target UC exists.
4. **Taxonomy decision** ✅ **DONE (2026-06-18, ADR-0004)** — the `EXT`/`IND-<S>`
   infix, the `extended/` and `industry/<sector>/` tier trees, and the sector-letter
   register (R=Retail, L=Logistics, M=Manufacturing) are ratified in
   `docs/architecture/adr/0004-industry-variant-use-case-tier-taxonomy.md`. The
   bracket-schema `id` pattern and the `registry_builder` use-case scan were widened
   so extension-tier UCs validate like core.

**Delivered — first slice (2026-06-18):** `COM-IND-R001` Basket & Category Cross-Sell
(Retail) is authored end-to-end and passes the Golden Thread gates: 5 new KPIs
(`retail.basket.items_per_transaction`, `retail.category.crosssell_rate.pct`,
`retail.basket.value.average`, `retail.promotion.attachment_rate.pct`,
`customer.rfm.frequency_score`), the new commercial action code `C-M3.1` inheriting
`DEC-SPINE-COM-BASKET_CROSSSELL`, the bracket + prose factsheet under
`core/usecases/industry/retail/`, and the `DecisionSpine_UseCase_Map.yaml` entry —
so prerequisites #1 and #3 are satisfied **for this UC**. The other five §7 use cases
remain to be authored deliberately, one governed slice at a time.

Reference: branch `claude/enhance-factsheets-quality-7YkI9`; salvage audit in PR that
introduced this entry; taxonomy ratified in ADR-0004.

---

## Resolved Items

| Item | Resolved | Notes |
|---|---|---|
| 45 unbound `tableEx` visuals on Overview pages | 2026-03-27 | Fixed via `component_30s` binding in `page_builder.py` |
| All Main_1/2/3 rendered as tableEx | 2026-03-27 | Fixed template loop ordering bug |
| Aurora theme not applied | 2026-03-27 | Applied to all 15 reports via `report.json.themeCollection` |
| Date slicers flat (no hierarchy) | 2026-03-27 | `CalendarYearMonth` column added to all `dim_date.tmdl` |
| No Figma/Penpot layout bridge | 2026-03-27 | `figma_layout_bridge.py` + `penpot_layout_bridge.py` implemented |
| No CI binding validation | 2026-03-27 | `validate_bindings.py` implemented (local pass: 15/15) |
| fact_action_outcome missing from Gold layer | 2026-04-20 | 5-year synthetic Parquet generated; all 15 Impactful action codes present |
| No action-code outcome loop in reports | 2026-04-20 | `[Action Outcome Rate %]` and 3 companion measures in all 5 domain models |
| deploy_pbip required manual Power BI Desktop | 2026-04-20 | `deploy_pbip` MCP tool chains IR generation → `fab import` automatically |
| No DAX execution without Desktop | 2026-04-20 | `execute_dax` MCP tool wraps `execute_dax.py` via fab+az CLI |
| Missing Parquet for fact_quality_costs, fact_complaints, fact_supplier_risk | 2026-05-27 | Gold data committed (2020–2024 partitions). One-time script `generate_missing_facts.py` archived to `internal/archive/showcases/gold_maintenance/`. |
| `fix_bracket_component30s.py` one-time repair | 2026-05-27 | All 16 UseCase_Bracket.yaml files confirmed clean. Script archived to `internal/archive/tooling/maintenance/`. |
| TMDL `/// Data contract pending` stubs on 3 fact tables (was §1) | 2026-06-17 | Stub comments removed and M partitions wired to the Gold path; no `.tmdl` contains the marker (commit `9348f59`). |
| `validate_bindings.py` not wired into GitHub Actions (was §5) | 2026-06-17 | Already wired into `.github/workflows/stage1.yml` (per-domain `--strict`). |
