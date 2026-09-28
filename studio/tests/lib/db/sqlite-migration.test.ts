/**
 * Tests for migrateBracketLifecyclePrimaryKey (bracket_lifecycle composite-PK fix).
 *
 * Exercises the exported migration function directly against a raw
 * better-sqlite3 database seeded with the pre-fix schema, independent of the
 * getDb() singleton (which always starts from the post-fix schema).
 */

import { describe, it, expect } from 'vitest';
import Database from 'better-sqlite3';
import { migrateAiPolicyReviewStatus, migrateBracketLifecyclePrimaryKey } from '../../../src/lib/db/sqlite';

function createPreFixDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE projects (
      id TEXT PRIMARY KEY DEFAULT 'default',
      name TEXT NOT NULL DEFAULT 'Test'
    );
    INSERT INTO projects (id) VALUES ('default'), ('proj-a'), ('proj-b');

    CREATE TABLE bracket_lifecycle (
      bracket_id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
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

describe('migrateBracketLifecyclePrimaryKey', () => {
  it('rebuilds the table onto a composite (bracket_id, project_id) primary key, preserving data', () => {
    const db = createPreFixDb();
    db.prepare(
      "INSERT INTO bracket_lifecycle (bracket_id, project_id, status, submitted_by) VALUES ('COM-001', 'proj-a', 'approved', 'user-a@co.com')",
    ).run();

    migrateBracketLifecyclePrimaryKey(db);

    const sql = (
      db.prepare("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'bracket_lifecycle'").get() as {
        sql: string;
      }
    ).sql;
    expect(sql).toContain('PRIMARY KEY (bracket_id, project_id)');

    const row = db.prepare('SELECT * FROM bracket_lifecycle WHERE bracket_id = ?').get('COM-001') as {
      project_id: string;
      status: string;
      submitted_by: string;
    };
    expect(row.project_id).toBe('proj-a');
    expect(row.status).toBe('approved');
    expect(row.submitted_by).toBe('user-a@co.com');
  });

  it('is idempotent — a second run on an already-migrated table is a no-op', () => {
    const db = createPreFixDb();
    db.prepare("INSERT INTO bracket_lifecycle (bracket_id, project_id) VALUES ('COM-001', 'proj-a')").run();

    migrateBracketLifecyclePrimaryKey(db);
    migrateBracketLifecyclePrimaryKey(db);

    const count = (db.prepare('SELECT COUNT(*) as n FROM bracket_lifecycle').get() as { n: number }).n;
    expect(count).toBe(1);
  });

  it('after migration, the same bracket_id can exist independently across two projects', () => {
    const db = createPreFixDb();
    // Pre-fix schema physically cannot hold two rows with the same bracket_id
    // (PK was bracket_id alone) — migrate first, then insert the second row.
    db.prepare("INSERT INTO bracket_lifecycle (bracket_id, project_id, status) VALUES ('COM-001', 'proj-a', 'approved')").run();
    migrateBracketLifecyclePrimaryKey(db);
    db.prepare("INSERT INTO bracket_lifecycle (bracket_id, project_id, status) VALUES ('COM-001', 'proj-b', 'draft')").run();

    const rows = db.prepare('SELECT project_id, status FROM bracket_lifecycle WHERE bracket_id = ? ORDER BY project_id').all(
      'COM-001',
    ) as Array<{ project_id: string; status: string }>;
    expect(rows).toEqual([
      { project_id: 'proj-a', status: 'approved' },
      { project_id: 'proj-b', status: 'draft' },
    ]);
  });

  it('falls back an orphaned project_id (references a deleted project) to \'default\' instead of violating the new FK', () => {
    const db = createPreFixDb();
    db.pragma('foreign_keys = ON');
    db.prepare(
      "INSERT INTO bracket_lifecycle (bracket_id, project_id, status) VALUES ('COM-005', 'proj-deleted', 'approved')",
    ).run();

    expect(() => migrateBracketLifecyclePrimaryKey(db)).not.toThrow();

    const row = db.prepare('SELECT project_id, status FROM bracket_lifecycle WHERE bracket_id = ?').get('COM-005') as {
      project_id: string;
      status: string;
    };
    expect(row.project_id).toBe('default');
    expect(row.status).toBe('approved');
  });

  it('is a no-op on a database that already has the composite primary key', () => {
    const d = new Database(':memory:');
    d.exec(`
      CREATE TABLE projects (id TEXT PRIMARY KEY);
      INSERT INTO projects (id) VALUES ('default');
      CREATE TABLE bracket_lifecycle (
        bracket_id TEXT NOT NULL,
        project_id TEXT NOT NULL DEFAULT 'default',
        status TEXT NOT NULL DEFAULT 'draft',
        submitted_by TEXT,
        approved_by TEXT,
        justification TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (bracket_id, project_id)
      );
      INSERT INTO bracket_lifecycle (bracket_id) VALUES ('COM-001');
    `);

    expect(() => migrateBracketLifecyclePrimaryKey(d)).not.toThrow();
    const count = (d.prepare('SELECT COUNT(*) as n FROM bracket_lifecycle').get() as { n: number }).n;
    expect(count).toBe(1);
  });
});

describe('migrateAiPolicyReviewStatus (C-22)', () => {
  function preDb(): Database.Database {
    const d = new Database(':memory:');
    d.exec(`
      CREATE TABLE projects (id TEXT PRIMARY KEY);
      INSERT INTO projects (id) VALUES ('p');
      CREATE TABLE ai_policy_reviews (
        id TEXT PRIMARY KEY, project_id TEXT NOT NULL, revision_hash TEXT NOT NULL, route_id TEXT NOT NULL,
        route_hash TEXT NOT NULL, decision_ref TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
        submitted_by TEXT NOT NULL, submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
        reviewed_by TEXT, reviewed_at TEXT, rationale TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id)
      );
      ALTER TABLE ai_policy_reviews ADD COLUMN route_expires_at TEXT;
      INSERT INTO ai_policy_reviews (id, project_id, revision_hash, route_id, route_hash, decision_ref, status, submitted_by)
      VALUES ('r1', 'p', 'r', 'route', 'h', 'd', 'pending', 'a@example.com');
    `);
    return d;
  }

  it('allows expired, keeps rows and is idempotent', () => {
    const d = preDb();
    expect(() => d.prepare("UPDATE ai_policy_reviews SET status = 'expired'").run()).toThrow();
    migrateAiPolicyReviewStatus(d);
    migrateAiPolicyReviewStatus(d);
    d.prepare("UPDATE ai_policy_reviews SET status = 'expired'").run();
    expect(d.prepare('SELECT id, status, route_expires_at FROM ai_policy_reviews').all())
      .toEqual([{ id: 'r1', status: 'expired', route_expires_at: null }]);
    expect(() => d.prepare("UPDATE ai_policy_reviews SET status = 'deleted'").run()).toThrow();
  });
});
