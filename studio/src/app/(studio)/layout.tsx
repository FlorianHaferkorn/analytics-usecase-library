import { StudioSidebar } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';

export default function StudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '260px 1fr',
        gridTemplateRows: '56px 1fr',
        minHeight: '100vh',
      }}
    >
      <StudioSidebar />
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <StudioHeader />
        <main
          style={{
            flex: 1,
            padding: 'var(--sp-3)',
            overflow: 'auto',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
