/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/ai/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

export interface DataContract {
  domain: string;
  version: string;
  owner: string;
  dimension: {
    name: string;
    columns: {
      name: string;
      type: string;
      role?: string;
      ref?: string;
      nullable?: boolean;
    }[];
  }[];
  fact: {
    name: string;
    grain: string;
    columns: {
      name: string;
      type: string;
      agg?: string;
      ref?: string;
      nullable?: boolean;
    }[];
  }[];
  settings?: {
    grain_rules?: string;
    naming?: string;
    currency?: string;
    time_zone?: string;
  };
}
