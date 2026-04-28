import type { Metadata } from 'next';
import { SessionProvider } from 'next-auth/react';
import { Geist, Geist_Mono } from 'next/font/google';
import '@/styles/globals.css';

const geist = Geist({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-geist',
});

const geistMono = Geist_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-geist-mono',
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
      data-density="airy"
      data-fonts="geist"
      className={`${geist.variable} ${geistMono.variable}`}
    >
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
