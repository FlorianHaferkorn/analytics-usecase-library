/**
 * TypeScript types for Template Manifest and Visual Registry.
 *
 * Sources:
 *   core/templates/page_templates/template_manifest.yaml
 *   core/templates/page_templates/visual_registry.yaml
 *   tooling/generator/schemas/template_manifest.schema.json
 *   tooling/generator/schemas/visual_registry.schema.json
 *
 * Keep in sync with the YAML files and the JSON Schemas.
 * These types are consumed by the Studio manifest loader (Gate 2).
 */

// ─────────────────────────────────────────────────────────────────────────────
// Enumerations
// ─────────────────────────────────────────────────────────────────────────────

export type PageFamilyId = 'T1' | 'T2' | 'T3' | 'T4';

export type TemplateVariantId =
  | 'T1_Portfolio'
  | 'T1_Trend'
  | 'T2_DriverBridge'
  | 'T2_Comparative'
  | 'T2_Funnel'
  | 'T3_ExceptionQueue'
  | 'T3_ProcessControl'
  | 'T3_IncidentMonitor'
  | 'T4_ActionDecision'
  | 'T4_OptionComparison'
  | 'T4_Sensitivity';

export type GridTemplate =
  | 'pulse'
  | 'pulse_asymmetric'
  | 'executive_kpi'
  | 'investigator'
  | 'investigator_focus'
  | 'action_matrix'
  | null;

export type InformationBlockId =
  | 'status_signal'
  | 'time_trend'
  | 'variance_explanation'
  | 'entity_ranking'
  | 'exception_list'
  | 'structural_mix'
  | 'prescriptive_action'
  | 'detail_matrix'
  | 'root_cause_context'
  | null;

export type AttentionLayer = '3s' | '30s' | '300s';

export type ReadingPattern = 'z_pattern' | 'f_pattern' | 'gutenberg';

export type RuleSeverity = 'error' | 'warning' | 'info';

// ─────────────────────────────────────────────────────────────────────────────
// Template Manifest Types
// ─────────────────────────────────────────────────────────────────────────────

export interface CanvasSpec {
  width: number;
  height: number;
}

export interface GridSpec {
  columns: number;
  rows: number;
  outer_margin_px?: number;
  gutter_px?: number;
  internal_padding_px?: number;
  zone_gap_px?: number;
}

export interface SlotDefinition {
  slot_id: string;
  information_block: InformationBlockId;
  mandatory: boolean;
  note?: string;
  filter_rule?: string;
  condition?: string;
}

export interface TemplateVariant {
  variant_id: TemplateVariantId;
  name: string;
  description: string;
  grid_template: GridTemplate;
  alternate_grid_template?: GridTemplate;
  overview_slots: SlotDefinition[];
  detail_slots: SlotDefinition[];
}

export interface PageFamily {
  family_id: PageFamilyId;
  name: string;
  decision_question: string;
  audience: string[];
  time_horizon: string;
  primary_layers: AttentionLayer[];
  reading_pattern: ReadingPattern;
  disallowed_slots: string[];
  mandatory_slots: string[];
  max_slicers: number;
  narrative_template: string;
  action_code_required?: boolean;
  variants: TemplateVariant[];
}

export interface TemplateManifest {
  manifest_version: string;
  design_canvas: CanvasSpec;
  production_canvas: CanvasSpec;
  grid: GridSpec;
  page_families: PageFamily[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Visual Registry Types
// ─────────────────────────────────────────────────────────────────────────────

export interface InputField {
  field: string;
  type?: string;
  mandatory: boolean;
  note?: string;
  values?: string[];
  computed?: string;
  formula?: string;
  validation?: string;
  grain?: string[];
  example?: string;
  format?: string;
  max_items?: number;
  max_words?: number;
  max_sentences?: number;
  item_schema?: Record<string, unknown>;
}

export interface AllowedVisual {
  visual_id: string;
  pbip_type: string;
  is_default: boolean;
  condition: string | null;
  source: string;
  orientation?: 'horizontal' | 'vertical';
  small_multiples?: boolean;
  custom_visual_name?: string;
}

export interface ForbiddenVisual {
  visual_id: string;
  pbip_type?: string;
  reason: string;
  applies_when?: string;
}

export interface QualityRule {
  rule_id: string;
  description: string;
  source: string;
  severity: RuleSeverity;
  applies_when?: string;
}

export interface InformationBlock {
  block_id: Exclude<InformationBlockId, null>;
  purpose: string;
  primary_layer: AttentionLayer;
  slot_compatibility: string[];
  page_types: PageFamilyId[];
  layer_restriction?: string;
  action_code_required?: boolean;
  activation_condition?: string;
  required_inputs: InputField[];
  allowed_visuals: AllowedVisual[];
  forbidden_visuals: ForbiddenVisual[];
  quality_rules: QualityRule[];
}

export interface VisualRegistry {
  registry_version: string;
  information_blocks: InformationBlock[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Lookup helpers (used by Studio manifest loader in Gate 2)
// ─────────────────────────────────────────────────────────────────────────────

/** Find a variant definition by its ID across all page families. */
export function findVariant(
  manifest: TemplateManifest,
  variantId: TemplateVariantId,
): TemplateVariant | undefined {
  for (const family of manifest.page_families) {
    const v = family.variants.find((v) => v.variant_id === variantId);
    if (v) return v;
  }
  return undefined;
}

/** Find a page family by its short ID (T1, T2, T3, T4). */
export function findFamily(
  manifest: TemplateManifest,
  familyId: PageFamilyId,
): PageFamily | undefined {
  return manifest.page_families.find((f) => f.family_id === familyId);
}

/** Find an information block by its ID in the registry. */
export function findBlock(
  registry: VisualRegistry,
  blockId: Exclude<InformationBlockId, null>,
): InformationBlock | undefined {
  return registry.information_blocks.find((b) => b.block_id === blockId);
}

/** Return the default allowed visual for a block. */
export function defaultVisual(
  registry: VisualRegistry,
  blockId: Exclude<InformationBlockId, null>,
): AllowedVisual | undefined {
  const block = findBlock(registry, blockId);
  return block?.allowed_visuals.find((v) => v.is_default);
}

/** All valid TemplateVariantId values (useful for runtime validation). */
export const ALL_VARIANT_IDS: readonly TemplateVariantId[] = [
  'T1_Portfolio', 'T1_Trend',
  'T2_DriverBridge', 'T2_Comparative', 'T2_Funnel',
  'T3_ExceptionQueue', 'T3_ProcessControl', 'T3_IncidentMonitor',
  'T4_ActionDecision', 'T4_OptionComparison', 'T4_Sensitivity',
] as const;

/** All valid InformationBlockId values (excluding null). */
export const ALL_BLOCK_IDS: readonly Exclude<InformationBlockId, null>[] = [
  'status_signal', 'time_trend', 'variance_explanation',
  'entity_ranking', 'exception_list', 'structural_mix',
  'prescriptive_action', 'detail_matrix', 'root_cause_context',
] as const;
