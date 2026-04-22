'use client';

import type { RegisteredPlugin } from '@/lib/plugins/plugin-types';
import { StudioButton } from '@/components/ui/studio-page';

interface Props {
  plugin: RegisteredPlugin;
  onToggle: (id: string, enabled: boolean) => void;
  onRemove: (id: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  tool: 'var(--mint)',
  widget: 'var(--gold)',
  datasource: 'var(--info)',
};

export function PluginCard({ plugin, onToggle, onRemove }: Props) {
  const { manifest, enabled } = plugin;
  const typeColor = TYPE_COLORS[manifest.type] ?? 'var(--ink-3)';
  const registeredLabel = Number.isFinite(plugin.registeredAt)
    ? new Date(plugin.registeredAt).toLocaleDateString('de-DE')
    : 'n/a';

  return (
    <div
      style={{
        padding: '16px',
        background: enabled
          ? `linear-gradient(180deg, color-mix(in srgb, var(--panel) 88%, ${typeColor} 12%), var(--panel))`
          : 'var(--panel)',
        borderRadius: 'var(--radius-lg)',
        border: `1px solid ${enabled ? 'color-mix(in srgb, var(--line) 75%, ' + typeColor + ' 25%)' : 'var(--line)'}`,
        opacity: enabled ? 1 : 0.72,
        boxShadow: enabled ? `0 18px 40px color-mix(in srgb, ${typeColor} 10%, transparent)` : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '8px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)' }}>
              {manifest.name}
            </span>
            <span
              style={{
                fontSize: '0.5625rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                color: typeColor,
                padding: '2px 7px',
                backgroundColor: `color-mix(in srgb, ${typeColor} 15%, transparent)`,
                borderRadius: 'var(--radius-sm)',
                border: `1px solid color-mix(in srgb, ${typeColor} 30%, transparent)`,
              }}
            >
              {manifest.type}
            </span>
            <span
              style={{
                fontSize: '0.5625rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                color: enabled ? 'var(--mint)' : 'var(--gold)',
                padding: '2px 7px',
                backgroundColor: enabled ? 'color-mix(in srgb, var(--mint) 14%, transparent)' : 'color-mix(in srgb, var(--gold) 14%, transparent)',
                borderRadius: 'var(--radius-sm)',
                border: `1px solid ${enabled ? 'color-mix(in srgb, var(--mint) 30%, transparent)' : 'color-mix(in srgb, var(--gold) 30%, transparent)'}`,
              }}
            >
              {enabled ? 'enabled' : 'disabled'}
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '0.6875rem', color: 'var(--ink-4)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--info)' }}>{manifest.id}</span>
            <span>v{manifest.version}</span>
            <span>{manifest.author}</span>
            <span>added {registeredLabel}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={() => onToggle(manifest.id, !enabled)}
            style={{ accentColor: 'var(--mint)' }}
          />
          <StudioButton
            onClick={() => onRemove(manifest.id)}
            tone="warning"
            variant="ghost"
            style={{ backgroundColor: 'transparent', border: '1px solid var(--line)', color: 'var(--ink-3)', cursor: 'pointer', fontSize: '0.875rem', borderRadius: 'var(--radius-sm)', width: '28px', height: '28px' }}
          >
            ×
          </StudioButton>
        </div>
      </div>
      <p style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginBottom: '8px' }}>
        {manifest.description}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px', marginBottom: '8px' }}>
        <div style={{ padding: '8px 10px', backgroundColor: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>Entrypoint</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--ink-2)', fontFamily: 'var(--font-mono)' }}>{manifest.entrypoint}</p>
        </div>
        <div style={{ padding: '8px 10px', backgroundColor: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>Lifecycle</p>
          <p style={{ fontSize: '0.75rem', color: manifest.lifecycle ? 'var(--mint)' : 'var(--ink-3)' }}>{manifest.lifecycle ? 'registered' : 'not declared'}</p>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '0.6875rem', color: 'var(--ink-4)' }}>
        <span style={{ color: 'var(--ink-3)' }}>Hooks</span>
        {manifest.hooks && manifest.hooks.length > 0 ? manifest.hooks.map((hook) => (
          <span
            key={hook}
            style={{
              padding: '4px 8px',
              borderRadius: '9999px',
              border: '1px solid var(--line)',
              backgroundColor: 'var(--bg-2)',
              color: 'var(--ink-2)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {hook}
          </span>
        )) : (
          <span style={{ color: 'var(--ink-4)' }}>none</span>
        )}
      </div>
    </div>
  );
}
