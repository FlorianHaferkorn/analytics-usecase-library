/**
 * Tests for Audit Hash Chain — tamper detection.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';

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

import { computeEventHash, chainEvent, verifyChain, getLastHash } from '../../src/lib/db/audit-chain';
import type { AuditEvent } from '../../src/lib/db/audit-repo';

function insertEvent(id: string, entityType = 'bracket', entityId = 'B-1', action = 'create'): void {
  testDb.prepare(`
    INSERT INTO audit_events (id, project_id, actor, entity_type, entity_id, action, diff_json)
    VALUES (?, 'default', 'test@co.com', ?, ?, ?, '{}')
  `).run(id, entityType, entityId, action);
}

describe('audit-chain', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM audit_events');
  });

  it('computes a deterministic SHA-256 hash', () => {
    const event: AuditEvent = {
      id: 'aud-1',
      project_id: 'default',
      actor: 'test@co.com',
      entity_type: 'bracket',
      entity_id: 'B-1',
      action: 'create',
      diff_json: '{}',
      created_at: '2024-01-01 00:00:00',
    };
    const hash1 = computeEventHash(event, '');
    const hash2 = computeEventHash(event, '');
    expect(hash1).toBe(hash2);
    expect(hash1).toHaveLength(64); // SHA-256 hex
  });

  it('produces different hashes with different prevHash', () => {
    const event: AuditEvent = {
      id: 'aud-1',
      project_id: 'default',
      actor: 'test@co.com',
      entity_type: 'bracket',
      entity_id: 'B-1',
      action: 'create',
      diff_json: '{}',
      created_at: '2024-01-01 00:00:00',
    };
    const h1 = computeEventHash(event, '');
    const h2 = computeEventHash(event, 'abc123');
    expect(h1).not.toBe(h2);
  });

  it('chains an event and stores hash', () => {
    insertEvent('aud-1');
    const hash = chainEvent('aud-1');
    expect(hash).toHaveLength(64);

    const row = testDb.prepare('SELECT prev_hash, hash FROM audit_events WHERE id = ?').get('aud-1') as { prev_hash: string; hash: string };
    expect(row.prev_hash).toBe('');
    expect(row.hash).toBe(hash);
  });

  it('chains second event to first', () => {
    insertEvent('aud-1');
    const hash1 = chainEvent('aud-1');

    insertEvent('aud-2', 'bracket', 'B-2');
    const hash2 = chainEvent('aud-2');

    expect(hash2).not.toBe(hash1);

    const row = testDb.prepare('SELECT prev_hash FROM audit_events WHERE id = ?').get('aud-2') as { prev_hash: string };
    expect(row.prev_hash).toBe(hash1);
  });

  it('verifies a valid chain', () => {
    insertEvent('aud-1');
    chainEvent('aud-1');
    insertEvent('aud-2', 'project', 'default', 'update');
    chainEvent('aud-2');
    insertEvent('aud-3', 'theme', 'default', 'update');
    chainEvent('aud-3');

    const result = verifyChain();
    expect(result.valid).toBe(true);
    expect(result.checked).toBe(3);
  });

  it('detects a tampered event', () => {
    insertEvent('aud-1');
    chainEvent('aud-1');
    insertEvent('aud-2', 'bracket', 'B-2');
    chainEvent('aud-2');

    // Tamper with the first event's diff
    testDb.prepare("UPDATE audit_events SET diff_json = '{\"tampered\":true}' WHERE id = 'aud-1'").run();

    const result = verifyChain();
    expect(result.valid).toBe(false);
    expect(result.brokenAt).toBe('aud-1');
  });

  it('returns valid for empty chain', () => {
    const result = verifyChain();
    expect(result.valid).toBe(true);
    expect(result.checked).toBe(0);
  });

  it('getLastHash returns empty string for empty chain', () => {
    expect(getLastHash()).toBe('');
  });

  it('getLastHash returns most recent hash', () => {
    insertEvent('aud-1');
    const hash = chainEvent('aud-1');
    expect(getLastHash()).toBe(hash);
  });
});
