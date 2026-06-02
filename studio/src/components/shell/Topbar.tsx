'use client';

import { usePathname } from 'next/navigation';

interface TopbarProps {
  onSettings?: () => void;
  onAskStudio?: () => void;
}

export function Topbar({ onSettings, onAskStudio }: TopbarProps) {
  const pathname = usePathname();

  // Build breadcrumb from pathname
  const segments = pathname
    ?.split('/')
    .filter(Boolean)
    .map((seg) => ({
      label: seg.charAt(0).toUpperCase() + seg.slice(1),
      path: '/' + seg,
    })) || [];

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-panel">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2">
        {segments.map((seg, i) => (
          <div key={i} className="flex items-center gap-2">
            {i > 0 && <span className="text-foreground-subtle text-xs">/</span>}
            <span className="text-sm text-foreground-muted">{seg.label}</span>
          </div>
        ))}
        {!segments.length && <span className="text-sm text-foreground-muted">Studio</span>}
      </div>

      {/* Actions */}
      {onAskStudio && (
        <button
          type="button"
          onClick={onAskStudio}
          className="mr-2 px-3 py-1.5 rounded-lg text-sm text-foreground-muted hover:bg-hover transition-colors"
        >
          Ask Studio
        </button>
      )}
      <button
        type="button"
        onClick={onSettings}
        aria-label="Settings"
        className="p-2 rounded-lg text-foreground-subtle hover:bg-hover transition-colors"
        title="Settings"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="8" cy="8" r="2" />
          <path d="M8 3v1M8 12v1M3 8h1M12 8h1M4.5 4.5l.7.7M10.8 11.1l.7.7M4.5 11.5l.7-.7M10.8 4.8l.7-.7" />
        </svg>
      </button>
    </header>
  );
}
