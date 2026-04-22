'use client';

import { useEffect, useState } from 'react';
import type { ActiveNotification } from '@/lib/notifications/rule-types';
import { StudioButton } from '@/components/ui/studio-page';

interface Props {
  notifications: ActiveNotification[];
  onDismiss: (id: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  EarlyWarning: 'var(--warning)',
  RequiredIntervention: 'var(--danger)',
  PrescriptiveExecution: '#DC2626',
};

const SEVERITY_LABELS: Record<string, string> = {
  EarlyWarning: 'Warning',
  RequiredIntervention: 'Intervention',
  PrescriptiveExecution: 'Critical',
};

export function ToastContainer({ notifications, onDismiss }: Props) {
  const [visible, setVisible] = useState<Set<string>>(new Set());

  useEffect(() => {
    const newIds = notifications.filter((n) => !n.dismissed).map((n) => n.id);
    setVisible(new Set(newIds));

    // Auto-dismiss after 8 seconds
    const timers = newIds.map((id) =>
      setTimeout(() => onDismiss(id), 8000),
    );
    return () => timers.forEach(clearTimeout);
  }, [notifications, onDismiss]);

  const active = notifications.filter((n) => visible.has(n.id) && !n.dismissed);
  if (active.length === 0) return null;

  return (
    <div style={{ position: 'fixed', top: 64, right: 16, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: 360 }}>
      {active.map((n) => {
        const color = SEVERITY_COLORS[n.result.severity] ?? 'var(--ink-3)';
        return (
          <div
            key={n.id}
            style={{
              padding: 'var(--pad)',
              backgroundColor: 'var(--panel)',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${color}`,
              borderLeft: `4px solid ${color}`,
              animation: 'slideIn 0.3s ease-out',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.6875rem', fontWeight: 700, color, textTransform: 'uppercase' }}>
                {SEVERITY_LABELS[n.result.severity] ?? n.result.severity}
              </span>
              <StudioButton
                onClick={() => onDismiss(n.id)}
                variant="ghost"
                style={{
                  color: 'var(--ink-4)',
                  fontSize: '0.875rem',
                  padding: 0,
                  minWidth: '20px',
                  minHeight: '20px',
                }}
              >
                ×
              </StudioButton>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--ink-2)' }}>
              {n.result.message}
            </p>
          </div>
        );
      })}
    </div>
  );
}
