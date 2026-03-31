'use client';

import type { NotificationRule } from '@/lib/notifications/rule-types';

interface Props {
  rules: NotificationRule[];
  onToggle: (ruleId: string, enabled: boolean) => void;
  onDelete: (ruleId: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  EarlyWarning: 'var(--gold)',
  RequiredIntervention: 'var(--danger)',
  PrescriptiveExecution: '#DC2626',
};

export function RulesList({ rules, onToggle, onDelete }: Props) {
  if (rules.length === 0) {
    return <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>No rules configured yet.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-0-5)' }}>
      {rules.map((rule) => (
        <div
          key={rule.id}
          style={{
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--slate-700)',
            opacity: rule.enabled ? 1 : 0.5,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--sp-1)',
          }}
        >
          <input
            type="checkbox"
            checked={rule.enabled}
            onChange={() => onToggle(rule.id, !rule.enabled)}
            style={{ accentColor: 'var(--mint)' }}
          />
          <span
            style={{
              width: '6px', height: '6px', borderRadius: '50%',
              backgroundColor: SEVERITY_COLORS[rule.severity] ?? 'var(--slate-400)',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--slate-100)', fontWeight: 600, flex: 1 }}>
            {rule.name}
          </span>
          <span style={{ fontSize: '0.6875rem', color: 'var(--slate-400)' }}>
            {rule.kpiId} {rule.condition} {rule.threshold}
            {rule.condition === 'between' && rule.thresholdUpper !== undefined ? `–${rule.thresholdUpper}` : ''}
          </span>
          <button
            onClick={() => onDelete(rule.id)}
            style={{
              background: 'none', border: 'none', color: 'var(--slate-500)',
              cursor: 'pointer', fontSize: '0.75rem',
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
