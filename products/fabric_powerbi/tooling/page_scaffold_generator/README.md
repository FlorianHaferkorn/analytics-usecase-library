# Page Scaffold Generator

Generates standardized Power BI page structures (PBIP format) from governance files.

## Overview

The Page Scaffold Generator creates Power BI report page structures based on:
- Use case page template mappings
- Visual-to-slot mapping rules
- Layout grid system specifications
- Color semantics and formatting rules

Layout is **adaptive** (positions and sizes depend on page type T1–T4 and the actual visuals for the use case). Pages and visuals use **speaking names** (e.g. `Page_COM001_Overview`, `KPI_1`, `Trend`, `Slicer_Date`) instead of Power BI default hex IDs.

**Design spec:** [MOCKUP_DESIGN_SPEC.md](MOCKUP_DESIGN_SPEC.md) — principles, layout rules per page type, typography, spacing, decision question, accessibility.

**Validation:** [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) — checklist for analytics path and UI/UX before treating a layout as done.

## Installation

```bash
cd products/fabric_powerbi/tooling/page_scaffold_generator
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python generate_page_scaffold.py \
  --use-case COM-001 \
  --page overview \
  --theme "Brand Blue__Monochromatic__Light__#118DFF" \
  --output showcases/aurora_group/reports/COM-001.Report \
  --mockup showcases/aurora_group/reports/COM-001_mockup.html
```

### Python API

```python
from page_scaffold_generator import PageScaffoldGenerator, MockupGenerator

# Generate scaffold
generator = PageScaffoldGenerator(
    use_case_id="COM-001",
    page_name="overview",
    theme_name="Brand Blue__Monochromatic__Light__#118DFF"
)

generator.load_config()
generator.generate()

# Validate
errors = generator.validate()
if errors:
    print(f"Validation errors: {errors}")

# Write PBIP structure
generator.write(Path("COM-001.Report"))

# Generate HTML mockup
mockup_gen = MockupGenerator()
page_structure = generator.get_page_structure()
mockup_gen.generate_mockup(
    page_structure=page_structure,
    use_case_id="COM-001",
    page_name="overview",
    output_path=Path("COM-001_mockup.html")
)
```

## Arguments

- `--use-case`: Use case ID (e.g., COM-001, OPS-001)
- `--page`: Page name (`overview` or `detail`)
- `--theme`: Optional theme name (defaults to framework default)
- `--output`: Output path for .Report folder
- `--mockup`: Optional output path for HTML mockup
- `--repo-root`: Repository root path (auto-detected if not provided)

## Output Structure

The generator creates a PBIP folder structure with **speaking names** (no hex IDs):

```
COM-001.Report/
  definition/
    report.json
    pages.json
    version.json
    pages/
      Page_COM001_Overview/
        page.json
        visuals/
          KPI_1/
            visual.json
          KPI_2/
            visual.json
          Trend/
            visual.json
          Variance/
            visual.json
          Slicer_Date/
            visual.json
          ...
      Page_COM001_Detail/
        page.json
        visuals/
          KPI_1/
            ...
          DetailMatrix/
            visual.json
          ...
```

## HTML Mockup

The HTML mockup provides a visual preview of the page layout (same layout engine as PBIP):
- Visual placeholders with **speaking labels** (e.g. KPI_1, Trend, Slicer_Date)
- Color-coded visual types and CSS variables (see design spec)
- Page type (T1/T2/T3/T4) and optional decision question in header
- Grid overlay and "Toggle Dimensions" for developer vs presentation mode
- Export as image option (requires html2canvas if used)

Open the generated HTML file in a browser to preview the layout before opening in Power BI Desktop.

## Configuration Files

The generator reads from these governance files:

- Use case UX SSOT: `core/usecases/core/<ID>_*/UseCase_Bracket.yaml` (`ux_layout_rules`)
- `core/templates/page_templates/governance/Visual_to_Slot_Mapping.yaml`
- `core/templates/page_templates/governance/Layout_Grid_System.yaml`
- `core/templates/page_templates/governance/Color_Semantics_Formatting.yaml`

