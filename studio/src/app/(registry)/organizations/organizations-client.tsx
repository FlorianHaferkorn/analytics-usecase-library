'use client';

/**
 * Minimal org management UI (ADR-0014, I-9.2) — create an org, add/remove
 * members with an org role, assign/unassign projects. Deliberately not wired
 * into navigation/ProjectSwitcher — proving the model works doesn't require
 * changing the primary nav UX, and that's explicitly deferred (ADR-0014 O-1
 * covers the real invitation/onboarding flow).
 */

import { useEffect, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioFormField, StudioFormGrid, StudioInlineStat, StudioInput, StudioSelect } from '@/components/ui/studio-data';

interface OrgSummary {
  id: string;
  name: string;
  created_at: string;
}

interface ProjectSummary {
  id: string;
  name: string;
  org_id: string | null;
}

interface OrgMemberRow {
  user_id: string;
  org_id: string;
  org_role: 'owner' | 'admin' | 'member';
  created_at: string;
}

interface OrgDetail {
  organization: OrgSummary;
  members: OrgMemberRow[];
  projects: Array<{ id: string; name: string }>;
}

interface Props {
  initialOrganizations: OrgSummary[];
  projects: ProjectSummary[];
}

export function OrganizationsClient({ initialOrganizations, projects }: Props) {
  const [organizations, setOrganizations] = useState(initialOrganizations);
  const [selectedId, setSelectedId] = useState<string | null>(initialOrganizations[0]?.id ?? null);
  const [detail, setDetail] = useState<OrgDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newOrgName, setNewOrgName] = useState('');
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState<'owner' | 'admin' | 'member'>('member');
  const [assignProjectId, setAssignProjectId] = useState('');

  async function loadDetail(orgId: string) {
    setError(null);
    const res = await fetch(`/api/org/${orgId}`);
    const json = await res.json() as OrgDetail & { error?: { message?: string } };
    if (!res.ok) {
      setError(json.error?.message ?? `HTTP ${res.status}`);
      setDetail(null);
      return;
    }
    setDetail(json);
  }

  useEffect(() => {
    if (selectedId) loadDetail(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  async function createOrg() {
    if (!newOrgName.trim()) return;
    const res = await fetch('/api/org', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newOrgName.trim() }),
    });
    if (res.ok) {
      const { organization } = await res.json();
      setOrganizations((prev) => [organization, ...prev]);
      setSelectedId(organization.id);
      setNewOrgName('');
    }
  }

  async function addMember() {
    if (!selectedId || !memberEmail.trim()) return;
    const res = await fetch(`/api/org/${selectedId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: memberEmail.trim(), orgRole: memberRole }),
    });
    if (res.ok) {
      setMemberEmail('');
      loadDetail(selectedId);
    } else {
      const json = await res.json();
      setError(json.error?.message ?? 'Failed to add member');
    }
  }

  async function removeMember(email: string) {
    if (!selectedId) return;
    const res = await fetch(`/api/org/${selectedId}/members?email=${encodeURIComponent(email)}`, { method: 'DELETE' });
    if (res.ok) loadDetail(selectedId);
  }

  async function assignProject() {
    if (!selectedId || !assignProjectId) return;
    const res = await fetch(`/api/org/${selectedId}/assign-project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projectId: assignProjectId }),
    });
    if (res.ok) {
      setAssignProjectId('');
      loadDetail(selectedId);
    }
  }

  async function unassignProject(projectId: string) {
    if (!selectedId) return;
    const res = await fetch(`/api/org/${selectedId}/assign-project?projectId=${encodeURIComponent(projectId)}`, { method: 'DELETE' });
    if (res.ok) loadDetail(selectedId);
  }

  const unassignedProjects = projects.filter((p) => p.org_id !== selectedId);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 'var(--pad)', alignItems: 'start' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <StudioPanel title="Organizations" description="Optional grouping over projects.">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {organizations.map((org) => (
              <StudioButton
                key={org.id}
                onClick={() => setSelectedId(org.id)}
                variant="ghost"
                style={{
                  justifyContent: 'flex-start',
                  backgroundColor: org.id === selectedId ? 'var(--bg-2)' : 'transparent',
                  border: `1px solid ${org.id === selectedId ? 'var(--accent)' : 'transparent'}`,
                }}
              >
                {org.name}
              </StudioButton>
            ))}
            {organizations.length === 0 && <StudioInlineStat>No organizations yet.</StudioInlineStat>}
          </div>
          <div style={{ display: 'flex', gap: '4px', marginTop: '12px' }}>
            <StudioInput
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && createOrg()}
              placeholder="New org name..."
            />
            <StudioButton onClick={createOrg} tone="success" variant="primary">Create</StudioButton>
          </div>
        </StudioPanel>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {error && <StudioInlineStat>{error}</StudioInlineStat>}
        {!detail ? (
          <StudioEmptyState title="No organization selected" description="Select or create an organization to manage its members and projects." />
        ) : (
          <>
            <StudioPanel title={detail.organization.name} description={`Created ${detail.organization.created_at}`}>
              <StudioInlineStat>{detail.members.length} member{detail.members.length === 1 ? '' : 's'} · {detail.projects.length} project{detail.projects.length === 1 ? '' : 's'}</StudioInlineStat>
            </StudioPanel>

            <StudioPanel title="Members" description="Org role only grants project access as a fallback when no explicit project role is set (never overrides one).">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {detail.members.map((m) => (
                  <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.8125rem' }}>{m.user_id} — {m.org_role}</span>
                  </div>
                ))}
                {detail.members.length === 0 && <StudioInlineStat>No members yet.</StudioInlineStat>}
              </div>
              <StudioFormGrid columns="2fr 1fr auto">
                <StudioFormField label="Email"><StudioInput value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} placeholder="user@example.com" /></StudioFormField>
                <StudioFormField label="Role">
                  <StudioSelect value={memberRole} onChange={(e) => setMemberRole(e.target.value as typeof memberRole)}>
                    <option value="member">member</option>
                    <option value="admin">admin</option>
                    <option value="owner">owner</option>
                  </StudioSelect>
                </StudioFormField>
                <StudioFormField label=" "><StudioButton onClick={addMember} tone="success" variant="primary">Add</StudioButton></StudioFormField>
              </StudioFormGrid>
            </StudioPanel>

            <StudioPanel title="Projects" description="Assigning a project here does not change its existing project_members rows (ADR-0014: sticky, no silent migration).">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {detail.projects.map((p) => (
                  <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '0.8125rem' }}>{p.name}</span>
                    <StudioButton onClick={() => unassignProject(p.id)} variant="ghost">Unassign</StudioButton>
                  </div>
                ))}
                {detail.projects.length === 0 && <StudioInlineStat>No projects assigned — this org groups no projects yet.</StudioInlineStat>}
              </div>
              <StudioFormGrid columns="2fr auto">
                <StudioFormField label="Project">
                  <StudioSelect value={assignProjectId} onChange={(e) => setAssignProjectId(e.target.value)}>
                    <option value="">Select a project...</option>
                    {unassignedProjects.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}{p.org_id ? ' (in another org)' : ''}</option>
                    ))}
                  </StudioSelect>
                </StudioFormField>
                <StudioFormField label=" "><StudioButton onClick={assignProject} disabled={!assignProjectId} tone="success" variant="primary">Assign</StudioButton></StudioFormField>
              </StudioFormGrid>
            </StudioPanel>
          </>
        )}
      </div>
    </div>
  );
}
