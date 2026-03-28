/**
 * Tests for Audit Repository.
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

import {
  logAuditEvent,
  getAuditEvents,
  getAuditEventsByEntity,
  getAuditEventCount,
} from '../../src/lib/db/audit-repo';

describe('audit-repo', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM audit_events');
  });

  it('logs an audit event and returns it', () => {
    const event = logAuditEvent('bracket', 'COM-001', 'update', {
      before: { yaml: 'old' },
      after: { yaml: 'new' },
    });
    expect(event.id).toMatch(/^aud-/);
    expect(event.entity_type).toBe('bracket');
    expect(event.entity_id).toBe('COM-001');
    expect(event.action).toBe('update');
    expect(event.project_id).toBe('default');
  });

  it('stores diff as JSON', () => {
    const event = logAuditEvent('theme', 'default', 'update', {
      before: { primary: '#000' },
      after: { primary: '#FFF' },
    });
    const diff = JSON.parse(event.diff_json);
    expect(diff.before).toEqual({ primary: '#000' });
    expect(diff.after).toEqual({ primary: '#FFF' });
  });

  it('queries events by project in reverse chronological order', () => {
    logAuditEvent('bracket', 'COM-001', 'create', { before: null, after: {} });
    logAuditEvent('bracket', 'COM-002', 'create', { before: null, after: {} });
    logAuditEvent('project', 'default', 'update', { before: null, after: {} });
    const events = getAuditEvents('default');
    expect(events).toHaveLength(3);
    // All events returned for the project
    const entityIds = events.map((e) => e.entity_id);
    expect(entityIds).toContain('COM-001');
    expect(entityIds).toContain('COM-002');
    expect(entityIds).toContain('default');
  });

  it('queries events by entity type and id', () => {
    logAuditEvent('bracket', 'COM-001', 'create', { before: null, after: {} });
    logAuditEvent('bracket', 'COM-001', 'update', { before: {}, after: {} });
    logAuditEvent('bracket', 'COM-002', 'create', { before: null, after: {} });
    const events = getAuditEventsByEntity('bracket', 'COM-001');
    expect(events).toHaveLength(2);
  });

  it('respects limit and offset', () => {
    for (let i = 0; i < 10; i++) {
      logAuditEvent('bracket', `B-${i}`, 'create', { before: null, after: {} });
    }
    const page1 = getAuditEvents('default', 3, 0);
    const page2 = getAuditEvents('default', 3, 3);
    expect(page1).toHaveLength(3);
    expect(page2).toHaveLength(3);
    expect(page1[0].entity_id).not.toBe(page2[0].entity_id);
  });

  it('counts events for a project', () => {
    logAuditEvent('bracket', 'COM-001', 'create', { before: null, after: {} });
    logAuditEvent('bracket', 'COM-002', 'update', { before: {}, after: {} });
    expect(getAuditEventCount('default')).toBe(2);
  });

  it('preserves actor when provided', () => {
    const event = logAuditEvent('project', 'default', 'update', {
      before: null,
      after: {},
    }, 'default', 'user@example.com');
    expect(event.actor).toBe('user@example.com');
  });

  it('handles create action with null before', () => {
    const event = logAuditEvent('bracket', 'NEW-001', 'create', {
      before: null,
      after: { title: 'New Bracket' },
    });
    const diff = JSON.parse(event.diff_json);
    expect(diff.before).toBeNull();
    expect(diff.after).toEqual({ title: 'New Bracket' });
  });
});
