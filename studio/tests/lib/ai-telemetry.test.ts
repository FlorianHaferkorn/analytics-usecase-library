import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';
import { computeCostUsd, PRICE_TABLE, PRICE_TABLE_VERSION } from '@/lib/ai/pricing';

// --- in-memory DB, injected via the sqlite module (mirrors audit-repo.test) ---
let testDb: Database.Database;
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => testDb }));

function freshDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE llm_step_events (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL DEFAULT 'default',
      use_case_id TEXT, domain TEXT, task_role TEXT NOT NULL, capability_role TEXT NOT NULL,
      provider TEXT NOT NULL, model TEXT NOT NULL,
      input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
      cache_read_tokens INTEGER NOT NULL DEFAULT 0, cache_write_tokens INTEGER NOT NULL DEFAULT 0,
      reasoning_tokens INTEGER NOT NULL DEFAULT 0, latency_ms INTEGER NOT NULL DEFAULT 0,
      ok INTEGER NOT NULL DEFAULT 1, error TEXT, cost_usd REAL,
      cost_verified INTEGER NOT NULL DEFAULT 0, price_table_version TEXT,
      raw_usage_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
  return d;
}

describe('computeCostUsd (versioned price table)', () => {
  it('computes verified cost for a priced Anthropic model', () => {
    const r = computeCostUsd('claude-sonnet-4-6', { inputTokens: 1_000_000, outputTokens: 1_000_000 });
    expect(r).not.toBeNull();
    expect(r!.costUsd).toBeCloseTo(3 + 15, 6); // $3/M in + $15/M out
    expect(r!.verified).toBe(true);
    expect(r!.priceTableVersion).toBe(PRICE_TABLE_VERSION);
  });

  it('flags unverified provider pricing', () => {
    expect(computeCostUsd('gpt-4o', { inputTokens: 0, outputTokens: 0 })!.verified).toBe(false);
  });

  it('returns null (UNCOMPUTED, not 0) for an unpriced model', () => {
    expect(computeCostUsd('some-unknown-model', { inputTokens: 1000, outputTokens: 1000 })).toBeNull();
  });

  it('every priced model declares verified explicitly', () => {
    for (const [model, p] of Object.entries(PRICE_TABLE)) {
      expect(typeof p.verified, model).toBe('boolean');
    }
  });
});

describe('recordAiStep + summarizeUsage (honesty: missing ≠ zero)', () => {
  beforeEach(() => { testDb = freshDb(); });

  it('records a priced step with computed cost', async () => {
    const { recordAiStep } = await import('@/lib/ai/telemetry');
    const { summarizeUsage } = await import('@/lib/db/llm-events-repo');
    recordAiStep({
      taskRole: 'default', capabilityRole: 'balanced', provider: 'anthropic',
      model: 'claude-sonnet-4-6', usage: { inputTokens: 1_000_000, outputTokens: 0 }, latencyMs: 100,
    });
    const s = summarizeUsage();
    expect(s.steps).toBe(1);
    expect(s.costUsd).toBeCloseTo(3, 6);
    expect(s.uncomputedCostSteps).toBe(0);
    expect(s.unverifiedCostSteps).toBe(0);
  });

  it('counts an unpriced step as uncomputed, never summed as 0 cost', async () => {
    const { recordAiStep } = await import('@/lib/ai/telemetry');
    const { summarizeUsage } = await import('@/lib/db/llm-events-repo');
    recordAiStep({
      taskRole: 'default', capabilityRole: 'balanced', provider: 'x',
      model: 'mystery-model', usage: { inputTokens: 500, outputTokens: 500 }, latencyMs: 50,
    });
    const s = summarizeUsage();
    expect(s.steps).toBe(1);
    expect(s.uncomputedCostSteps).toBe(1);
    expect(s.costUsd).toBe(0); // no priced rows contributed
  });

  it('flags unverified-priced steps and counts errors', async () => {
    const { recordAiStep } = await import('@/lib/ai/telemetry');
    const { summarizeUsage } = await import('@/lib/db/llm-events-repo');
    recordAiStep({ taskRole: 'documentation', capabilityRole: 'fast-cheap', provider: 'openai',
      model: 'gpt-4o', usage: { inputTokens: 1_000_000, outputTokens: 0 }, latencyMs: 10 });
    recordAiStep({ taskRole: 'documentation', capabilityRole: 'fast-cheap', provider: 'openai',
      model: 'gpt-4o', usage: {}, latencyMs: 10, ok: false, error: 'boom' });
    const s = summarizeUsage();
    expect(s.steps).toBe(2);
    expect(s.unverifiedCostSteps).toBe(2);
    expect(s.errors).toBe(1);
  });
});
