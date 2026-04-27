'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { CatalogKpi } from '@/lib/core/catalog-loader';
import { useMemo } from 'react';

interface MetricsTableProps {
  metrics: CatalogKpi[];
  searchQuery: string;
}

export function MetricsTable({ metrics, searchQuery }: MetricsTableProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeDomain = searchParams.get('domain');

  const filtered = useMemo(() => {
    return metrics.filter((m) => {
      // Search filter
      if (
        searchQuery &&
        !(
          m.kpi_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.business.definition.toLowerCase().includes(searchQuery.toLowerCase())
        )
      ) {
        return false;
      }

      // Domain filter
      if (
        activeDomain &&
        (!m.domain_tag || !m.domain_tag.includes(activeDomain))
      ) {
        return false;
      }

      return true;
    });
  }, [metrics, searchQuery, activeDomain]);

  const handleRowClick = (kpiId: string) => {
    router.push(`/detail/kpi/${kpiId}`);
  };

  if (filtered.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 rounded-lg border border-border bg-panel">
        <div className="text-center">
          <p className="text-sm text-foreground-muted mb-2">No metrics found</p>
          {searchQuery && (
            <p className="text-2xs text-foreground-subtle">
              Try adjusting your search or filters
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-panel-subtle">
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Name
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Key
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Type
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Domain
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Owner
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Grain
            </th>
            <th className="px-4 py-2.5 text-left text-2xs font-semibold text-foreground-muted uppercase">
              Updated
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {filtered.map((metric) => (
            <tr
              key={metric.kpi_id}
              onClick={() => handleRowClick(metric.kpi_id)}
              className="hover:bg-hover cursor-pointer transition-colors"
            >
              <td className="px-4 py-3 font-medium text-foreground">
                {metric.kpi_key}
              </td>
              <td className="px-4 py-3 text-2xs font-mono text-foreground-muted">
                {metric.technical.dax_name}
              </td>
              <td className="px-4 py-3 text-xs text-foreground-muted">
                {metric.kpi_type}
              </td>
              <td className="px-4 py-3 text-xs text-foreground-muted">
                {metric.domain_tag?.[0] || '—'}
              </td>
              <td className="px-4 py-3 text-xs text-foreground-muted">
                {metric.governance.business_owner || '—'}
              </td>
              <td className="px-4 py-3 text-xs text-foreground-muted">
                {metric.business.grain_scope || '—'}
              </td>
              <td className="px-4 py-3 text-xs text-foreground-muted">
                {metric.governance.last_review
                  ? new Date(metric.governance.last_review).toLocaleDateString()
                  : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
