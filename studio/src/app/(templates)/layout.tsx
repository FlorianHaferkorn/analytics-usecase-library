import StudioLayoutShell from '@/components/shell/StudioLayoutShell';

export default function TemplatesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <StudioLayoutShell>{children}</StudioLayoutShell>;
}
