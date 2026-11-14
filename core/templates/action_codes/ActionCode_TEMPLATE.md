# Action Code Template (Canonical v2.0)

This file contains exactly one YAML block that defines a single Action Code.
It is designed to be:

- human-readable (customer-ready),
- machine-readable (agent generation & validation),
- scalable (strict structure, minimal free text),
- maintainable (stable IDs & governance roles).

**v2.0 changes:** Removed `lifecycle`, `category`, `tags`, `strategic_alignment`.
KPI lists are IDs only. Governance roles (`owner_role`, `steward_role`) promoted to top level.

---

```yaml
schema_version: "2.0"

inherits_decision_spine: null

id: "<e.g. C-P1.1>"
name: "<Short action name>"
owner_domain: "<Commercial | SupplyChain | CustomerValue | Liquidity | Operations | Governance_ESG>"
impact_dimension: "<Growth | Profitability | Liquidity | Service | CustomerValue | Risk | Governance | ESG>"

status: "<draft | active | deprecated>"

owner_role: "<Accountable governance role, e.g. Pricing Lead>"
steward_role: "<Data quality governance role, e.g. Commercial BI Lead>"

use_case_links:
  core_use_cases: []
  related_use_cases: []

kpis:
  trigger_kpis:
    - "<KpiId>"
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

# Action contract (D-833 step 1, required since 14.11.2026). Derive from the fields above with
# `python -m tooling.migration.action_code_vertrag --apply`; never estimate: unknown = nicht_belegt.
parameters:
  - { name: period, type: period, required: true, grain: "<scope.default_grain>", source_field: scope.default_grain }
  - { name: trigger_level, type: trigger_level, required: true, allowed_values: [L1, L2, L3], source_field: trigger.levels }
  - { name: "<snake_case>", label: "<scope.default_perspective entry>", type: dimension_member, required: true,
      binding: nicht_belegt, source_field: scope.default_perspective }
preconditions:
  combine: guardrails_all_and_trigger_any
  checks:
    - { id: level_l1, role: trigger, kind: kpi_level, ref: trigger.levels.L1.condition, kpi_id: "<KPI-...>", pruefbar: true }
permitted_role:
  source_field: governance.approvals_required
  roles:
    - { approver: "<entry of approvals_required>", role_id: "<org_roles id or nicht_belegt>" }
review:
  required: true
  state: vorgeschlagen

quality_rules:
  - "All kpi_id values must exist in KPI catalog."
  - "Trigger severity must be strictly increasing from L1 to L3."
  - "impact.expected_range.metric_kpi_id must be one of kpis.outcome_kpis."
  - "If status=deprecated then a replacement action code should be referenced."
  - "No free-text trigger notes: use gating_rules and structured filters."
  - "owner_role and steward_role must differ."
```
