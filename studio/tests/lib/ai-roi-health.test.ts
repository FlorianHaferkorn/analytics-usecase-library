import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';
import { computeRoi } from '@/lib/ai/roi';

// --- in-memory DB injected via the sqlite module (same pattern as telemetry test) ---
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

describe('computeRoi (honest ROI)', () => {
  it('computes positive ROI when value exceeds cost', () => {
    const r = computeRoi({ cost: { llmUsd: 10 }, value: { timeUsd: 100 } });
    expect(r.status).toBe('computed');
    if (r.status === 'computed') {
      expect(r.roi).toBeCloseTo((100 - 10) / 10, 6);
      expect(r.includedProxies).toEqual(['timeUsd']);
      expect(r.missingProxies).toContain('kpiUsd');
    }
  });

  it('applies the attribution discount', () => {
    const r = computeRoi({ cost: { llmUsd: 10 }, value: { timeUsd: 100 }, attribution: 0.5 });
    if (r.status === 'computed') expect(r.valueUsd).toBe(50);
  });

  it('notes when attribution is defaulted to 1', () => {
    const r = computeRoi({ cost: { llmUsd: 10 }, value: { timeUsd: 100 } });
    if (r.status === 'computed') expect(r.notes.some((n) => n.includes('attribution defaulted'))).toBe(true);
  });

  it('is UNCOMPUTED (not 0) when no value proxy is supplied — missing ≠ zero', () => {
    const r = computeRoi({ cost: { llmUsd: 10 } });
    expect(r.status).toBe('uncomputed');
    if (r.status === 'uncomputed') expect(r.reason).toMatch(/no value proxies/);
  });

  it('is UNCOMPUTED when cost is 0 (no division-by-zero fiction)', () => {
    const r = computeRoi({ cost: { llmUsd: 0 }, value: { timeUsd: 100 } });
    expect(r.status).toBe('uncomputed');
    if (r.status === 'uncomputed') expect(r.reason).toMatch(/cost is 0/);
  });

  it('sums multiple proxies + extra cost components', () => {
    const r = computeRoi({ cost: { llmUsd: 10, humanUsd: 10 }, value: { timeUsd: 50, kpiUsd: 50 } });
    if (r.status === 'computed') {
      expect(r.costUsd).toBe(20);
      expect(r.valueUsd).toBe(100);
      expect(r.roi).toBeCloseTo((100 - 20) / 20, 6);
    }
  });
});

describe('buildAiHealth', () => {
  beforeEach(() => { testDb = freshDb(); });

  it('flags incomplete + unverified cost and leaves ROI uncomputed without value', async () => {
    const { recordAiStep } = await import('@/lib/ai/telemetry');
    const { buildAiHealth } = await import('@/lib/ai/health');
    recordAiStep({ taskRole: 'd', capabilityRole: 'balanced', provider: 'openai', model: 'gpt-4o',
      usage: { inputTokens: 1_000_000, outputTokens: 0 }, latencyMs: 1 }); // unverified price
    recordAiStep({ taskRole: 'd', capabilityRole: 'balanced', provider: 'x', model: 'unpriced',
      usage: { inputTokens: 10, outputTokens: 10 }, latencyMs: 1 }); // uncomputed cost

    const h = buildAiHealth();
    expect(h.usage.steps).toBe(2);
    expect(h.roi.status).toBe('uncomputed');
    expect(h.warnings.some((w) => w.includes('unvollständig'))).toBe(true);
    expect(h.warnings.some((w) => w.includes('unverifizierte'))).toBe(true);
  });

  it('computes ROI when value proxies are supplied, warning that cost is incomplete', async () => {
    const { recordAiStep } = await import('@/lib/ai/telemetry');
    const { buildAiHealth } = await import('@/lib/ai/health');
    recordAiStep({ taskRole: 'd', capabilityRole: 'balanced', provider: 'anthropic', model: 'claude-sonnet-4-6',
      usage: { inputTokens: 1_000_000, outputTokens: 0 }, latencyMs: 1 }); // $3 verified
    recordAiStep({ taskRole: 'd', capabilityRole: 'balanced', provider: 'x', model: 'unpriced',
      usage: { inputTokens: 1, outputTokens: 1 }, latencyMs: 1 }); // uncomputed

    const h = buildAiHealth({ value: { timeUsd: 300 }, attribution: 1 });
    expect(h.roi.status).toBe('computed');
    expect(h.warnings.some((w) => w.includes('Ober'))).toBe(true); // ROI-on-incomplete-cost note
  });
});
