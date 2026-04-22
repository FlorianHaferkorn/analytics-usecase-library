import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';
import { GlobalOverlays, type GlobalOverlaysProps } from '@/components/ui/global-overlays';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { type SerializablePaletteItem } from '@/components/ui/command-palette';

export default async function StudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Load live data in parallel
  const [kpis, brackets, actions] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
  ]);

  // Build serializable palette items
  const paletteItems: SerializablePaletteItem[] = [
    ...kpis.map((k) => ({
      kind: 'kpi' as const,
      id: k.kpi_id,
      label: k.kpi_key,
      sub: `/catalog?kpi=${k.kpi_id}`,
      status: k.governance?.certification_status ?? undefined,
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
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '248px 1fr',
        gridTemplateRows: 'var(--h-row) 1fr',
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      <StudioSidebar />
      <div style={{ display: 'flex', flexDirection: 'column', gridRow: '1 / -1', gridColumn: '2' }}>
        <StudioHeader />
        <main
          style={{
            flex: 1,
            padding: 'var(--pad)',
            overflow: 'auto',
            background: 'var(--bg)',
          }}
        >
          <div style={{ width: '100%', maxWidth: '1680px', margin: '0 auto' }}>
            {children}
          </div>
        </main>
      </div>
      <GlobalOverlays {...overlaysProps} />
    </div>
  );
}
