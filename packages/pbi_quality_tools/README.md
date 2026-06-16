# pbi-quality-tools

A standalone Power BI / PBIP quality toolkit extracted from ALUCA (Analytics Library of Use Cases).

Use it **without cloning the full repo** to validate, repair, and diagnose Power BI report artifacts.

## Features

- Validate PBIR report structure (page size, visual bounds, required slots, forbidden visuals)
- Validate $schema URLs against pinned Microsoft schema versions
- Detect broken DAX measure references
- Self-heal deterministic violations (page size, visual bounds, schema URLs)
- Generate compact quality summaries for CI and AI agents
- Extensible BPA rule sets for TMDL and DAX

## Install (local development)

```bash
# From repo root
pip install -e packages/pbi_quality_tools

# Or install directly from this folder
pip install -e .
```

## Commands

```bash
# Validate all reports under a dist folder
pbi-quality validate --dist-root products/fabric/powerbi/dist

# Validate a single report
pbi-quality validate --dist-root /path/to/MyReport.Report

# Repair (self-heal) deterministic violations
pbi-quality repair --dist-root products/fabric/powerbi/dist

# Dry-run repair (show what would change)
pbi-quality repair --dist-root products/fabric/powerbi/dist --dry-run

# Quick diagnosis of a PBIP root
pbi-quality doctor --pbip-root products/fabric/powerbi/dist

# Compact summary mode (for CI / agent prompts)
pbi-quality validate --dist-root products/fabric/powerbi/dist --summary
```

## What is NOT included (repo-only)

The following capabilities require the full ALUCA repo:

- Golden Thread validation (KPI catalog, action codes, use case brackets)
- Measure Dictionary vs TMDL reconciliation
- Page template compliance (requires UseCase_Bracket.yaml)
- Aurora gold data Parquet validation
- Full Stage 1 governance checks

## Design principles

- Zero Aurora/repo-specific imports in the package
- Safe path guard: self-heal only writes inside `.Report/definition/`
- Deterministic fixes only; content/business logic is never auto-changed
- Token-efficient: `--summary` produces compact output for AI agents
