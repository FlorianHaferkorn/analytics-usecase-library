# Microsoft Fabric / Power BI Implementation

Tool-specific adapter for the ActionReady Analytics Framework on **Microsoft Fabric + Power BI**. Core framework stays in `core/`; this folder is the single entry for implementers.

---

## Start here (single entry)

| Step | Action | Where |
|------|--------|--------|
| 1 | Read architecture and data layers (Silver-first) | `guide/README.md` → `guide/fabric_architecture_best_practices.md` |
| 2 | Align data: **Silver** contracts | `core/data_contracts/` — we define Silver; Gold + Semantics are built from it |
| 3 | Implement semantic model and measures | `guide/fabric_powerbi.md`, `guide/tmdl_best_practices.md`; generate TMDL from KPI catalog |
| 4 | Run validation | From repo root: `.\tooling\run_stage1_checks.ps1` then `.\products\fabric_powerbi\tooling\run_fabric_checks.ps1` |
| 5 | (Optional) Set up Fabric workspaces and deploy | `deployment/USAGE.md` |

Full procedure: `core/implementation_guides/playbook_strategy_to_first_report.md`.

---

## Design principles

- **Separation of concerns:** Framework (`core/`) is tool-agnostic; this implementation consumes it and does not change it.
- **Stable public API:** Use cases, KPI catalog, data contracts, action codes are the contract; products depend on them.
- **Generated vs source:** Generated output lives in `dist/` or showcase paths; never mixed with source under `core/` or `guide/`.
- **Single entry per audience:** Implementers start here → `guide/` → tools and deployment as needed.
- **Minimal cross-dependency:** This implementation references `core/`; framework does not reference implementation.

---

## Data layers (Silver-first)

We standardize on **4 physical + 1 logical** layers. See `core/strategy_operating_model/operating_model/data_layers_standard.md`.

- **We define Silver** via data contracts (`core/data_contracts/domains/`, `sources/`).
- **We deliver Gold + Semantics** (report packages, semantic models). Gold is derived from Silver.
- **Staging and Bronze** are out of scope unless explicitly included.

Procedure: Start from Silver contracts; then build Gold and the semantic layer. Do not start from Gold-only.

---

## Folder structure (streamlined)

| Path | Role |
|------|------|
| **guide/** | Single entry for reading: architecture, Fabric/Power BI mapping, TMDL. Start with `guide/README.md`. |
| **tools/** | Validation (`run_fabric_checks.ps1`), theme, page scaffold, apply_report_theme. No framework logic. |
| **validation/** | Fabric-specific check scripts (measures vs KPI, TMDL, DAX). Invoked via `tools/run_fabric_checks.ps1`. |
| **deployment/** | Setup and release scripts (workspaces, Git, fabric-cicd). Optional; see `deployment/USAGE.md`. |
| **dist/** | Generated TMDL per use case (customer rollout). Not mixed with source. |
| **pbip_templates/** | Canonical PBIP skeletons. References: `showcases/sample_pbip_report/`, `showcases/aurora_group/`. |

Framework (`core/`), Stage 1 and generation (`tooling/`), and showcases (`showcases/`) are outside this folder; this implementation only references them.

---

## Output modes (generated TMDL)

| Mode | Use | Output |
|------|-----|--------|
| **Aurora showcase** | Framework proof, single _Measures.tmdl | `showcases/aurora_group/semantic_models/.../tables/` (use `-UseAuroraShowcase`) |
| **dist** | Customer rollout / CI, per-use-case TMDL | `dist/<UseCase>/<UseCase>.SemanticModel/...` |

---

## Key references

| Need | Location |
|------|----------|
| Data layers (Silver-first) | `core/strategy_operating_model/operating_model/data_layers_standard.md` |
| Silver contracts | `core/data_contracts/` |
| Playbook (strategy → first report) | `core/implementation_guides/playbook_strategy_to_first_report.md` |
| Stage 1 (CI gate) | `tooling/run_stage1_checks.ps1` |
| Fabric checks | `products/fabric_powerbi/tooling/run_fabric_checks.ps1` |
