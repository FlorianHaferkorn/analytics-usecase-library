'use client';

import { useState, useCallback, useEffect } from 'react';
import { ColorPicker } from '@/components/brand/color-picker';
import { LayoutPreview } from '@/components/brand/layout-preview';
import { DashboardLayout } from '@/components/dashboard/dashboard-layout';
import { ThemeExportPanel } from '@/components/brand/theme-export-panel';
import { CssPreview } from '@/components/brand/css-preview';
import { ContrastBadge } from '@/components/brand/contrast-badge';
import { useProjectStore, DEFAULT_THEME } from '@/lib/store/project-store';
import type { ThemeConfig } from '@/lib/store/project-store';
import { StudioFormField, StudioSelect } from '@/components/ui/studio-data';
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

type RightTab = '3s' | '30s' | '300s' | 'overview' | 'export';

const RIGHT_TABS: Array<{ value: RightTab; label: string }> = [
  { value: '3s', label: 'Pulse (3s)' },
  { value: '30s', label: 'Investigator (30s)' },
  { value: '300s', label: 'Action (300s)' },
  { value: 'overview', label: '3-30-300' },
  { value: 'export', label: 'Export' },
];

export function BrandLabClient() {
  const theme = useProjectStore((s) => s.theme);
  const projectId = useProjectStore((s) => s.projectId);
  const storeSetTheme = useProjectStore((s) => s.setTheme);
  const [activeTab, setActiveTab] = useState<RightTab>('3s');
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

  // Dynamically load Google Font whenever fontFamily changes
  useEffect(() => {
    const family = theme.fontFamily;
    if (!family || family === 'system-ui') return;
    const id = 'brand-lab-gfont';
    let link = document.getElementById(id) as HTMLLinkElement | null;
    if (!link) {
      link = document.createElement('link');
      link.id = id;
      link.rel = 'stylesheet';
      document.head.appendChild(link);
    }
    const encoded = family.replace(/ /g, '+');
    link.href = `https://fonts.googleapis.com/css2?family=${encoded}:wght@300;400;500;600;700&display=swap`;
  }, [theme.fontFamily]);

  const themeChanged = JSON.stringify(theme) !== JSON.stringify(DEFAULT_THEME);

  // Detect which preset (if any) is currently active
  const activePreset = Object.entries(PRESET_THEMES).find(([, preset]) =>
    Object.entries(preset).every(([key, value]) => theme[key as keyof ThemeConfig] === value)
  )?.[0] ?? null;

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Design"
        title="Brand Lab"
        description="Tune theme tokens, preview the 3-30-300 experience, and export a coherent visual language without page-specific styling drift."
        badge={theme.fontFamily}
        tone="warning"
        actions={
          <>
            {themeChanged && (
              <StudioButton
                onClick={() => storeSetTheme(DEFAULT_THEME)}
                tone="default"
                variant="ghost"
              >
                Reset
              </StudioButton>
            )}
            <StudioButton onClick={() => void handleSaveTheme()} tone="warning" variant="primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save Theme'}
            </StudioButton>
          </>
        }
      />

      <StudioMetricBar>
        <StudioMetric label="Theme" value={themeChanged ? 'custom' : 'default'} meta={themeChanged ? 'diverges from default' : 'using default tokens'} tone={themeChanged ? 'warning' : 'success'} />
        <StudioMetric label="Primary" value={theme.primary.toUpperCase()} meta="accent color token" tone="info" />
        <StudioMetric label="Radius" value={`${theme.borderRadius}px`} meta="border radius token" />
        <StudioMetric label="Weight" value={String(theme.fontWeight ?? 400)} meta="global font weight" />
      </StudioMetricBar>

      <div style={{ display: 'grid', gridTemplateColumns: '320px minmax(0, 1fr)', gap: 'var(--sp-2)', minHeight: 0, flex: 1 }}>
      {/* Left: Theme Editor */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--sp-1-5)',
          overflow: 'auto',
        }}
      >
        {/* Presets */}
        <StudioPanel title="Presets" description="Seed the theme with a visual direction before fine-tuning individual tokens." tone="warning">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-1)' }}>
            {Object.entries(PRESET_THEMES).map(([name, preset]) => {
              const isActive = activePreset === name;
              return (
                <StudioButton
                  key={name}
                  onClick={() => updateTheme(preset)}
                  variant="ghost"
                  style={{
                    padding: 'var(--sp-1)',
                    backgroundColor: isActive ? 'var(--slate-800)' : 'var(--slate-900)',
                    border: isActive ? `1px solid ${preset.primary}` : '1px solid var(--slate-700)',
                    textAlign: 'left',
                    display: 'block',
                    width: '100%',
                    position: 'relative',
                  }}
                >
                  {isActive && (
                    <span style={{
                      position: 'absolute', top: '6px', right: '6px',
                      fontSize: '0.5rem', fontWeight: 700, color: preset.primary,
                      textTransform: 'uppercase', letterSpacing: '0.06em',
                    }}>Active</span>
                  )}
                  <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
                    <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.primary }} />
                    <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.secondary }} />
                    <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: preset.background }} />
                  </div>
                  <p style={{ margin: 0, fontSize: '0.6875rem', color: isActive ? 'var(--slate-100)' : 'var(--slate-300)' }}>{name}</p>
                </StudioButton>
              );
            })}
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
            <StudioFormField label="Font Family">
              <StudioSelect
                value={theme.fontFamily}
                onChange={(e) => updateTheme({ fontFamily: e.target.value })}
                style={{
                  padding: 'var(--sp-0-5) var(--sp-1)',
                  fontSize: '0.8125rem',
                }}
              >
                <option value="Inter">Inter</option>
                <option value="DM Sans">DM Sans</option>
                <option value="Plus Jakarta Sans">Plus Jakarta Sans</option>
                <option value="IBM Plex Sans">IBM Plex Sans</option>
              </StudioSelect>
            </StudioFormField>
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
            <StudioFormField label="Shadow">
              <StudioSelect
                value={theme.shadow ?? 'none'}
                onChange={(e) => updateTheme({ shadow: e.target.value })}
                style={{
                  padding: 'var(--sp-0-5) var(--sp-1)',
                  fontSize: '0.8125rem',
                }}
              >
                <option value="none">None</option>
                <option value="0 1px 2px rgba(0,0,0,0.25)">Small</option>
                <option value="0 4px 6px rgba(0,0,0,0.3)">Medium</option>
                <option value="0 10px 15px rgba(0,0,0,0.35)">Large</option>
                <option value="0 20px 25px rgba(0,0,0,0.4)">Extra Large</option>
              </StudioSelect>
            </StudioFormField>
          </div>
        </StudioPanel>
      </div>

      {/* Right: Tabbed Preview & Export */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1-5)', minHeight: 0 }}>
        <StudioToolbar>
          <StudioSegmentedControl
            value={activeTab}
            onChange={setActiveTab}
            options={RIGHT_TABS}
          />
        </StudioToolbar>

        {/* Dashboard layers */}
        {(activeTab === '3s' || activeTab === '30s' || activeTab === '300s') && (
          <StudioPanel title="Live Dashboard Preview" description="Inspect the active layer with the current theme tokens applied." tone="success" style={{ flex: 1 }}>
            <DashboardLayout theme={theme} layer={activeTab} />
          </StudioPanel>
        )}

        {/* 3-30-300 overview thumbnails */}
        {activeTab === 'overview' && (
          <StudioPanel title="Page Templates" description="Click any template to open the full interactive preview." style={{ flex: 1 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--sp-1-5)' }}>
              {([
                { layer: '3s' as const, label: 'Pulse (3s)', desc: 'Status KPI cards' },
                { layer: '30s' as const, label: 'Investigator (30s)', desc: 'Trend + waterfall' },
                { layer: '300s' as const, label: 'Action (300s)', desc: 'Evidence grid' },
              ]).map(({ layer, label, desc }) => (
                <button
                  key={layer}
                  onClick={() => setActiveTab(layer)}
                  style={{
                    background: 'none',
                    border: '1px solid var(--slate-700)',
                    borderRadius: 'var(--radius-md)',
                    padding: 0,
                    cursor: 'pointer',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--slate-500)')}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--slate-700)')}
                >
                  <LayoutPreview theme={theme} layer={layer} />
                  <div style={{ padding: 'var(--sp-1) var(--sp-1-5)', borderTop: '1px solid var(--slate-700)', textAlign: 'left' }}>
                    <p style={{ margin: 0, fontSize: '0.75rem', fontWeight: 600, color: 'var(--slate-100)' }}>{label}</p>
                    <p style={{ margin: 0, fontSize: '0.6875rem', color: 'var(--slate-500)', marginTop: '2px' }}>{desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </StudioPanel>
        )}

        {/* Export */}
        {activeTab === 'export' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1-5)', flex: 1 }}>
            <CssPreview theme={theme} />
            <ThemeExportPanel theme={theme} />
          </div>
        )}
      </div>
      </div>
    </StudioPage>
  );
}
