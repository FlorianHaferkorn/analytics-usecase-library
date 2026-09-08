/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

/**
 * Aligned mirror of tooling/validation/schemas/action_code.schema.json. Kept here to avoid schema drift for AI tooling. Lean v2.0: removed lifecycle, category, tags, strategic_alignment; KPI lists as IDs only; governance roles at top level.
 */
export interface ActionCodeDefinitionV20AIMirror {
  schema_version: '2.0';
  inherits_decision_spine?: string | null;
  id: string;
  name: string;
  owner_domain: string;
  impact_dimension: string;
  status: 'draft' | 'active' | 'deprecated';
  /**
   * Accountable governance role for this action (not a person name).
   */
  owner_role: string;
  /**
   * Data quality / implementation governance role (must differ from owner_role).
   */
  steward_role: string;
  use_case_links?: {
    core_use_cases?: string[];
    related_use_cases?: string[];
  };
  kpis: {
    /**
     * KPI IDs (must exist in KPI catalog).
     *
     * @minItems 1
     */
    trigger_kpis: [string, ...string[]];
    /**
     * KPI IDs used as guardrails.
     */
    guardrail_kpis?: string[];
    /**
     * KPI IDs used to measure action outcome.
     */
    outcome_kpis?: string[];
  };
  scope: {
    default_grain: string;
    default_perspective: string[];
    supported_slices: string[];
    exclusions: string[];
  };
  trigger: {
    type?: string;
    evaluation?: {
      grain: string;
      window: {
        kind: string;
        length: number;
        unit: string;
      };
      persistence: {
        required: boolean;
        min_consecutive_periods: number;
      };
      minimum_data: {
        min_observations: number;
        volume_guardrail?: {
          enabled: boolean;
          metric_kpi_id: string;
          comparator: string;
          value: number | string;
          unit: string;
        };
      };
    };
    levels?: {
      L1: Level;
      L2: Level;
      L3: Level;
    };
    gating_rules?: string[];
  };
  impact_valuation?: {
    method: 'DirectMarginImprovement' | 'CostAvoidance' | 'RevenueUplift' | 'CashRelease' | 'RiskAvoidance';
    currency: string;
    success_window: {
      duration: string;
      metric_kpi_id: string;
      success_criteria: {
        kind: 'return_to_baseline' | 'threshold_met';
        baseline_window?: string;
        comparator?: string;
        threshold?: number | string;
        unit?: string;
      };
    };
    calculation_logic: {
      standardized: string;
      latex?: string;
    };
    required_measures?: string[];
    attribution?: {
      method: 'before_after' | 'diff_in_diff' | 'holdout';
      notes?: string;
    };
  };
  impact: Record<string, unknown>;
  operational_execution: Record<string, unknown>;
  data_requirements?: Record<string, unknown>;
  automation?: Record<string, unknown>;
  tracking?: Record<string, unknown>;
  governance?: Record<string, unknown>;
  execution_bridge?: {
    type: 'Webhook' | 'PowerAutomate' | 'API';
    mode: 'dry_run' | 'live';
    endpoint_template: string;
    http?: Record<string, unknown>;
    auth_reference?: Record<string, unknown>;
    payload_definition: Record<string, unknown>;
    audit: Record<string, unknown>;
  };
  quality_rules: string[];
}
export interface Level {
  severity: string;
  condition: Record<string, unknown>;
}
