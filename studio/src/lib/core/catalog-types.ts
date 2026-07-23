/** Client-safe KPI catalog shape (no fs imports). */

export interface CatalogKpi {
  kpi_id: string;
  kpi_key: string;
  kpi_type: string;
  kpi_role: string;
  impact_dimension: string;
  domain_tag: string[];
  use_case_ref: string[];
  action_code_ref: string[];
  calc_type: string;
  business: {
    purpose: string;
    definition: string;
    grain_scope: string;
    unit_format: string;
    interpretation: string;
  };
  technical: {
    dax_name: string;
    formatString: string;
    description: string;
    dax_expression: string;
    depends_on_measures: string[];
    lineage: string[];
  };
  governance: {
    business_owner: string;
    data_owner: string;
    steward: string;
    review_cycle: string;
    validation_process: string;
    qa_rules: string[];
    version: string;
  };
  metadata_quality: {
    completeness_score: number;
    last_review: string;
  };
}
