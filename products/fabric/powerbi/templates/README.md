# PBIP Templates

This folder will hold **canonical PBIP skeletons** for:
- Semantic model (dataset) structure (TMDL, relationships, partitions)
- Report structure aligned to 3-30-300 (page types, navigation, placeholders)

## Why templates

Templates are the fastest way to make implementation:
- repeatable,
- consistent,
- easy to review,
- and AI-assisted (generate from governed specs, then validate).

## Current references (until templates are migrated/created here)

- Sample report/theme scaffold: `showcases/sample_pbip_report/`
- Aurora PBIP assets: `showcases/aurora_group/semantic_models/`
- Page templates and governance: `core/templates/page_templates/`

## Themes

Template and sample reports (e.g. `showcases/sample_pbip_report/Procurement_Wireframe_Theme.Report`) **ship with a theme pre-applied**: `definition/report.json` references a base theme and a custom theme in `StaticResources/RegisteredResources/`. Reports created from scaffolds or generated elsewhere can have themes applied via `tools/apply_report_theme.py` (single report or batch: `--batch-showcase`, `--batch`, `--batch-file`; see `tools/README.md`).

