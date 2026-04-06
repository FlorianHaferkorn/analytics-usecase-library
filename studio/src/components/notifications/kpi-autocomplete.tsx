'use client';

import { useState, useCallback } from 'react';
import { StudioInput } from '@/components/ui/studio-data';

interface Props {
  value: string;
  onChange: (value: string) => void;
  kpiIds: string[];
  placeholder?: string;
}

/**
 * KPI Autocomplete — combobox with datalist filtering against KPI catalog IDs.
 */
export function KpiAutocomplete({ value, onChange, kpiIds, placeholder }: Props) {
  const [listId] = useState(() => `kpi-list-${Math.random().toString(36).slice(2, 6)}`);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(e.target.value);
    },
    [onChange],
  );

  return (
    <>
      <StudioInput
        type="text"
        list={listId}
        value={value}
        onChange={handleChange}
        placeholder={placeholder ?? 'Select KPI (e.g., margin.gm.pct)'}
        style={{ fontSize: '0.75rem', padding: '4px var(--sp-1)', borderRadius: 'var(--radius-sm)' }}
        autoComplete="off"
      />
      <datalist id={listId}>
        {kpiIds.map((id) => (
          <option key={id} value={id} />
        ))}
      </datalist>
    </>
  );
}
