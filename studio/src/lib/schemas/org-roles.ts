/**
 * AUTO-GENERATED — DO NOT EDIT
 *
 * Generated from tooling/generator/schemas/ by scripts/generate-types.mjs
 * Re-generate with: npm run generate:types
 */

/**
 * Governed SSOT for organization role definitions. All owner_role and steward_role references in brackets and action codes must exist here.
 */
export interface OrgRegistryV10 {
  schema_version: '1.0';
  /**
   * @minItems 1
   */
  roles: [
    {
      /**
       * Snake_case role identifier (e.g. head_of_sales).
       */
      id: string;
      /**
       * Human-readable role title.
       */
      title: string;
      /**
       * Business domain this role belongs to.
       */
      domain: string;
      /**
       * Optional longer description of the role's responsibilities.
       */
      description?: string;
      /**
       * Legacy display names that map to this role (for migration).
       */
      aliases?: string[];
    },
    ...{
      /**
       * Snake_case role identifier (e.g. head_of_sales).
       */
      id: string;
      /**
       * Human-readable role title.
       */
      title: string;
      /**
       * Business domain this role belongs to.
       */
      domain: string;
      /**
       * Optional longer description of the role's responsibilities.
       */
      description?: string;
      /**
       * Legacy display names that map to this role (for migration).
       */
      aliases?: string[];
    }[]
  ];
}
