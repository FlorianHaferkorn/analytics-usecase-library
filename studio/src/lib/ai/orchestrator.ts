/**
 * AI Orchestrator — server-side model router (config-driven, ADR-0008 I-6.6).
 *
 * Model + provider choice comes from the layered AI config (`config/route-model.ts`),
 * NOT from hardcoded constants. This module stays LLM-agnostic: it names no model id
 * and no fixed provider priority — both arrive from the resolved config. The only place
 * a model id lives is the L0 capability→model map (`config/defaults.ts`).
 *
 * All secret reads go through @/lib/secrets (provider chosen via SECRETS_PROVIDER).
 * Provider *presence* is detected from env (presence, not value — allowed per studio/CLAUDE.md).
 */

import { createAnthropic } from '@ai-sdk/anthropic';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import type { LanguageModel } from 'ai';
import { getSecret } from '@/lib/secrets';
import { chooseModel, type ModelChoice } from './config/route-model';
import { loadAiConfigLayers } from './config/load-layers';
import type { Provider } from './config/defaults';

export type AIProvider = Provider;

interface ProviderConfig {
  provider: AIProvider;
  apiKey: string;
  /** Concrete model id — resolved from config (ADR-0008); never defaulted here. */
  model: string;
}

/** Low-level provider-adapter boundary: build a model instance. Stays LLM-agnostic. */
export function createModel(config: ProviderConfig): LanguageModel {
  switch (config.provider) {
    case 'google': {
      const google = createGoogleGenerativeAI({ apiKey: config.apiKey });
      return google(config.model);
    }
    case 'anthropic': {
      const anthropic = createAnthropic({ apiKey: config.apiKey });
      return anthropic(config.model);
    }
    case 'openai': {
      const openai = createOpenAI({ apiKey: config.apiKey });
      return openai(config.model);
    }
  }
}

/** Whether a BYO key is configured for a provider (env presence check, not value read). */
export function providerSecretPresent(provider: Provider): boolean {
  switch (provider) {
    case 'google': return Boolean(process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY);
    case 'anthropic': return Boolean(process.env.ANTHROPIC_API_KEY);
    case 'openai': return Boolean(process.env.OPENAI_API_KEY);
  }
}

async function secretFor(provider: Provider): Promise<string> {
  if (provider === 'google') {
    try {
      return await getSecret('GOOGLE_API_KEY');
    } catch {
      return await getSecret('GEMINI_API_KEY');
    }
  }
  return getSecret(provider === 'anthropic' ? 'ANTHROPIC_API_KEY' : 'OPENAI_API_KEY');
}

/**
 * Create a server-side language model for a task-role, driven by the layered config.
 * Picks provider + concrete model via `chooseModel` (preferenceOrder ∩ allowed ∩ residency
 * ∩ secret-present), then reads the secret and builds the model. Returns null if no usable
 * provider is configured (callers already handle null).
 *
 * When `opts` (project/domain) is given, the customer's APPROVED L1/L2 override layers
 * are folded in (I-6.6 V5); without it, only the universal L0 applies.
 */
export interface ResolvedModel {
  model: LanguageModel;
  /** The routing decision — carry to telemetry (provider, modelId, capabilityRole). */
  choice: ModelChoice;
}

/**
 * Resolve the model AND expose the routing choice (for telemetry, I-6.6 V3). Same
 * selection as createServerModel; returns null if no usable provider is configured.
 */
export async function resolveServerModel(
  taskRole = 'default',
  opts?: { projectId?: string; domainId?: string },
): Promise<ResolvedModel | null> {
  const layers = opts ? loadAiConfigLayers(opts.projectId ?? 'default', opts.domainId) : undefined;
  const choice = chooseModel(taskRole, { secretPresent: providerSecretPresent, layers, domainId: opts?.domainId });
  if (!choice) return null;
  try {
    const apiKey = await secretFor(choice.provider);
    return { model: createModel({ provider: choice.provider, apiKey, model: choice.modelId }), choice };
  } catch {
    return null;
  }
}

export async function createServerModel(
  taskRole = 'default',
  opts?: { projectId?: string; domainId?: string },
): Promise<LanguageModel | null> {
  const resolved = await resolveServerModel(taskRole, opts);
  return resolved?.model ?? null;
}
