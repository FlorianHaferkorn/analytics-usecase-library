/**
 * Tests for the in-process ReBAC evaluator (ADR-0014 parity, ADR-0016 Option A).
 *
 * The 9 cases mirror docs/architecture/research/authz-fga-cases.json (facts-level
 * encoding) — the same vectors a future OpenFGA check() suite would run against the
 * engine. Pins the non-additive override: an explicit project row wins over the
 * org-derived fallback in both directions.
 */

import { describe, it, expect } from 'vitest';
import { evaluatePermissions, effectiveRole, type AuthzFacts } from '@/lib/authz/rebac-eval';

interface Case {
  name: string;
  facts: AuthzFacts;
  view: boolean;
  edit: boolean;
  admin: boolean;
}

const CASES: Case[] = [
  { name: '1 explicit viewer caps org owner (O-4 lockout)', facts: { projectHasOrg: true, orgRole: 'owner', projectExplicit: 'viewer' }, view: true, edit: false, admin: false },
  { name: '2 org owner, no explicit -> admin', facts: { projectHasOrg: true, orgRole: 'owner', projectExplicit: null }, view: true, edit: true, admin: true },
  { name: '3 org member, no explicit -> viewer', facts: { projectHasOrg: true, orgRole: 'member', projectExplicit: null }, view: true, edit: false, admin: false },
  { name: '4 solo project, explicit admin', facts: { projectHasOrg: false, orgRole: null, projectExplicit: 'admin' }, view: true, edit: true, admin: true },
  { name: '5 explicit editor caps org owner', facts: { projectHasOrg: true, orgRole: 'owner', projectExplicit: 'editor' }, view: true, edit: true, admin: false },
  { name: '6 solo project, nothing -> no access', facts: { projectHasOrg: false, orgRole: null, projectExplicit: null }, view: false, edit: false, admin: false },
  { name: '7 org admin, no explicit -> admin', facts: { projectHasOrg: true, orgRole: 'admin', projectExplicit: null }, view: true, edit: true, admin: true },
  { name: '8 project has org but user not a member -> no access', facts: { projectHasOrg: true, orgRole: null, projectExplicit: null }, view: false, edit: false, admin: false },
  { name: '9 break-glass: owner + explicit admin -> full', facts: { projectHasOrg: true, orgRole: 'owner', projectExplicit: 'admin' }, view: true, edit: true, admin: true },
];

describe('ReBAC in-process evaluator — ADR-0014 case matrix', () => {
  for (const c of CASES) {
    it(c.name, () => {
      const p = evaluatePermissions(c.facts);
      expect(p.can_view).toBe(c.view);
      expect(p.can_edit).toBe(c.edit);
      expect(p.can_admin).toBe(c.admin);
    });
  }

  it('effectiveRole is consistent with the highest granted permission', () => {
    expect(effectiveRole({ projectHasOrg: true, orgRole: 'owner', projectExplicit: 'viewer' })).toBe('viewer');
    expect(effectiveRole({ projectHasOrg: true, orgRole: 'owner', projectExplicit: null })).toBe('admin');
    expect(effectiveRole({ projectHasOrg: false, orgRole: null, projectExplicit: null })).toBe(null);
  });
});
