'use client';

import { useState, useEffect, useCallback } from 'react';
import type { RegisteredPlugin } from '@/lib/plugins/plugin-types';
import { PluginCard } from '@/components/plugins/plugin-card';

export function PluginsClient() {
  const [plugins, setPlugins] = useState<RegisteredPlugin[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPlugins = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/plugins');
      const data = await res.json();
      setPlugins(data.plugins ?? []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPlugins(); }, [loadPlugins]);

  const handleToggle = useCallback(async (pluginId: string, enabled: boolean) => {
    await fetch('/api/plugins', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pluginId, enabled }),
    });
    setPlugins((prev) =>
      prev.map((p) =>
        p.manifest.id === pluginId ? { ...p, enabled } : p,
      ),
    );
  }, []);

  const handleRemove = useCallback(async (pluginId: string) => {
    await fetch(`/api/plugins?pluginId=${pluginId}`, { method: 'DELETE' });
    setPlugins((prev) => prev.filter((p) => p.manifest.id !== pluginId));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-50)' }}>
            Plugins
          </h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', marginTop: '4px' }}>
            Manage extensions that add tools, widgets, and data sources to Studio.
          </p>
        </div>
        <span
          style={{
            padding: '4px var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--slate-700)',
            fontSize: '0.75rem',
            color: 'var(--slate-300)',
          }}
        >
          {plugins.length} plugin{plugins.length !== 1 ? 's' : ''} installed
        </span>
      </div>

      {loading ? (
        <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>Loading plugins...</p>
      ) : plugins.length === 0 ? (
        <div
          style={{
            padding: 'var(--sp-4)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
            textAlign: 'center',
          }}
        >
          <p style={{ fontSize: '0.875rem', color: 'var(--slate-300)', marginBottom: 'var(--sp-1)' }}>
            No plugins installed
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>
            Add plugin manifests to the <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--mint)' }}>/plugins</code> directory to get started.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
          {plugins.map((p) => (
            <PluginCard
              key={p.manifest.id}
              plugin={p}
              onToggle={handleToggle}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}

      {/* SDK Documentation */}
      <div
        style={{
          padding: 'var(--sp-2)',
          backgroundColor: 'var(--slate-800)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
        }}
      >
        <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1)' }}>
          Plugin SDK
        </h3>
        <pre
          style={{
            fontSize: '0.6875rem',
            color: 'var(--slate-300)',
            fontFamily: 'var(--font-mono)',
            backgroundColor: 'var(--slate-900)',
            padding: 'var(--sp-1-5)',
            borderRadius: 'var(--radius-md)',
            overflow: 'auto',
            lineHeight: 1.5,
          }}
        >
{`// plugins/my-plugin/manifest.json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "Your Team",
  "type": "tool",
  "description": "Adds custom KPI calculations",
  "entrypoint": "index.ts",
  "hooks": ["onKpiEvaluate"]
}`}
        </pre>
      </div>
    </div>
  );
}
