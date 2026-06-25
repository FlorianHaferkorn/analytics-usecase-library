/**
 * pricing — the versioned LLM price table + cost computation (ADR-0008 §7/§8, I-6.6 V3).
 *
 * Prices are versioned CONFIG data (not scattered literals): one table, one version
 * stamp recorded with every telemetry row, so a cost can always be traced to the prices
 * that produced it. Honesty (ADR-0008 §8): Anthropic/Claude prices are repo-verified;
 * Google/OpenAI prices come from secondary sources (vendor pages returned HTTP 403 in the
 * I-6.6 research) and are marked `verified: false` — confirm live before trusting them.
 *
 * An unknown model returns `null` (UNCOMPUTED), never 0 — missing ≠ zero (ADR-0008 §7).
 * Prices are USD per 1,000,000 tokens.
 */

export const PRICE_TABLE_VERSION = '2026-06-25';

export interface ModelPrice {
  inputPerM: number;
  outputPerM: number;
  /** false = sourced from secondary data, not the vendor's own page (ADR-0008 §8). */
  verified: boolean;
}

export const PRICE_TABLE: Record<string, ModelPrice> = {
  // Anthropic — repo-verified (house doctrine).
  'claude-opus-4-8': { inputPerM: 5, outputPerM: 25, verified: true },
  'claude-sonnet-4-6': { inputPerM: 3, outputPerM: 15, verified: true },
  'claude-haiku-4-5-20251001': { inputPerM: 1, outputPerM: 5, verified: true },
  'claude-fable-5': { inputPerM: 10, outputPerM: 50, verified: true },
  // Google / OpenAI — UNVERIFIED (secondary sources; vendor pages 403 in research).
  'gemini-2.0-flash': { inputPerM: 0.1, outputPerM: 0.4, verified: false },
  'gpt-4o': { inputPerM: 2.5, outputPerM: 10, verified: false },
  'gpt-4o-mini': { inputPerM: 0.15, outputPerM: 0.6, verified: false },
};

export interface UsageTokens {
  inputTokens: number;
  outputTokens: number;
}

export interface CostResult {
  costUsd: number;
  verified: boolean;
  priceTableVersion: string;
}

/** Compute cost for a model+usage, or null (UNCOMPUTED) when the model is not priced. */
export function computeCostUsd(model: string, usage: UsageTokens): CostResult | null {
  const p = PRICE_TABLE[model];
  if (!p) return null;
  const costUsd = (usage.inputTokens / 1e6) * p.inputPerM + (usage.outputTokens / 1e6) * p.outputPerM;
  return { costUsd, verified: p.verified, priceTableVersion: PRICE_TABLE_VERSION };
}
