import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { HealthPageClient } from './health-client';

export default function HealthPage() {
  return (
<<<<<<< HEAD
    <StudioPage style={{ gap: 'var(--sp-3)' }}>
=======
    <StudioPage style={{ gap: 'var(--pad)' }}>
>>>>>>> claude/implement-execution-plan-bZbSq
      <StudioPageHeader
        eyebrow="Registry / Health"
        title="Framework Health Scorecard"
        description="H1–H6 metrics measuring Golden Thread coverage, action coverage, TMDL alignment, data readiness, governance maturity, and test coverage."
        badge="Refreshable"
        tone="info"
      />
      <HealthPageClient />
    </StudioPage>
  );
}
