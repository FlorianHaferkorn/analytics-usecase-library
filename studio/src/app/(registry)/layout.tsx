import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';

export default function RegistryLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '260px 1fr',
        gridTemplateRows: '56px 1fr',
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
            padding: 'var(--sp-3)',
            overflow: 'auto',
            background: 'radial-gradient(circle at top right, color-mix(in srgb, var(--info) 8%, transparent), transparent 30%), linear-gradient(180deg, var(--slate-950), var(--slate-900))',
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
