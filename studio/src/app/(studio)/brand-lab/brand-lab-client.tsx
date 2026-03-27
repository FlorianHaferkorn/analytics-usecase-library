'use client';

import { useState } from 'react';
import { ColorPicker } from '@/components/brand/color-picker';
import { LayoutPreview } from '@/components/brand/layout-preview';
import type { ThemeConfig } from '@/lib/store/project-store';

const DEFAULT_THEME: ThemeConfig = {
  primary: '#00D4AA',
  secondary: '#FFB800',
  accent: '#3B82F6',
  background: '#1E293B',
  surface: '#0F172A',
  text: '#F1F5F9',
  fontFamily: 'Inter',
  borderRadius: 8,
};

const PRESET_THEMES: Record<string, Partial<ThemeConfig>> = {
  'Aurora Monochromatic': {
    primary: '#2ECDE7',
    secondary: '#FFB800',
    background: '#1A1A2E',
    surface: '#16213E',
  },
  'Corporate Blue': {
    primary: '#2563EB',
    secondary: '#F59E0B',
    background: '#1E293B',
    surface: '#0F172A',
  },
  'Forest Green': {
    primary: '#10B981',
    secondary: '#F97316',
    background: '#1A2332',
    surface: '#0D1520',
  },
  'Warm Slate': {
    primary: '#F472B6',
    secondary: '#A78BFA',
    background: '#292524',
    surface: '#1C1917',
  },
};

export function BrandLabClient() {
  const [theme, setTheme] = useState<ThemeConfig>(DEFAULT_THEME);
  const [activeLayer, setActiveLayer] = useState<'3s' | '30s' | '300s'>('3s');

  const updateTheme = (partial: Partial<ThemeConfig>) => {
    setTheme((prev) => ({ ...prev, ...partial }));
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 'var(--sp-3)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* Left: Theme Editor */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--sp-2)',
          overflow: 'auto',
        }}
      >
        {/* Presets */}
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
          }}
        >
          <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1-5)' }}>
            Presets
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-1)' }}>
            {Object.entries(PRESET_THEMES).map(([name, preset]) => (
              <button
                key={name}
                onClick={() => updateTheme(preset)}
                style={{
                  padding: 'var(--sp-1)',
                  backgroundColor: 'var(--slate-900)',
                  border: '1px solid var(--slate-700)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.primary }} />
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.secondary }} />
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.background }} />
                </div>
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-300)' }}>{name}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Color Editors */}
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
          }}
        >
          <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1-5)' }}>
            Colors
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1-5)' }}>
            <ColorPicker label="Primary" value={theme.primary} onChange={(v) => updateTheme({ primary: v })} />
            <ColorPicker label="Secondary" value={theme.secondary} onChange={(v) => updateTheme({ secondary: v })} />
            <ColorPicker label="Accent" value={theme.accent} onChange={(v) => updateTheme({ accent: v })} />
            <ColorPicker label="Background" value={theme.background} onChange={(v) => updateTheme({ background: v })} />
            <ColorPicker label="Surface" value={theme.surface} onChange={(v) => updateTheme({ surface: v })} />
            <ColorPicker label="Text" value={theme.text} onChange={(v) => updateTheme({ text: v })} />
          </div>
        </div>

        {/* Typography & Spacing */}
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
          }}
        >
          <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1-5)' }}>
            Typography & Layout
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--slate-400)', display: 'block', marginBottom: '4px' }}>Font Family</label>
              <select
                value={theme.fontFamily}
                onChange={(e) => updateTheme({ fontFamily: e.target.value })}
                style={{
                  width: '100%',
                  padding: 'var(--sp-0-5) var(--sp-1)',
                  backgroundColor: 'var(--slate-900)',
                  border: '1px solid var(--slate-700)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--slate-100)',
                  fontSize: '0.8125rem',
                }}
              >
                <option value="Inter">Inter</option>
                <option value="DM Sans">DM Sans</option>
                <option value="Plus Jakarta Sans">Plus Jakarta Sans</option>
                <option value="IBM Plex Sans">IBM Plex Sans</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--slate-400)', display: 'block', marginBottom: '4px' }}>
                Border Radius ({theme.borderRadius}px)
              </label>
              <input
                type="range"
                min={0}
                max={24}
                step={2}
                value={theme.borderRadius}
                onChange={(e) => updateTheme({ borderRadius: Number(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Right: Preview */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
        {/* Layer Tabs */}
        <div style={{ display: 'flex', gap: 'var(--sp-1)' }}>
          {(['3s', '30s', '300s'] as const).map((layer) => (
            <button
              key={layer}
              onClick={() => setActiveLayer(layer)}
              style={{
                padding: 'var(--sp-1) var(--sp-2)',
                backgroundColor: activeLayer === layer ? 'var(--slate-700)' : 'var(--slate-800)',
                border: `1px solid ${activeLayer === layer ? 'var(--mint)' : 'var(--slate-700)'}`,
                borderRadius: 'var(--radius-md)',
                color: activeLayer === layer ? 'var(--slate-50)' : 'var(--slate-400)',
                fontSize: '0.8125rem',
                fontWeight: activeLayer === layer ? 600 : 400,
                cursor: 'pointer',
                transition: 'all var(--duration-fast) var(--ease-out)',
              }}
            >
              {layer === '3s' ? 'Pulse (3s)' : layer === '30s' ? 'Investigator (30s)' : 'Action (300s)'}
            </button>
          ))}
        </div>

        {/* Live Preview */}
        <div style={{ flex: 1 }}>
          <LayoutPreview theme={theme} layer={activeLayer} />
        </div>

        {/* All layers side by side */}
        <div>
          <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1)' }}>
            3-30-300 Overview
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--sp-1)' }}>
            {(['3s', '30s', '300s'] as const).map((layer) => (
              <div key={layer} style={{ transform: 'scale(1)', transformOrigin: 'top left' }}>
                <LayoutPreview theme={theme} layer={layer} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
