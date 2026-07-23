'use client';

interface ForgePageSkeletonProps {
  title: string;
}

export function ForgePageSkeleton({ title }: ForgePageSkeletonProps) {
  return (
    <div
      data-testid="forge-page-skeleton"
      aria-busy="true"
      aria-label={`Loading ${title}`}
      style={{ display: 'grid', gap: 'var(--gap)' }}
    >
      <div style={{ display: 'grid', gap: 'var(--sp-2)' }}>
        <div
          style={{
            height: 28,
            width: 180,
            borderRadius: 6,
            background: 'var(--surface-2)',
          }}
        />
        <div
          style={{
            height: 14,
            width: 'min(420px, 90%)',
            borderRadius: 4,
            background: 'var(--surface-2)',
            opacity: 0.7,
          }}
        />
      </div>
      <div
        aria-hidden
        style={{
          minHeight: 320,
          borderRadius: 12,
          border: '1px solid var(--line)',
          background: 'var(--surface-1)',
        }}
      />
    </div>
  );
}
