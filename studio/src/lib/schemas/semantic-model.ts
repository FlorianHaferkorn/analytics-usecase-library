/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/generator/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface SemanticModel {
  model_id: string;
  tables: {
    name: string;
    type: string;
    columns?: string[];
    hidden?: string[];
  }[];
  relationships: {
    from_table: string;
    from_column: string;
    to_table: string;
    to_column: string;
    cardinality: string;
    direction: string;
    is_active?: boolean;
  }[];
  hierarchies?: string[];
  sort_by?: string[];
  security_tables?: string[];
  modeling_rules: string[];
}
