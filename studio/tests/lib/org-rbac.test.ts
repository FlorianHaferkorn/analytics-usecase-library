/**
 * Tests for the org layer over local-first (ADR-0014, I-9.2): org-repo.ts +
 * the two-stage checkAccess resolution in rbac-repo.ts.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.pragma('foreign_keys = ON');
  d.exec(`
    CREATE TABLE users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE projects (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE project_members (
      user_id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'viewer',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, project_id)
    );

    CREATE TABLE organizations (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE org_members (
      user_id TEXT NOT NULL,
      org_id TEXT NOT NULL,
      org_role TEXT NOT NULL DEFAULT 'member',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, org_id)
    );
  `);
  return d;
}

const testDb = createTestDb();

vi.mock('../../src/lib/db/sqlite', () => ({
  getDb: () => testDb,
}));

import {
  createOrganization,
  deleteOrganization,
  addOrgMember,
  checkOrgAccess,
  setProjectOrg,
  listOrgProjects,
} from '../../src/lib/db/org-repo';
import { checkAccess, addProjectMember } from '../../src/lib/db/rbac-repo';
import { projectRoleFromOrgRole, orgRoleAtLeast } from '../../src/lib/auth/rbac-types';

function seedUser(id: string) {
  testDb.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run(id, `${id}@test.local`, id);
}

function seedProject(id: string) {
  testDb.prepare('INSERT INTO projects (id, name) VALUES (?, ?)').run(id, id);
}

describe('org-repo', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
    seedUser('u2');
    seedProject('p1');
  });

  it('creates an organization', () => {
    const org = createOrganization('Acme');
    expect(org.name).toBe('Acme');
    expect(org.id).toBeTruthy();
  });

  it('adds and checks org membership', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u1', 'owner');
    expect(checkOrgAccess(org.id, 'u1', 'owner')).toBeTruthy();
    expect(checkOrgAccess(org.id, 'u1', 'admin')).toBeTruthy(); // owner >= admin
    expect(checkOrgAccess(org.id, 'u2', 'member')).toBeUndefined(); // not a member
  });

  it('member role does not satisfy an admin check', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u2', 'member');
    expect(checkOrgAccess(org.id, 'u2', 'admin')).toBeUndefined();
    expect(checkOrgAccess(org.id, 'u2', 'member')).toBeTruthy();
  });

  it('assigns and unassigns a project', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    expect(listOrgProjects(org.id)).toHaveLength(1);
    setProjectOrg('p1', null);
    expect(listOrgProjects(org.id)).toHaveLength(0);
  });

  it('ON DELETE SET NULL: deleting an org reverts its projects to solo, not orphaned', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    deleteOrganization(org.id);
    const project = testDb.prepare('SELECT org_id FROM projects WHERE id = ?').get('p1') as { org_id: string | null };
    expect(project.org_id).toBeNull();
  });
});

describe('projectRoleFromOrgRole (ADR-0014 Festlegung 4b: conservative, no editor path)', () => {
  it('maps owner and admin to project admin', () => {
    expect(projectRoleFromOrgRole('owner')).toBe('admin');
    expect(projectRoleFromOrgRole('admin')).toBe('admin');
  });
  it('maps member to project viewer, never editor', () => {
    expect(projectRoleFromOrgRole('member')).toBe('viewer');
  });
});

describe('orgRoleAtLeast', () => {
  it('orders member < admin < owner', () => {
    expect(orgRoleAtLeast('owner', 'member')).toBe(true);
    expect(orgRoleAtLeast('member', 'owner')).toBe(false);
    expect(orgRoleAtLeast('admin', 'admin')).toBe(true);
  });
});

describe('checkAccess two-stage resolution (ADR-0014 Festlegung 4)', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
    seedUser('u2');
    seedProject('p1');
  });

  it('unaffected baseline: explicit project_members row works exactly as before, no org involved', () => {
    addProjectMember('p1', 'u1', 'editor');
    expect(checkAccess('p1', 'u1', 'editor')).toBeTruthy();
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined();
  });

  it('no project row, no org on the project -> no access (unchanged from pre-ADR-0014 behavior)', () => {
    expect(checkAccess('p1', 'u1', 'viewer')).toBeUndefined();
  });

  it('org fallback: no explicit project row, but project belongs to an org the user is admin of -> admin access', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'admin');

    const access = checkAccess('p1', 'u1', 'admin');
    expect(access).toBeTruthy();
    expect(access!.role).toBe('admin');
  });

  it('org fallback: member role only grants viewer, never editor or admin', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'member');

    expect(checkAccess('p1', 'u1', 'viewer')).toBeTruthy();
    expect(checkAccess('p1', 'u1', 'editor')).toBeUndefined();
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined();
  });

  it('no merge: an explicit viewer row caps access even if the user is an org owner', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner'); // org owner, would otherwise resolve to admin
    addProjectMember('p1', 'u1', 'viewer'); // explicit, narrower project role

    const access = checkAccess('p1', 'u1', 'viewer');
    expect(access!.role).toBe('viewer'); // explicit row wins, not merged up to admin
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined(); // org owner does NOT bypass this
  });

  it('project belongs to an org, but the user is not a member of that org -> no access', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u2', 'owner'); // different user
    expect(checkAccess('p1', 'u1', 'viewer')).toBeUndefined();
  });

  it('unassigning a project from its org removes the fallback path', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'admin');
    expect(checkAccess('p1', 'u1', 'admin')).toBeTruthy();

    setProjectOrg('p1', null);
    expect(checkAccess('p1', 'u1', 'viewer')).toBeUndefined();
  });
});
