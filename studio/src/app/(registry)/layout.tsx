import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';

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
    </div>
  );
}
