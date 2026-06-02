'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { CatalogKpi } from '@/lib/core/catalog-loader';
import type { ActionCodeDefinitionV20AIMirror, DataContract, UseCaseBracketV20Lean } from '@/lib/schemas';
import { LibraryTabs } from '@/components/library/LibraryTabs';
import { MetricsTable } from '@/components/library/MetricsTable';
import { EntityTable } from '@/components/library/EntityTable';
import {
  actionRows,
  dimensionRows,
  filterLibraryRows,
  sourceRows,
  useCaseRows,
} from '@/lib/studio/library-rows';

interface LibraryClientProps {
  metrics: CatalogKpi[];
  contracts: DataContract[];
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
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') ?? '');

  // Canonical tab slug per DETAIL_IA.md; accept legacy ?tab=metrics from mockups.
  const tabParam = searchParams.get('tab');
  const activeTab = tabParam === 'metrics' ? 'kpis' : tabParam || 'kpis';
  const activeDomain = searchParams.get('domain');

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

  const dimRows = useMemo(
    () => filterLibraryRows(dimensionRows(contracts), searchQuery, activeDomain),
    [contracts, searchQuery, activeDomain],
  );
  const srcRows = useMemo(
    () => filterLibraryRows(sourceRows(contracts), searchQuery, activeDomain),
    [contracts, searchQuery, activeDomain],
  );
  const actRows = useMemo(
    () => filterLibraryRows(actionRows(actions), searchQuery, activeDomain),
    [actions, searchQuery, activeDomain],
  );
  const ucRows = useMemo(
    () => filterLibraryRows(useCaseRows(useCases), searchQuery, activeDomain),
    [useCases, searchQuery, activeDomain],
  );

  const tabs = [
    { id: 'kpis', label: 'Metrics', count: metrics.length },
    { id: 'dimensions', label: 'Dimensions', count: dimensionRows(contracts).length },
    { id: 'sources', label: 'Sources', count: contracts.length },
    { id: 'actions', label: 'Action Codes', count: actions.length },
    { id: 'usecases', label: 'Use Cases', count: useCases.length },
  ];

  const handleClearDomainFilter = () => {
    const current = new URLSearchParams(searchParams.toString());
    current.delete('domain');
    window.history.pushState(null, '', `?${current.toString()}`);
    window.location.reload();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-end justify-between mb-5">
        <div>
          <h1 className="text-[28px] font-medium tracking-[-0.02em] text-foreground mb-1">Library</h1>
          <p className="text-[13px] text-foreground-muted">
            Governed KPIs, dimensions, sources, action codes, and use cases.
          </p>
        </div>
      </div>

      <LibraryTabs tabs={tabs} activeTab={activeTab} />

      <div className="flex gap-2 mb-[14px] items-center">
        <div className="flex-1 flex items-center gap-2.5 px-3 py-2 rounded-lg border border-border bg-panel">
          <svg
            width="13"
            height="13"
            viewBox="0 0 13 13"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            aria-hidden
          >
            <circle cx="5" cy="5" r="4" />
            <line x1="8.5" y1="8.5" x2="12" y2="12" />
          </svg>
          <input
            id="library-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${activeTab}…`}
            className="flex-1 bg-transparent text-[13px] text-foreground outline-none"
          />
          <span className="text-2xs font-mono text-foreground-muted opacity-50">/</span>
        </div>

        {activeDomain && (
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-hover border border-border text-xs">
            <span className="text-foreground-muted">Domain:</span>
            <span className="font-medium text-foreground">{activeDomain}</span>
            <button
              type="button"
              onClick={handleClearDomainFilter}
              className="ml-1 text-foreground-muted hover:text-foreground"
              aria-label="Clear domain filter"
            >
              ×
            </button>
          </div>
        )}
      </div>

      <div className="flex-1">
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
    </div>
  );
}
