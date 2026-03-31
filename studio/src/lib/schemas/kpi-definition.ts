/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface KPIDefinitionCatalogEntry {
  kpi_id: string;
  kpi_key: string;
  kpi_type: string;
  kpi_role?: string;
  impact_dimension: string;
  /**
   * @minItems 1
   */
  domain_tag: [string, ...string[]];
  use_case_ref: string[];
  action_code_ref: string[];
  calc_type: string;
  business?: {
    [k: string]: unknown | undefined;
  };
  technical?: {
    [k: string]: unknown | undefined;
  };
  governance?: {
    [k: string]: unknown | undefined;
  };
  metadata_quality?: {
    [k: string]: unknown | undefined;
  };
  /**
   * Causal relationships that quantify how influencing KPIs affect this KPI (typically strategic KPI).
   */
  causal_links?: {
    model_type: 'local_linear_beta' | 'elasticity' | 'piecewise_linear' | 'lookup';
    /**
     * Date the model was last reviewed or estimated.
     */
    as_of: string;
    /**
     * @minItems 1
     */
    links: [CausalLink, ...CausalLink[]];
  };
  [k: string]: unknown | undefined;
}
export interface CausalLink {
  influencing_kpi_id: string;
  effect: {
    kind: 'pp_to_pp' | 'pct_to_pct' | 'abs_to_abs' | 'elasticity';
    coefficient: number;
    direction: 'positive' | 'negative';
    interpretation: string;
  };
  applicability?: {
    grain: string;
    segments?: string[];
    valid_range?: {
      from_min?: number;
      from_max?: number;
    };
  };
  formula: {
    /**
     * Deterministic string format for math and units (preferred for downstream processing).
     */
    standardized: string;
    /**
     * Optional LaTeX representation.
     */
    latex?: string;
  };
  evidence?: {
    source?: string;
    confidence?: 'Low' | 'Medium' | 'High';
    notes?: string;
  };
}
