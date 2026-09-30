# Core Framework (Tool-Agnostic SSOT)

## Purpose

`core/` contains the governed, tool-agnostic source of truth for the ActionReady framework.

## Includes

- strategy and operating model (`strategy_operating_model/`)
- use cases and factsheet templates (`usecases/`)
- KPI catalog (`kpi_catalog/`)
- action codes and decision spines (`action_codes/`)
- semantic model definitions (`semantic_models/`)
- data contracts (`data_contracts/`)
- business objects (`business_objects/`, D-608) — derived from contracts + KPI lineage
- reusable templates (`templates/`)
- implementation playbooks (`implementation_guides/`)

Terminology is grounded in KPI Catalog definitions and semantic metadata; there is no separate glossary SSOT.

## Boundaries

- `core/` defines meaning and governance.
- `products/` implements platform-specific products.
- `tooling/` automates generation and validation.

Use `docs/README.md` as the global entry point.
