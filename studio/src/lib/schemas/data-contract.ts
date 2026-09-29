/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/generator/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

/**
 * Columns of the definition this domain's model uses (domain view); default all.
 *
 * @minItems 1
 */
export type UsesColumns = [string, ...string[]];

export interface DataContract {
  domain: string;
  version: string;
  owner: string;
  dimension: (DimensionTable | ConformedReference)[];
  fact: (FactTable | ConformedReference)[];
  quality_rules?: QualityRules;
  settings?: {
    grain_rules?: string;
    naming?: string;
    currency?: string;
    /**
     * IANA time zone of the business calendar, e.g. Europe/Berlin.
     */
    timezone?: string;
    /**
     * First day of the fiscal year as MM-DD.
     */
    fiscal_year_start?: string;
    /**
     * Partition mode for all tables in this contract. Import = M/Power Query partitions (local parquet). DirectLake = entity partitions pointing to Fabric Lakehouse Delta tables.
     */
    storage_mode?: 'Import' | 'DirectLake';
    /**
     * Fabric Lakehouse item GUID. Required when storage_mode = DirectLake. Used to build the DL_Lakehouse named expression in expressions.tmdl.
     */
    lakehouse_id?: string;
    /**
     * Fabric Workspace GUID. Required when storage_mode = DirectLake.
     */
    workspace_id?: string;
  };
}
export interface DimensionTable {
  name: string;
  description?: string;
  purpose?: string;
  columns: Column[];
  uses_columns?: UsesColumns;
  /**
   * false = the Aurora showcase has no data for this table (missing = present).
   */
  showcase?: boolean;
  /**
   * Slowly changing dimension type.
   */
  scd_type?: 0 | 1 | 2;
}
export interface Column {
  name: string;
  type: string;
  /**
   * `key` marks the surrogate key of a dimension (FK target of `ref`).
   */
  role?: string;
  /**
   * FK: name of the referenced dimension (its `role: key` column).
   */
  ref?: string;
  /**
   * true = NULL allowed. Missing = never NULL.
   */
  nullable?: boolean;
  /**
   * Default aggregation of a measure column (sum, avg, max ...).
   */
  agg?: string;
  unit?: string;
  /**
   * Relationship cardinality of an FK column, e.g. many-to-one.
   */
  cardinality?: string;
  description?: string;
  /**
   * Enumerated domain of values — grounds NL -> column-value mapping and the column `Values:` projection.
   */
  allowed_values?: (string | number | boolean)[];
  /**
   * Curated natural-language synonyms — projected into the model linguistic schema (cultures/linguisticMetadata) for Copilot/Q&A and into the `///` Synonyms facet.
   */
  synonyms?: string[];
  /**
   * Physical Gold column when `name` is the business/model name (TMDL column + sourceColumn split). Must differ from `name` (checked by check_validate_data_contracts.py).
   */
  source_column?: string;
  /**
   * FK only: never NULL; the value (e.g. -1) is the placeholder row of the referenced dimension. Requires `ref`; `nullable` must not be true (checked by check_validate_data_contracts.py).
   */
  unknown_member?: string | number;
  /**
   * Structured, machine-run value rules (A-20/A-23).
   *
   * @minItems 1
   */
  checks?: [CheckEntry, ...CheckEntry[]];
  /**
   * Target design: not (yet) delivered by the Aurora showcase or read by a model.
   */
  target_state?: boolean;
}
/**
 * Exactly one rule key out of gte, gt, lte, lt, between, in, gte_column, lte_column; optionally when_present: true. Semantics: core/data_contracts/domains/README.md.
 */
export interface CheckEntry {
  gte?: number;
  gt?: number;
  lte?: number;
  lt?: number;
  /**
   * [lo, hi], inclusive, lo <= hi.
   *
   * @minItems 2
   * @maxItems 2
   */
  between?: [number, number];
  /**
   * @minItems 1
   */
  in?: [string | number, ...(string | number)[]];
  /**
   * Another column of the same table.
   */
  gte_column?: string;
  /**
   * Another column of the same table.
   */
  lte_column?: string;
  /**
   * Only non-NULL values are checked.
   */
  when_present?: true;
}
/**
 * Conformed reference (Bus-Matrix, 29.09.2026): the table is defined once, in the owning domain named by conformed_from; this domain only uses it. No columns, no own table fields.
 */
export interface ConformedReference {
  name: string;
  /**
   * Owning domain (its `domain:` value) that holds the only definition.
   */
  conformed_from: string;
  uses_columns?: UsesColumns;
}
export interface FactTable {
  name: string;
  description?: string;
  purpose?: string;
  columns: Column[];
  uses_columns?: UsesColumns;
  /**
   * false = the Aurora showcase has no data for this table (missing = present).
   */
  showcase?: boolean;
  grain: string;
  /**
   * Prose QA notes that do not structure (the machine-run rules live in column `checks`).
   */
  qa?: string[];
}
/**
 * What does not structure (A-20/A-23): freshness and prose rules. Not-null, FK, unknown member and value ranges live on the columns (nullable, ref, unknown_member, checks).
 */
export interface QualityRules {
  /**
   * One cadence for the contract, or one per table.
   */
  freshness_sla?:
    | string
    | {
        [k: string]: string | undefined;
      };
  key_nullability?: string[];
  referential_integrity?: string[];
  value_ranges?: string[];
}
