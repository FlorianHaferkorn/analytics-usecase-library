import StudioLayoutShell from '@/components/shell/StudioLayoutShell';

export default function StudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <StudioLayoutShell>{children}</StudioLayoutShell>;
}
