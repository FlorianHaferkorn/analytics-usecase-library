'use client';

import { useState, useCallback } from 'react';
import { ColorPicker } from '@/components/brand/color-picker';
import { LayoutPreview } from '@/components/brand/layout-preview';
import { VisualGallery } from '@/components/brand/visual-gallery';
import { DashboardLayout } from '@/components/dashboard/dashboard-layout';
import { ThemeExportPanel } from '@/components/brand/theme-export-panel';
import { CssPreview } from '@/components/brand/css-preview';
import { ContrastBadge } from '@/components/brand/contrast-badge';
import { useProjectStore, DEFAULT_THEME } from '@/lib/store/project-store';
import type { ThemeConfig } from '@/lib/store/project-store';
import { StudioButton, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioSegmentedControl, StudioToolbar } from '@/components/ui/studio-page';

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
  const [activeBottomTab, setActiveBottomTab] = useState<'overview' | 'gallery'>('overview');
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

  const themeChanged = JSON.stringify(theme) !== JSON.stringify(DEFAULT_THEME);

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Design"
        title="Brand Lab"
        description="Tune theme tokens, preview the 3-30-300 experience, and export a coherent visual language without page-specific styling drift."
        badge={theme.fontFamily}
        tone="warning"
        actions={<StudioButton onClick={() => void handleSaveTheme()} tone="warning" variant="primary" disabled={saving}>{saving ? 'Saving…' : 'Save Theme'}</StudioButton>}
      />

      <StudioMetricBar>
        <StudioMetric label="Preset state" value={themeChanged ? 'custom' : 'default'} meta="theme token divergence" tone={themeChanged ? 'warning' : 'success'} />
        <StudioMetric label="Preview layer" value={activeLayer} meta="active dashboard focus" tone="info" />
        <StudioMetric label="Preview tab" value={activeBottomTab} meta="bottom canvas mode" />
      </StudioMetricBar>

      <div style={{ display: 'grid', gridTemplateColumns: '320px minmax(0, 1fr)', gap: 'var(--sp-3)', minHeight: 0, flex: 1 }}>
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
        <StudioPanel title="Presets" description="Seed the theme with a visual direction before fine-tuning individual tokens." tone="warning">
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
        </StudioPanel>

        {/* Color Editors */}
        <StudioPanel title="Colors" description="Work directly on primary, contrast, surface and accent tokens." tone="info">
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
        </StudioPanel>

        {/* Typography & Spacing */}
        <StudioPanel title="Typography & Layout" description="Control typography rhythm, radius and shadow from one governed surface.">
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
        </StudioPanel>
      </div>

      {/* Right: Preview */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
        <StudioToolbar>
          <StudioSegmentedControl
            value={activeLayer}
            onChange={setActiveLayer}
            options={[
              { value: '3s', label: 'Pulse (3s)' },
              { value: '30s', label: 'Investigator (30s)' },
              { value: '300s', label: 'Action (300s)' },
            ]}
          />
        </StudioToolbar>

        {/* Live Dashboard Preview */}
        <StudioPanel title="Live Dashboard Preview" description="Inspect the active layer with the current theme tokens applied." tone="success" style={{ flex: 1 }}>
          <DashboardLayout theme={theme} layer={activeLayer} />
        </StudioPanel>

        {/* Bottom: 3-30-300 Overview + Visual Gallery (tabbed) */}
        <StudioPanel title="Preview Modes" description="Switch between structural overview and visual gallery without leaving the page.">
          <div style={{ marginBottom: 'var(--sp-1)' }}>
            <StudioSegmentedControl
              value={activeBottomTab}
              onChange={setActiveBottomTab}
              options={[
                { value: 'overview', label: '3-30-300 Übersicht' },
                { value: 'gallery', label: 'Visual Gallery' },
              ]}
            />
          </div>

          {activeBottomTab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--sp-1)' }}>
              {(['3s', '30s', '300s'] as const).map((layer) => (
                <div key={layer}>
                  <LayoutPreview theme={theme} layer={layer} />
                </div>
              ))}
            </div>
          )}

          {activeBottomTab === 'gallery' && (
            <VisualGallery theme={theme} />
          )}
        </StudioPanel>

        {/* CSS Preview + Export */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-2)' }}>
          <CssPreview theme={theme} />
          <ThemeExportPanel theme={theme} onSave={handleSaveTheme} saving={saving} />
        </div>
      </div>
      </div>
    </StudioPage>
  );
}
