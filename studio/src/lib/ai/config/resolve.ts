/**
 * resolve — pure resolver for the layered AI-orchestration config (ADR-0008, I-6.6).
 *
 * Folds L0 (universal-optimal) → L1 (customer) → L2 (domain) into one effective
 * config for a given task-role, applying each field's merge kind. PURE: no I/O,
 * no clock, no RNG — inputs fully determine output (so it is trivially testable;
 * loading the layers is a separate impure concern).
 *
 * Governing safety rule (ADR-0008 §2): a customer/domain layer may only TIGHTEN
 * L0, never loosen it. Encoded by the merge kinds (clamp/intersect/or) and proven
 * by property tests. `MERGE_SPEC` mirrors the `x-merge` annotations in
 * `tooling/generator/schemas/ai_config.schema.json` (parity-tested).
 */

export type CapabilityRole = 'fast-cheap' | 'balanced' | 'deep-reasoner' | 'long-context';
export type DataResidency = 'any' | 'eu-only' | 'us-only';
export type AttributionMethod = 'before_after' | 'diff_in_diff' | 'holdout';
export type MergeKind =
  | 'override' | 'clamp-min' | 'clamp-max' | 'clamp-strict'
  | 'intersect' | 'or' | 'clamp-max-per-key';

export interface RoutingRole {
  taskRole: string;
  capabilityRole: CapabilityRole;
  minCapabilityTier?: number;
}

export interface AiConfigLayer {
  schema_version: '1.0.0';
  layer: 'L0' | 'L1' | 'L2';
  scope?: { tenantId?: string | null; domainId?: string | null };
  routing?: { roles?: RoutingRole[] };
  tokenPolicy?: { maxOutputTokens?: number; maxContextTokens?: number; temperatureDefault?: number };
  providerPolicy?: { allowedProviders?: string[]; preferenceOrder?: string[]; dataResidency?: DataResidency };
  eval?: { thresholds?: Record<string, number>; requireHumanReview?: boolean };
  telemetry?: { sampleRate?: number; redactPII?: boolean };
  roi?: { attributionMethod?: AttributionMethod; weighting?: Record<string, number> };
}

export interface EffectiveAiConfig {
  taskRole: string;
  capabilityRole: CapabilityRole;
  minCapabilityTier: number;
  tokenPolicy: { maxOutputTokens: number; maxContextTokens: number; temperatureDefault: number };
  providerPolicy: { allowedProviders: string[]; preferenceOrder: string[]; dataResidency: DataResidency };
  eval: { thresholds: Record<string, number>; requireHumanReview: boolean };
  telemetry: { sampleRate: number; redactPII: boolean };
  roi: { attributionMethod: AttributionMethod; weighting: Record<string, number> };
}

/** Merge kind per field — MUST mirror x-merge in ai_config.schema.json (parity-tested). */
export const MERGE_SPEC: Record<string, MergeKind> = {
  'routing.roles[].capabilityRole': 'override',
  'routing.roles[].minCapabilityTier': 'clamp-max',
  'tokenPolicy.maxOutputTokens': 'clamp-min',
  'tokenPolicy.maxContextTokens': 'clamp-min',
  'tokenPolicy.temperatureDefault': 'override',
  'providerPolicy.allowedProviders': 'intersect',
  'providerPolicy.preferenceOrder': 'override',
  'providerPolicy.dataResidency': 'clamp-strict',
  'eval.thresholds': 'clamp-max-per-key',
  'eval.requireHumanReview': 'or',
  'telemetry.sampleRate': 'clamp-max',
  'telemetry.redactPII': 'or',
  'roi.attributionMethod': 'override',
  'roi.weighting': 'override',
};

export class AiConfigError extends Error {}

const RESIDENCY_RANK: Record<DataResidency, number> = { any: 0, 'eu-only': 1, 'us-only': 1 };

/** Most specific present value wins (layers passed in L0→L1→L2 order). */
function override<T>(values: T[]): T | undefined {
  return values.length ? values[values.length - 1] : undefined;
}

function clampStrictResidency(values: DataResidency[]): DataResidency {
  const restrictive = values.filter((v) => RESIDENCY_RANK[v] > 0);
  const distinct = [...new Set(restrictive)];
  if (distinct.length > 1) {
    throw new AiConfigError(`irreconcilable dataResidency across layers: ${distinct.join(', ')}`);
  }
  return distinct[0] ?? 'any';
}

