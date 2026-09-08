import type { Metadata } from 'next';
import { SessionProvider } from 'next-auth/react';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'ALUCA Studio',
  description: 'Governed analytics delivery — from strategy and KPI meaning to validated target artifacts.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      data-theme="dark"
      data-density="balanced"
      data-fonts="inter"
    >
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
