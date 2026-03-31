'use client';

import { useState, useCallback } from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
  kpiIds: string[];
  placeholder?: string;
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
      <input
        type="text"
        list={listId}
        value={value}
        onChange={handleChange}
        placeholder={placeholder ?? 'Select KPI (e.g., margin.gm.pct)'}
        style={inputStyle}
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
