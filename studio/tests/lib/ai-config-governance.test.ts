import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';
import type { AiConfigLayer } from '@/lib/ai/config/resolve';

// in-memory DB + stub audit-repo (avoid audit-chain wiring) + real schema validation.
let testDb: Database.Database;
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => testDb }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: vi.fn() }));

function freshDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE ai_config_layers (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL DEFAULT 'default', layer TEXT NOT NULL,
      domain_id TEXT NOT NULL DEFAULT '', config_json TEXT NOT NULL,
      schema_version TEXT NOT NULL DEFAULT '1.0.0', status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT, approved_by TEXT, justification TEXT, effective_hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (project_id, layer, domain_id)
    );
  `);
  return d;
}

// A valid L1 that bans anthropic (tightens the L0 provider allow-list).
const L1_BAN_ANTHROPIC: AiConfigLayer = {
  schema_version: '1.0.0', layer: 'L1',
  providerPolicy: { allowedProviders: ['google', 'openai'] },
};

beforeEach(() => { testDb = freshDb(); });

describe('ai-config governance', () => {
  it('rejects an invalid layer at save', async () => {
    const { upsertConfigLayer, AiConfigGovernanceError } = await import('@/lib/db/ai-config-repo');
    const bad = { schema_version: '1.0.0', layer: 'L1', tokenPolicy: { maxOutputTokens: -5 } } as unknown as AiConfigLayer;
    expect(() => upsertConfigLayer({ layer: 'L1', config: bad })).toThrow(AiConfigGovernanceError);
  });

  it('serves a layer only after it is approved (draft is not served)', async () => {
    const { upsertConfigLayer, transitionConfigLayer, getApprovedLayers } = await import('@/lib/db/ai-config-repo');
    upsertConfigLayer({ layer: 'L1', config: L1_BAN_ANTHROPIC });
    expect(getApprovedLayers('default').l1).toBeUndefined(); // still draft

    transitionConfigLayer('default', 'L1', '', 'submit', 'alice', 'propose ban');
    transitionConfigLayer('default', 'L1', '', 'approve', 'bob', 'ok');
    expect(getApprovedLayers('default').l1?.providerPolicy?.allowedProviders).toEqual(['google', 'openai']);
  });

  it('enforces the two-person rule on approve', async () => {
    const { upsertConfigLayer, transitionConfigLayer, AiConfigGovernanceError } = await import('@/lib/db/ai-config-repo');
    upsertConfigLayer({ layer: 'L1', config: L1_BAN_ANTHROPIC });
    transitionConfigLayer('default', 'L1', '', 'submit', 'alice', 'propose');
    expect(() => transitionConfigLayer('default', 'L1', '', 'approve', 'alice', 'self'))
      .toThrow(AiConfigGovernanceError);
  });

  it('editing an approved layer resets it to draft (must be re-approved)', async () => {
    const { upsertConfigLayer, transitionConfigLayer, getConfigLayer } = await import('@/lib/db/ai-config-repo');
    upsertConfigLayer({ layer: 'L1', config: L1_BAN_ANTHROPIC });
    transitionConfigLayer('default', 'L1', '', 'submit', 'alice', 'p');
    transitionConfigLayer('default', 'L1', '', 'approve', 'bob', 'ok');
    upsertConfigLayer({ layer: 'L1', config: { ...L1_BAN_ANTHROPIC, providerPolicy: { allowedProviders: ['openai'] } } });
    expect(getConfigLayer('default', 'L1')!.status).toBe('draft');
  });

  it('requires a domainId for L2', async () => {
    const { upsertConfigLayer, AiConfigGovernanceError } = await import('@/lib/db/ai-config-repo');
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2' };
    expect(() => upsertConfigLayer({ layer: 'L2', config: l2 })).toThrow(AiConfigGovernanceError);
  });
});

describe('approved L1 flows through to routing (end-to-end)', () => {
  it('an approved provider ban removes anthropic from the choice', async () => {
    const { upsertConfigLayer, transitionConfigLayer } = await import('@/lib/db/ai-config-repo');
    const { loadAiConfigLayers } = await import('@/lib/ai/config/load-layers');
    const { chooseModel } = await import('@/lib/ai/config/route-model');

    upsertConfigLayer({ layer: 'L1', config: L1_BAN_ANTHROPIC });
    transitionConfigLayer('default', 'L1', '', 'submit', 'alice', 'p');
    transitionConfigLayer('default', 'L1', '', 'approve', 'bob', 'ok');

    const layers = loadAiConfigLayers('default');
    const choice = chooseModel('default', { secretPresent: () => true, layers });
    expect(choice?.provider).toBe('google'); // anthropic banned by approved L1
  });
});
