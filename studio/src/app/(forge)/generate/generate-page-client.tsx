'use client';

import { DeliveryClient } from '@/app/(studio)/delivery/delivery-client';
import { ForgePageSkeleton } from '@/components/forge/forge-page-skeleton';
import { useForgeBootstrapContext } from '@/components/providers/forge-bootstrap-provider';

export function GeneratePageClient() {
  const { data, loading, error } = useForgeBootstrapContext();

  if (loading && !data) {
    return <ForgePageSkeleton title="Generate" />;
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
    kpiCount:
      1 + bracket.influencingKpiIds.length + (bracket.supportingKpiIds?.length ?? 0),
    actionCount: bracket.actionCodeIds.length,
  }));

  return <DeliveryClient brackets={bracketSummaries} />;
}
