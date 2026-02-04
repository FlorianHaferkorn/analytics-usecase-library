# Aurora Group Showcase

Purpose:
Demonstrate the ActionReady Analytics Framework end-to-end with a realistic synthetic company.

What’s inside

```yaml
aurora_group/
  company/          # Profile, operating model, org/value chain
  data/             # Synthetic contracts and sample extracts
  models/           # Sample semantic model for Aurora
  usecases/         # Demo core use cases (links to canonical framework/usecases factsheets)
  reporting/        # PBIP layouts and screenshots (3–30–300)
```

How to use

- Start with `company/Aurora_Group_Profile.md` and `company/Aurora_Operating_Model.md`.
- Sample data lives in `data/gold/` (Delta tables: `gold/facts/fact_sales`, `gold/dimensions/dim_*`). Data contracts and source definitions are in `framework/data_contracts/`; this showcase consumes gold-layer outputs.
- Build the model from `models/core_action_ready_model.yaml` (or use the semantic model in `semantic_models/`).
- Implement pages following `framework/templates/page_templates/*` and `reporting/pbip_layouts.md`.
- Align use cases with the canonical factsheets in `framework/usecases/core/` (references to main library).

To reproduce

1. Clone the repo and open from repo root.
2. Run framework checks: `_internal/tools/validation/run_all_checks.ps1` (or stage 1 only: `run_stage1_checks.ps1`).
3. For Fabric/Power BI: run `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1`; generate TMDL measures into `implementations/microsoft_fabric_powerbi/dist` if needed.
4. Point the Aurora semantic model/dataset to `showcases/aurora_group/data/gold/` (or your deployed gold path).

Scope for the demo

- COM-001, COM-002, COM-003
- OPS-001
- SCM-001
- FIN-001
See `usecases/core/*.md` in this folder for demo-specific pointers to canonical factsheets, data, and layouts.

Relations

- WHY: mirrors Aurora strategy and org in `company/`.
- HOW: uses operating-model rules from `framework/strategy_operating_model/operating_model/semantic_layer.md` and `data_governance.md`.
- WITH WHAT: relies on Action Codes, KPI catalog, measure dictionary.
- PATTERNS: applies the 3–30–300 templates from `framework/templates/page_templates/`.

