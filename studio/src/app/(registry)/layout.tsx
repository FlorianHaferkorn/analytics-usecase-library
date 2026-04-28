import { Suspense } from 'react';
import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';
import { GlobalOverlays } from '@/components/ui/global-overlays';

export default function RegistryLayout({ children }: { children: React.ReactNode }) {
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
      <Suspense fallback={<aside style={{ borderRight: '1px solid var(--line)' }} />}>
        <StudioSidebar />
      </Suspense>
      <div style={{ display: 'flex', flexDirection: 'column', gridRow: '1 / -1', gridColumn: '2' }}>
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
          <div style={{ width: '100%', maxWidth: '1680px', margin: '0 auto' }}>
            {children}
          </div>
        </main>
      </div>
      <GlobalOverlays />
    </div>
  );
}
