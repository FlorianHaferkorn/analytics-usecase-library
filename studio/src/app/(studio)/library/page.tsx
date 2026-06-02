import { Metadata } from 'next';
import { Suspense } from 'react';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllContracts } from '@/lib/core/contract-loader';
import { LibraryClient } from './library-client';

export const metadata: Metadata = {
  title: 'Library | Studio',
};

export default async function LibraryPage() {
  const [metrics, contracts, actions, useCases] = await Promise.all([
    loadKpiCatalog(),
    loadAllContracts(),
    loadAllActionCodes(),
    loadAllBrackets(),
  ]);

  return (
    <Suspense fallback={<div className="text-foreground-muted text-[13px]">Loading library…</div>}>
      <LibraryClient
        metrics={metrics}
        contracts={contracts}
        actions={actions}
        useCases={useCases}
      />
    </Suspense>
  );
}
