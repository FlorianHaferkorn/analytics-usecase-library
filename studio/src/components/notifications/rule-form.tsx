'use client';

import { useState } from 'react';
import type { RuleCondition, EscalationSeverity } from '@/lib/notifications/rule-types';
import { KpiAutocomplete } from './kpi-autocomplete';
import { StudioButton } from '@/components/ui/studio-page';
import { StudioFormField, StudioFormGrid, StudioInput, StudioSelect } from '@/components/ui/studio-data';

interface Props {
  onSubmit: (data: {
    name: string; kpiId: string; condition: RuleCondition;
    threshold: number; thresholdUpper?: number;
    severity: EscalationSeverity; spineId?: string;
  }) => void;
  kpiIds?: string[];
}

export function RuleForm({ onSubmit, kpiIds = [] }: Props) {
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
    <StudioFormGrid>
      <StudioFormField label="Rule name">
        <StudioInput placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} />
      </StudioFormField>
      <StudioFormField label="KPI">
        <KpiAutocomplete value={kpiId} onChange={setKpiId} kpiIds={kpiIds} />
      </StudioFormField>
      <StudioFormField label="Condition">
        <StudioSelect value={condition} onChange={(e) => setCondition(e.target.value as RuleCondition)}>
          <option value="lt">&lt; Less than</option>
          <option value="gt">&gt; Greater than</option>
          <option value="eq">= Equals</option>
          <option value="between">Between</option>
        </StudioSelect>
      </StudioFormField>
      <StudioFormField label="Threshold">
        <StudioInput type="number" placeholder="Threshold" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
      </StudioFormField>
      {condition === 'between' && (
        <StudioFormField label="Upper threshold">
          <StudioInput type="number" placeholder="Upper threshold" value={thresholdUpper} onChange={(e) => setThresholdUpper(e.target.value)} />
        </StudioFormField>
      )}
      <StudioFormField label="Severity">
        <StudioSelect value={severity} onChange={(e) => setSeverity(e.target.value as EscalationSeverity)}>
          <option value="EarlyWarning">Early Warning</option>
          <option value="RequiredIntervention">Required Intervention</option>
          <option value="PrescriptiveExecution">Prescriptive Execution</option>
        </StudioSelect>
      </StudioFormField>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-start' }}>
        <StudioButton onClick={handleSubmit} tone="success" variant="primary" style={{ minWidth: '140px' }}>
          Add Rule
        </StudioButton>
      </div>
    </StudioFormGrid>
  );
}
