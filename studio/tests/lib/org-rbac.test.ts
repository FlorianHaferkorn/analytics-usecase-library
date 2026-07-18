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
      business_role_id TEXT,
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
  setMemberBusinessRole,
  listOrgMembersWithDetails,
  getOrgMember,
} from '../../src/lib/db/org-repo';
import { checkAccess, addProjectMember, getProjectMember, removeProjectMember } from '../../src/lib/db/rbac-repo';
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

describe('business_role_id — display-only link to org_roles.yaml (ADR-0014 O-3)', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
    seedUser('u2');
    seedProject('p1');
  });

  it('addOrgMember accepts and stores an optional business_role_id', () => {
    const org = createOrganization('Acme');
    const member = addOrgMember(org.id, 'u1', 'member', 'finance_bi_lead');
    expect(member.business_role_id).toBe('finance_bi_lead');
  });

  it('defaults business_role_id to null when omitted (backward compatible)', () => {
    const org = createOrganization('Acme');
    const member = addOrgMember(org.id, 'u1', 'member');
    expect(member.business_role_id).toBeNull();
  });

  it('setMemberBusinessRole updates the label without touching org_role', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u1', 'admin');
    const updated = setMemberBusinessRole(org.id, 'u1', 'plant_manager');
    expect(updated!.business_role_id).toBe('plant_manager');
    expect(updated!.org_role).toBe('admin'); // unchanged

    const cleared = setMemberBusinessRole(org.id, 'u1', null);
    expect(cleared!.business_role_id).toBeNull();
  });

  it('setMemberBusinessRole never grants or changes RBAC access', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'member'); // org fallback only ever grants viewer
    setMemberBusinessRole(org.id, 'u1', 'head_of_supply_chain'); // a senior-sounding title
    expect(checkAccess('p1', 'u1', 'viewer')).toBeTruthy();
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined(); // label alone grants nothing
  });

  it('listOrgMembersWithDetails joins email/name and carries business_role_id', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u1', 'owner', 'finance_bi_lead');
    addOrgMember(org.id, 'u2', 'member');

    const rows = listOrgMembersWithDetails(org.id);
    expect(rows).toHaveLength(2);
    const u1Row = rows.find((r) => r.user_id === 'u1')!;
    expect(u1Row.email).toBe('u1@test.local');
    expect(u1Row.business_role_id).toBe('finance_bi_lead');
    const u2Row = rows.find((r) => r.user_id === 'u2')!;
    expect(u2Row.business_role_id).toBeNull();
  });
});

describe('org-owner break-glass override (ADR-0014 O-4) — repo-level mechanics', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
    seedProject('p1');
  });

  it('reproduces the lockout: an org owner capped by an old, narrow project_members row', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner'); // org owner, would resolve to admin via fallback
    addProjectMember('p1', 'u1', 'viewer'); // stale, narrow explicit row predates org ownership

    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined(); // Festlegung 4: no merge, capped at viewer
  });

  it('the override mechanism (an explicit admin grant on the owner\'s own project) lifts the cap', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'viewer');
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined();

    // This is exactly what POST /api/org/[orgId]/break-glass does after its
    // org-owner + project-belongs-to-org guards pass.
    const before = getProjectMember('p1', 'u1');
    expect(before!.role).toBe('viewer');
    addProjectMember('p1', 'u1', 'admin');

    expect(checkAccess('p1', 'u1', 'admin')).toBeTruthy(); // now resolves via the (now real) explicit row
  });

  it('org membership alone (member org_role) never becomes an override target — the route gates on owner, not just admin', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u1', 'member');
    expect(checkOrgAccess(org.id, 'u1', 'owner')).toBeUndefined(); // route's guard would reject this actor
  });

  it('the route\'s precondition check refuses when the actor is already admin (fallback alone, no explicit row) — not a general "grab admin" shortcut', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner'); // no explicit project_members row at all
    // The route's POST checks `checkAccess(projectId, actor.id, 'admin')` BEFORE
    // mutating — this must already be truthy here (fallback alone gives admin),
    // which is exactly what makes the route refuse to "grab" it via an explicit grant.
    expect(checkAccess('p1', 'u1', 'admin')).toBeTruthy();
  });

  it('DELETE (self-revert) removes the explicit row and reverts to normal two-stage resolution', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'viewer');
    addProjectMember('p1', 'u1', 'admin'); // as if break-glass POST already ran

    expect(getProjectMember('p1', 'u1')!.role).toBe('admin');
    removeProjectMember('p1', 'u1'); // what DELETE /break-glass does
    expect(getProjectMember('p1', 'u1')).toBeUndefined();
    // Reverts to the org fallback, which for an owner still resolves to admin —
    // the point of DELETE is removing the stale explicit row, not demotion by itself.
    expect(checkAccess('p1', 'u1', 'admin')).toBeTruthy();
  });

  it('DELETE reflects a later org-role demotion correctly, where a stale explicit row would not', () => {
    const org = createOrganization('Acme');
    setProjectOrg('p1', org.id);
    addOrgMember(org.id, 'u1', 'owner');
    addProjectMember('p1', 'u1', 'admin'); // break-glass grant while still owner

    addOrgMember(org.id, 'u1', 'member'); // demoted to member later
    expect(checkAccess('p1', 'u1', 'admin')).toBeTruthy(); // stale explicit row still masks the demotion

    removeProjectMember('p1', 'u1'); // DELETE /break-glass
    expect(checkAccess('p1', 'u1', 'admin')).toBeUndefined(); // now correctly reflects the demotion (member -> viewer fallback)
    expect(checkAccess('p1', 'u1', 'viewer')).toBeTruthy();
  });
});

describe('O-1 bootstrap: org creator becomes its first owner', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM org_members; DELETE FROM organizations; DELETE FROM project_members; DELETE FROM projects; DELETE FROM users;');
    seedUser('u1');
  });

  it('the exact sequence POST /api/org runs (createOrganization then addOrgMember owner) leaves the creator as sole owner', () => {
    const org = createOrganization('Acme');
    addOrgMember(org.id, 'u1', 'owner');

    const member = getOrgMember(org.id, 'u1');
    expect(member!.org_role).toBe('owner');
    expect(checkOrgAccess(org.id, 'u1', 'owner')).toBeTruthy();
  });
});
