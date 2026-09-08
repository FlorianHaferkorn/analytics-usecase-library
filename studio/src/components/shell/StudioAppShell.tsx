'use client';

import { Suspense, useEffect, useState } from 'react';
import { StudioSidebar, type DomainStat } from '@/components/ui/studio-sidebar';
import { StudioHeader } from '@/components/ui/studio-header';
import { GlobalOverlays } from '@/components/ui/global-overlays';
import { Settings } from './Settings';
import { AuroraBootstrap } from '@/components/providers/aurora-bootstrap';
import { BrandBootstrap } from '@/components/providers/brand-bootstrap';
import { DomainFilterProvider } from '@/components/providers/domain-filter-provider';
import type { ShellPaletteItem } from '@/lib/studio/build-palette-items';
import type { AuroraBootstrapData } from '@/lib/aurora/bootstrap-data';
import type { ThemeConfig } from '@/lib/store/project-store';
import styles from './StudioAppShell.module.css';
import { ProjectScopeBoundary, ScopeIndicator } from '@/components/project/project-scope-boundary';
import { useProjectStore } from '@/lib/store/project-store';

export interface StudioAppShellProps {
  children: React.ReactNode;
  paletteItems?: ShellPaletteItem[];
  domains?: DomainStat[];
  auroraBootstrap?: AuroraBootstrapData;
  brandBootstrap?: Partial<ThemeConfig> | null;
}

export function StudioAppShell({
  children,
  paletteItems = [],
  domains = [],
  auroraBootstrap,
  brandBootstrap,
}: StudioAppShellProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const scope = useProjectStore(s => s.dataScope);

  useEffect(() => {
    const onTweaks = () => setSettingsOpen(true);
    window.addEventListener('studio:open-tweaks', onTweaks);
    return () => window.removeEventListener('studio:open-tweaks', onTweaks);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSettingsOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <DomainFilterProvider>
    <div className={styles.shell}>
      <Suspense
        fallback={
          <aside className={styles.sidebarFallback} />
        }
      >
        <StudioSidebar domains={scope === 'library' ? domains : []} />
      </Suspense>

      <div className={styles.workspace}>
        <StudioHeader />
        <ScopeIndicator />
        <main className={`studio-main ${styles.main}`}>
          <ProjectScopeBoundary>{children}</ProjectScopeBoundary>
        </main>
      </div>

      <GlobalOverlays key={scope} paletteItems={scope === 'library' ? paletteItems : []} />
      {scope === 'library' && auroraBootstrap && <AuroraBootstrap data={auroraBootstrap} />}
      {scope === 'library' && brandBootstrap && <BrandBootstrap theme={brandBootstrap} />}
      <Settings isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
    </DomainFilterProvider>
  );
}
