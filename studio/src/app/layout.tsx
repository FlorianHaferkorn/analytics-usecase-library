import type { Metadata } from 'next';
import { SessionProvider } from 'next-auth/react';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'ActionReady Studio',
  description: 'NotebookLM for Business Steering — from Strategy to Action',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-density="airy" data-fonts="geist">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&family=Inter:wght@400;450;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Serif&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
