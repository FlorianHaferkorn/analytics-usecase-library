'use client';

import { StudioInput } from '@/components/ui/studio-data';

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function ColorPicker({ label, value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
      <StudioInput
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: '32px',
          height: '32px',
          border: '2px solid var(--slate-600)',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'transparent',
          padding: 0,
        }}
      />
      <div>
        <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>{label}</p>
        <p style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--slate-500)' }}>
          {value}
        </p>
      </div>
    </div>
  );
}
