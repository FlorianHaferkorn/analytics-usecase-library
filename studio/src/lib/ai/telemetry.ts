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

/** Subset of the AI SDK usage object we read (names vary across SDK/provider versions). */
interface RawUsage {
  inputTokens?: number;
  outputTokens?: number;
  promptTokens?: number;
  completionTokens?: number;
  cachedInputTokens?: number;
  reasoningTokens?: number;
  inputTokenDetails?: { cacheReadTokens?: number; cacheWriteTokens?: number };
  outputTokenDetails?: { reasoningTokens?: number };
}

/** Normalize the AI SDK's `result.usage` into our token shape (tolerant of naming drift). */
export function extractUsage(raw: unknown): AiStep['usage'] {
  const u = (raw ?? {}) as RawUsage;
  return {
    inputTokens: u.inputTokens ?? u.promptTokens ?? 0,
    outputTokens: u.outputTokens ?? u.completionTokens ?? 0,
    cacheReadTokens: u.cachedInputTokens ?? u.inputTokenDetails?.cacheReadTokens,
    cacheWriteTokens: u.inputTokenDetails?.cacheWriteTokens,
    reasoningTokens: u.reasoningTokens ?? u.outputTokenDetails?.reasoningTokens,
  };
}

/** Record a step, swallowing any telemetry error — telemetry must never break a request. */
export function safeRecordAiStep(step: AiStep): void {
  try {
    recordAiStep(step);
  } catch {
    /* telemetry is best-effort; never propagate into the request path */
  }
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
