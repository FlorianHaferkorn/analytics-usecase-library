'use client';

interface Props {
  count: number;
  onClick: () => void;
}

export function NotificationBell({ count, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      style={{
        position: 'relative',
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        fontSize: '1.125rem',
        padding: '4px',
        color: count > 0 ? 'var(--gold)' : 'var(--slate-500)',
      }}
      title={`${count} active notification${count !== 1 ? 's' : ''}`}
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
    </button>
  );
}
