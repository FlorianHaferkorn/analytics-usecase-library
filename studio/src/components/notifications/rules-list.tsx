'use client';

import type { NotificationRule } from '@/lib/notifications/rule-types';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';

interface Props {
  rules: NotificationRule[];
  onToggle: (ruleId: string, enabled: boolean) => void;
  onDelete: (ruleId: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  EarlyWarning: 'var(--warning)',
  RequiredIntervention: 'var(--danger)',
  PrescriptiveExecution: '#DC2626',
};

export function RulesList({ rules, onToggle, onDelete }: Props) {
  if (rules.length === 0) {
    return <StudioEmptyState title="No rules configured yet" description="Add a first notification rule to start evaluating KPI thresholds and escalation triggers." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {rules.map((rule) => (
        <StudioPanel
          key={rule.id}
          tone={rule.enabled ? 'default' : 'warning'}
          style={{ opacity: rule.enabled ? 1 : 0.62, padding: '8px var(--pad)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%', flexWrap: 'wrap' }}>
            <input
              type="checkbox"
              checked={rule.enabled}
              onChange={() => onToggle(rule.id, !rule.enabled)}
              style={{ accentColor: 'var(--accent)' }}
            />
            <span
              style={{
                width: '6px', height: '6px', borderRadius: '50%',
                backgroundColor: SEVERITY_COLORS[rule.severity] ?? 'var(--ink-3)',
              }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--ink)', fontWeight: 600, flex: 1, minWidth: '180px' }}>
              {rule.name}
            </span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--ink-3)' }}>
              {rule.kpiId} {rule.condition} {rule.threshold}
              {rule.condition === 'between' && rule.thresholdUpper !== undefined ? `–${rule.thresholdUpper}` : ''}
            </span>
            <StudioButton onClick={() => onDelete(rule.id)} variant="ghost" style={{ padding: '4px 8px', minWidth: '32px' }}>
              ×
            </StudioButton>
          </div>
        </StudioPanel>
      ))}
    </div>
  );
}
