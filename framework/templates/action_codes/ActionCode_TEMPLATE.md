# Action Code Template (Canonical)

This file contains exactly one YAML block that defines a single Action Code.
It is designed to be:

- human-readable (customer-ready),
- machine-readable (agent generation & validation),
- scalable (strict structure, minimal free text),
- maintainable (stable IDs & lifecycle handling).

---

```yaml
schema_version: "1.1"

id: "<e.g. C-P1.1>"
name: "<Short action name>"
owner_domain: "<Commercial | SupplyChain | CustomerValue | Liquidity | Operations | Governance_ESG>"
impact_dimension: "<Growth | Profitability | Liquidity | Service | CustomerValue | Risk | Governance | ESG>"

status: "<draft | active | deprecated>"
lifecycle:
  introduced_date: "<YYYY-MM-DD>"
  deprecated_date: null
  replaced_by: null
  change_notes: []

category:
  group: "<e.g. Price & Discount Management>"
  theme: "<e.g. Correct Price Leakage>"

tags: []

strategic_alignment:
  strategic_kpis:
    - id: "<StrategicKpiId>"
      role: "<primary | secondary>"
  decisions_enabled: []
  non_goals: []

use_case_links:
  core_use_cases: []
  related_use_cases: []

kpis:
  trigger_kpis:
    - kpi_id: "<KpiId>"
      label: "<Human label>"
      semantic_ref:
        model_domain: "<SemanticModelDomain>"
        measure: "<MeasureName>"
  guardrail_kpis: []
  outcome_kpis: []

scope:
  default_grain: "<day | week | month>"
  default_perspective: ["<Org>", "<Product>", "<Customer>"]
  supported_slices: []
  exclusions: []

trigger:
  type: "<Deviation | Pattern | Risk | Structural>"
  evaluation:
    grain: "<day | week | month>"
    window:
      kind: "<rolling | fixed>"
      length: 1
      unit: "periods"
    persistence:
      required: false
      min_consecutive_periods: 1
    minimum_data:
      min_observations: 1
      volume_guardrail:
        enabled: false
        metric_kpi_id: "<KpiId>"
        comparator: "<gte | gt>"
        value: 0
        unit: "<amount | qty | % | index>"
  levels:
    L1:
      severity: "EarlyWarning"
      condition:
        metric_kpi_id: "<KpiId>"
        comparator: "<lt | lte | gt | gte | eq | neq>"
        threshold:
          basis: "<target | plan | ly | baseline | absolute>"
          value: 0
          unit: "<pp | % | amount | qty | days | index>"
        filters: []
    L2:
      severity: "RequiredIntervention"
      condition:
        metric_kpi_id: "<KpiId>"
        comparator: "<lt | lte | gt | gte | eq | neq>"
        threshold:
          basis: "<target | plan | ly | baseline | absolute>"
          value: 0
          unit: "<pp | % | amount | qty | days | index>"
        filters: []
    L3:
      severity: "PrescriptiveExecution"
      condition:
        metric_kpi_id: "<KpiId>"
        comparator: "<lt | lte | gt | gte | eq | neq>"
        threshold:
          basis: "<target | plan | ly | baseline | absolute>"
          value: 0
          unit: "<pp | % | amount | qty | days | index>"
        filters: []
  gating_rules: []

impact:
  category: "<Low | Medium | High>"
  expected_range:
    metric_kpi_id: "<KpiId>"
    value_low: 0
    value_high: 0
    unit: "<pp | % | amount | qty | days | index>"
    time_to_effect:
      min_periods: 1
      max_periods: 1
  mechanism: []
  confidence:
    level: "<Low | Medium | High>"
    rationale: []

operational_execution:
  primary_owner_role: "<Role>"
  stakeholders: []
  prerequisites: []
  steps: []
  effort:
    level: "<Low | Medium | High>"
    typical_duration_days: 0
  risks_and_tradeoffs: []

data_requirements:
  required_entities: []
  semantic_dependencies:
    measures: []
    tables: []

automation:
  detection:
    enabled: false
    evaluation_frequency: "<daily | weekly | monthly>"
    output: ""
  suggested_actions:
    enabled: false
    outputs: []
  copilot_prompts: []

tracking:
  execution_log:
    enabled: false
    recommended_storage: "fact_action_execution"
    minimum_fields: []
  outcome_evaluation:
    enabled: false
    recommended_storage: "fact_action_outcome"
    minimum_fields: []

governance:
  approvals_required: []
  rollback_plan: []
  documentation_links: []

quality_rules:
  - "All kpi_id values must exist in KPI catalog."
  - "Trigger severity must be strictly increasing from L1 to L3."
  - "impact.expected_range.metric_kpi_id must be one of kpis.outcome_kpis."
  - "If status=deprecated then lifecycle.replaced_by is required."
  - "No free-text trigger notes: use gating_rules and structured filters."
```
