#!/usr/bin/env bash
# create_spur1_prs.sh
# Creates 3 GitHub PRs for Spur 1 (Fabric Showcase) changes.
# Run this script from your LOCAL machine (not inside the VM) in the repo root.
#
# Prerequisites:
#   - git configured with your GitHub credentials
#   - GitHub CLI (gh) installed: https://cli.github.com
#   - gh auth login completed
#
# Usage:
#   bash tooling/create_spur1_prs.sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

MAIN_BRANCH="main"
echo "Creating Spur 1 PRs from $(pwd)"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PR 1: Generator Fixes (page_builder, figma/penpot bridges, slicer, etc.)
# ─────────────────────────────────────────────────────────────────────────────
echo "=== PR 1: Generator Fixes ==="
git checkout "$MAIN_BRANCH"
git checkout -b feat/generator-fixes 2>/dev/null || git checkout feat/generator-fixes

git add \
  "products/fabric/powerbi/tooling/page_scaffold_generator/page_builder.py" \
  "products/fabric/powerbi/tooling/page_scaffold_generator/visual_builder.py" \
  "products/fabric/powerbi/tooling/page_scaffold_generator/config_loader.py" \
  "products/fabric/powerbi/tooling/page_scaffold_generator/slicer_builder.py" \
  "products/fabric/powerbi/tooling/page_scaffold_generator/figma_layout_bridge.py" \
  "products/fabric/powerbi/tooling/page_scaffold_generator/penpot_layout_bridge.py" \
  "core/templates/page_templates/grid_templates/action_matrix.json"

git commit -m "feat(generator): fix chart visual bindings + add Figma/Penpot layout bridges

- page_builder.py: component_30s binding so Main_1/2/3 use correct visual
  types (lineChart/barChart) instead of falling through to tableEx;
  position_mode=absolute for Figma/Penpot pixel layouts; slicer_entity handler
