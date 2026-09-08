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
 *
 * Renders ⌘K on macOS / iOS, Ctrl K elsewhere. Avoids the awkward "⌘K on Windows"
 * problem from hardcoded strings. Returns the non-Mac form during SSR (safer
 * default until hydration), then swaps after mount.
 */
export function KbdShortcut({ k, meta = true, style, className }: KbdShortcutProps) {
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';
    setIsMac(/Mac|iPhone|iPad|iPod/i.test(ua));
  }, []);

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    minWidth: 20, minHeight: 20, padding: '0 var(--space-1)',
    fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', fontWeight: 500,
    color: 'var(--ink-3)', background: 'var(--bg-2)',
    border: '1px solid var(--line)', borderRadius: 5,
    fontStyle: 'normal',
    ...style,
  };

  if (!meta) {
    return <kbd style={baseStyle} className={className}>{k}</kbd>;
  }

  return (
    <kbd style={baseStyle} className={className}>
      {isMac ? '⌘' : 'Ctrl'}
      {k && (isMac ? k : ` ${k}`)}
    </kbd>
  );
}
