export interface UseCaseDraft {
  schema_version: "2.0";
  id: string;
  title: string;
  domain: string;
  governance: {
    owner_role: string;
    steward_role: string;
  };
  orchestration: {
    strategic_kpi_id: string;
    influencing_kpi_ids: string[];
    action_code_ids: string[];
    supporting_kpi_ids?: string[];
  };
  value_driver_model: {
    formula: string;
    impact_direction: "maximize" | "minimize";
    primary_driver?: string;
    impact_logic?: string;
    critical_threshold?: number;
  };
  ux_layout_rules: {
    report_structure: string;
    page_1_summary: {
      title: string;
      page_type: string;
      template_id?: string;
      component_3s: { kpi_id: string; visual_type: string };
      component_30s: Array<{ kpi_id?: string; kpi_ids?: string[]; visual_type: string }>;
    };
    page_2_execution: {
      title: string;
      page_type: string;
      template_id?: string;
      component_300s: {
        evidence_grain: string;
        evidence_columns: string[];
        action_panel: boolean;
        payload_mode: "full" | "summary" | "minimal";
      };
    };
  };
  documentation: {
    business_factsheet: string;
  };
  overrides?: Record<string, unknown>;
}

export const EMPTY_DRAFT: UseCaseDraft = {
  schema_version: "2.0",
  id: "NEW-001",
  title: "New Use Case",
  domain: "Commercial",
  governance: {
    owner_role: "",
    steward_role: "",
  },
  orchestration: {
    strategic_kpi_id: "",
    influencing_kpi_ids: [],
    action_code_ids: [],
    supporting_kpi_ids: [],
  },
  value_driver_model: {
    formula: "",
    impact_direction: "maximize",
    primary_driver: "",
    impact_logic: "",
  },
  ux_layout_rules: {
    report_structure: "2-Page-Lead",
    page_1_summary: {
      title: "Overview",
      page_type: "T1_Strategic_Overview",
      template_id: "pulse",
      component_3s: { kpi_id: "", visual_type: "kpi_card" },
      component_30s: [],
    },
    page_2_execution: {
      title: "Execution",
      page_type: "T2_Tactical_Variance",
      template_id: "action_matrix",
      component_300s: {
        evidence_grain: "entity_month",
        evidence_columns: [],
        action_panel: true,
        payload_mode: "full",
      },
    },
  },
  documentation: {
    business_factsheet: "./Business_Factsheet.md",
  },
};

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface Source {
  id: string;
  type: "url" | "text";
  name: string;
  content: string;
  include_in_chat: boolean;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}
