# Core Use Case Definition of Done (DoD)

## 1. Scope

This Definition of Done (DoD) applies to all **core use cases** under:

- `core/usecases/core/*`

A core use case is considered **build-ready** (ready for semantic model and report implementation) only if all criteria in this document are fulfilled.

## 2. Global Preconditions

Before any individual use case can be marked as build-ready:

- Strategic KPIs and key questions are defined in `core/strategy_operating_model/company/*`.
- Action Codes portfolio and rationale are defined in `core/action_codes/*`.
- KPI catalogs and schema are valid according to  
  `core/templates/kpi_catalog_templates/kpi_catalog_SCHEMA.md` and `run_all_checks.ps1`.
- Use case templates (Business Factsheet and UseCase_Bracket.yaml) are stable and referenced in  
  `core/usecases/templates/*`.

## 3. Business DoD (per Use Case)

A core use case’s **Business Factsheet** is considered done when:

- The file `core/usecases/core/<UC-ID>_*/Business_Factsheet.md`:
  - Follows the v1.2 template in `core/usecases/templates/usecase_factsheet_business.md`.
  - Passes validation via `check_schema_validation.ps1`.
- The following content is complete and consistent:
  - **Business Summary & Business Value**: Clear, 1–3 paragraphs, no TBD.
  - **Core Business Questions**: List of concrete questions, not tool-focused.
  - **Required KPIs**:
    - All `required_kpi_ids` exist in `core/kpi_catalog/*`.
    - No placeholder IDs remain.
  - **Triggers & Action Codes**:
    - Action Codes exist in `core/action_codes/README.md`.
    - Action code subscriptions are declared in `UseCase_Bracket.yaml` (`orchestration.action_code_ids`).
    - All Action Codes are prescriptive (Do / Stop / Shift).
    - No diagnostic-only or interpretive Action Codes remain.
    - Expected impact and risks are explicitly stated.
  - **Page Layout (3–30–300)**:
    - 3s / 30s / 300s views are described and mapped to existing page templates.
  - **Data Requirements, Risks & Assumptions**:
    - No open TBD markers in critical fields.

## 4. Technical DoD (per Use Case)

A core use case’s **UseCase_Bracket.yaml** is considered done when:

- The file `core/usecases/core/<UC-ID>_*/UseCase_Bracket.yaml`:
  - Follows the schema in `tooling/ai/schemas/usecase_bracket.schema.json`.
  - Passes validation via `check_schema_validation.ps1`.
- The following content is complete and consistent:
  - **Model References**:
    - `semantic_model_id` and `semantic_model_definition_path` reference existing files in `core/semantic_models/*`.
  - **KPI → Measure Mapping**:
    - All required KPIs from the Business Factsheet are mapped to measures.
    - KPI IDs exist in `core/kpi_catalog/*`.
  - **Data Contract Scope**:
    - Referenced tables and columns exist in `core/data_contracts/domains/*.yaml`.
    - Grain and keys are consistent with the domain data contracts.
  - **Semantic Model Requirements**:
    - Domain and core action-ready models are clearly referenced.
    - No conflicting or duplicate model definitions.
  - **Measures Inventory**:
    - Measures are documented in `core/semantic_models/domains/Measure_Dictionary_*.md`.
    - Naming, grain, unit, and lineage are documented.
  - **RLS / OLS**:
    - RLS/OLS concept is described (even if not yet implemented).
  - **QA & Validation**:
    - At least basic rules are defined (reconciliation with domain reports, zero-checks, range-checks).

## 5. Tooling & Automation DoD

For a core use case to be build-ready:

- `run_all_checks.ps1` completes without errors:
  - `validate_factsheets.ps1`
  - `validate_kpi_catalog.ps1`
  - `check_factsheet_vs_kpi.ps1`
- If `_Measures.tmdl` files exist for the use case:
  - `products/fabric/powerbi/tooling/validation/check_measures_vs_kpi.ps1` passes without missing KPI references.
- AI schemas for business factsheet and use case bracket:
  - `tooling/ai/schemas/business_factsheet_v1_2.schema.json`
  - `tooling/ai/schemas/usecase_bracket.schema.json`  
  are aligned with the current templates.

## 6. Build-Ready Status

A core use case is considered **build-ready** when:

- Business DoD (Section 3) is fulfilled.
- Technical DoD (Section 4) is fulfilled.
- Tooling & Automation DoD (Section 5) is fulfilled.

At that point, the use case may be tagged (e.g. in frontmatter or inventory) with:

- `status: build_ready`

and handed over to:

- MCPs / engineers for semantic model and report implementation, or
- automation/agents for measure generation and validation.

No report implementation should start before the use case is build-ready according to this DoD.

