import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { bracketDetailPath, type PaletteEntityKind } from '@/lib/studio/entity-ia';

export interface ShellPaletteItem {
  kind: 'kpi' | 'usecase' | 'action';
  id: string;
  label: string;
  sub: string;
  href: string;
}

function detailPath(kind: PaletteEntityKind, id: string): string {
  return `/detail/${kind}/${encodeURIComponent(id)}`;
}

/** Server-side palette entities for Command Palette (DETAIL_IA.md). */
export async function buildShellPaletteItems(): Promise<ShellPaletteItem[]> {
  const [kpis, brackets, actions] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
  ]);

  return [
    ...kpis.map((k) => ({
      kind: 'kpi' as const,
      id: k.kpi_id,
      label: k.kpi_key,
      sub: k.domain_tag?.[0] ?? 'kpi',
      href: detailPath('kpi', k.kpi_id),
    })),
    ...brackets.map((b) => ({
      kind: 'usecase' as const,
      id: b.id,
      label: b.title,
      sub: 'use case',
      href: bracketDetailPath(b.id),
    })),
    ...actions.map((a) => ({
      kind: 'action' as const,
      id: a.id,
      label: a.name ?? a.id,
      sub: 'action',
      href: detailPath('action', a.id),
    })),
  ];
}
