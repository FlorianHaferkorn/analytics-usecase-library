import { StudioAppShell } from './StudioAppShell';
import { buildShellPaletteItems } from '@/lib/studio/build-palette-items';

export default async function StudioLayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const paletteItems = await buildShellPaletteItems();
  return <StudioAppShell paletteItems={paletteItems}>{children}</StudioAppShell>;
}
