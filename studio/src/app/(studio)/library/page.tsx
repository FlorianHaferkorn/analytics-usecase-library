import { Metadata } from 'next';
import { Suspense } from 'react';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllContracts } from '@/lib/core/contract-loader';
import { LibraryClient } from './library-client';
import Link from 'next/link';
import { CatalogLibrary } from '@/components/registry/catalog-library';
import styles from '@/components/project/project-scope.module.css';

export const metadata: Metadata = {
  title: 'Library | Studio',
};

export default async function LibraryPage({ searchParams }: { searchParams: Promise<{ view?: string; tab?: string; kpi?: string }> }) {
  const query = await searchParams;
  const manage = query.view === 'manage';
  const [metrics, contracts, actions, useCases] = await Promise.all([
    loadKpiCatalog(),
    loadAllContracts(),
    loadAllActionCodes(),
    loadAllBrackets(),
  ]);

  return (
    <Suspense fallback={<div className="text-foreground-muted text-[13px]">Loading library…</div>}>
      <nav className={styles.scope} aria-label="Library tools"><Link href="/library" aria-current={!manage ? 'page' : undefined}>Browse assets</Link><Link href="/library?view=manage" aria-current={manage ? 'page' : undefined}>Manage definitions</Link></nav>
      {manage ? <CatalogLibrary kpis={metrics} brackets={useCases} actions={actions} highlightKpiId={query.kpi ?? null} initialTab={query.tab ?? 'kpis'} /> : <LibraryClient
        metrics={metrics}
        contracts={contracts}
        actions={actions}
        useCases={useCases}
      />}
    </Suspense>
  );
}
