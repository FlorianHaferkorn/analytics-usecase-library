'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { CatalogKpi } from '@/lib/core/catalog-loader';
import { LibraryTabs } from '@/components/library/LibraryTabs';
import { MetricsTable } from '@/components/library/MetricsTable';

interface LibraryClientProps {
  metrics: CatalogKpi[];
}

export function LibraryClient({ metrics }: LibraryClientProps) {
  const searchParams = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');

  const activeTab = searchParams.get('tab') || 'metrics';
  const activeDomain = searchParams.get('domain');

  // Handle "/" hotkey for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only trigger if not in input/textarea
      if (
        e.key === '/' &&
        !(
          document.activeElement?.tagName === 'INPUT' ||
          document.activeElement?.tagName === 'TEXTAREA'
        )
      ) {
        e.preventDefault();
        const searchInput = document.getElementById('library-search') as HTMLInputElement;
        searchInput?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const tabs = [
    { id: 'metrics', label: 'Metrics', count: metrics.length },
    { id: 'dimensions', label: 'Dimensions', count: 0 },
    { id: 'sources', label: 'Sources', count: 0 },
  ];

  const handleClearDomainFilter = () => {
    const current = new URLSearchParams(searchParams);
    current.delete('domain');
    window.history.pushState(null, '', `?${current.toString()}`);
    window.location.reload();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-end justify-between mb-5">
        <div>
          <h1 className="text-[28px] font-medium tracking-[-0.02em] text-foreground mb-1">Library</h1>
          <p className="text-[13px] text-foreground-muted">
            The single source of truth for every metric, dimension and source.
          </p>
        </div>
        <button className="px-3.5 py-2 flex items-center gap-2 rounded-lg bg-foreground text-background text-[13px] font-medium hover:opacity-90 transition-opacity">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <line x1="7" y1="1" x2="7" y2="13" />
            <line x1="1" y1="7" x2="13" y2="7" />
          </svg>
          New metric
        </button>
      </div>

      {/* Tabs */}
      <LibraryTabs tabs={tabs} activeTab={activeTab} />

      {/* Filters */}
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
              onClick={handleClearDomainFilter}
              className="ml-1 text-foreground-muted hover:text-foreground inline-flex items-center"
              title="Clear filter"
              aria-label="Clear filter"
            >
              <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="m4 4 8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1">
        {activeTab === 'metrics' && (
          <MetricsTable metrics={metrics} searchQuery={searchQuery} />
        )}

        {activeTab === 'dimensions' && (
          <div className="flex items-center justify-center py-16 rounded-lg border border-border bg-panel">
            <div className="text-center">
              <p className="text-sm font-medium text-foreground mb-1">Dimensions</p>
              <p className="text-2xs text-foreground-muted">Coming in Phase 2</p>
            </div>
          </div>
        )}

        {activeTab === 'sources' && (
          <div className="flex items-center justify-center py-16 rounded-lg border border-border bg-panel">
            <div className="text-center">
              <p className="text-sm font-medium text-foreground mb-1">Data Sources</p>
              <p className="text-2xs text-foreground-muted">Coming in Phase 2</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
