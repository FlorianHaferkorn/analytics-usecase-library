/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface MeasureInventory {
  measures: {
    measure_name: string;
    kpi_id: string;
    purpose: string;
    folder: string;
    format: string;
    type: string;
    dependencies?: string[];
  }[];
}
