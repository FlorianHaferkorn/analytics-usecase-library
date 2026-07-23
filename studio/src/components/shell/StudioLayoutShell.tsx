import { StudioAppShell } from './StudioAppShell';
import { buildShellPaletteItems } from '@/lib/studio/build-palette-items';
import { buildDomainStats } from '@/lib/studio/build-domain-stats';
import { getAuroraBootstrapData } from '@/lib/aurora/bootstrap-data';
import { getBrandBootstrapTheme } from '@/lib/aurora/brand-bootstrap-data';
import type { DomainStat } from '@/components/ui/studio-sidebar';

const DOMAIN_HUES = [215, 195, 245, 165, 270, 80, 220, 140];

export default async function StudioLayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [paletteItems, domainRows, auroraBootstrap, brandBootstrap] = await Promise.all([
    buildShellPaletteItems(),
    buildDomainStats().catch(() => []),
    Promise.resolve(getAuroraBootstrapData()),
    Promise.resolve(getBrandBootstrapTheme()),
  ]);

  const domains: DomainStat[] = domainRows.map((domain, index) => ({
    name: domain.name,
    count: domain.count,
    hue: DOMAIN_HUES[index % DOMAIN_HUES.length]!,
  }));

  return (
    <StudioAppShell paletteItems={paletteItems} domains={domains} auroraBootstrap={auroraBootstrap} brandBootstrap={brandBootstrap}>
      {children}
    </StudioAppShell>
  );
}
