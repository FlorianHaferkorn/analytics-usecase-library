# Known Gaps & Deferred Items

This document tracks known limitations, placeholder content, and deferred activation steps for the Analytics Usecase Library (Spur 1 — Fabric Showcase).

Last updated: 2026-03-27

---

## 1. Missing Fact Tables — Gold Layer Data Contracts

Three fact tables are missing Parquet data in the Gold Layer. The TMDL definitions are in place (reports load cleanly with empty partitions), but the measures return BLANK until real data is provisioned.

| Fact Table | Used By | Missing Columns | Status |
|---|---|---|---|
| `fact_quality_costs` | OPS-003 `[Cost of Poor Quality]` | COPQ Amount, Scrap/Rework/Warranty Cost | Stub TMDL ✅ — Parquet pending MES integration |
| `fact_complaints` | OPS-003 `[Complaint Rate %]` | Complaint Count, Resolved Count, Resolution Days | Stub TMDL ✅ — Parquet pending CRM feed |
| `fact_supplier_risk` | FIN-001 `[Supplier Risk Score]` | Risk Score, Delivery/Quality/Financial Risk | Stub TMDL ✅ — Parquet pending procurement data contract |

**How to provision Parquet data (local machine with pyarrow):**
```bash
python3 showcases/aurora_group/data/gold/generate_missing_facts.py
```
This generates ~60K synthetic rows per table using the same seed and company profile as existing facts. Once run, commit the new `facts/fact_quality_costs/`, `facts/fact_complaints/`, `facts/fact_supplier_risk/` folders.

**TMDL locations:**
- `products/fabric/powerbi/dist/Operations.SemanticModel/definition/tables/fact_quality_costs.tmdl`
- `products/fabric/powerbi/dist/Operations.SemanticModel/definition/tables/fact_complaints.tmdl`
- `products/fabric/powerbi/dist/Finance.SemanticModel/definition/tables/fact_supplier_risk.tmdl`

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

## 5. `validate_bindings.py` — CI Integration ✅ Wired via MCP

The CI validation script `products/fabric/powerbi/tooling/validate_bindings.py` is implemented and passes locally (15/15 reports, 0 errors). It is now also callable via the `validate_bindings` MCP tool in Studio.

**To integrate in GitHub Actions:**
```yaml
# .github/workflows/validate.yml
- name: Validate report bindings
  run: python3 products/fabric/powerbi/tooling/validate_bindings.py --dist-dir products/fabric/powerbi/dist --strict
```

**MCP tool:** `studio mcp validate_bindings --strict` — returns exit code and full output.

---

## 6. Layout Templates — Figma / Penpot Design Files Not Yet Created

Three new absolute-position layout templates are defined as JSON:
- `pulse_asymmetric.json` — 52% dominant + 2× stacked 22.5% charts
- `investigator_focus.json` — 64% focus + 34% stacked support
- `executive_kpi.json` — 240px KPI strip + large trend + compact side panels

These JSON templates work standalone (grid layouts). To use them with Penpot/Figma pixel-perfect designs, the corresponding design files need to be created in Penpot (see section 3 above) and the `penpot://` URIs added to each `UseCase_Bracket.yaml`.

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
| COM-001 golden fixture test failure (snapshot regression) | 2026-04-22 | Verified test passing; dist files match golden fixture; no action required |
