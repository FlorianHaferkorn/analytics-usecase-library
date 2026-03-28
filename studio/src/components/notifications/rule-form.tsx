'use client';

import { useState } from 'react';
import type { RuleCondition, EscalationSeverity } from '@/lib/notifications/rule-types';

interface Props {
  onSubmit: (data: {
    name: string; kpiId: string; condition: RuleCondition;
    threshold: number; thresholdUpper?: number;
    severity: EscalationSeverity; spineId?: string;
  }) => void;
}

const inputStyle = {
  padding: '4px var(--sp-1)',
  backgroundColor: 'var(--slate-900)',
  border: '1px solid var(--slate-700)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--slate-100)',
  fontSize: '0.75rem',
  width: '100%',
};

export function RuleForm({ onSubmit }: Props) {
  const [name, setName] = useState('');
  const [kpiId, setKpiId] = useState('');
  const [condition, setCondition] = useState<RuleCondition>('lt');
  const [threshold, setThreshold] = useState('');
  const [thresholdUpper, setThresholdUpper] = useState('');
  const [severity, setSeverity] = useState<EscalationSeverity>('EarlyWarning');

  const handleSubmit = () => {
    if (!name.trim() || !kpiId.trim() || !threshold) return;
    onSubmit({
      name: name.trim(),
      kpiId: kpiId.trim(),
      condition,
      threshold: Number(threshold),
      thresholdUpper: condition === 'between' ? Number(thresholdUpper) : undefined,
      severity,
    });
    setName(''); setKpiId(''); setThreshold(''); setThresholdUpper('');
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-1)', padding: 'var(--sp-1-5)', backgroundColor: 'var(--slate-800)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)' }}>
      <input placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />
      <input placeholder="KPI ID (e.g., margin.gm.pct)" value={kpiId} onChange={(e) => setKpiId(e.target.value)} style={inputStyle} />
      <select value={condition} onChange={(e) => setCondition(e.target.value as RuleCondition)} style={inputStyle}>
        <option value="lt">&lt; Less than</option>
        <option value="gt">&gt; Greater than</option>
        <option value="eq">= Equals</option>
        <option value="between">Between</option>
      </select>
      <input type="number" placeholder="Threshold" value={threshold} onChange={(e) => setThreshold(e.target.value)} style={inputStyle} />
      {condition === 'between' && (
        <input type="number" placeholder="Upper threshold" value={thresholdUpper} onChange={(e) => setThresholdUpper(e.target.value)} style={inputStyle} />
      )}
      <select value={severity} onChange={(e) => setSeverity(e.target.value as EscalationSeverity)} style={inputStyle}>
        <option value="EarlyWarning">Early Warning</option>
        <option value="RequiredIntervention">Required Intervention</option>
        <option value="PrescriptiveExecution">Prescriptive Execution</option>
      </select>
      <button
        onClick={handleSubmit}
        style={{
          padding: '6px var(--sp-1-5)',
          backgroundColor: 'var(--mint)',
          border: 'none',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--slate-950)',
          fontSize: '0.75rem',
          fontWeight: 600,
          cursor: 'pointer',
          gridColumn: condition === 'between' ? 'auto' : '2',
        }}
      >
        Add Rule
      </button>
    </div>
  );
}
