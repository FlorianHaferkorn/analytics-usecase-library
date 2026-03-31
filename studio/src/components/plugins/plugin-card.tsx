'use client';

import type { RegisteredPlugin } from '@/lib/plugins/plugin-types';

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

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        opacity: enabled ? 1 : 0.5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--sp-1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            {manifest.name}
          </span>
          <span
            style={{
              fontSize: '0.5625rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: typeColor,
              padding: '1px 6px',
              backgroundColor: `color-mix(in srgb, ${typeColor} 15%, transparent)`,
              borderRadius: 'var(--radius-sm)',
            }}
          >
            {manifest.type}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={() => onToggle(manifest.id, !enabled)}
            style={{ accentColor: 'var(--mint)' }}
          />
          <button
            onClick={() => onRemove(manifest.id)}
            style={{ background: 'none', border: 'none', color: 'var(--slate-500)', cursor: 'pointer', fontSize: '0.875rem' }}
          >
            ×
          </button>
        </div>
      </div>
      <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginBottom: 'var(--sp-1)' }}>
        {manifest.description}
      </p>
      <div style={{ display: 'flex', gap: 'var(--sp-2)', fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
        <span>v{manifest.version}</span>
        <span>by {manifest.author}</span>
        {manifest.hooks && manifest.hooks.length > 0 && (
          <span>Hooks: {manifest.hooks.join(', ')}</span>
        )}
      </div>
    </div>
  );
}
