# archive

Purpose:
Historical storage for deprecated content, superseded artifacts, and tooling output (automated cleanup). All archive content is **not authoritative** and must not be referenced by governed artifacts or tooling.

Scope:
- **Curated (dated folders):** Deprecated action codes, legacy KPI catalogs, superseded measure dictionaries, legacy use case structures, framework evolution docs.
- **Tooling output (`tooling/`):** Populated by scripts only. `tooling/ghosts/` — files moved by `archive_ghosts.py`; `tooling/kpi_orphans/` — KPI orphan YAML and move log from `extract_kpi_orphans.py`. Registry and validators ignore these paths.
- Not: Active or customer-ready content.

Structure:
- `tooling/` — Tooling output; see `tooling/README.md`. Do not edit by hand.
- Dated folders (YYYY-MM) preserve historical context:
  - `deprecated_action_codes_2026-01/` - 21 superseded action code definitions
  - `deprecated_specs_2026-01/` - 2 obsolete specification files
  - `legacy_kpi_catalogs_2026-01/` - 9 pre-consolidation KPI catalog files
  - `legacy_measure_dicts_2026-01/` - 2 archived measure dictionary files
  - `legacy_usecases_2026-01/` - 2 superseded use case structures
  - `legacy_aurora_models_2026-02/` - 1 legacy Aurora showcase model (generic cross-domain, superseded by domain-specific blueprints)
  - `glossary_2026-02/`, `lean2_cutover_2026-02/`, etc.

Policy (curated and tooling):
- Content is frozen for historical reference or script output only.
- Do not reference archived items in active documentation.
- Registry/validators ignore this directory; no Stage 1 or registry build uses archive content.
- Restoration: To reactivate an orphan KPI, re-add to `core/kpi_catalog/KPI_Catalog.md` and ensure it is referenced by an active bracket or subscribed action code.
- Contoso- or vendor-specific references are legacy only and not part of the current, tenant-agnostic ActionReady blueprint.

Relations:
Outside the 4-layer framework; historical record only.
