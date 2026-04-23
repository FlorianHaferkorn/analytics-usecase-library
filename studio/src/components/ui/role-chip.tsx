'use client';

import type { ResolvedRole } from '@/lib/core/org-role-loader';

interface Props {
  roleId: string;
  resolved?: ResolvedRole;
  size?: 'sm' | 'md';
}

/** Format a raw snake_case or spaced role id into a readable title. */
function formatRawId(id: string): string {
  return id
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Format a raw id into 1-2 letter initials (fallback for unresolved ids). */
function rawInitials(id: string): string {
  const words = id.replace(/_/g, ' ').split(' ').filter((w) => w.length > 0);
  return words
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

export function RoleChip({ roleId, resolved, size = 'sm' }: Props) {
  const circleSize = size === 'sm' ? 24 : 28;
  const fontSize = 10;

  if (resolved) {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 7,
        }}
      >
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: circleSize,
            height: circleSize,
            borderRadius: '50%',
            flexShrink: 0,
            background: `oklch(0.55 0.12 ${resolved.hue})`,
            color: '#0d0e10',
            fontSize,
            fontWeight: 600,
            lineHeight: 1,
            userSelect: 'none',
          }}
        >
          {resolved.avatar_initials}
        </span>
        <span
          style={{
            fontSize: 13,
            color: 'var(--ink-2)',
            lineHeight: 1.3,
          }}
        >
          {resolved.title}
        </span>
      </span>
    );
  }

  // Fallback: roleId not resolved — format nicely from raw string
  const displayTitle = formatRawId(roleId);
  const initials = rawInitials(roleId);

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 7,
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: circleSize,
          height: circleSize,
          borderRadius: '50%',
          flexShrink: 0,
          background: 'var(--panel)',
          color: 'var(--ink-4)',
          fontSize,
          fontWeight: 600,
          lineHeight: 1,
          border: '1px solid var(--line)',
          userSelect: 'none',
        }}
      >
        {initials}
      </span>
      <span
        style={{
          fontSize: 13,
          color: 'var(--ink-2)',
          lineHeight: 1.3,
        }}
      >
        {displayTitle}
      </span>
    </span>
  );
}
