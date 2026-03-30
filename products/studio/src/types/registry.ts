export interface KpiRecord {
  id: string;
  title?: string;
  kpi_type?: string;
  impact_dimension?: string;
  domain_tag?: string[];
  calc_type?: string;
  status?: string;
  business?: {
    purpose?: string;
    definition?: string;
    grain_scope?: string;
    unit_format?: string;
  };
  technical?: {
    measure_name?: string;
    description?: string;
    depends_on_measures?: string[];
  };
  governance?: {
    business_owner?: string;
    data_owner?: string;
  };
  source?: string;
}

export interface ActionCodeRecord {
  id: string;
  name?: string;
  owner_domain?: string;
  impact_dimension?: string;
  status?: string;
  owner_role?: string;
  steward_role?: string;
  kpis?: string[];
  scope?: Record<string, unknown>;
  trigger?: Record<string, unknown>;
  impact?: Record<string, unknown>;
  source?: string;
  raw?: Record<string, unknown>;
}

export interface UseCaseRecord {
  id: string;
  title?: string;
  domain?: string;
  governance?: {
    owner_role?: string;
    steward_role?: string;
  };
  orchestration?: {
    strategic_kpi_id?: string;
    influencing_kpi_ids?: string[];
    action_code_ids?: string[];
    supporting_kpi_ids?: string[];
  };
  value_driver_model?: {
    formula?: string;
    impact_direction?: "maximize" | "minimize";
    primary_driver?: string;
    impact_logic?: string;
  };
  ux_layout_rules?: Record<string, unknown>;
  source?: string;
  raw?: Record<string, unknown>;
}

export interface Registry {
  meta: {
    generated_at_utc: string;
    registry_version: string;
  };
  objects: {
    kpis: Record<string, KpiRecord>;
    action_codes: Record<string, ActionCodeRecord>;
    use_cases: Record<string, UseCaseRecord>;
  };
}

export interface CatalogSnapshot {
  kpi_ids: string[];
  action_code_ids: string[];
  use_case_ids: string[];
  allowed_grains: string[];
}
