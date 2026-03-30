/**
 * Tests for RBAC Repository and Role Hierarchy.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';

/* ------------------------------------------------------------------ */
/* In-memory DB with users + project_members tables                    */
/* ------------------------------------------------------------------ */

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.pragma('foreign_keys = ON');
  d.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY DEFAULT 'default',
      name TEXT NOT NULL DEFAULT 'Test',
      strategy_anchor TEXT NOT NULL DEFAULT '',
      theme_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT OR IGNORE INTO projects (id) VALUES ('default');

    CREATE TABLE IF NOT EXISTS project_members (
      user_id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'viewer',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, project_id),
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    INSERT INTO users (id, email, name) VALUES ('u1', 'admin@co.com', 'Admin');
    INSERT INTO users (id, email, name) VALUES ('u2', 'editor@co.com', 'Editor');
    INSERT INTO users (id, email, name) VALUES ('u3', 'viewer@co.com', 'Viewer');
  `);
  return d;
}

/* ------------------------------------------------------------------ */
/* roleAtLeast unit tests                                              */
/* ------------------------------------------------------------------ */

import { roleAtLeast } from '@/lib/auth/rbac-types';

describe('roleAtLeast', () => {
  it('admin >= admin', () => expect(roleAtLeast('admin', 'admin')).toBe(true));
  it('admin >= editor', () => expect(roleAtLeast('admin', 'editor')).toBe(true));
  it('admin >= viewer', () => expect(roleAtLeast('admin', 'viewer')).toBe(true));
  it('editor >= editor', () => expect(roleAtLeast('editor', 'editor')).toBe(true));
  it('editor >= viewer', () => expect(roleAtLeast('editor', 'viewer')).toBe(true));
  it('editor < admin', () => expect(roleAtLeast('editor', 'admin')).toBe(false));
  it('viewer >= viewer', () => expect(roleAtLeast('viewer', 'viewer')).toBe(true));
  it('viewer < editor', () => expect(roleAtLeast('viewer', 'editor')).toBe(false));
  it('viewer < admin', () => expect(roleAtLeast('viewer', 'admin')).toBe(false));
});

/* ------------------------------------------------------------------ */
/* RBAC repo integration tests (in-memory DB)                          */
/* ------------------------------------------------------------------ */

// We test the DB logic directly since rbac-repo imports from sqlite singleton.
// We replicate the same SQL logic here.

describe('RBAC DB operations', () => {
  let db: Database.Database;

  beforeEach(() => {
    db = createTestDb();
  });

  it('adds a project member', () => {
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u1', 'default', 'admin');
    const row = db.prepare('SELECT * FROM project_members WHERE user_id = ? AND project_id = ?').get('u1', 'default') as { role: string };
    expect(row.role).toBe('admin');
  });

  it('removes a project member', () => {
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u1', 'default', 'admin');
    const result = db.prepare('DELETE FROM project_members WHERE user_id = ? AND project_id = ?').run('u1', 'default');
    expect(result.changes).toBe(1);
  });

  it('returns undefined for non-member', () => {
    const row = db.prepare('SELECT * FROM project_members WHERE user_id = ? AND project_id = ?').get('u1', 'default');
    expect(row).toBeUndefined();
  });

  it('lists all members of a project', () => {
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u1', 'default', 'admin');
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u2', 'default', 'editor');
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u3', 'default', 'viewer');
    const rows = db.prepare('SELECT * FROM project_members WHERE project_id = ?').all('default');
    expect(rows).toHaveLength(3);
  });

  it('enforces checkAccess with role hierarchy', () => {
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u2', 'default', 'editor');
    const member = db.prepare('SELECT * FROM project_members WHERE user_id = ? AND project_id = ?').get('u2', 'default') as { role: string } | undefined;
    expect(member).toBeDefined();
    // Editor can act as editor
    expect(roleAtLeast(member!.role as 'admin' | 'editor' | 'viewer', 'editor')).toBe(true);
    // Editor cannot act as admin
    expect(roleAtLeast(member!.role as 'admin' | 'editor' | 'viewer', 'admin')).toBe(false);
  });

  it('upserts member role via INSERT OR REPLACE', () => {
    db.prepare('INSERT INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u1', 'default', 'viewer');
    db.prepare('INSERT OR REPLACE INTO project_members (user_id, project_id, role) VALUES (?, ?, ?)').run('u1', 'default', 'admin');
    const row = db.prepare('SELECT * FROM project_members WHERE user_id = ? AND project_id = ?').get('u1', 'default') as { role: string };
    expect(row.role).toBe('admin');
  });

  it('auto-provisions user record', () => {
    const email = 'new@co.com';
    const existing = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
    expect(existing).toBeUndefined();

    db.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run('u-new', email, 'New User');
    const created = db.prepare('SELECT * FROM users WHERE email = ?').get(email) as { id: string; email: string };
    expect(created.email).toBe(email);
  });
});