- visual_builder.py: dataLabels (OutsideEnd) for build_horizontal_bar
- config_loader.py: layout_source (figma:// and penpot:// URIs); period token
  updated to CalendarYearMonth
- slicer_builder.py: default slicer field changed to dim_date.CalendarYearMonth
- figma_layout_bridge.py: NEW — Figma MCP → position_mode=absolute layout dicts
- penpot_layout_bridge.py: NEW — Penpot JSON → same absolute-position schema
- action_matrix.json: split Slicer_Pane into Slicer_Pane + Slicer_Entity

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin feat/generator-fixes

gh pr create \
  --title "feat(generator): fix chart visual bindings + Figma/Penpot layout bridges" \
  --base "$MAIN_BRANCH" \
  --body "$(cat <<'BODY'
## Summary

- **Fixes 45 unbound `tableEx` visuals** on Overview pages: `component_30s` binding now correctly maps Main_1/2/3 to their configured visual types (lineChart, clusteredBarChart, etc.)
- **Adds Figma layout bridge** (`figma_layout_bridge.py`): reads design context from Figma MCP and produces `position_mode=absolute` layout dicts — graceful offline fallback to static template
- **Adds Penpot layout bridge** (`penpot_layout_bridge.py`): free open-source Figma alternative; parses Penpot JSON export into same absolute-position schema
- **Slicer field**: changed default from `dim_date.Date` (calendar picker) to `dim_date.CalendarYearMonth` (sortable YYYY-MM dropdown)
- **action_matrix.json**: split Slicer_Pane into Slicer_Pane + Slicer_Entity so OrgName filter gets its own slot on detail pages
- **config_loader.py**: reads `layout_source` URI from bracket YAML; supports `figma://` and `penpot://` schemes

## Test plan

- [ ] Run `validate_bindings.py --dist-dir products/fabric/powerbi/dist` → expect 15/15 ✅, 0 errors
- [ ] Open COM-001 in Power BI Desktop → Overview page should show lineChart for Main_1, not tableEx
- [ ] Check Slicer_Date on Overview → should show YYYY-MM dropdown values
- [ ] Check action_matrix detail page → Slicer_Entity should appear separately from Slicer_Pane

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"

echo ""
echo "✅ PR 1 created"

# ─────────────────────────────────────────────────────────────────────────────
# PR 2: Dist Reports — 15 regenerated .Report folders + dim_date TMDL
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== PR 2: Dist Reports ==="
git checkout "$MAIN_BRANCH"
git checkout -b feat/dist-reports-spur1 2>/dev/null || git checkout feat/dist-reports-spur1

git add \
  "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report" \
  "products/fabric/powerbi/dist/COM-002_Margin_Price_Performance.Report" \
  "products/fabric/powerbi/dist/COM-003_Customer_Value.Report" \
  "products/fabric/powerbi/dist/COM-004_Promotion_Effectiveness.Report" \
  "products/fabric/powerbi/dist/FIN-001_Cash_Liquidity_Performance.Report" \
  "products/fabric/powerbi/dist/FIN-002_Cost_Performance.Report" \
  "products/fabric/powerbi/dist/OPS-001_Operations_Performance.Report" \
  "products/fabric/powerbi/dist/OPS-002_Asset_Performance.Report" \
  "products/fabric/powerbi/dist/OPS-003_Quality_Yield.Report" \
  "products/fabric/powerbi/dist/SCM-001_Inventory_Performance.Report" \
  "products/fabric/powerbi/dist/SCM-002_Supply_Reliability_OTIF.Report" \
  "products/fabric/powerbi/dist/SCM-003_Forecast_vs_Actual.Report" \
  "products/fabric/powerbi/dist/XD-001_Service_Level_Performance.Report" \
  "products/fabric/powerbi/dist/XD-002_Resource_Utilization.Report" \
  "products/fabric/powerbi/dist/XD-003_Executive_KPI_Overview.Report" \
  "products/fabric/powerbi/dist/Commercial.SemanticModel/definition/tables/dim_date.tmdl" \
  "products/fabric/powerbi/dist/Experience.SemanticModel/definition/tables/dim_date.tmdl" \
  "products/fabric/powerbi/dist/Finance.SemanticModel/definition/tables/dim_date.tmdl" \
  "products/fabric/powerbi/dist/Operations.SemanticModel/definition/tables/dim_date.tmdl" \
  "products/fabric/powerbi/dist/SupplyChain.SemanticModel/definition/tables/dim_date.tmdl"

git commit -m "dist: regenerate all 15 reports + apply Aurora theme + CalendarYearMonth slicers

- All 15 reports regenerated with --force-full
- Aurora theme applied to all: customTheme in themeCollection + JSON in StaticResources
- Slicer_Date now uses dim_date.CalendarYearMonth (YYYY-MM sortable dropdown)
- All chart visuals correctly bound (Main_1=lineChart, Main_2=barChart, Main_3=barChart)
- Validate_bindings result: 15/15 pass, 0 errors, 0 warnings
- dim_date.tmdl: added CalendarYearMonth calculated column (FORMAT([Date], YYYY-MM))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin feat/dist-reports-spur1

gh pr create \
  --title "dist: regenerate all 15 Spur 1 reports — Aurora theme + CalendarYearMonth" \
  --base "$MAIN_BRANCH" \
  --body "$(cat <<'BODY'
## Summary

Full regeneration of all 15 Spur 1 reports with 3 improvements applied:

1. **Aurora theme** added to all 15 `report.json` files (`themeCollection.customTheme`) + theme JSON copied to `StaticResources/RegisteredResources/` where missing
2. **CalendarYearMonth slicers**: all `Slicer_Date` and `Slicer_Pane` visuals now use `dim_date.CalendarYearMonth` (YYYY-MM format) instead of the raw date field — shows as sortable dropdown instead of calendar picker
3. **Correct chart visual types**: Main_1/2/3 use lineChart/barChart as configured in each `UseCase_Bracket.yaml`, no more fallback to tableEx

Reports: COM-001 through COM-004, FIN-001/002, OPS-001 through OPS-003, SCM-001 through SCM-003, XD-001 through XD-003

## Test plan

- [ ] `validate_bindings.py --dist-dir products/fabric/powerbi/dist` → 15/15 ✅
- [ ] Open any .Report in Power BI Desktop → Aurora blue palette should be applied
- [ ] Filter slicers should show YYYY-MM values (e.g. "2024-01", "2024-02")
- [ ] `dim_date.tmdl` in each SemanticModel shows `CalendarYearMonth` calculated column

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"

echo ""
echo "✅ PR 2 created"

# ─────────────────────────────────────────────────────────────────────────────
# PR 3: Tooling & Docs
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== PR 3: Tooling & Docs ==="
git checkout "$MAIN_BRANCH"
git checkout -b feat/tooling-docs-spur1 2>/dev/null || git checkout feat/tooling-docs-spur1

git add \
  "products/fabric/powerbi/tooling/validate_bindings.py" \
  "KNOWN_GAPS.md" \
  "core/templates/page_templates/grid_templates/pulse_asymmetric.json" \
  "core/templates/page_templates/grid_templates/investigator_focus.json" \
  "core/templates/page_templates/grid_templates/executive_kpi.json" \
  "docs/penpot_layout_design_guide.md" \
  "tooling/create_spur1_prs.sh"

git commit -m "tooling: add binding validator, KNOWN_GAPS, new layout templates, Penpot guide

- validate_bindings.py: CI script — checks all .Report dirs for unbound chart
  visuals and wrong visual types; exit 0 = pass, exit 1 = fail; --strict mode
  treats WARNs as ERRORs; designed for Azure Pipelines / GitHub Actions
- KNOWN_GAPS.md: documents placeholder measures, Aurora theme desktop step,
  Penpot/Figma activation steps, CI integration todo
- pulse_asymmetric.json: 52% dominant trend + 2× stacked 22.5% support charts
- investigator_focus.json: 64% large focus + 34% stacked support columns
- executive_kpi.json: 240px KPI strip + large trend + compact side panels
  (all 3 use position_mode=absolute for pixel-perfect Penpot/Figma support)
- docs/penpot_layout_design_guide.md: how to create Penpot templates and
  activate penpot:// URIs in UseCase_Bracket.yaml

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin feat/tooling-docs-spur1

gh pr create \
  --title "tooling: CI binding validator + KNOWN_GAPS + 3 new layout templates" \
  --base "$MAIN_BRANCH" \
  --body "$(cat <<'BODY'
## Summary

Three new additions to the tooling and documentation layer:

**validate_bindings.py** — CI-ready validation script for PBIP reports
- Checks every chart visual has ≥1 projection (non-empty binding)
- Flags `tableEx` on Main_1/2/3 chart slots as ERROR
- Checks required slots per page type (Overview: KPI_Cards, Main_1, Main_2, Slicer_Date)
- Exit code 0 = pass; add to CI pipeline with: `python3 products/fabric/powerbi/tooling/validate_bindings.py --dist-dir products/fabric/powerbi/dist`

**KNOWN_GAPS.md** — tracks placeholder measures, deferred items, activation steps for Aurora theme and Penpot layouts

**3 new absolute-position layout templates** (`pulse_asymmetric`, `investigator_focus`, `executive_kpi`) — use `position_mode: absolute` with pixel coordinates; ready for Penpot design overlay

**docs/penpot_layout_design_guide.md** — step-by-step guide for creating Penpot layout templates and wiring them to reports via `penpot://` URIs in `UseCase_Bracket.yaml`

## Test plan

- [ ] `python3 products/fabric/powerbi/tooling/validate_bindings.py --dist-dir products/fabric/powerbi/dist` → 15/15 ✅
- [ ] `python3 products/fabric/powerbi/tooling/validate_bindings.py --dist-dir products/fabric/powerbi/dist --strict` → still ✅
- [ ] Verify KNOWN_GAPS.md renders correctly in GitHub
- [ ] Open `pulse_asymmetric.json` — verify slot positions sum to ≈1920×1080 canvas

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"

echo ""
echo "✅ PR 3 created"
echo ""
echo "════════════════════════════════════════════════════════"
echo "All 3 PRs created successfully!"
echo "  - feat/generator-fixes"
echo "  - feat/dist-reports-spur1"
echo "  - feat/tooling-docs-spur1"
echo ""
echo "Check your PRs at: https://github.com/FlorianHaferkorn/analytics-usecase-library/pulls"
