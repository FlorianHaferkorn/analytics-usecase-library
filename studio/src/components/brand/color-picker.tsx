'use client';

import { StudioInput } from '@/components/ui/studio-data';

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function ColorPicker({ label, value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <StudioInput
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: '32px',
          height: '32px',
          border: '1px solid var(--line)',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'transparent',
          padding: 0,
        }}
      />
      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>{label}</p>
        <p style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--ink-4)' }}>
          {value}
        </p>
      </div>
    </div>
  );
}
