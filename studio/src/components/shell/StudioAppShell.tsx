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
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        background: 'var(--bg)',
      }}
    >
      <Suspense
        fallback={
          <aside
            style={{
              width: 248,
              flexShrink: 0,
              borderRight: '1px solid var(--line)',
              background: 'var(--bg)',
            }}
          />
        }
      >
        <StudioSidebar domains={domains} />
      </Suspense>

      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
        <StudioHeader />
        <main
          className="studio-main"
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 'var(--pad)',
            background: 'var(--bg)',
          }}
        >
          {children}
        </main>
      </div>

      <GlobalOverlays paletteItems={paletteItems} />
      {auroraBootstrap && <AuroraBootstrap data={auroraBootstrap} />}
      {brandBootstrap && <BrandBootstrap theme={brandBootstrap} />}
      <Settings isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
    </DomainFilterProvider>
  );
}
