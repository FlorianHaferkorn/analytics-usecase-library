'use client';

import { useState, useCallback } from 'react';
import { ColorPicker } from '@/components/brand/color-picker';
import { LayoutPreview } from '@/components/brand/layout-preview';
import { DashboardLayout } from '@/components/dashboard/dashboard-layout';
import { ThemeExportPanel } from '@/components/brand/theme-export-panel';
import { CssPreview } from '@/components/brand/css-preview';
import { ContrastBadge } from '@/components/brand/contrast-badge';
import { useProjectStore, DEFAULT_THEME } from '@/lib/store/project-store';
import type { ThemeConfig } from '@/lib/store/project-store';

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
  const theme = useProjectStore((s) => s.theme);
  const projectId = useProjectStore((s) => s.projectId);
  const storeSetTheme = useProjectStore((s) => s.setTheme);
  const [activeLayer, setActiveLayer] = useState<'3s' | '30s' | '300s'>('3s');
  const [saving, setSaving] = useState(false);

  const updateTheme = (partial: Partial<ThemeConfig>) => {
    storeSetTheme(partial);
  };

  const handleSaveTheme = useCallback(async () => {
    setSaving(true);
    try {
      await fetch('/api/theme', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId, theme }),
      });
    } finally {
      setSaving(false);
    }
  }, [projectId, theme]);

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
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
              <div style={{ flex: 1 }}><ColorPicker label="Primary" value={theme.primary} onChange={(v) => updateTheme({ primary: v })} /></div>
              <ContrastBadge fg={theme.primary} bg={theme.background} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
              <div style={{ flex: 1 }}><ColorPicker label="Secondary" value={theme.secondary} onChange={(v) => updateTheme({ secondary: v })} /></div>
              <ContrastBadge fg={theme.secondary} bg={theme.background} />
            </div>
            <ColorPicker label="Accent" value={theme.accent} onChange={(v) => updateTheme({ accent: v })} />
            <ColorPicker label="Background" value={theme.background} onChange={(v) => updateTheme({ background: v })} />
            <ColorPicker label="Surface" value={theme.surface} onChange={(v) => updateTheme({ surface: v })} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
              <div style={{ flex: 1 }}><ColorPicker label="Text" value={theme.text} onChange={(v) => updateTheme({ text: v })} /></div>
              <ContrastBadge fg={theme.text} bg={theme.background} />
            </div>
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
                Font Weight ({theme.fontWeight ?? 400})
              </label>
              <input
                type="range"
                min={300}
                max={700}
                step={100}
                value={theme.fontWeight ?? 400}
                onChange={(e) => updateTheme({ fontWeight: Number(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--slate-400)', display: 'block', marginBottom: '4px' }}>
                Line Height ({theme.lineHeight ?? 1.5})
              </label>
              <input
                type="range"
                min={1.25}
                max={1.75}
                step={0.05}
                value={theme.lineHeight ?? 1.5}
                onChange={(e) => updateTheme({ lineHeight: Number(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--slate-400)', display: 'block', marginBottom: '4px' }}>
                Letter Spacing ({(theme.letterSpacing ?? 0).toFixed(3)}em)
              </label>
              <input
                type="range"
                min={-0.025}
                max={0.05}
                step={0.005}
                value={theme.letterSpacing ?? 0}
                onChange={(e) => updateTheme({ letterSpacing: Number(e.target.value) })}
                style={{ width: '100%' }}
              />
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
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--slate-400)', display: 'block', marginBottom: '4px' }}>Shadow</label>
              <select
                value={theme.shadow ?? 'none'}
                onChange={(e) => updateTheme({ shadow: e.target.value })}
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
                <option value="none">None</option>
                <option value="0 1px 2px rgba(0,0,0,0.25)">Small</option>
                <option value="0 4px 6px rgba(0,0,0,0.3)">Medium</option>
                <option value="0 10px 15px rgba(0,0,0,0.35)">Large</option>
                <option value="0 20px 25px rgba(0,0,0,0.4)">Extra Large</option>
              </select>
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

        {/* Live Dashboard Preview */}
        <div style={{ flex: 1 }}>
          <DashboardLayout theme={theme} layer={activeLayer} />
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

        {/* CSS Preview + Export */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)' }}>
          <CssPreview theme={theme} />
          <ThemeExportPanel theme={theme} onSave={handleSaveTheme} saving={saving} />
        </div>
      </div>
    </div>
  );
}
