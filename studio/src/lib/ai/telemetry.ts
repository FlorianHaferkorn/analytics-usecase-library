/**
 * telemetry — record one AI step's usage + computed cost (I-6.6 V3, ADR-0008 §6/§7).
 *
 * The call-site primitive: after an LLM call, hand it the routing choice, the token
 * usage (from the AI SDK's normalized `result.usage`), timing and attribution; this
 * computes cost via the versioned price table and writes one `llm_step_events` row.
 * Cost is UNCOMPUTED (null) when the model is unpriced — missing ≠ zero (ADR-0008 §7).
 */

import { computeCostUsd, type UsageTokens } from './pricing';
import { recordLlmStep, type LlmStepEvent } from '@/lib/db/llm-events-repo';

export interface AiStep {
  taskRole: string;
  capabilityRole: string;
  provider: string;
  model: string;
  usage: Partial<UsageTokens> & {
    cacheReadTokens?: number;
    cacheWriteTokens?: number;
    reasoningTokens?: number;
  };
  latencyMs: number;
  ok?: boolean;
  error?: string | null;
  projectId?: string;
  useCaseId?: string | null;
  domain?: string | null;
  /** raw provider usage object, kept for auditing SDK mapping quirks (ADR-0008 §6). */
  rawUsage?: unknown;
}

export function recordAiStep(step: AiStep): LlmStepEvent {
  const inputTokens = step.usage.inputTokens ?? 0;
  const outputTokens = step.usage.outputTokens ?? 0;
  const cost = computeCostUsd(step.model, { inputTokens, outputTokens });
  return recordLlmStep({
    projectId: step.projectId,
    useCaseId: step.useCaseId ?? null,
    domain: step.domain ?? null,
    taskRole: step.taskRole,
    capabilityRole: step.capabilityRole,
    provider: step.provider,
    model: step.model,
    inputTokens,
    outputTokens,
    cacheReadTokens: step.usage.cacheReadTokens,
    cacheWriteTokens: step.usage.cacheWriteTokens,
    reasoningTokens: step.usage.reasoningTokens,
    latencyMs: step.latencyMs,
    ok: step.ok,
    error: step.error ?? null,
    costUsd: cost?.costUsd ?? null,
    costVerified: cost?.verified ?? false,
    priceTableVersion: cost?.priceTableVersion ?? null,
    rawUsage: step.rawUsage,
  });
}
