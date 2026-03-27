/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

/**
 * Machine-readable SSOT for a use case. Links strategic KPI, influencing KPIs, action codes, governance roles, value driver model, and structured UX layout rules.
 */
export interface UseCaseBracketV20Lean {
  schema_version: '2.0';
  /**
   * Use case ID (e.g. COM-001, FIN-002, XD-003).
   */
  id: string;
  /**
   * Human-readable use case title.
   */
  title: string;
  /**
   * Business domain (Commercial, Finance, Operations, SupplyChain, XD).
   */
  domain: string;
  governance: {
    /**
     * Business accountability role ID (must exist in org_roles.yaml).
     */
    owner_role: string;
    /**
     * Data/definition accountability role ID (must exist in org_roles.yaml).
     */
    steward_role: string;
  };
  orchestration: {
    /**
     * Exactly 1 strategic (North Star) KPI ID from KPI catalog.
     */
    strategic_kpi_id: string;
    /**
     * Diagnostic lever KPI IDs from KPI catalog.
     */
    influencing_kpi_ids: string[];
    /**
     * Subscribed action code IDs from core/action_codes.
     */
    action_code_ids: string[];
    /**
     * KPI IDs required to calculate strategic/influencing/action KPIs (report BoM). Registry validates bracket completeness via depends_on closure.
     */
    supporting_kpi_ids?: string[];
  };
  value_driver_model: {
    /**
     * Mathematical relationship: StrategicKPI = f(InfluencingKPIs...).
     */
    formula: string;
    /**
     * Whether the strategic KPI should be maximized or minimized.
     */
    impact_direction: 'maximize' | 'minimize';
    /**
     * The main influencing KPI ID that drives the strategic KPI.
     */
    primary_driver?: string;
    /**
     * Narrative explaining how the primary driver affects the strategic KPI.
     */
    impact_logic?: string;
    /**
     * Optional deviation trigger (e.g. 0.05 = 5%).
     */
    critical_threshold?: number;
  };
  ux_layout_rules: {
    /**
     * Report pattern (e.g. 2-Page-Lead).
     */
    report_structure: string;
    /**
     * Optional canvas size for grid-based report (default 1920×1080). Enables proportional scaling when changed.
     */
    report_canvas?: {
      /**
       * Page width in pixels (Full HD: 1920).
       */
      width?: number;
      /**
       * Page height in pixels (Full HD: 1080).
       */
      height?: number;
    };
    page_1_summary: {
      title: string;
      /**
       * Grid page template for Overview (3s/30s): pulse = 6 KPI slots + 3 main; investigator = left slicer + focus + support.
       */
      template_id?: 'pulse' | 'investigator';
      component_3s: {
        /**
         * North Star KPI ID.
         */
        kpi_id: string;
        /**
         * Abstract visual type (tool-agnostic). Fabric maps to PBI visualType in products/fabric/powerbi.
         */
        visual_type: 'kpi_card';
      };
      /**
       * Diagnostic visuals for the 30-second layer.
       */
      component_30s: {
        /**
         * Single KPI ID.
         */
        kpi_id?: string;
        /**
         * Multiple KPI IDs for composite visuals.
         */
        kpi_ids?: string[];
        /**
         * Abstract visual type (tool-agnostic). Fabric maps to PBI visualType in products/fabric/powerbi.
         */
        visual_type:
          | 'trend_line'
          | 'bar_chart'
          | 'waterfall'
          | 'hundred_percent_stacked_bar'
          | 'stacked_bar'
          | 'funnel'
          | 'kpi_card';
        /**
         * Explicit slot assignment for Overview (when set, overrides heuristic).
         */
        slot_id?: 'Main_1' | 'Main_2' | 'Main_3';
      }[];
    };
    page_2_execution: {
      title: string;
      /**
       * Grid page template for Detail (300s): investigator = left slicer + focus + support; action_matrix = narrative + matrix.
       */
      template_id?: 'investigator' | 'action_matrix';
      component_300s: {
        /**
         * Grain of the evidence table — must match a governed fact-table grain from core/data_contracts/domains/*.yaml. Placeholder 'transaction_line' is forbidden; refer to internal/evidence_grain_audit_results.md for correct values.
         */
        evidence_grain: string;
        /**
         * Columns for the evidence table.
         */
        evidence_columns: string[];
        /**
         * KPI IDs or measure names for Detail_Matrix value columns (optional).
         */
        evidence_measures?: string[];
        /**
         * Whether to show the action panel.
         */
        action_panel: boolean;
        /**
         * How much action code detail to inject.
         */
        payload_mode: 'full' | 'summary' | 'minimal';
      };
    };
  };
  documentation: {
    /**
     * Relative path to Business_Factsheet.md.
     */
    business_factsheet: string;
  };
  /**
   * Optional visual bindings (axis, legend, rows, values, sort, topN) per page/slot. Written by UX Layout Editor; do not edit by hand.
   */
  ux_bindings?: {
    [k: string]: unknown | undefined;
  };
  overrides?: {
    /**
     * Custom folder name in Power BI semantic model.
     */
    measure_folder?: string;
    /**
     * Path to the related data contract YAML.
     */
    data_contract_ref?: string;
    [k: string]: unknown | undefined;
  };
}
