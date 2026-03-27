# Known Gaps & Deferred Items

This document tracks known limitations, placeholder content, and deferred activation steps for the Analytics Usecase Library (Spur 1 — Fabric Showcase).

Last updated: 2026-03-27

---

## 1. Placeholder Measures (Pending Data Contracts)

Four use cases contain placeholder measures that return `0` or `BLANK()` because the underlying data source schema has not yet been finalized. These will be replaced once the data contracts are signed off.

| Use Case | Measure | Status | Owner |
|---|---|---|---|
| FIN-001 Cash & Liquidity | `[CashConversionCycleDays]` | Placeholder — awaiting AR/AP schema | Finance Domain |
| FIN-002 Cost Performance | `[AllocatedOverheadPct]` | Placeholder — awaiting cost allocation table | Finance Domain |
| OPS-003 Quality & Yield | `[ScrapRatePct]` | Placeholder — awaiting MES integration | Operations Domain |
| XD-003 Executive KPI Overview | `[NPS_Score]` | Placeholder — awaiting CX survey feed | Experience Domain |

**When resolved:** Update the relevant `UseCase_Bracket.yaml` under `core/usecases/core/<ID>/`, re-run `generate_full_report.py --use-case <ID> --force-full`, and remove the row from this table.

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

## 5. `validate_bindings.py` — CI Integration

The CI validation script `products/fabric/powerbi/tooling/validate_bindings.py` is implemented and passes locally (15/15 reports, 0 errors). It has **not yet been wired into Azure Pipelines / GitHub Actions**.

**To integrate:**
```yaml
# .github/workflows/validate.yml
- name: Validate report bindings
  run: python3 products/fabric/powerbi/tooling/validate_bindings.py --dist-dir products/fabric/powerbi/dist --strict
```

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
