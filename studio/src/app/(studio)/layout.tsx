import { Suspense } from 'react';
import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';
import { GlobalOverlays, type GlobalOverlaysProps } from '@/components/ui/global-overlays';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { type SerializablePaletteItem } from '@/components/ui/command-palette';

export interface DomainStat {
  name: string;
  count: number;
  hue: number;
}

const DOMAIN_HUES: Record<string, number> = {
  revenue: 250, growth: 150, product: 310,
  retention: 30, operations: 130, finance: 200,
  marketing: 60, customer: 350,
};

export default async function StudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [kpis, brackets, actions] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
  ]);

  // Build domain stats from KPI domain_tag
  const domainMap = new Map<string, number>();
  kpis.forEach((k) => {
    const d = k.domain_tag?.[0] ?? 'other';
    domainMap.set(d, (domainMap.get(d) ?? 0) + 1);
  });
  const domains: DomainStat[] = Array.from(domainMap).map(([name, count], i) => ({
    name,
    count,
    hue: DOMAIN_HUES[name] ?? 200 + i * 50,
  }));

  const paletteItems: SerializablePaletteItem[] = [
    ...kpis.map((k) => ({
      kind: 'kpi' as const,
      id: k.kpi_id,
      label: k.kpi_key,
      sub: `/catalog?kpi=${k.kpi_id}`,
    })),
    ...brackets.map((b) => ({
      kind: 'bracket' as const,
      id: b.id,
      label: b.title,
      sub: `/steering?bracket=${b.id}`,
    })),
    ...actions.map((a) => ({
      kind: 'action' as const,
      id: a.id,
      label: a.name ?? a.id,
      sub: `/catalog?action=${a.id}`,
    })),
  ];

  const overlaysProps: GlobalOverlaysProps = { paletteItems };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Suspense fallback={<aside style={{ width: 248, flexShrink: 0, borderRight: '1px solid var(--line)' }} />}>
        <StudioSidebar domains={domains} />
      </Suspense>
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Suspense fallback={<header style={{ height: 56, borderBottom: '1px solid var(--line)' }} />}>
          <StudioHeader />
        </Suspense>
        <main
          style={{
            flex: 1,
            padding: 'var(--pad)',
            overflow: 'auto',
            background: 'var(--bg)',
          }}
        >
          <div style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
            {children}
          </div>
        </main>
      </div>
      <GlobalOverlays {...overlaysProps} />
    </div>
  );
}
