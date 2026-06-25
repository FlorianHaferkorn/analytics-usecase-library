/**
 * llm-events-repo — persistence for AI usage telemetry (I-6.6 V3, ADR-0008 §6).
 *
 * One row per LLM step in the local SQLite (no cloud). Attribution is data
 * (project/use_case/domain), not code. Aggregation keeps the honesty rule
 * missing ≠ zero (ADR-0008 §7): rows with an UNCOMPUTED cost are counted
 * separately, never silently summed as 0.
 */

import { randomUUID } from 'node:crypto';
import { getDb } from './sqlite';

export interface LlmStepEvent {
  id: string;
  project_id: string;
  use_case_id: string | null;
  domain: string | null;
  task_role: string;
  capability_role: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  reasoning_tokens: number;
  latency_ms: number;
  ok: number;
  error: string | null;
  cost_usd: number | null;
  cost_verified: number;
  price_table_version: string | null;
  raw_usage_json: string;
  created_at: string;
}

export interface RecordLlmStepInput {
  projectId?: string;
  useCaseId?: string | null;
  domain?: string | null;
  taskRole: string;
  capabilityRole: string;
  provider: string;
  model: string;
  inputTokens?: number;
  outputTokens?: number;
  cacheReadTokens?: number;
  cacheWriteTokens?: number;
  reasoningTokens?: number;
  latencyMs?: number;
  ok?: boolean;
  error?: string | null;
  costUsd?: number | null;
  costVerified?: boolean;
  priceTableVersion?: string | null;
  rawUsage?: unknown;
}

export function recordLlmStep(input: RecordLlmStepInput): LlmStepEvent {
  const db = getDb();
  const id = randomUUID();
  db.prepare(`
    INSERT INTO llm_step_events (
      id, project_id, use_case_id, domain, task_role, capability_role, provider, model,
      input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
      latency_ms, ok, error, cost_usd, cost_verified, price_table_version, raw_usage_json
    ) VALUES (
      @id, @project_id, @use_case_id, @domain, @task_role, @capability_role, @provider, @model,
      @input_tokens, @output_tokens, @cache_read_tokens, @cache_write_tokens, @reasoning_tokens,
      @latency_ms, @ok, @error, @cost_usd, @cost_verified, @price_table_version, @raw_usage_json
    )
  `).run({
    id,
    project_id: input.projectId ?? 'default',
    use_case_id: input.useCaseId ?? null,
    domain: input.domain ?? null,
    task_role: input.taskRole,
    capability_role: input.capabilityRole,
    provider: input.provider,
    model: input.model,
    input_tokens: input.inputTokens ?? 0,
    output_tokens: input.outputTokens ?? 0,
    cache_read_tokens: input.cacheReadTokens ?? 0,
    cache_write_tokens: input.cacheWriteTokens ?? 0,
    reasoning_tokens: input.reasoningTokens ?? 0,
    latency_ms: input.latencyMs ?? 0,
    ok: input.ok === false ? 0 : 1,
    error: input.error ?? null,
    cost_usd: input.costUsd ?? null,
    cost_verified: input.costVerified ? 1 : 0,
    price_table_version: input.priceTableVersion ?? null,
    raw_usage_json: JSON.stringify(input.rawUsage ?? {}),
  });
  return db.prepare('SELECT * FROM llm_step_events WHERE id = ?').get(id) as LlmStepEvent;
}

export function getLlmStepEvents(projectId = 'default', limit = 100): LlmStepEvent[] {
  return getDb()
    .prepare('SELECT * FROM llm_step_events WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT ?')
    .all(projectId, limit) as LlmStepEvent[];
}

export interface UsageSummary {
  steps: number;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  /** steps whose cost is UNCOMPUTED (no price) — surfaced, never summed as 0. */
  uncomputedCostSteps: number;
  /** steps whose cost used unverified provider pricing (ADR-0008 §8). */
  unverifiedCostSteps: number;
  errors: number;
}

export function summarizeUsage(projectId = 'default'): UsageSummary {
  const row = getDb().prepare(`
    SELECT
      COUNT(*)                                        AS steps,
      COALESCE(SUM(input_tokens), 0)                  AS inputTokens,
      COALESCE(SUM(output_tokens), 0)                 AS outputTokens,
      COALESCE(SUM(cost_usd), 0)                      AS costUsd,
      SUM(CASE WHEN cost_usd IS NULL THEN 1 ELSE 0 END)                       AS uncomputedCostSteps,
      SUM(CASE WHEN cost_usd IS NOT NULL AND cost_verified = 0 THEN 1 ELSE 0 END) AS unverifiedCostSteps,
      SUM(CASE WHEN ok = 0 THEN 1 ELSE 0 END)         AS errors
    FROM llm_step_events WHERE project_id = ?
  `).get(projectId) as Record<string, number>;
  return {
    steps: row.steps ?? 0,
    inputTokens: row.inputTokens ?? 0,
    outputTokens: row.outputTokens ?? 0,
    costUsd: row.costUsd ?? 0,
    uncomputedCostSteps: row.uncomputedCostSteps ?? 0,
    unverifiedCostSteps: row.unverifiedCostSteps ?? 0,
    errors: row.errors ?? 0,
  };
}
