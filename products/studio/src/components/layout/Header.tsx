"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/theme";

const nav = [
  { href: "/", label: "Explorer" },
  { href: "/studio", label: "Studio" },
  { href: "/brand", label: "Brand" },
];

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      className="p-1.5 rounded-md text-theme-tertiary hover:text-theme hover:bg-theme-tertiary transition-colors cursor-pointer"
      title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
    >
      {theme === "light" ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      )}
    </button>
  );
}

export function Header() {
  const pathname = usePathname();
  return (
    <header className="h-12 border-b border-theme bg-theme flex items-center px-6 gap-6 shrink-0">
      <Link href="/" className="flex items-center gap-2 font-semibold text-brand-mint">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <span className="text-sm">ActionReady Studio</span>
      </Link>

      <nav className="flex items-center gap-0.5">
        {nav.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors
                ${active
                  ? "bg-theme-tertiary text-theme"
                  : "text-theme-secondary hover:text-theme hover:bg-theme-tertiary"
                }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-theme-tertiary font-mono hidden sm:block">
          Golden Thread
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
