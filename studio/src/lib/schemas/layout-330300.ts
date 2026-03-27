/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface Layout330300Layout {
  kpi_cards: {
    kpi_id: string;
    visual_type: string;
    sparkline_field?: string;
    comparison?: string;
    status_logic?: string;
  }[];
  visuals_30s: {
    name: string;
    visual_type: string;
    x_axis: string;
    y_axis: string;
    segment?: string;
    default_filters?: string;
  }[];
  diagnostics_300s: {
    name: string;
    visual_type: string;
    columns?: string[];
    sort_by?: string;
    limit?: number;
  }[];
  slicers: {
    field: string;
    type: string;
    default?: string;
  }[];
  tooltips: {
    fields?: string[];
    notes?: string;
  };
}
