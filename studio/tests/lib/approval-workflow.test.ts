/**
 * Tests for Approval Workflow.
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

    CREATE TABLE IF NOT EXISTS bracket_lifecycle (
      bracket_id TEXT PRIMARY KEY,
      status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT,
      approved_by TEXT,
      justification TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
  return d;
}

const testDb = createTestDb();

vi.mock('../../src/lib/db/sqlite', () => ({
  getDb: () => testDb,
}));

import {
  getLifecycle,
  submitForReview,
  approve,
  reject,
  reopen,
} from '../../src/lib/governance/approval-workflow';

describe('approval-workflow', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM bracket_lifecycle');
    testDb.exec('DELETE FROM audit_events');
  });

  it('initializes bracket as draft', () => {
    const lifecycle = getLifecycle('UC001');
    expect(lifecycle.status).toBe('draft');
    expect(lifecycle.bracket_id).toBe('UC001');
  });

  it('submits for review from draft', () => {
    getLifecycle('UC001');
    const result = submitForReview('UC001', 'user@co.com', 'Ready for review');
    expect(result.status).toBe('review');
    expect(result.submitted_by).toBe('user@co.com');
  });

  it('approves from review', () => {
    getLifecycle('UC001');
    submitForReview('UC001', 'user@co.com', 'Ready');
    const result = approve('UC001', 'admin@co.com', 'Looks good');
    expect(result.status).toBe('approved');
    expect(result.approved_by).toBe('admin@co.com');
  });

  it('rejects from review', () => {
    getLifecycle('UC001');
    submitForReview('UC001', 'user@co.com', 'Ready');
    const result = reject('UC001', 'admin@co.com', 'Needs improvement');
    expect(result.status).toBe('rejected');
  });

  it('blocks invalid transitions', () => {
    getLifecycle('UC001');
    expect(() => approve('UC001', 'admin@co.com', 'Try')).toThrow('Invalid transition');
  });

  it('blocks self-approval', () => {
    getLifecycle('UC001');
    submitForReview('UC001', 'user@co.com', 'Ready');
    expect(() => approve('UC001', 'user@co.com', 'Self-approve')).toThrow('Cannot approve your own');
  });

  it('allows reopen from rejected', () => {
    getLifecycle('UC001');
    submitForReview('UC001', 'user@co.com', 'Ready');
    reject('UC001', 'admin@co.com', 'No');
    const result = reopen('UC001', 'user@co.com', 'Fixed issues');
    expect(result.status).toBe('draft');
  });

  it('logs audit event for each transition', () => {
    getLifecycle('UC001');
    submitForReview('UC001', 'user@co.com', 'Ready');
    const events = testDb.prepare('SELECT * FROM audit_events WHERE entity_type = ?').all('governance');
    expect(events.length).toBeGreaterThanOrEqual(1);
  });
});
