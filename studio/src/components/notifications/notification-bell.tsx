'use client';

import { StudioButton } from '@/components/ui/studio-page';

interface Props {
  count: number;
  onClick: () => void;
}

export function NotificationBell({ count, onClick }: Props) {
  return (
    <StudioButton
      onClick={onClick}
      variant="ghost"
      style={{
        position: 'relative',
        padding: '0',
        color: count > 0 ? 'var(--ink)' : 'var(--ink-3)',
        width: '30px',
        height: '30px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '7px',
      }}
    >
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor"
           strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M4 11.5V7a4 4 0 0 1 8 0v4.5M2.5 11.5h11M6.5 13.5a1.5 1.5 0 0 0 3 0"/>
      </svg>
      {count > 0 && (
        <span
          style={{
            position: 'absolute',
            top: '2px',
            right: '2px',
            background: 'var(--accent)',
            color: 'var(--accent-ink)',
            fontSize: '9px',
            fontWeight: 700,
            borderRadius: '999px',
            minWidth: '14px',
            height: '14px',
            padding: '0 3px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid var(--bg)',
            lineHeight: 1,
          }}
        >
          {count > 9 ? '9+' : count}
        </span>
      )}
    </StudioButton>
  );
}
