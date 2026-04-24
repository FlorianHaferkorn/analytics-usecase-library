import type { Metadata } from 'next';
import { SessionProvider } from 'next-auth/react';
import { Inter, JetBrains_Mono } from 'next/font/google';
import '@/styles/globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-jetbrains-mono',
});

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
