/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface BusinessFactsheetV12 {
  metadata: {
    use_case_id: string;
    use_case_name: string;
    domain: string;
    business_owner: string;
    decision_owner: string;
    kpi_owner?: string;
    reporting_level: string;
    analytics_stage: string;
    status?: string;
    links?: {
      dataset_model?: string;
      page_template?: string;
    };
  };
  summary: {
    purpose: string;
    business_value: string;
    out_of_scope: string[];
  };
  /**
   * @minItems 3
   */
  business_questions: [string, string, string, ...string[]];
  /**
   * @minItems 1
   */
  required_kpis: [
    {
      id: string;
      name: string;
      purpose: string;
      definition_short: string;
      unit: string;
      grain: string;
      agg: string;
      target: string;
      interpretation: string;
      lineage?: string;
    },
    ...{
      id: string;
      name: string;
      purpose: string;
      definition_short: string;
      unit: string;
      grain: string;
      agg: string;
      target: string;
      interpretation: string;
      lineage?: string;
    }[]
  ];
  business_logic: {
    logic_summary?: string;
    triggers?: {
      kpi: string;
      condition: string;
      threshold: string;
      scope: string;
      exclusion?: string;
      action_code: string;
    }[];
  };
  action_codes: {
    code: string;
    name: string;
    trigger: string;
    description: string;
    expected_kpi_impact: string;
    level: string;
    owner: string;
  }[];
  layout_330300: {
    kpi_cards: string[];
    visuals_30s: {
      visual_name: string;
      visual_type: string;
      x_axis: string;
      y_axis: string;
      segment: string;
      default_filters: string;
    }[];
    diagnostics_300s: string[];
    slicers: string[];
  };
  data_requirements: {
    required_facts?: string[];
    required_dimensions?: string[];
    required_grain?: string;
    required_time_range?: string;
    required_slicers?: string[];
  };
  dependencies: {
    assumptions?: string[];
    constraints?: string[];
  };
  success_criteria: string[];
  risks: string[];
}
