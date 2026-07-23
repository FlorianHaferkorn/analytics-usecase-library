import { cache } from 'react';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { domainRoot } from '@/lib/studio/domain-filter';

export interface DomainStatRow {
  name: string;
  count: number;
}

/** Sidebar domain counts from use-case bracket roots (matches Forge filter keys). */
export const buildDomainStats = cache(async (): Promise<DomainStatRow[]> => {
  const brackets = await loadAllBrackets().catch(() => []);
  const counts = new Map<string, number>();

  for (const bracket of brackets) {
    const label = domainRoot(bracket.domain);
    if (!label) continue;
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([name, count]) => ({ name, count }));
});
