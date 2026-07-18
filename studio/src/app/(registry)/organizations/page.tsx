import { listOrganizations } from '@/lib/db/org-repo';
import { listProjects } from '@/lib/db/project-repo';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { OrganizationsClient } from './organizations-client';

export default async function OrganizationsPage() {
  const organizations = listOrganizations();
  const projects = listProjects().map((p) => ({ id: p.id, name: p.name, org_id: p.org_id }));

  return (
    <StudioPage style={{ gap: 'var(--pad)' }}>
      <StudioPageHeader
        eyebrow="Registry / Organizations"
        title="Organizations"
        description="Optional grouping layer over projects (ADR-0014) — no organization configured behaves exactly like today's solo mode; this is opt-in, not a new requirement."
        badge={`${organizations.length} org${organizations.length === 1 ? '' : 's'}`}
        tone="info"
      />
      <OrganizationsClient initialOrganizations={organizations} projects={projects} />
    </StudioPage>
  );
}
