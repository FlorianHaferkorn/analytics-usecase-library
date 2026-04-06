# Measure Dictionary - Governance

Schema: see `core/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Actions Routed Count
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_routed.count
  semantic_model: Governance_SemanticModel
  display_folder: 06_Execution
  category: KPI
  expression:
    logical: Actions Routed Count = Count of routed action instances in the period.
    aggregation_method: count
  documentation:
    description: Count of routed action instances.
    notes: 'Grain: action_instance. Unit: count.

      Lineage: fact_action_governance[ActionInstanceId].

      QA: Exclude duplicates and canceled actions.

      '
  dependencies:
    columns:
    - fact_action_governance[ActionInstanceId]
  governance:
    owner: Executive Office
    status: active
    version: v0.1
    last_review: TBD
- measure_name: Action Outcome Rate %
  is_kpi_measure: true
  kpi_id_ref: enterprise.action_outcome_rate.pct
  semantic_model: Governance_SemanticModel
  display_folder: 06_Execution
  category: KPI
  expression:
    logical: Action Outcome Rate % = Successful Actions / Routed Actions.
    aggregation_method: ratio
  documentation:
    description: Share of routed actions that achieved the intended outcome.
    notes: 'Grain: action_instance. Unit: %.

      Lineage: fact_action_governance[Outcome Success Flag], fact_action_governance[ActionInstanceId].

      QA: Outcome definition and evaluation window must be consistent.

      '
  dependencies:
    columns:
    - fact_action_governance[Outcome Success Flag]
    - fact_action_governance[ActionInstanceId]
  governance:
    owner: Executive Office
    status: active
    version: v0.1
    last_review: TBD
```

