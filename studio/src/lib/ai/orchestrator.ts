/**
 * AI Orchestrator — Server-side model router.
 *
 * Supports Google Gemini (GOOGLE_API_KEY / GEMINI_API_KEY),
 * Anthropic Claude (ANTHROPIC_API_KEY), and OpenAI GPT (OPENAI_API_KEY).
 * Priority: Google → Anthropic → OpenAI.
 *
 * All secret reads go through @/lib/secrets so that the provider
 * (env, Azure Key Vault, AWS Secrets Manager) is configured once via
 * the SECRETS_PROVIDER environment variable.
 */

import { createAnthropic } from '@ai-sdk/anthropic';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import type { LanguageModel } from 'ai';
import { getSecret } from '@/lib/secrets';

export type AIProvider = 'google' | 'anthropic' | 'openai';

interface ProviderConfig {
  provider: AIProvider;
  apiKey: string;
  model?: string;
}

const DEFAULT_MODELS: Record<AIProvider, string> = {
  google: 'gemini-2.0-flash',
  anthropic: 'claude-sonnet-4-20250514',
  openai: 'gpt-4o',
};

/** Create a language model instance from provider config. */
export function createModel(config: ProviderConfig): LanguageModel {
  const modelId = config.model ?? DEFAULT_MODELS[config.provider];

  switch (config.provider) {
    case 'google': {
      const google = createGoogleGenerativeAI({ apiKey: config.apiKey });
      return google(modelId);
    }
    case 'anthropic': {
      const anthropic = createAnthropic({ apiKey: config.apiKey });
      return anthropic(modelId);
    }
    case 'openai': {
      const openai = createOpenAI({ apiKey: config.apiKey });
      return openai(modelId);
    }
  }
}

/** Detect which AI provider is configured. Priority: Google → Anthropic → OpenAI. */
export function detectServerProvider(): AIProvider | null {
  if (process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY) return 'google';
  if (process.env.ANTHROPIC_API_KEY) return 'anthropic';
  if (process.env.OPENAI_API_KEY) return 'openai';
  return null;
}

/**
 * Create a server-side language model from secrets.
 * Secret names map directly to env-var names so that the dev-env adapter
 * works without any extra configuration.
 * Returns null if no AI provider is configured.
 */
export async function createServerModel(): Promise<LanguageModel | null> {
  const provider = detectServerProvider();
  if (!provider) return null;

  let apiKey: string;
  try {
    if (provider === 'google') {
      // Try GOOGLE_API_KEY first, fall back to GEMINI_API_KEY.
      try {
        apiKey = await getSecret('GOOGLE_API_KEY');
      } catch {
        apiKey = await getSecret('GEMINI_API_KEY');
      }
    } else if (provider === 'anthropic') {
      apiKey = await getSecret('ANTHROPIC_API_KEY');
    } else {
      apiKey = await getSecret('OPENAI_API_KEY');
    }
  } catch {
    // Secret not available — treat as unconfigured rather than crashing.
    return null;
  }

  return createModel({ provider, apiKey });
}
