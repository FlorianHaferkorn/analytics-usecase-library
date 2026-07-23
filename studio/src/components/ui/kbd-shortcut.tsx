'use client';

import { useEffect, useState } from 'react';

interface KbdShortcutProps {
  /** Key after the modifier — e.g. 'K' for Cmd/Ctrl+K. Pass empty for plain keys like 'N'. */
  k: string;
  /** When true, shows ⌘ on Mac, Ctrl on others. When false, only the key (no modifier). */
  meta?: boolean;
  style?: React.CSSProperties;
  className?: string;
}

/**
 * Platform-aware keyboard shortcut indicator.
 * Renders a stable SSR placeholder until mount to avoid hydration mismatch.
 */
export function KbdShortcut({ k, meta = true, style, className }: KbdShortcutProps) {
  const [mounted, setMounted] = useState(false);
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(/Mac|iPhone|iPad|iPod/i.test(navigator.userAgent));
    setMounted(true);
  }, []);

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    minWidth: 18, height: 18, padding: '0 5px',
    fontFamily: 'var(--font-mono)', fontSize: 10.5, fontWeight: 500,
    color: 'var(--ink-3)', background: 'var(--bg-2)',
    border: '1px solid var(--line)', borderRadius: 'var(--radius-md)',
    fontStyle: 'normal',
    ...style,
  };

  if (!meta) {
    return <kbd style={baseStyle} className={className}>{k}</kbd>;
  }

  const label = !mounted
    ? `Ctrl${k ? ` ${k}` : ''}`
    : isMac
      ? `⌘${k}`
      : `Ctrl${k ? ` ${k}` : ''}`;

  return (
    <kbd style={baseStyle} className={className} suppressHydrationWarning>
      {label}
    </kbd>
  );
}
