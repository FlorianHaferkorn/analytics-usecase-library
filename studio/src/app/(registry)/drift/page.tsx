import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { DriftPageClient } from './drift-client';
import { runDriftScan } from '@/lib/validation/drift-scanner';

export default async function DriftPage() {
  const report = await runDriftScan();
  const issueCount = report.issues.length;

  return (
<<<<<<< HEAD
    <StudioPage style={{ gap: 'var(--sp-3)' }}>
=======
    <StudioPage style={{ gap: 'var(--pad)' }}>
>>>>>>> claude/implement-execution-plan-bZbSq
      <StudioPageHeader
        eyebrow="Registry / Drift"
        title="Catalog ↔ TMDL Drift"
        description="Detects divergence between KPI catalog definitions and TMDL measure implementations. Zero issues = green main."
        badge={issueCount === 0 ? 'Green — no drift' : `${issueCount} issue${issueCount === 1 ? '' : 's'}`}
        tone={issueCount === 0 ? 'success' : report.counts.error > 0 ? 'warning' : 'info'}
      />
      <DriftPageClient initialReport={report} />
    </StudioPage>
  );
}
