'use client';

import { card, cardHead } from '@/components/registry/kpi-detail-tabs';
import { ColorPicker } from '@/components/brand/color-picker';
import type { ThemeConfig } from '@/lib/store/project-store';

interface Props {
  theme: ThemeConfig;
  onUpdate: (partial: Partial<ThemeConfig>) => void;
  onSave: () => void;
  saving: boolean;
}

const SECTION_LABEL: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: 'var(--ink-3)',
  marginBottom: '12px',
};

const BG_PRESETS: Array<{ label: string; background: string; surface: string }> = [
  { label: 'Obsidian', background: '#0d0e10', surface: '#131416' },
  { label: 'Midnight', background: '#0e0f1a', surface: '#131620' },
  { label: 'Slate',    background: '#13151f', surface: '#1a1c28' },
];

const FONTS: Array<{ name: string; family: string; sample: string }> = [
  { name: 'Inter',           family: "'Inter', sans-serif",           sample: 'Aa 0123' },
  { name: 'DM Sans',         family: "'DM Sans', sans-serif",         sample: 'Aa 0123' },
  { name: 'JetBrains Mono',  family: "'JetBrains Mono', monospace",   sample: 'Aa 0123' },
];

export function TweaksTab({ theme, onUpdate, onSave, saving }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '4px 0' }}>

      {/* Section 1 — Color Overrides */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>Color Overrides</span>
        </div>
        <div style={{ padding: '16px' }}>
          <p style={SECTION_LABEL as React.CSSProperties}>Accent</p>
          <div style={{ marginBottom: '16px' }}>
            <ColorPicker
              label="Accent"
              value={theme.primary}
              onChange={(c) => onUpdate({ primary: c })}
            />
          </div>

          <p style={SECTION_LABEL as React.CSSProperties}>Background Palette</p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {BG_PRESETS.map((preset) => {
              const isActive = theme.background === preset.background;
              return (
                <button
                  key={preset.label}
                  onClick={() => onUpdate({ background: preset.background, surface: preset.surface })}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    border: isActive
                      ? '1px solid var(--accent)'
                      : '1px solid var(--line)',
                    color: isActive ? 'var(--accent)' : 'var(--ink-3)',
                    background: isActive ? 'var(--accent-soft)' : 'transparent',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Section 2 — Typography */}
      <div style={card}>
        <div style={cardHead}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>Typography</span>
        </div>
        <div style={{ padding: '16px' }}>
          <p style={SECTION_LABEL as React.CSSProperties}>Font Family</p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {FONTS.map((font) => {
              const isActive = theme.fontFamily === font.name;
              return (
                <button
                  key={font.name}
                  onClick={() => onUpdate({ fontFamily: font.name })}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '6px',
                    border: isActive
                      ? '1px solid var(--accent)'
                      : '1px solid var(--line)',
                    background: isActive ? 'var(--accent-soft)' : 'transparent',
                    cursor: 'pointer',
                    minWidth: '100px',
                    textAlign: 'center',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <p style={{
                    margin: 0,
                    fontSize: '13px',
                    fontWeight: 500,
                    color: isActive ? 'var(--accent)' : 'var(--ink)',
                    fontFamily: font.family,
                  }}>
                    {font.name}
                  </p>
                  <p style={{
                    margin: '4px 0 0',
                    fontSize: '11px',
                    color: 'var(--ink-3)',
                    fontFamily: font.family,
                  }}>
                    {font.sample}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Section 3 — Apply to Brand Spec */}
      <div style={{ padding: '0 2px' }}>
        <p style={SECTION_LABEL as React.CSSProperties}>Apply to Brand Spec</p>
        <p style={{ fontSize: '13px', color: 'var(--ink-3)', marginBottom: '12px', lineHeight: 1.5 }}>
          Saves accent color, background palette, and font family to{' '}
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            core/brand/BrandSpec.schema.yaml
          </code>.
        </p>
        <button
          onClick={onSave}
          disabled={saving}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: saving ? 'var(--ink-4)' : 'var(--accent)',
            color: saving ? 'var(--ink-3)' : '#0d0e10',
            fontSize: '13px',
            fontWeight: 600,
            cursor: saving ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s ease',
          }}
        >
          {saving ? 'Saving…' : 'Save to Brand Spec'}
        </button>
      </div>

    </div>
  );
}
