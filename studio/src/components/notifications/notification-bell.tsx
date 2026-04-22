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
        fontSize: '1.125rem',
        padding: '4px',
        color: count > 0 ? 'var(--warning)' : 'var(--ink-4)',
        minWidth: '32px',
        minHeight: '32px',
      }}
    >
      🔔
      {count > 0 && (
        <span
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            backgroundColor: 'var(--danger)',
            color: '#fff',
            fontSize: '0.5625rem',
            fontWeight: 700,
            borderRadius: '50%',
            width: '14px',
            height: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {count > 9 ? '9+' : count}
        </span>
      )}
    </StudioButton>
  );
}
