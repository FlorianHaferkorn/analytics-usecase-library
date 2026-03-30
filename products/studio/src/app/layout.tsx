import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "ActionReady Studio",
  description: "Golden Thread Analytics Use Case Designer",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="h-screen flex flex-col overflow-hidden">
        <ThemeProvider>
          <Header />
          <main className="flex-1 overflow-hidden">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
