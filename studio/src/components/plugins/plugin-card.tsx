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
  const typeColor = TYPE_COLORS[manifest.type] ?? 'var(--slate-400)';
  const registeredLabel = Number.isFinite(plugin.registeredAt)
    ? new Date(plugin.registeredAt).toLocaleDateString('de-DE')
    : 'n/a';

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        background: enabled
          ? `linear-gradient(180deg, color-mix(in srgb, var(--slate-800) 88%, ${typeColor} 12%), var(--slate-800))`
          : 'linear-gradient(180deg, var(--slate-850, #202835), var(--slate-800))',
        borderRadius: 'var(--radius-lg)',
        border: `1px solid ${enabled ? 'color-mix(in srgb, var(--slate-700) 75%, ' + typeColor + ' 25%)' : 'var(--slate-700)'}`,
        opacity: enabled ? 1 : 0.72,
        boxShadow: enabled ? `0 18px 40px color-mix(in srgb, ${typeColor} 10%, transparent)` : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--sp-1)', marginBottom: 'var(--sp-1)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
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
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
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
            style={{ backgroundColor: 'transparent', border: '1px solid var(--slate-700)', color: 'var(--slate-400)', cursor: 'pointer', fontSize: '0.875rem', borderRadius: 'var(--radius-sm)', width: '28px', height: '28px' }}
          >
            ×
          </StudioButton>
        </div>
      </div>
      <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginBottom: 'var(--sp-1)' }}>
        {manifest.description}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px', marginBottom: 'var(--sp-1)' }}>
        <div style={{ padding: '8px 10px', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)', borderRadius: 'var(--radius-md)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>Entrypoint</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-200)', fontFamily: 'var(--font-mono)' }}>{manifest.entrypoint}</p>
        </div>
        <div style={{ padding: '8px 10px', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)', borderRadius: 'var(--radius-md)' }}>
          <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>Lifecycle</p>
          <p style={{ fontSize: '0.75rem', color: manifest.lifecycle ? 'var(--mint)' : 'var(--slate-400)' }}>{manifest.lifecycle ? 'registered' : 'not declared'}</p>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center', fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
        <span style={{ color: 'var(--slate-400)' }}>Hooks</span>
        {manifest.hooks && manifest.hooks.length > 0 ? manifest.hooks.map((hook) => (
          <span
            key={hook}
            style={{
              padding: '4px 8px',
              borderRadius: '9999px',
              border: '1px solid var(--slate-700)',
              backgroundColor: 'var(--slate-900)',
              color: 'var(--slate-300)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {hook}
          </span>
        )) : (
          <span style={{ color: 'var(--slate-500)' }}>none</span>
        )}
      </div>
    </div>
  );
}
