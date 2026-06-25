/**
 * defaults — the L0 (universal-optimal) AI config + the capability→model map (ADR-0008, I-6.6).
 *
 * This is the ONE place a concrete model-ID literal may appear (ADR-0008 §3, §9a):
 * `CAPABILITY_MODEL_MAP` maps an abstract capability-role × provider → a concrete
 * model id. `orchestrator.ts` and every other core path stay LLM-agnostic — they
 * never name a model. Swapping a model = editing this L0 map (a versioned data
 * change), not a code edit.
 *
 * L1 (customer) / L2 (domain) layers are loaded from the DB in a later vertical;
 * until then resolution runs on L0 alone (which is complete by construction).
 *
 * Honesty (ADR-0008 §8): Anthropic/Claude model ids are repo-verified. Google and
 * OpenAI ids reuse the single ids the app already shipped and are NOT per-role
 * verified (provider pricing pages returned HTTP 403 during I-6.6 research) — they
 * are flagged here and must be confirmed live before per-role tiering is trusted.
 */

import type { AiConfigLayer, CapabilityRole, DataResidency } from './resolve';

export type Provider = 'anthropic' | 'google' | 'openai';

/** capability-role × provider → concrete model id. The ONLY model-id literals in the app. */
export const CAPABILITY_MODEL_MAP: Record<CapabilityRole, Record<Provider, string>> = {
  // Anthropic ids are repo-verified (latest Claude per house doctrine).
  'fast-cheap':    { anthropic: 'claude-haiku-4-5-20251001', google: 'gemini-2.0-flash', openai: 'gpt-4o-mini' },
  'balanced':      { anthropic: 'claude-sonnet-4-6',          google: 'gemini-2.0-flash', openai: 'gpt-4o' },
  'deep-reasoner': { anthropic: 'claude-opus-4-8',            google: 'gemini-2.0-flash', openai: 'gpt-4o' },
  'long-context':  { anthropic: 'claude-sonnet-4-6',          google: 'gemini-2.0-flash', openai: 'gpt-4o' },
  // ⚠ Google/OpenAI per-role ids are placeholders pending live verification (ADR-0008 §8):
  // gemini-2.0-flash / gpt-4o(-mini) are the ids the app already used; the proper per-role
  // tiers (e.g. a deep-reasoner Gemini/OpenAI model) must be filled in once verified.
};

/** Which residencies a provider can satisfy. `any` only by default — EU/US hosting must be
 *  configured + verified, never assumed (ADR-0008 honesty; compliance lives in `compliance/`). */
export const PROVIDER_RESIDENCY: Record<Provider, DataResidency[]> = {
  anthropic: ['any'],
  google: ['any'],
  openai: ['any'],
};

/**
 * L0 universal-optimal layer. Complete (every effective field derivable) so the resolver
 * never produces a partial config. Customers can only TIGHTEN this via L1/L2 (ADR-0008 §2).
 *
 * preferenceOrder puts **anthropic first**: it is the verified, per-role-tiered provider
 * (house doctrine "default to latest Claude"); google/openai are fallbacks whose per-role
 * tiering is not yet verified.
 */
export const L0_DEFAULT: AiConfigLayer = {
  schema_version: '1.0.0',
  layer: 'L0',
  routing: {
    roles: [
      { taskRole: 'default', capabilityRole: 'balanced' },
      { taskRole: 'kpi-draft', capabilityRole: 'balanced' },
      { taskRole: 'action-draft', capabilityRole: 'balanced' },
      { taskRole: 'source-discovery', capabilityRole: 'balanced' },
      { taskRole: 'bracket-synthesis', capabilityRole: 'deep-reasoner' },
      { taskRole: 'gate-repair', capabilityRole: 'deep-reasoner' },
      { taskRole: 'documentation', capabilityRole: 'fast-cheap' },
    ],
  },
  tokenPolicy: { maxOutputTokens: 8192, maxContextTokens: 200000, temperatureDefault: 0.2 },
  providerPolicy: {
    allowedProviders: ['anthropic', 'google', 'openai'],
    preferenceOrder: ['anthropic', 'google', 'openai'],
    dataResidency: 'any',
  },
  eval: { thresholds: {}, requireHumanReview: false },
  telemetry: { sampleRate: 1, redactPII: true },
  roi: { attributionMethod: 'before_after', weighting: {} },
};
