/**
 * route-model — pick provider + concrete model for a task-role from the layered config (ADR-0008, I-6.6).
 *
 * Flow (ADR-0008 §3 / T5 §4.3): resolve effective config → choose the first provider in
 * `preferenceOrder` that is allowed, satisfies data-residency, AND has a configured secret →
 * map (capabilityRole, provider) → concrete model id via the L0 map. No model-id literal lives
 * here; the only source of model ids is `CAPABILITY_MODEL_MAP`.
 *
 * Pure given its inputs: `secretPresent` and the layers are injected, so it is unit-testable
 * without touching env or the DB. Returns null when no usable provider is configured.
 */

import { resolveAiConfig, type AiConfigLayer, type CapabilityRole, type EffectiveAiConfig } from './resolve';
import { CAPABILITY_MODEL_MAP, PROVIDER_RESIDENCY, L0_DEFAULT, type Provider } from './defaults';

export interface ModelChoice {
  provider: Provider;
  modelId: string;
  capabilityRole: CapabilityRole;
  effective: EffectiveAiConfig;
}

const KNOWN_PROVIDERS = Object.keys(PROVIDER_RESIDENCY) as Provider[];

function isKnownProvider(p: string): p is Provider {
  return (KNOWN_PROVIDERS as string[]).includes(p);
}

/**
 * Choose a model for `taskRole`. `secretPresent(provider)` reports whether a BYO key is
 * configured for that provider. `layers` defaults to L0-only (L1/L2 land in a later vertical).
 * Returns null if no allowed + residency-satisfying + secret-present provider has a mapped model.
 */
export function chooseModel(
  taskRole: string,
  opts: {
    secretPresent: (provider: Provider) => boolean;
    layers?: { l0: AiConfigLayer; l1?: AiConfigLayer; l2?: AiConfigLayer };
    domainId?: string;
  },
): ModelChoice | null {
  const layers = opts.layers ?? { l0: L0_DEFAULT };
  const effective = resolveAiConfig(layers, { taskRole, domainId: opts.domainId });
  const { allowedProviders, preferenceOrder, dataResidency } = effective.providerPolicy;
  const roleModels = CAPABILITY_MODEL_MAP[effective.capabilityRole];

  for (const candidate of preferenceOrder) {
    if (!isKnownProvider(candidate)) continue;
    if (!allowedProviders.includes(candidate)) continue;
    if (dataResidency !== 'any' && !PROVIDER_RESIDENCY[candidate].includes(dataResidency)) continue;
    if (!opts.secretPresent(candidate)) continue;
    const modelId = roleModels[candidate];
    if (!modelId) continue;
    return { provider: candidate, modelId, capabilityRole: effective.capabilityRole, effective };
  }
  return null;
}
