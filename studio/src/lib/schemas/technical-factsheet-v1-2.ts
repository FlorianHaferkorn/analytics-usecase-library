/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface TechnicalFactsheetV12 {
  metadata: {
    use_case_id: string;
    domain: string;
    technical_owner: string;
    model_id: string;
    source_systems?: string[];
    business_factsheet_link?: string;
  };
  model_references: {
    domain_data_contracts?: string[];
    source_contracts?: string[];
    semantic_models?: string[];
  };
  kpi_measure_map: {
    kpi_id: string;
    measure_name: string;
    format: string;
    folder: string;
    type: string;
  }[];
  data_contract_scope: {
    facts?: Record<string, unknown>[];
    dimensions?: Record<string, unknown>[];
    security?: Record<string, unknown>[];
  };
  semantic_model: {
    tables?: string[];
    relationships?: {
      from_table: string;
      from_column: string;
      to_table: string;
      to_column: string;
      cardinality: string;
      direction: string;
    }[];
    hierarchies?: string[];
    sort_by_rules?: string[];
    modeling_rules?: string[];
  };
  measure_inventory: {
    measure_name: string;
    kpi_or_supporting: string;
    purpose: string;
    folder: string;
    format: string;
    measure_type: string;
  }[];
  dax_definitions: {
    name: string;
    definition: string;
    comment?: string;
  }[];
  security: {
    rls?: string;
    ols?: string;
    security_tables?: string[];
  };
  technical_assumptions: string[];
  deployment: {
    mode?: string;
    refresh?: string;
    aggregations?: string;
    workspace?: string;
  };
  qa_rules: {
    check: string;
    rule: string;
    threshold: string;
    automated: boolean;
    owner: string;
  }[];
}
