# Fabric / Power BI Domain Model Blueprints

## Purpose

Domain-specific semantic model blueprints that:

- Define which use cases, tables, relationships, and measures belong to each domain
- Drive TMDL generation (via `tooling/generator/` or the Fabric orchestrator)
- Rely on **data contracts** in `core/data_contracts/domains/`. Aurora gold data lives in `showcases/aurora_group/data/gold/`.

## Architecture

```
Tool-agnostic:
├── core/data_contracts/domains/      # Table schemas per domain
├── core/kpi_catalog/                 # KPI definitions with DAX
└── semantic_models/domains/          # Measure dictionaries (conceptual)

Fabric product (this repo):
├── products/fabric/powerbi/blueprints/   # ← YOU ARE HERE: Model blueprints
├── products/fabric/powerbi/dist/        # Generated TMDL (SemanticModel) and reports
└── products/fabric/powerbi/orchestrator/ # Pipeline (orchestrate_full_model.ps1)
```

## Contents

- **`Commercial.yaml`** – Commercial domain model (COM-001 through COM-004)
  - Use Cases: Sales Performance, Margin & Price, Customer Value, Promotion Effectiveness
  - Tables: dim_date, dim_org, dim_product, dim_customer, fact_sales
  - Status: **Active** (COM-002 complete, COM-001/003/004 pending DAX)

- **`Finance.yaml`** – Finance domain model (FIN-001, FIN-002)
  - Use Cases: Cash & Liquidity, Cost Performance
  - Tables: dim_date, dim_org, dim_account, fact_finance, fact_gl_journal, fact_working_capital
  - Status: **Placeholder** (to be implemented after Commercial validation)

- **`Operations.yaml`** – Operations domain model (OPS-001, OPS-002, OPS-003)
  - Use Cases: OEE Performance, Asset Reliability, Quality & Yield
  - Tables: dim_date, dim_org, dim_asset, dim_product, fact_ops, fact_inventory_snapshot
  - Status: **Blueprint complete** (relationships and display_folders defined; DAX in KPI Catalog for OPS-* still to be added)

- **`SupplyChain.yaml`** – Supply Chain domain (SCM-001, SCM-002, SCM-003). Stub for domain semantic model.
- **`Experience.yaml`** – Experience domain (XD-001, XD-002, XD-003). Stub for domain semantic model.
- **`core_action_ready_model.yaml.legacy`** – Original generic cross-domain model; archived to `internal/archive/legacy_aurora_models_2026-02/`

## Usage

### 1. Creating New Domain Models

Use `Commercial.yaml` as template:
```yaml
model_id: aurora_{domain}
domain: {Domain}
use_cases: [{UC-001}, {UC-002}, ...]
tables:
  dimensions: [...]
  facts: [...]
relationships: [...]
display_folders: [...]
```

### 2. Generating TMDL Semantic Models

```powershell
# Generate Commercial semantic model from blueprint (output to Fabric dist)
./tooling/generator/generate_semantic_model_from_blueprint.ps1 `
  -Blueprint "products/fabric/powerbi/blueprints/Commercial.yaml" `
  -Output "products/fabric/powerbi/dist/Commercial.SemanticModel"
```

### 3. Populating Measures

Measures are sourced from:
- **DAX Expressions**: `core/kpi_catalog/KPI_Catalog.md` (field: `dax_expression`)
- **Display Folders**: `semantic_models/domains/{Domain}/Measure_Dictionary_{Domain}.md`

Ensure KPI Catalog has `dax_expression: |` fields populated before generation.

## Dependencies

Each model blueprint requires:
1. **Data Contracts**: Domain table schemas in `data_contracts/domains/{domain}.yaml`
2. **KPI Catalog**: DAX expressions for all strategic KPIs referenced in use cases
3. **Measure Dictionary**: Display folder mappings in `semantic_models/domains/{Domain}/`
4. **Gold Layer Data**: Aurora synthetic data in `showcases/aurora_group/data/gold/` (or deployed path)

## Implementation Status

| Domain | Model File | Use Cases | Measures | Status |
|--------|-----------|-----------|----------|--------|
| Commercial | Commercial.yaml | COM-001 to COM-004 | 24 KPIs total | 🟡 Partial (6/24 complete) |
| Finance | Finance.yaml | FIN-001 to FIN-002 | TBD | 🔴 Placeholder |
| Operations | Operations.yaml | OPS-001 to OPS-003 | Display folders defined | 🟡 Blueprint complete (DAX pending) |

**Legend**: 🟢 Complete | 🟡 Partial | 🔴 Placeholder

## Next Steps

In-file comments in `Operations.yaml` and `Finance.yaml` point to this section.

1. **Complete Commercial Domain** (Priority 1):
   - [ ] Add DAX expressions for COM-001 (7 measures) to KPI Catalog
   - [ ] Add DAX expressions for COM-003 (8 measures) to KPI Catalog
   - [ ] Add DAX expressions for COM-004 (5 measures) to KPI Catalog
   - [ ] Generate Commercial.SemanticModel TMDL
   - [ ] Test in Power BI Desktop

2. **Finance Domain** (Priority 2):
   - [ ] Complete Finance.yaml blueprint
   - [ ] Add DAX expressions for FIN-001, FIN-002 to KPI Catalog
   - [ ] Generate Finance.SemanticModel TMDL

3. **Operations Domain** (Priority 3):
   - [ ] Complete Operations.yaml blueprint
   - [ ] Add DAX expressions for OPS-001, OPS-002, OPS-003 to KPI Catalog
   - [ ] Generate Operations.SemanticModel TMDL

## Governance

- **Business Owner**: Domain-specific (see individual model files)
- **Technical Owner**: Analytics Core Team
- **Maintainers**: aurora-showcase-team
- **Review Cycle**: Monthly (after each domain completion)

**Note**: For framework definitions, refer to `semantic_models/domains/` and `core/kpi_catalog/`. The Fabric orchestrator (`products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1`) generates dist from core use cases and KPI catalog; these blueprints support alternative generation paths if needed.


