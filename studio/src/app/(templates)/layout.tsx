import { AppShell } from '@/components/shell/AppShell';

export default function TemplatesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
