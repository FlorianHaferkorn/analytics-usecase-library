/**
 * AI Orchestrator — BYOK (Bring Your Own Key) Router
 *
 * Routes AI requests to the appropriate provider based on the user's
 * configured API key. Supports Anthropic Claude and OpenAI GPT.
 */

import { createAnthropic } from '@ai-sdk/anthropic';
import { createOpenAI } from '@ai-sdk/openai';
import type { LanguageModel } from 'ai';

export type AIProvider = 'anthropic' | 'openai';

interface ProviderConfig {
  provider: AIProvider;
  apiKey: string;
  model?: string;
}

const DEFAULT_MODELS: Record<AIProvider, string> = {
  anthropic: 'claude-sonnet-4-20250514',
  openai: 'gpt-4o',
};

/** Create a language model instance from BYOK configuration. */
export function createModel(config: ProviderConfig): LanguageModel {
  const modelId = config.model ?? DEFAULT_MODELS[config.provider];

  switch (config.provider) {
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

/** Detect provider from API key prefix. */
export function detectProvider(apiKey: string): AIProvider {
  if (apiKey.startsWith('sk-ant-')) return 'anthropic';
  return 'openai';
}
