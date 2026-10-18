import type { Metadata } from 'next';
import { SessionProvider } from 'next-auth/react';
import localFont from 'next/font/local';
import '@/styles/globals.css';

// Fonts ship with the app (OFL-1.1, npm @fontsource-variable/*): the build needs no
// network and every browser, CI runner included, renders the same metrics. The
// variables feed --font-inter/--font-jetbrains-mono in styles/tokens.css.
const inter = localFont({
  src: '../../node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2',
  weight: '100 900',
  display: 'swap',
  variable: '--font-inter-face',
});

const jetbrainsMono = localFont({
  src: '../../node_modules/@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2',
  weight: '100 800',
  display: 'swap',
  variable: '--font-jetbrains-mono-face',
});

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
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