function intersect(arrays: string[][]): string[] {
  if (!arrays.length) return [];
  // Preserve the first (least specific) layer's order; keep only providers in all layers.
  return arrays[0].filter((p) => arrays.every((a) => a.includes(p)));
}

function clampMaxPerKey(objs: Record<string, number>[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const o of objs) for (const [k, v] of Object.entries(o)) {
    out[k] = k in out ? Math.max(out[k], v) : v;
  }
  return out;
}

function required<T>(value: T | undefined, field: string): T {
  if (value === undefined) throw new AiConfigError(`L0 is incomplete: missing '${field}'`);
  return value;
}

/**
 * Resolve the three layers into the effective config for one task-role.
 * L0 must be complete (every effective field derivable) — else AiConfigError.
 */
export function resolveAiConfig(
  layers: { l0: AiConfigLayer; l1?: AiConfigLayer; l2?: AiConfigLayer },
  ctx: { taskRole: string; domainId?: string },
): EffectiveAiConfig {
  const ordered = [layers.l0, layers.l1, layers.l2].filter(Boolean) as AiConfigLayer[];
  const present = <T>(pick: (l: AiConfigLayer) => T | undefined): T[] =>
    ordered.map(pick).filter((v): v is T => v !== undefined && v !== null);

  // routing — the role matching ctx.taskRole, merged across layers.
  const roleEntries = ordered
    .map((l) => l.routing?.roles?.find((r) => r.taskRole === ctx.taskRole))
    .filter((r): r is RoutingRole => Boolean(r));
  if (!roleEntries.length) {
    throw new AiConfigError(`no routing role for taskRole '${ctx.taskRole}' (L0 must define it)`);
  }
  const capabilityRole = required(override(roleEntries.map((r) => r.capabilityRole)), `routing[${ctx.taskRole}].capabilityRole`);
  const tierVals = roleEntries.map((r) => r.minCapabilityTier).filter((n): n is number => n !== undefined);
  const minCapabilityTier = tierVals.length ? Math.max(...tierVals) : 0;

  const maxOutputTokens = Math.min(...required(nonEmpty(present((l) => l.tokenPolicy?.maxOutputTokens)), 'tokenPolicy.maxOutputTokens'));
  const maxContextTokens = Math.min(...required(nonEmpty(present((l) => l.tokenPolicy?.maxContextTokens)), 'tokenPolicy.maxContextTokens'));
  const temperatureDefault = required(override(present((l) => l.tokenPolicy?.temperatureDefault)), 'tokenPolicy.temperatureDefault');

  const allowedProviders = intersect(present((l) => l.providerPolicy?.allowedProviders));
  const preferenceOrder = required(override(present((l) => l.providerPolicy?.preferenceOrder)), 'providerPolicy.preferenceOrder');
  const dataResidency = clampStrictResidency(present((l) => l.providerPolicy?.dataResidency));

  const thresholds = clampMaxPerKey(present((l) => l.eval?.thresholds));
  const requireHumanReview = present((l) => l.eval?.requireHumanReview).some(Boolean);

  const sampleRate = Math.max(...required(nonEmpty(present((l) => l.telemetry?.sampleRate)), 'telemetry.sampleRate'));
  const redactPII = present((l) => l.telemetry?.redactPII).some(Boolean);

  const attributionMethod = required(override(present((l) => l.roi?.attributionMethod)), 'roi.attributionMethod');
  const weighting = override(present((l) => l.roi?.weighting)) ?? {};

  if (allowedProviders.length === 0) {
    throw new AiConfigError('effective allowedProviders is empty after intersection (no usable provider)');
  }

  return {
    taskRole: ctx.taskRole,
    capabilityRole,
    minCapabilityTier,
    tokenPolicy: { maxOutputTokens, maxContextTokens, temperatureDefault },
    providerPolicy: { allowedProviders, preferenceOrder, dataResidency },
    eval: { thresholds, requireHumanReview },
    telemetry: { sampleRate, redactPII },
    roi: { attributionMethod, weighting },
  };
}

function nonEmpty<T>(arr: T[]): T[] | undefined {
  return arr.length ? arr : undefined;
}
