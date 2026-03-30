/**
 * Tests for Audit Helpers — actor capture utilities.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import Database from 'better-sqlite3';

/* ------------------------------------------------------------------ */
/* In-memory DB setup                                                  */
/* ------------------------------------------------------------------ */

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY DEFAULT 'default',
      name TEXT NOT NULL DEFAULT 'Test',
      strategy_anchor TEXT NOT NULL DEFAULT '',
      theme_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT OR IGNORE INTO projects (id) VALUES ('default');

    CREATE TABLE IF NOT EXISTS audit_events (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      actor TEXT NOT NULL DEFAULT 'system',
      entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL,
      action TEXT NOT NULL,
      diff_json TEXT NOT NULL DEFAULT '{}',
      prev_hash TEXT,
      hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );
  `);
  return d;
}

const testDb = createTestDb();

vi.mock('../../src/lib/db/sqlite', () => ({
  getDb: () => testDb,
}));

vi.mock('../../src/lib/auth/session', () => ({
  getSessionUser: vi.fn(),
}));

import { auditWithActor, auditWithKnownActor } from '../../src/lib/db/audit-helpers';
import { getSessionUser } from '../../src/lib/auth/session';

const mockGetSessionUser = vi.mocked(getSessionUser);

describe('audit-helpers', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM audit_events');
    vi.clearAllMocks();
  });

  it('auditWithActor captures session user as actor', async () => {
    mockGetSessionUser.mockResolvedValue({ id: 'u1', email: 'admin@co.com', name: 'Admin' });

    const event = await auditWithActor('bracket', 'COM-001', 'update', {
      before: { yaml: 'old' },
      after: { yaml: 'new' },
    });
    expect(event.actor).toBe('admin@co.com');
  });

  it('auditWithActor falls back to system when no session', async () => {
    mockGetSessionUser.mockResolvedValue(null);

    const event = await auditWithActor('bracket', 'COM-001', 'create', {
      before: null,
      after: { yaml: 'new' },
    });
    expect(event.actor).toBe('system');
  });

  it('auditWithKnownActor uses the provided actor', () => {
    const event = auditWithKnownActor('cron@system', 'notification_rule', 'rule-1', 'update', {
      before: { enabled: true },
      after: { enabled: false },
    });
    expect(event.actor).toBe('cron@system');
  });

  it('auditWithActor supports notification_rule entity type', async () => {
    mockGetSessionUser.mockResolvedValue({ id: 'u1', email: 'user@co.com', name: 'User' });

    const event = await auditWithActor('notification_rule', 'rule-1', 'create', {
      before: null,
      after: { name: 'Alert Rule' },
    });
    expect(event.entity_type).toBe('notification_rule');
  });

  it('auditWithActor supports plugin entity type', async () => {
    mockGetSessionUser.mockResolvedValue({ id: 'u1', email: 'user@co.com', name: 'User' });

    const event = await auditWithActor('plugin', 'calc-v1', 'create', {
      before: null,
      after: { name: 'Calculator' },
    });
    expect(event.entity_type).toBe('plugin');
  });

  it('auditWithActor supports export entity type', async () => {
    mockGetSessionUser.mockResolvedValue({ id: 'u1', email: 'user@co.com', name: 'User' });

    const event = await auditWithActor('export', 'fabric-001', 'export', {
      before: null,
      after: { format: 'tmdl' },
    });
    expect(event.entity_type).toBe('export');
    expect(event.action).toBe('export');
  });

  it('auditWithKnownActor stores justification in diff', () => {
    const event = auditWithKnownActor('admin@co.com', 'governance', 'bracket-1', 'approve', {
      before: { status: 'review' },
      after: { status: 'approved' },
      justification: 'Reviewed by CFO',
    });
    const diff = JSON.parse(event.diff_json);
    expect(diff.justification).toBe('Reviewed by CFO');
  });

  it('auditWithActor uses custom projectId', async () => {
    mockGetSessionUser.mockResolvedValue({ id: 'u1', email: 'user@co.com', name: 'User' });

    const event = await auditWithActor('bracket', 'COM-001', 'update', {
      before: null,
      after: {},
    }, 'default');
    expect(event.project_id).toBe('default');
  });
});
