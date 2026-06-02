'use client';

import { useRouter } from 'next/navigation';
import type { LibraryRow } from '@/lib/studio/library-rows';

interface EntityTableProps {
  rows: LibraryRow[];
  emptyLabel: string;
}

export function EntityTable({ rows, emptyLabel }: EntityTableProps) {
  const router = useRouter();

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 rounded-lg border border-border bg-panel">
        <p className="text-sm text-foreground-muted">{emptyLabel}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-border bg-panel-subtle">
            <th className="px-6 py-3 text-left text-2xs font-medium text-foreground-muted uppercase tracking-[0.06em]">
              Name
            </th>
            <th className="px-6 py-3 text-left text-2xs font-medium text-foreground-muted uppercase tracking-[0.06em]">
              Id
            </th>
            <th className="px-6 py-3 text-left text-2xs font-medium text-foreground-muted uppercase tracking-[0.06em]">
              Domain
            </th>
            <th className="px-6 py-3 text-left text-2xs font-medium text-foreground-muted uppercase tracking-[0.06em]">
              Meta
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => router.push(row.href)}
              className="border-b border-border last:border-0 cursor-pointer hover:bg-hover transition-colors"
            >
              <td className="px-6 py-3.5 font-medium text-foreground">{row.name}</td>
              <td className="px-6 py-3.5 font-mono text-2xs text-foreground-muted">{row.sub ?? row.id}</td>
              <td className="px-6 py-3.5 text-foreground-muted">{row.domain ?? '—'}</td>
              <td className="px-6 py-3.5 text-foreground-muted">{row.meta ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
