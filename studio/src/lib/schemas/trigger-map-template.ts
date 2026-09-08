/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface TriggerMapTemplate {
  settings: {
    timezone: string;
    currency_default: string;
    evaluation_default_window: string;
  };
  governance: {
    status: string;
    owner: string;
    last_reviewed: string;
    change_notes: string | null;
  };
  scopes: {
    scope_id: string;
    description: string;
    filters: Record<string, unknown>;
  }[];
  mappings: {
    mapping_id: string;
    action_code_id: string;
    owner_domain: string;
    scope_id: string;
    surfacing: {
      primary_page_type: string;
      secondary_page_types: string[];
      attention_priority: string;
      needs_action_panel: boolean;
    };
    trigger: {
      trigger_type: string;
      persistence: {
        periods: number;
        period_grain: string;
      };
      cooldown: {
        periods: number;
        period_grain: string;
      };
      conditions: Record<string, unknown>[];
      suppress_if: string[];
    };
    evaluation_tracking: {
      evaluation_window: string;
      leading_indicators: {
        kpi_id: string;
        expected_direction: string;
        tolerance: number;
      }[];
      lagging_indicators: string[];
      success_rule: string;
    };
    operational_metadata: {
      escalation_path: string | null;
      notes: string | null;
    };
  }[];
}
