# Legacy Archive

This directory contains artifacts that were removed from the governed repository through automated cleanup processes.
Files here are **not authoritative** and must not be referenced by governed artifacts or tooling.

## Contents

| Item | Moved from | Reason | Replacement |
|---|---|---|---|
| `kpi_catalog_orphans.yaml` | `core/kpi_catalog/KPI_Catalog.md` (extracted chunks) | Orphan KPIs not referenced by any active UseCase_Bracket or subscribed Action Code (transitive linkage) | Remove or re-link via `UseCase_Bracket.yaml` to reactivate |
| `kpi_catalog_orphans_move_log.json` | n/a (generated) | Extraction log for KPI orphan cleanup | n/a |

## Policy

- **Registry/validators ignore this directory.** Files here do not participate in Stage 1 checks, registry builds, or schema validation.
- **Restoration:** To reactivate an orphan KPI, re-add its definition to `core/kpi_catalog/KPI_Catalog.md` and ensure it is referenced by an active bracket or subscribed action code.
- **Deletion:** Files may be permanently deleted after one release cycle if no reactivation is needed.

## Related legacy locations

| Location | Purpose |
|---|---|
| `internal/archive/` | Historical framework artifacts, deprecated action codes, legacy KPI catalogs, legacy measure dictionaries. Internal reference only. |
| `internal/archive/deprecated_action_codes_2026-01/` | Action codes deprecated during framework consolidation. |
| `internal/archive/legacy_kpi_catalogs_2026-01/` | Per-dimension KPI catalogs superseded by unified `core/kpi_catalog/KPI_Catalog.md`. |
| `internal/archive/legacy_measure_dicts_2026-01/` | Measure dictionaries superseded by domain-level dictionaries under `semantic_models/`. |
