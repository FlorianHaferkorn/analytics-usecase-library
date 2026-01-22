# Aurora Group Showcase

Purpose:
Demonstrate the ActionReady Analytics Framework end-to-end with a realistic synthetic company.

What’s inside

```yaml
aurora_group/
  company/          # Profile, operating model, org/value chain
  data/             # Synthetic contracts and sample extracts
  models/           # Sample semantic model for Aurora
  usecases/         # Demo core use cases (links to canonical factsheets)
  reporting/        # PBIP layouts and screenshots (3–30–300)
```

How to use

- Start with `company/Aurora_Group_Profile.md` and `company/Aurora_Operating_Model.md`.
- Load sample data per `data/sample_data/README.md` using contracts in `data/sample_data_contracts/`.
- Build the model from `models/core_action_ready_model.yaml` using the OneLake-conform contracts.
- Implement pages following `framework/templates/page_templates/*` and `reporting/pbip_layouts.md`.
- Align use cases with the canonical factsheets in `usecases/core/` (references to main library).

Scope for the demo

- COM-001, COM-002, COM-003
- OPS-001
- SCM-001
- FIN-001
See `usecases/core/*.md` in this folder for demo-specific pointers to canonical factsheets, data, and layouts.

Relations

- WHY: mirrors Aurora strategy and org in `company/`.
- HOW: uses operating-model rules from `docs/operating_model/semantic_layer.md` and `data_governance.md`.
- WITH WHAT: relies on Action Codes, KPI catalog, measure dictionary.
- PATTERNS: applies the 3–30–300 templates from `framework/templates/page_templates/`.

