import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { ApprovalsClient } from './approvals-client';

export default async function ApprovalsPage() {
  const brackets = await loadAllBrackets();
  const bracketList = brackets.map((b) => ({
    id: b.id,
    title: b.title,
    domain: b.domain,
  }));

  return (
    <StudioPage style={{ gap: 'var(--pad)' }}>
      <StudioPageHeader
        eyebrow="Registry / Approvals"
        title="Governance Approvals"
        description="Review, approve, and manage the lifecycle of use case brackets. Select a bracket to inspect its governance state and review comments."
        badge={`${brackets.length} bracket${brackets.length === 1 ? '' : 's'}`}
        tone="info"
      />
      <ApprovalsClient brackets={bracketList} />
    </StudioPage>
  );
}
