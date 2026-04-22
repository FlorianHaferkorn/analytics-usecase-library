'use client';

import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import { StudioInput, StudioInlineStat, StudioTableCell } from '@/components/ui/studio-data';

interface Props {
  kpis: CatalogKpi[];
  pageSize?: number;
}

/**
 * Virtualized KPI list — renders only visible items using IntersectionObserver.
 * Used when KPI count > 50 for smooth scroll performance without external deps.
 */
export function KpiRegistryVirtual({ kpis, pageSize = 50 }: Props) {
  const [visibleCount, setVisibleCount] = useState(pageSize);
  const [filter, setFilter] = useState('');
  const sentinelRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(() => {
    if (!filter) return kpis;
    const q = filter.toLowerCase();
    return kpis.filter(
      (k) =>
        k.kpi_id.toLowerCase().includes(q) ||
        k.kpi_key.toLowerCase().includes(q) ||
        k.business?.purpose?.toLowerCase().includes(q),
    );
  }, [kpis, filter]);

  const visible = useMemo(
    () => filtered.slice(0, visibleCount),
    [filtered, visibleCount],
  );

  const loadMore = useCallback(() => {
    if (visibleCount < filtered.length) {
      setVisibleCount((prev) => Math.min(prev + pageSize, filtered.length));
    }
  }, [visibleCount, filtered.length, pageSize]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) loadMore();
      },
      { rootMargin: '200px' },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  // Reset visible count when filter changes
  useEffect(() => {
    setVisibleCount(pageSize);
  }, [filter, pageSize]);

  return (
    <div>
      <StudioInput
        type="text"
        placeholder="Search KPIs..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{
          padding: '8px 12px',
          fontSize: '0.8125rem',
          marginBottom: 'var(--sp-1)',
        }}
      />

      <div style={{ maxHeight: '600px', overflow: 'auto' }}>
        {visible.map((kpi) => (
          <div
            key={kpi.kpi_id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--sp-1)',
              padding: '8px 12px',
              borderBottom: '1px solid var(--line)',
            }}
          >
            <StudioTableCell style={{ fontFamily: 'var(--font-mono)', color: 'var(--mint)', fontSize: '0.75rem', minWidth: '200px', borderTop: 'none', padding: 0 }}>
              {kpi.kpi_id}
            </StudioTableCell>
            <StudioTableCell style={{ color: 'var(--ink)', flex: 1, borderTop: 'none', padding: 0 }}>
              {kpi.kpi_key}
            </StudioTableCell>
            <StudioTableCell style={{ color: 'var(--ink-3)', fontSize: '0.75rem', borderTop: 'none', padding: 0 }}>
              {(kpi.domain_tag ?? []).join(', ')}
            </StudioTableCell>
          </div>
        ))}

        {visibleCount < filtered.length && (
          <div ref={sentinelRef} style={{ height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--ink-4)' }}>
              Loading more... ({visible.length} of {filtered.length})
            </span>
          </div>
        )}
      </div>

      <StudioInlineStat>
        Showing {visible.length} of {filtered.length} KPIs
      </StudioInlineStat>
    </div>
  );
}
