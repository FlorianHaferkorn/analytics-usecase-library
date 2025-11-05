# Page Templates — Mapping

These minimal JSON templates define the report page structure referred to by the `page_template` field in Use Case front‑matter. The Agent uses them to scaffold visuals and slicers.

- Template files: `templates/pages/*.json`
- Bindings:
  - `@required_kpi_ids` → list of KPI IDs from the Use Case
  - `@segments` → segments from the Use Case (also used for slicers)
  - `@filters_default` → default filter presets

## Templates
- `overview_drivers_details`
  - File: `templates/pages/overview_drivers_details.json`
  - Sections: header (KPI cards), trend, drivers (decomposition/bridge), details (ranking table)
- `drivers_details`
  - File: `templates/pages/drivers_details.json`
  - Sections: drivers (cards + decomposition/bridge), details (table + matrix)

Notes
- Templates are intentionally abstract; the Agent decides concrete visual types and binds measures by resolving `required_kpi_ids`.
- Slicers are created from `segments`; default filters from `filters_default` are applied.
- Theme/layout styling is handled in the separate project and is not included here.

Last updated: 04.11.2025