## T2 Action Teaser and layout

- **T2 pages:** By default the generator adds a slim **Action Teaser** textbox at x=1570 (width 350) with text *"Key actions from variance → see Detail or T4"* per [ActionPanel_Spec.md](../../../../core/templates/page_templates/components/ActionPanel_Spec.md). Content area width is 1510. Set `action_teaser: false` in page slots config to omit the teaser.
- **T4 pages:** Full Action Panel placeholder is emitted when `needs_action_panel` is true.
- **Measure binding:** Visuals are emitted with empty `queryState` by default. To pre-bind measures, extend the generator to look up KPI→measure name from `master_registry.json` (derived from `UseCase_Bracket.yaml` + KPI Catalog by `registry_builder.py`) instead of a factsheet mapping. Pass `kpi_measures` and slot-specific `measure_ref`/`category_entity`/`category_property`; `VisualBuilder.build_kpi_card` already accepts optional `measure_ref` and fills Data projections for `_Measures`.

## Validation

The generator validates:
- Speaking page name (e.g. `Page_COM001_Overview`)
- Template assignment (T1–T4)
- Slicer count (max 4)
- Action Panel presence for T4 pages
- Detail Matrix only on detail pages

For **analytics path and UI/UX**, use [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) (stakeholder review).

## Examples

### Generate COM-001 Overview Page

```bash
python generate_page_scaffold.py \
  --use-case COM-001 \
  --page overview \
  --output showcases/aurora_group/reports/COM-001.Report \
  --mockup showcases/aurora_group/reports/COM-001_overview_mockup.html
```

### Generate COM-001 Detail Page

```bash
python generate_page_scaffold.py \
  --use-case COM-001 \
  --page detail \
  --output showcases/aurora_group/reports/COM-001.Report \
  --mockup showcases/aurora_group/reports/COM-001_detail_mockup.html
```

## Testing

Run tests with pytest:

```bash
python -m pytest tests/test_scaffold_generator.py -v
```

## Troubleshooting

### Theme Not Found

If you get a "Theme not found" error:
1. Check that the theme file exists in `theme_generator/themes/`
2. Verify the theme name matches the filename (without .json extension)
3. Use `--theme` argument to specify the correct theme name

### Validation Errors

If validation fails:
1. Check that the use case has a `UseCase_Bracket.yaml`
2. Verify the page name is `overview` or `detail`
3. Ensure template assignment matches the mapping rules

### Visual Positioning Issues

If visuals are positioned incorrectly:
1. Check `Layout_Grid_System.yaml` for positioning rules
2. Verify `ux_layout_rules` in the bracket (3s/30s/300s intent and action panel)
3. Review the HTML mockup to see actual positions

## Architecture

- **ConfigLoader**: Loads governance YAML files
- **LayoutCalculator**: Calculates visual positions and sizes
- **VisualBuilder**: Builds visual JSON structures
- **SlicerBuilder**: Builds slicer JSON structures
- **PageBuilder**: Builds page structures
- **PBIPWriter**: Writes PBIP file structure
- **MockupGenerator**: Generates HTML/CSS mockups
- **PageScaffoldGenerator**: Main orchestrator class

## References

- **Design spec**: [MOCKUP_DESIGN_SPEC.md](MOCKUP_DESIGN_SPEC.md)
- **Validation checklist**: [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)
- **Governance files**: `core/templates/page_templates/governance/`
- **Example PBIP**: `showcases/sample_pbip_report/Procurement_Wireframe_Theme.Report/`

### Design references (layout and hierarchy)

- [Tremor template-dashboard-oss](https://github.com/tremorlabs/template-dashboard-oss) — analytics layout and visual hierarchy
- [Tabler layout fluid](https://preview.tabler.io/layout-fluid.html) — fluid grid, dashboard layouts
- [Microsoft Power BI design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips) — authority guidance
