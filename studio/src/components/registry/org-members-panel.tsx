'use client';

/**
 * Org members list + add-member form (ADR-0014, I-9.2/O-3).
 *
 * Extracted out of organizations-client.tsx to keep that file under the
 * repo's 300-line-per-component convention (studio/CLAUDE.md) once the O-3
 * business-role display/edit surface was added.
 *
 * O-3: business_role_id is a purely display-only link to
 * core/organization/org_roles.yaml (RoleChip, same component the bracket
 * owner_role/steward_role fields already use) — it never affects RBAC.
 */

import { useEffect, useState } from 'react';
import { StudioButton, StudioPanel } from '@/components/ui/studio-page';
import { StudioFormField, StudioFormGrid, StudioInlineStat, StudioInput, StudioSelect } from '@/components/ui/studio-data';
import { RoleChip } from '@/components/ui/role-chip';
import type { ResolvedRole } from '@/lib/core/org-role-loader';

export interface OrgMemberRow {
  user_id: string;
  org_id: string;
  org_role: 'owner' | 'admin' | 'member';
  business_role_id: string | null;
  email: string;
  name: string;
  created_at: string;
}

interface Props {
  orgId: string;
  members: OrgMemberRow[];
  onChanged: () => void;
}

export function OrgMembersPanel({ orgId, members, onChanged }: Props) {
  const [roles, setRoles] = useState<Map<string, ResolvedRole>>(new Map());
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState<'owner' | 'admin' | 'member'>('member');
  const [memberBusinessRoleId, setMemberBusinessRoleId] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/core/roles')
      .then((res) => res.json())
      .then((json: { roles: ResolvedRole[] }) => {
        setRoles(new Map(json.roles.map((r) => [r.id, r])));
      })
      .catch(() => {});
  }, []);

  async function addMember() {
    if (!memberEmail.trim()) return;
    setError(null);
    const res = await fetch(`/api/org/${orgId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: memberEmail.trim(),
        orgRole: memberRole,
        businessRoleId: memberBusinessRoleId || null,
      }),
    });
    if (res.ok) {
      setMemberEmail('');
      setMemberBusinessRoleId('');
      onChanged();
    } else {
      const json = await res.json();
      setError(json.error?.message ?? 'Failed to add member');
    }
  }

  async function removeMember(email: string) {
    const res = await fetch(`/api/org/${orgId}/members?email=${encodeURIComponent(email)}`, { method: 'DELETE' });
    if (res.ok) onChanged();
  }

  async function updateBusinessRole(email: string, businessRoleId: string) {
    const res = await fetch(`/api/org/${orgId}/members`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, businessRoleId: businessRoleId || null }),
    });
    if (res.ok) onChanged();
  }

  const roleOptions = [...roles.values()].sort((a, b) => a.title.localeCompare(b.title));

  return (
    <StudioPanel title="Members" description="Org role only grants project access as a fallback when no explicit project role is set (never overrides one). Business role is display-only.">
      {error && <StudioInlineStat>{error}</StudioInlineStat>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {members.map((m) => (
          <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', padding: '6px 8px', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', minWidth: 0 }}>
              <span style={{ fontSize: '0.8125rem' }}>{m.name} <span style={{ color: 'var(--ink-4)' }}>({m.email})</span> — {m.org_role}</span>
              {m.business_role_id && <RoleChip roleId={m.business_role_id} resolved={roles.get(m.business_role_id)} />}
            </div>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
              <StudioSelect
                value={m.business_role_id ?? ''}
                onChange={(e) => updateBusinessRole(m.email, e.target.value)}
                style={{ fontSize: '0.75rem' }}
              >
                <option value="">No business role</option>
                {roleOptions.map((r) => (
                  <option key={r.id} value={r.id}>{r.title}</option>
                ))}
              </StudioSelect>
              <StudioButton onClick={() => removeMember(m.email)} variant="ghost">Remove</StudioButton>
            </div>
          </div>
        ))}
        {members.length === 0 && <StudioInlineStat>No members yet.</StudioInlineStat>}
      </div>
      <StudioFormGrid columns="2fr 1fr 2fr auto">
        <StudioFormField label="Email"><StudioInput value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} placeholder="user@example.com" /></StudioFormField>
        <StudioFormField label="Role">
          <StudioSelect value={memberRole} onChange={(e) => setMemberRole(e.target.value as typeof memberRole)}>
            <option value="member">member</option>
            <option value="admin">admin</option>
            <option value="owner">owner</option>
          </StudioSelect>
        </StudioFormField>
        <StudioFormField label="Business role (optional)">
          <StudioSelect value={memberBusinessRoleId} onChange={(e) => setMemberBusinessRoleId(e.target.value)}>
            <option value="">None</option>
            {roleOptions.map((r) => (
              <option key={r.id} value={r.id}>{r.title}</option>
            ))}
          </StudioSelect>
        </StudioFormField>
        <StudioFormField label=" "><StudioButton onClick={addMember} tone="success" variant="primary">Add</StudioButton></StudioFormField>
      </StudioFormGrid>
    </StudioPanel>
  );
}
