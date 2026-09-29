'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import type { CatalogKpi } from '@/lib/core/catalog-types';
import type { ActionCodeDefinitionV20AIMirror, UseCaseBracketV20Lean } from '@/lib/schemas';
import type { ResolvedContract } from '@/lib/core/contract-loader';
import { LibraryTabs } from '@/components/library/LibraryTabs';
import { MetricsTable } from '@/components/library/MetricsTable';
import { EntityTable } from '@/components/library/EntityTable';
import { StudioInput } from '@/components/ui/studio-data';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import {
  actionRows,
  dimensionRows,
  filterLibraryRows,
  sourceRows,
  useCaseRows as buildUseCaseRows,
} from '@/lib/studio/library-rows';

interface LibraryClientProps {
  metrics: CatalogKpi[];
  contracts: ResolvedContract[];
  actions: ActionCodeDefinitionV20AIMirror[];
  useCases: UseCaseBracketV20Lean[];
}

export function LibraryClient({
  metrics,
  contracts,
  actions,
  useCases,
}: LibraryClientProps) {
  const searchParams = useSearchParams();
  const { domainFilter, clearDomainFilter } = useDomainFilter();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') ?? '');
  const [activeTab, setActiveTab] = useState(() => {
    const tabParam = searchParams.get('tab');
    return tabParam === 'metrics' ? 'kpis' : tabParam || 'kpis';
  });

  useEffect(() => {
    const syncFromUrl = () => {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');
      setActiveTab(tabParam === 'metrics' ? 'kpis' : tabParam || 'kpis');
    };
    window.addEventListener('popstate', syncFromUrl);
    return () => window.removeEventListener('popstate', syncFromUrl);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        !(document.activeElement instanceof HTMLInputElement) &&
        !(document.activeElement instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault();
        (document.getElementById('library-search') as HTMLInputElement)?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const dimRowsBase = useMemo(() => dimensionRows(contracts), [contracts]);
  const srcRowsBase = useMemo(() => sourceRows(contracts), [contracts]);
  const actRowsBase = useMemo(() => actionRows(actions), [actions]);
  const ucRowsBase = buildUseCaseRows(useCases);

  const dimRows = useMemo(
    () => filterLibraryRows(dimRowsBase, searchQuery, domainFilter),
    [dimRowsBase, searchQuery, domainFilter],
  );
  const srcRows = useMemo(
    () => filterLibraryRows(srcRowsBase, searchQuery, domainFilter),
    [srcRowsBase, searchQuery, domainFilter],
  );
  const actRows = useMemo(
    () => filterLibraryRows(actRowsBase, searchQuery, domainFilter),
    [actRowsBase, searchQuery, domainFilter],
  );
  const ucRows = useMemo(
    () => filterLibraryRows(ucRowsBase, searchQuery, domainFilter),
    [ucRowsBase, searchQuery, domainFilter],
  );

  const tabs = [
    { id: 'kpis', label: 'Metrics', count: metrics.length },
    { id: 'dimensions', label: 'Dimensions', count: dimensionRows(contracts).length },
    { id: 'sources', label: 'Sources', count: contracts.length },
    { id: 'actions', label: 'Action Codes', count: actions.length },
    { id: 'usecases', label: 'Use Cases', count: useCases.length },
  ];

  const handleClearDomainFilter = () => {
    clearDomainFilter();
  };

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Forge / Library"
        title="Library"
        description="Governed KPIs, dimensions, sources, action codes, and use cases — browse and open detail without leaving the Forge tools surface."
        badge={`${metrics.length} KPIs`}
        tone="info"
      />

      <LibraryTabs tabs={tabs} activeTab={activeTab} />

      <div style={{ display: 'flex', gap: 8, marginBottom: 14, alignItems: 'center' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10 }}>
          <StudioInput
            id="library-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${activeTab}…`}
            style={{ flex: 1, fontSize: 13 }}
          />
          <span style={{ fontSize: 'var(--text-2xs)', fontFamily: 'var(--font-mono)', color: 'var(--ink-4)', opacity: 0.75 }}>/</span>
        </div>

        {domainFilter && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 10px', borderRadius: 'var(--radius-md)',
            background: 'var(--hover)', border: '1px solid var(--line)', fontSize: 12,
          }}>
            <span style={{ color: 'var(--ink-3)' }}>Domain:</span>
            <span style={{ fontWeight: 500, color: 'var(--ink)' }}>{domainFilter}</span>
            <button
              type="button"
              onClick={handleClearDomainFilter}
              style={{ marginLeft: 4, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-3)' }}
              aria-label="Clear domain filter"
            >
              ×
            </button>
          </div>
        )}
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        {activeTab === 'kpis' && (
          <MetricsTable metrics={metrics} searchQuery={searchQuery} />
        )}
        {activeTab === 'dimensions' && (
          <EntityTable rows={dimRows} emptyLabel="No dimensions match your filters." />
        )}
        {activeTab === 'sources' && (
          <EntityTable rows={srcRows} emptyLabel="No data sources match your filters." />
        )}
        {activeTab === 'actions' && (
          <EntityTable rows={actRows} emptyLabel="No action codes match your filters." />
        )}
        {activeTab === 'usecases' && (
          <EntityTable rows={ucRows} emptyLabel="No use cases match your filters." />
        )}
      </div>
    </StudioPage>
  );
}
