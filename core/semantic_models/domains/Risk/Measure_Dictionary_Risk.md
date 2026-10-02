# Measure Dictionary - Risk

> **Generated view.** The source of truth is the per-measure files under [`measures/`](measures/). Edit those (or use ActionReady Studio); regenerate this file with `python tooling/codegen/measure_dictionary_files.py render`.

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Enterprise Value-at-Risk Index
  is_kpi_measure: true
  kpi_id_ref: KPI-GOV-004
  semantic_model: Risk_SemanticModel
  display_folder: 02_Enterprise
  category: KPI
  expression:
    logical: Enterprise Value-at-Risk Index = Weighted index of normalized domain risk signals.
    aggregation_method: average
  documentation:
    description: Composite enterprise risk index based on domain signals.
    notes: 'Grain: entity_month. Unit: index.

      Lineage: fact_risk[Value at Risk Index].

      QA: Weighting logic documented in upstream model.

      '
  dependencies:
    columns:
    - fact_risk[Value at Risk Index]
  governance:
    owner: Risk Analytics
    status: active
    version: v0.1
    last_review: TBD

- measure_name: Supplier Risk Score
  is_kpi_measure: true
  kpi_id_ref: KPI-SCM-022
  semantic_model: Risk_SemanticModel
  display_folder: 03_Supply
  category: KPI
  expression:
    logical: Supplier Risk Score = Composite risk score derived from supplier risk factors.
    aggregation_method: average
  documentation:
    description: Average supplier risk score across the selected scope.
    notes: 'Grain: supplier_month. Unit: score.

      Lineage: fact_supplier_risk[Risk Score].

      QA: Supplier score normalization documented.

      '
  dependencies:
    columns:
    - fact_supplier_risk[Risk Score]
  governance:
    owner: Risk Analytics
    status: active
    version: v0.1
    last_review: TBD

- measure_name: Supplier Risk Score (Entity)
  is_kpi_measure: false
  kpi_id_ref: ''
  semantic_model: Risk_SemanticModel
  display_folder: FIN-001
  category: Supporting
  expression:
    aggregation_method: custom
    logical: Supplier Risk Score (Entity) = VAR _Suppliers = ADDCOLUMNS ( VALUES ( dim_supplier[SupplierKey] ), "@AP", CALCULATE ( SUM ( fact_accounts_payable[AP Amount] ) ), "@Risk", CALCULATE ( AVERAGE ( fact_supplier_risk[Risk Score] ) ) ) VAR _Scored = FILTER ( _Suppliers, NOT ISBLANK ( [@Risk] ) ) RETURN DIVIDE ( SUMX ( _Scored, [@AP] * [@Risk] ), SUMX ( _Scored, [@AP] ) )
  documentation:
    description: 'AP-exposure-weighted supplier risk for the entity in filter context. Formula: SUMX over suppliers of (entity AP exposure × supplier Risk Score) / total entity AP exposure, over risk-scored suppliers only. Grain: entity_month · Unit: score (payables-weighted) · Owner: Risk Analytics · Status: active · Actions: F-C1.4 Rationale: risk-weighted payables exposure surfaces the liquidity risk a risky supplier base carries into the cash conversion cycle — makes supplier risk a legitimate entity-level column on the cash matrix rather than a global constant.'
    notes: 'Nachgetragen 01.10.2026: steht seit #421 (06f93e98c, 15.08.2026) in dist, ohne Dictionary-Eintrag (check_tmdl_vs_measure_dictionary rot). Ausdruck aus dem TMDL übernommen.'
  governance:
    owner: Risk Analytics
    status: active
    version: v1.0
    last_review: '2026-10-01'
```

