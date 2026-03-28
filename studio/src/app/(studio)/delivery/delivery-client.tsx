'use client';

import { useState, useCallback } from 'react';
import { cardStyle } from '@/lib/ui-styles';
import { ExportResults, type ExportResultItem } from '@/components/delivery/export-results';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
  kpiCount: number;
  actionCount: number;
}

interface Props {
  brackets: BracketSummary[];
}

const ADAPTERS = [
  {
    id: 'fabric',
    name: 'Microsoft Fabric / Power BI',
    description: 'Generate TMDL measures, semantic model, and .pbip report layouts',
    outputs: ['TMDL measures', 'Semantic model (XMLA)', 'PBIP report layout', 'DAX queries'],
    status: 'available' as const,
    endpoint: '/api/export/fabric',
  },
  {
    id: 'opensource',
    name: 'Open Source Stack',
    description: 'Export as SQL transformations and Evidence.dev markdown reports',
    outputs: ['SQL transformations', 'Evidence.dev pages', 'DuckDB queries', 'YAML config'],
    status: 'preview' as const,
    endpoint: '/api/export/opensource',
  },
  {
    id: 'cicd',
    name: 'CI/CD Pipeline',
    description: 'Deploy via GitHub Actions or Fabric REST API',
    outputs: ['GitHub Actions workflow', 'Validation pipeline', 'Fabric deploy script'],
    status: 'available' as const,
    endpoint: '/api/export/cicd',
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(
    new Set(brackets.map((b) => b.id))
  );
  const [isExporting, setIsExporting] = useState(false);
  const [exportResults, setExportResults] = useState<ExportResultItem[] | null>(null);

  const toggleBracket = (id: string) => {
    setSelectedBrackets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const adapter = ADAPTERS.find((a) => a.id === selectedAdapter)!;
  let totalKpis = 0;
  let totalActions = 0;
  for (const b of brackets) {
    if (selectedBrackets.has(b.id)) {
      totalKpis += b.kpiCount;
      totalActions += b.actionCount;
    }
  }

  const handleExport = useCallback(async () => {
    if (selectedBrackets.size === 0 || !adapter.endpoint) return;
    setIsExporting(true);
    setExportResults(null);

    try {
      const response = await fetch(adapter.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ useCaseIds: [...selectedBrackets] }),
      });
      if (!response.ok) throw new Error('Export failed');
      const data = await response.json();
      setExportResults(data.results);
    } catch (err) {
      setExportResults([{ useCaseId: 'error', error: err instanceof Error ? err.message : 'Export failed' }]);
    } finally {
      setIsExporting(false);
    }
  }, [selectedBrackets, adapter.endpoint]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-3)' }}>
        {/* Left: Adapter Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            Target Platform
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
            {ADAPTERS.map((a) => (
              <button
                key={a.id}
                onClick={() => setSelectedAdapter(a.id)}
                style={{
                  padding: 'var(--sp-2)',
                  backgroundColor: selectedAdapter === a.id ? 'var(--slate-700)' : 'var(--slate-800)',
                  border: `1px solid ${selectedAdapter === a.id ? 'var(--mint)' : 'var(--slate-700)'}`,
                  borderRadius: 'var(--radius-lg)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--duration-fast) var(--ease-out)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>{a.name}</span>
                  <span style={{
                    fontSize: '0.625rem', padding: '2px 8px', borderRadius: '9999px', fontWeight: 600,
                    backgroundColor: a.status === 'available' ? 'var(--mint)' : 'var(--gold)',
                    color: 'var(--slate-950)',
                  }}>
                    {a.status}
                  </span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>{a.description}</p>
              </button>
            ))}
          </div>

          <div style={cardStyle}>
            <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: 'var(--sp-1)' }}>
              Generated Outputs
            </h4>
            {adapter.outputs.map((output) => (
              <div key={output} style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', padding: '4px 0', fontSize: '0.8125rem', color: 'var(--slate-200)' }}>
                <span style={{ color: 'var(--mint)' }}>+</span>
                {output}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Scope Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>Export Scope</h3>
            <button
              onClick={() =>
                setSelectedBrackets(
                  selectedBrackets.size === brackets.length ? new Set() : new Set(brackets.map((b) => b.id))
                )
              }
              style={{ fontSize: '0.75rem', color: 'var(--mint)', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {selectedBrackets.size === brackets.length ? 'Deselect all' : 'Select all'}
            </button>
          </div>

          <div style={{ backgroundColor: 'var(--slate-800)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--slate-700)', overflow: 'hidden' }}>
            {brackets.map((bracket) => (
              <label
                key={bracket.id}
                style={{
                  display: 'flex', alignItems: 'center', gap: 'var(--sp-1)',
                  padding: 'var(--sp-1) var(--sp-1-5)', borderBottom: '1px solid var(--slate-700)',
                  cursor: 'pointer',
                  backgroundColor: selectedBrackets.has(bracket.id) ? 'var(--slate-750, #283548)' : 'transparent',
                }}
              >
                <input type="checkbox" checked={selectedBrackets.has(bracket.id)} onChange={() => toggleBracket(bracket.id)} style={{ accentColor: 'var(--mint)' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--info)', width: '60px' }}>{bracket.id}</span>
                <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--slate-100)' }}>{bracket.title}</span>
                <span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>{bracket.kpiCount} KPIs · {bracket.actionCount} Actions</span>
              </label>
            ))}
          </div>

          <div style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
              {selectedBrackets.size} use cases · {totalKpis} KPIs · {totalActions} actions
            </p>
            <button
              onClick={handleExport}
              disabled={selectedBrackets.size === 0 || isExporting}
              style={{
                padding: 'var(--sp-1) var(--sp-3)',
                backgroundColor: selectedBrackets.size > 0 && !isExporting ? 'var(--mint)' : 'var(--slate-600)',
                borderRadius: 'var(--radius-md)', border: 'none',
                color: 'var(--slate-950)', fontWeight: 700, fontSize: '0.875rem',
                cursor: selectedBrackets.size > 0 && !isExporting ? 'pointer' : 'not-allowed',
              }}
            >
              {isExporting ? 'Exporting...' : `Export to ${adapter.name.split('/')[0].trim()}`}
            </button>
          </div>
        </div>
      </div>

      {exportResults && (
        <ExportResults results={exportResults} adapterName={selectedAdapter} />
      )}
    </div>
  );
}
