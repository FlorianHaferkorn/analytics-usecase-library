'use client';
import { useProjectStore } from '@/lib/store/project-store';
import { useEffect } from 'react';

export function PendingDraftBanner() {
  const draft = useProjectStore((s) => s.pendingWizardDraft);
  const clear = useProjectStore((s) => s.clearPendingWizardDraft);

  // Auto-clear after 60 seconds
  useEffect(() => {
    if (!draft) return;
    const t = setTimeout(clear, 60_000);
    return () => clearTimeout(t);
  }, [draft, clear]);

  if (!draft) return null;

  return (
    <div style={{
      padding: '12px 16px',
      marginBottom: 'var(--gap)',
      borderRadius: 'var(--radius)',
      background: 'var(--accent-soft)',
      border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
    }}>
      <div>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Wizard draft ready
        </span>
        <p style={{ margin: '2px 0 0', fontSize: '0.875rem', color: 'var(--ink)', fontWeight: 500 }}>
          {draft.name}
        </p>
        <p style={{ margin: '2px 0 0', fontSize: '0.75rem', color: 'var(--ink-3)', fontFamily: 'var(--font-mono)' }}>
          {draft.ref} · {draft.domain} · {draft.type}
        </p>
      </div>
      <button
        onClick={clear}
        style={{ padding: '4px 8px', fontSize: '0.75rem', color: 'var(--ink-3)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)', background: 'transparent', cursor: 'pointer' }}
      >
        Dismiss
      </button>
    </div>
  );
}
