'use client';

import { useState, useEffect, useCallback, useMemo, type ReactNode } from 'react';
import type { RegisteredPlugin } from '@/lib/plugins/plugin-types';
import { ALL_HOOKS } from '@/lib/plugins/hook-contracts';
import { PluginCard } from '@/components/plugins/plugin-card';
import { StudioInput } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel } from '@/components/ui/studio-page';

export function PluginsClient() {
  const [plugins, setPlugins] = useState<RegisteredPlugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'tool' | 'widget' | 'datasource'>('all');
  const [stateFilter, setStateFilter] = useState<'all' | 'enabled' | 'disabled'>('all');

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

  const filteredPlugins = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return plugins.filter((plugin) => {
      const matchesQuery = normalizedQuery.length === 0 || [
        plugin.manifest.id,
        plugin.manifest.name,
        plugin.manifest.author,
        plugin.manifest.description,
        ...(plugin.manifest.hooks ?? []),
      ].some((value) => value.toLowerCase().includes(normalizedQuery));

      const matchesType = typeFilter === 'all' || plugin.manifest.type === typeFilter;
      const matchesState = stateFilter === 'all' || (stateFilter === 'enabled' ? plugin.enabled : !plugin.enabled);

      return matchesQuery && matchesType && matchesState;
    });
  }, [plugins, query, typeFilter, stateFilter]);

  const stats = useMemo(() => {
    const enabledCount = plugins.filter((plugin) => plugin.enabled).length;
    const disabledCount = plugins.length - enabledCount;
    const totalHooks = plugins.reduce((sum, plugin) => sum + (plugin.manifest.hooks?.length ?? 0), 0);
    const hookCoverage = Object.fromEntries(ALL_HOOKS.map((hook) => [hook, plugins.filter((plugin) => plugin.manifest.hooks?.includes(hook)).length])) as Record<(typeof ALL_HOOKS)[number], number>;
    const typeCounts = {
      tool: plugins.filter((plugin) => plugin.manifest.type === 'tool').length,
      widget: plugins.filter((plugin) => plugin.manifest.type === 'widget').length,
      datasource: plugins.filter((plugin) => plugin.manifest.type === 'datasource').length,
    };
    return {
      enabledCount,
      disabledCount,
      totalHooks,
      hookCoverage,
      typeCounts,
    };
  }, [plugins]);

  const hasActiveFilters = query.trim().length > 0 || typeFilter !== 'all' || stateFilter !== 'all';

  const resetFilters = useCallback(() => {
    setQuery('');
    setTypeFilter('all');
    setStateFilter('all');
  }, []);

  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Studio / Extensibility"
        title="Plugins"
        description="Manage extensions that add tools, widgets, and data sources to Studio while keeping hook coverage and plugin health visible at a glance."
        badge={`${plugins.length} installed`}
        tone="info"
      />

      <StudioMetricBar>
        <StudioMetric label="Installed" value={plugins.length} meta="registered in catalog" tone="info" />
        <StudioMetric label="Enabled" value={stats.enabledCount} meta="active in runtime" tone="success" />
        <StudioMetric label="Disabled" value={stats.disabledCount} meta="currently parked" tone="warning" />
        <StudioMetric label="Hook bindings" value={stats.totalHooks} meta={`${ALL_HOOKS.filter((hook) => stats.hookCoverage[hook] > 0).length}/${ALL_HOOKS.length} contracts covered`} />
      </StudioMetricBar>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--sp-2)' }}>
        <StudioPanel title="Catalog Controls" description="Filter the registry by plugin shape, runtime status, and hook keywords." action={<span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>{filteredPlugins.length} visible</span>} tone="info" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <StudioInput
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search id, name, author, description, hook"
              style={{
                padding: '8px 10px',
                fontSize: '0.75rem',
              }}
            />
            <StudioButton
              onClick={resetFilters}
              disabled={!hasActiveFilters}
              tone="info"
              variant={hasActiveFilters ? 'secondary' : 'ghost'}
              style={{
                padding: '8px 10px',
                fontSize: '0.75rem',
                whiteSpace: 'nowrap',
              }}
            >
              Reset
            </StudioButton>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '8px' }}>
            <MiniSignal label="Tools" value={stats.typeCounts.tool} accent="var(--mint)" />
            <MiniSignal label="Widgets" value={stats.typeCounts.widget} accent="var(--gold)" />
            <MiniSignal label="Data" value={stats.typeCounts.datasource} accent="var(--info)" />
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {(['all', 'tool', 'widget', 'datasource'] as const).map((value) => (
              <FilterChip key={value} active={typeFilter === value} onClick={() => setTypeFilter(value)}>
                {value}
              </FilterChip>
            ))}
            {(['all', 'enabled', 'disabled'] as const).map((value) => (
              <FilterChip key={value} active={stateFilter === value} onClick={() => setStateFilter(value)}>
                {value}
              </FilterChip>
            ))}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            <ScopePill label="Scope" value={typeFilter === 'all' ? 'all types' : typeFilter} />
            <ScopePill label="State" value={stateFilter === 'all' ? 'all states' : stateFilter} />
            <ScopePill label="Search" value={query.trim().length === 0 ? 'none' : query.trim()} />
          </div>
        </StudioPanel>

        <StudioPanel title="Hook Coverage" description="See which SDK contracts are actually implemented by installed plugins." action={<span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>{ALL_HOOKS.filter((hook) => stats.hookCoverage[hook] > 0).length}/{ALL_HOOKS.length} covered</span>} tone="success">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {ALL_HOOKS.map((hook) => (
              <div key={hook} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--slate-700)' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--slate-300)', fontFamily: 'var(--font-mono)' }}>{hook}</span>
                <span style={{ fontSize: '0.6875rem', color: stats.hookCoverage[hook] > 0 ? 'var(--mint)' : 'var(--slate-500)', fontWeight: 600 }}>{stats.hookCoverage[hook]}</span>
              </div>
            ))}
          </div>
        </StudioPanel>
      </div>

      {loading ? (
        <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>Loading plugins...</p>
      ) : plugins.length === 0 ? (
        <StudioEmptyState
          title="No plugins installed"
          description={<span>Add plugin manifests to the <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--mint)' }}>/plugins</code> directory to get started.</span>}
        />
      ) : filteredPlugins.length === 0 ? (
        <StudioEmptyState
          title="No plugins match the current filters"
          description="Adjust search, type, or state filters to widen the catalog view."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
          {filteredPlugins.map((p) => (
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
      <StudioPanel title="Plugin SDK" description="Reference manifest shape, typed hooks, and lifecycle callbacks from the same canonical surface." tone="warning">
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
  "hooks": ["onKpiEvaluate", "onExport", "onApproval"]
}

// Typed Hook Contracts
// Each hook receives a strongly-typed payload:
//   onBracketLoad → { bracketId, kpiIds, status }
//   onKpiEvaluate → { kpiId, value, previousValue?, delta? }
//   onThemeChange → { primary, secondary, background, fontFamily? }
//   onExport      → { format, bracketId, timestamp }
//   onApproval    → { bracketId, action, actor, status }

// Lifecycle Callbacks (optional)
// export const lifecycle = {
//   onLoad(ctx) {
//     console.log(\`\${ctx.pluginId} v\${ctx.pluginVersion} loaded\`);
//     console.log(\`Studio version: \${ctx.studioVersion}\`);
//   },
//   onUnload() {
//     console.log('Plugin unloaded — cleanup resources');
//   },
// };`}
        </pre>
      </StudioPanel>
    </StudioPage>
  );
}

function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <StudioButton
      onClick={onClick}
      tone={active ? 'success' : 'default'}
      variant={active ? 'secondary' : 'ghost'}
      style={{
        padding: '5px 10px',
        borderRadius: '9999px',
        fontSize: '0.6875rem',
        textTransform: 'capitalize',
      }}
    >
      {children}
    </StudioButton>
  );
}

function ScopePill({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ padding: '6px 8px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)', minWidth: '0' }}>
      <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '2px' }}>{label}</p>
      <p style={{ fontSize: '0.75rem', color: 'var(--slate-200)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '180px' }}>{value}</p>
    </div>
  );
}

function MiniSignal({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)' }}>
      <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>{label}</p>
      <p style={{ fontSize: '0.875rem', fontWeight: 700, color: accent }}>{value}</p>
    </div>
  );
}
