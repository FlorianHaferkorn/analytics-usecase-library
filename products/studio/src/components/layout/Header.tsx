"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/", label: "Explorer" },
  { href: "/studio", label: "Studio" },
  { href: "/brand", label: "Brand" },
];

export function Header() {
  const pathname = usePathname();
  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center px-6 gap-6 shrink-0">
      <Link href="/" className="flex items-center gap-2 font-semibold text-brand-primary">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <span>ActionReady Studio</span>
      </Link>

      <nav className="flex items-center gap-1">
        {nav.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors
                ${active
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="ml-auto text-xs text-slate-400 font-mono">
        Golden Thread · Analytics Use Case Library
      </div>
    </header>
  );
}
