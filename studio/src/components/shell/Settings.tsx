'use client';

import { useEffect, useState } from 'react';

type FontId = 'inter' | 'ibm' | 'geist' | 'serif';

interface SettingsState {
  theme: 'dark' | 'light';
  density: 'airy' | 'balanced' | 'dense';
  fonts: FontId;
  accentHue: number;
}

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

const ACCENT_PRESETS = [
  { name: 'Indigo', hue: 250 },
  { name: 'Emerald', hue: 150 },
  { name: 'Amber', hue: 75 },
  { name: 'Rose', hue: 20 },
  { name: 'Violet', hue: 290 },
  { name: 'Teal', hue: 190 },
  { name: 'Graphite', hue: 250, isMonochrome: true },
];

const FONT_PAIRINGS: Array<{ id: FontId; name: string; family: string }> = [
  { id: 'inter', name: 'Inter + JetBrains Mono', family: 'Inter' },
  { id: 'ibm', name: 'IBM Plex Sans + IBM Plex Mono', family: 'IBM Plex Sans' },
  { id: 'geist', name: 'Geist + Geist Mono', family: 'Geist' },
  { id: 'serif', name: 'Instrument Serif + Inter', family: 'Instrument Serif' },
];

export function Settings({ isOpen, onClose }: SettingsProps) {
  const [settings, setSettings] = useState<SettingsState>({
    theme: 'dark',
    density: 'balanced',
    fonts: 'inter',
    accentHue: 250,
  });

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('studio-settings-v1');
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch {}
    }
  }, [isOpen]);

  // Save to localStorage and update DOM
  const updateSettings = (partial: Partial<SettingsState>) => {
    const updated = { ...settings, ...partial };
    setSettings(updated);
    localStorage.setItem('studio-settings-v1', JSON.stringify(updated));

    // Apply to DOM
    const html = document.documentElement;
    if (partial.theme) html.setAttribute('data-theme', partial.theme);
    if (partial.density) html.setAttribute('data-density', partial.density);
    if (partial.fonts) html.setAttribute('data-fonts', partial.fonts);
    if (partial.accentHue !== undefined) {
      html.style.setProperty('--accent-hue', String(partial.accentHue));
      // Recalculate accent colors
      const L = 0.62;
      const C = 0.13;
      const H = partial.accentHue;
      html.style.setProperty('--accent', `oklch(${L} ${C} ${H})`);
      html.style.setProperty('--accent-soft', `oklch(${L} ${C} ${H} / 0.14)`);
      const accentInk =
        partial.theme === 'light'
          ? `oklch(0.98 0.01 ${H})`
          : `oklch(0.12 0.02 ${H})`;
      html.style.setProperty('--accent-ink', accentInk);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 z-modal flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md max-h-96 bg-panel rounded-lg shadow-lg border border-border flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-border px-6 py-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground font-display">Settings</h2>
          <button
            onClick={onClose}
            className="p-1 rounded text-foreground-subtle hover:bg-hover transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
              <line x1="2" y1="2" x2="14" y2="14" strokeWidth="1.5" />
              <line x1="14" y1="2" x2="2" y2="14" strokeWidth="1.5" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1 px-6 py-4 flex flex-col gap-6">
          {/* Theme */}
          <div>
            <label className="block text-xs font-semibold text-foreground-subtle mb-3">Theme</label>
            <div className="flex gap-2">
              {(['dark', 'light'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => updateSettings({ theme: t })}
                  className={`flex-1 px-3 py-2 rounded text-xs font-medium transition-colors ${
                    settings.theme === t
                      ? 'bg-accent text-accent-ink'
                      : 'bg-bg text-foreground-muted hover:bg-hover'
                  }`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Accent */}
          <div>
            <label className="block text-xs font-semibold text-foreground-subtle mb-3">Accent Color</label>
            <div className="grid grid-cols-4 gap-2 mb-3">
              {ACCENT_PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => updateSettings({ accentHue: preset.hue })}
                  className="p-2 rounded text-xs font-medium transition-all border-2"
                  style={{
                    borderColor: settings.accentHue === preset.hue ? 'var(--accent)' : 'transparent',
                    backgroundColor: `oklch(0.62 0.13 ${preset.hue})`,
                  }}
                  title={preset.name}
                >
                  {preset.isMonochrome ? 'Mono' : '●'}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="360"
                step="1"
                value={settings.accentHue}
                onChange={(e) => updateSettings({ accentHue: Number(e.target.value) })}
                className="flex-1 h-2 bg-line rounded-full"
              />
              <span className="text-xs text-foreground-subtle w-8">{settings.accentHue}°</span>
            </div>
          </div>

          {/* Density */}
          <div>
            <label className="block text-xs font-semibold text-foreground-subtle mb-3">Density</label>
            <div className="flex gap-2">
              {(['airy', 'balanced', 'dense'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => updateSettings({ density: d })}
                  className={`flex-1 px-3 py-2 rounded text-xs font-medium transition-colors ${
                    settings.density === d
                      ? 'bg-accent text-accent-ink'
                      : 'bg-bg text-foreground-muted hover:bg-hover'
                  }`}
                >
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Fonts */}
          <div>
            <label className="block text-xs font-semibold text-foreground-subtle mb-3">Font Pairing</label>
            <div className="flex flex-col gap-2">
              {FONT_PAIRINGS.map((fp) => (
                <button
                  key={fp.id}
                  onClick={() => updateSettings({ fonts: fp.id })}
                  className={`px-3 py-2 rounded text-xs transition-colors text-left ${
                    settings.fonts === fp.id
                      ? 'bg-accent text-accent-ink'
                      : 'bg-bg text-foreground-muted hover:bg-hover'
                  }`}
                  style={{ fontFamily: fp.family }}
                >
                  {fp.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-3 bg-bg-2 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-accent text-accent-ink text-xs font-medium hover:opacity-90 transition-opacity"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
