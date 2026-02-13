# templates

Purpose:
Reusable use case templates for business factsheets and bracket YAML files.

Scope:

- usecase_factsheet_business.md — Human-only template for business stakeholders (no technical IDs/formulas)
- UseCase_Bracket_TEMPLATE.yaml — Machine-readable SSOT template (orchestration, value driver, UX layout)
- Not: Platform configs, data contracts

Structure:
Business factsheets are for human storytelling and context; all technical configuration lives in the UseCase_Bracket.yaml.

Usage:

- Start new use cases by copying both templates into the use case directory
- Business factsheets must NOT contain YAML blocks, KPI IDs, or action code references
- UseCase_Bracket.yaml is the exclusive machine-readable source for the Registry Engine

Relations:
PATTERNS supporting core/usecases and core/strategy_operating_model alignment.
