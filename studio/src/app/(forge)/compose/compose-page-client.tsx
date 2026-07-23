'use client';

import { SimulatorClient } from '@/app/(studio)/simulator/simulator-client';
import { PendingDraftBanner } from '@/components/ui/pending-draft-banner';
import { ForgePageSkeleton } from '@/components/forge/forge-page-skeleton';
import { useForgeBootstrapContext } from '@/components/providers/forge-bootstrap-provider';

export function ComposePageClient() {
  const { data, loading, error } = useForgeBootstrapContext();

  if (loading && !data) {
    return <ForgePageSkeleton title="Compose" />;
  }

  if (error || !data) {
    return (
      <div style={{ color: 'var(--danger)' }}>
        {error ?? 'Forge data unavailable. Refresh the page or sign in again.'}
      </div>
    );
  }

  const bracketSummaries = data.brackets.map((bracket) => ({
    id: bracket.id,
    title: bracket.title,
    domain: bracket.domain,
    formula: bracket.formula,
    impactDirection: bracket.impactDirection,
    primaryDriver: bracket.primaryDriver,
    strategicKpiId: bracket.strategicKpiId,
    influencingKpiIds: bracket.influencingKpiIds,
    impactLogic: bracket.impactLogic,
  }));

  return (
    <>
      <PendingDraftBanner />
      <SimulatorClient
        brackets={bracketSummaries}
        spines={data.spines}
        auroraKpis={data.auroraKpis}
        auroraLinked={data.auroraLinked}
      />
    </>
  );
}
