# Page Scaffold Generator

Generates standardized Power BI page structures (PBIP format) from governance files.

## Overview

The Page Scaffold Generator creates Power BI report page structures based on:
- Use case page template mappings
- Visual-to-slot mapping rules
- Layout grid system specifications
- Color semantics and formatting rules

## Installation

```bash
cd implementations/microsoft_fabric_powerbi/tools/page_scaffold_generator
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

The generator creates a PBIP folder structure:

```
COM-001.Report/
  definition/
    report.json
    pages.json
    version.json
    pages/
      {page_id}/
        page.json
        visuals/
          {visual_id}/
            visual.json
```

## HTML Mockup

The HTML mockup provides a visual preview of the page layout:
- Visual placeholders with dimensions
- Color-coded visual types
- Grid overlay (toggleable)
- Export as image option

Open the generated HTML file in a browser to preview the layout before opening in Power BI Desktop.

## Configuration Files

The generator reads from these governance files:

- `framework/templates/page_templates/mappings/UseCase_PageTemplate_Map.yaml`
- `framework/templates/page_templates/governance/Visual_to_Slot_Mapping.yaml`
- `framework/templates/page_templates/governance/Layout_Grid_System.yaml`
- `framework/templates/page_templates/governance/Color_Semantics_Formatting.yaml`

## Validation

The generator validates:
- Page name pattern
- Template assignment
- Slicer count (max 4)
- Action Panel presence for T4 pages
- Detail Matrix only on detail pages

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
1. Check that the use case exists in `UseCase_PageTemplate_Map.yaml`
2. Verify the page name is `overview` or `detail`
3. Ensure template assignment matches the mapping rules

### Visual Positioning Issues

If visuals are positioned incorrectly:
1. Check `Layout_Grid_System.yaml` for positioning rules
2. Verify slot activations in `UseCase_PageTemplate_Map.yaml`
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

- **Specification**: `page_scaffold_spec.md`
- **Governance Files**: `framework/templates/page_templates/governance/`
- **Example PBIP**: `showcases/sample_pbip_report/Procurement_Wireframe_Theme.Report/`
