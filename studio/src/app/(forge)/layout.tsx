import StudioLayoutShell from '@/components/shell/StudioLayoutShell';
import { ForgeBootstrapProvider } from '@/components/providers/forge-bootstrap-provider';
import { loadForgeBootstrap } from '@/lib/core/forge-bootstrap';

export default async function ForgeLayout({ children }: { children: React.ReactNode }) {
  const initialPayload = await loadForgeBootstrap();

  return (
    <StudioLayoutShell>
      <ForgeBootstrapProvider initialPayload={initialPayload}>{children}</ForgeBootstrapProvider>
    </StudioLayoutShell>
  );
}
