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
- reusable templates (`templates/`)
- glossary (`glossary/`)
- implementation playbooks (`implementation_guides/`)

## Boundaries

- `core/` defines meaning and governance.
- `products/` implements platform-specific products.
- `tooling/` automates generation and validation.

Use `docs/README.md` as the global entry point.
