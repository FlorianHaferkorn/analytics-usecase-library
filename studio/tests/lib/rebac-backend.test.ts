/**
 * Tests for the in-process ReBAC backend (checkAccessReBAC) against a real DB.
 *
 * Unlike rebac-eval.test.ts (which tests the pure model) this exercises the
 * DB-fact-loading path directly — it runs in the DEFAULT `npm test` (no env flag),
 * so a regression in rebac-backend.ts is caught by CI, not only when someone sets
 * AUTHZ_BACKEND=rebac. Mirrors org-rbac.test.ts's in-memory-DB + vi.mock pattern.
 * The scenarios reproduce the ADR-0014 case matrix (authz-fga-cases.json).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.pragma('foreign_keys = ON');
  d.exec(`
    CREATE TABLE users (
      id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE projects (
      id TEXT PRIMARY KEY, name TEXT NOT NULL,
      org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE project_members (
      user_id TEXT NOT NULL, project_id TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'viewer',
      created_at TEXT NOT NULL DEFAULT (datetime('now')), PRIMARY KEY (user_id, project_id)
    );
    CREATE TABLE organizations (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE org_members (
      user_id TEXT NOT NULL, org_id TEXT NOT NULL, org_role TEXT NOT NULL DEFAULT 'member',
      business_role_id TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, org_id)
    );
  `);
  return d;
}

const testDb = createTestDb();
vi.mock('../../src/lib/db/sqlite', () => ({ getDb: () => testDb }));

import { createOrganization, addOrgMember, setProjectOrg } from '../../src/lib/db/org-repo';
import { addProjectMember } from '../../src/lib/db/rbac-repo';
import { checkAccessReBAC } from '../../src/lib/authz/rebac-backend';

function seedUser(id: string) {
  testDb.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run(id, `${id}@test.local`, id);
}
function seedProject(id: string) {
  testDb.prepare('INSERT INTO projects (id, name) VALUES (?, ?)').run(id, id);
}

describe('checkAccessReBAC (in-process backend, ADR-0014 matrix)', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
    seedUser('u2');
    seedProject('p1');
  });

  it('1 — explicit viewer caps an org owner (no merge, override downward)', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'viewer');
    expect(checkAccessReBAC('p1', 'u1', 'viewer')!.role).toBe('viewer');
    expect(checkAccessReBAC('p1', 'u1', 'admin')).toBeUndefined();
  });

  it('2 — org owner, no explicit row -> admin', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    expect(checkAccessReBAC('p1', 'u1', 'admin')!.role).toBe('admin');
  });

  it('3 — org member, no explicit row -> viewer only', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'member');
    expect(checkAccessReBAC('p1', 'u1', 'viewer')).toBeTruthy();
    expect(checkAccessReBAC('p1', 'u1', 'editor')).toBeUndefined();
    expect(checkAccessReBAC('p1', 'u1', 'admin')).toBeUndefined();
  });

  it('4 — solo project, explicit admin', () => {
    addProjectMember('p1', 'u1', 'admin');
    expect(checkAccessReBAC('p1', 'u1', 'admin')!.role).toBe('admin');
  });

  it('5 — explicit editor caps an org owner', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'editor');
    expect(checkAccessReBAC('p1', 'u1', 'editor')!.role).toBe('editor');
    expect(checkAccessReBAC('p1', 'u1', 'admin')).toBeUndefined();
  });

  it('6 — solo project, no access at all', () => {
    expect(checkAccessReBAC('p1', 'u1', 'viewer')).toBeUndefined();
  });

  it('8 — project belongs to an org the user is NOT a member of -> no access', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u2', 'owner'); // different user
    expect(checkAccessReBAC('p1', 'u1', 'viewer')).toBeUndefined();
  });

  it('9 — break-glass: an explicit admin grant lifts the cap', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'viewer');
    expect(checkAccessReBAC('p1', 'u1', 'admin')).toBeUndefined();
    addProjectMember('p1', 'u1', 'admin'); // break-glass
    expect(checkAccessReBAC('p1', 'u1', 'admin')!.role).toBe('admin');
  });

  it('returns a real created_at (never the empty-string fallback)', () => {
    addProjectMember('p1', 'u1', 'admin');
    const access = checkAccessReBAC('p1', 'u1', 'admin');
    expect(access!.created_at).toBeTruthy();
    expect(access!.created_at).not.toBe('');
  });
});
