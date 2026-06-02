import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';
import type { DataContract } from '@/lib/schemas';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { detailPath } from '@/lib/studio/entity-ia';

export interface LibraryRow {
  id: string;
  name: string;
  sub?: string;
  domain?: string;
  meta?: string;
  href: string;
}

export function kpiRows(kpis: CatalogKpi[]): LibraryRow[] {
  return kpis.map((k) => ({
    id: k.kpi_id,
    name: k.kpi_key,
    sub: k.kpi_id,
    domain: k.domain_tag?.[0],
    meta: k.kpi_type,
    href: detailPath('kpi', k.kpi_id),
  }));
}

export function dimensionRows(contracts: DataContract[]): LibraryRow[] {
  const rows: LibraryRow[] = [];
  for (const c of contracts) {
    for (const dim of c.dimension ?? []) {
      rows.push({
        id: `${c.domain}:${dim.name}`,
        name: dim.name,
        sub: `${dim.columns.length} columns`,
        domain: c.domain,
        meta: 'Dimension',
        href: detailPath('contract', c.domain),
      });
    }
  }
  return rows.sort((a, b) => a.name.localeCompare(b.name));
}

export function sourceRows(contracts: DataContract[]): LibraryRow[] {
  return contracts.map((c) => ({
    id: c.domain,
    name: c.domain,
    sub: `v${c.version}`,
    domain: c.domain,
    meta: c.owner,
    href: detailPath('contract', c.domain),
  }));
}

export function actionRows(actions: ActionCodeDefinitionV20AIMirror[]): LibraryRow[] {
  return actions.map((a) => ({
    id: a.id,
    name: a.name,
    sub: a.id,
    domain: a.owner_domain,
    meta: a.status,
    href: detailPath('action', a.id),
  }));
}

export function useCaseRows(brackets: UseCaseBracketV20Lean[]): LibraryRow[] {
  return brackets.map((b) => ({
    id: b.id,
    name: b.title,
    sub: b.id,
    domain: b.domain,
    meta: b.orchestration.strategic_kpi_id,
    href: detailPath('usecase', b.id),
  }));
}

export function filterLibraryRows(rows: LibraryRow[], query: string, domain?: string | null): LibraryRow[] {
  const q = query.trim().toLowerCase();
  return rows.filter((r) => {
    if (domain && r.domain && r.domain !== domain) return false;
    if (!q) return true;
    return (
      r.id.toLowerCase().includes(q) ||
      r.name.toLowerCase().includes(q) ||
      (r.sub?.toLowerCase().includes(q) ?? false) ||
      (r.meta?.toLowerCase().includes(q) ?? false)
    );
  });
}
