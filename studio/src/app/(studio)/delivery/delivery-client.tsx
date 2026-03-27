'use client';

import { useState } from 'react';

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
  },
  {
    id: 'opensource',
    name: 'Open Source Stack',
    description: 'Export as SQL transformations and Evidence.dev markdown reports',
    outputs: ['SQL transformations', 'Evidence.dev pages', 'DuckDB queries', 'YAML config'],
    status: 'preview' as const,
  },
  {
    id: 'cicd',
    name: 'CI/CD Pipeline',
    description: 'Deploy via GitHub Actions or Fabric REST API',
    outputs: ['GitHub Actions workflow', 'Fabric API deploy script', 'Validation pipeline'],
    status: 'planned' as const,
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(
    new Set(brackets.map((b) => b.id))
  );

  const toggleBracket = (id: string) => {
    setSelectedBrackets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const adapter = ADAPTERS.find((a) => a.id === selectedAdapter)!;
  const totalKpis = brackets
    .filter((b) => selectedBrackets.has(b.id))
    .reduce((sum, b) => sum + b.kpiCount, 0);
  const totalActions = brackets
    .filter((b) => selectedBrackets.has(b.id))
    .reduce((sum, b) => sum + b.actionCount, 0);

  return (
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
              onClick={() => a.status !== 'planned' && setSelectedAdapter(a.id)}
              style={{
                padding: 'var(--sp-2)',
                backgroundColor: selectedAdapter === a.id ? 'var(--slate-700)' : 'var(--slate-800)',
                border: `1px solid ${selectedAdapter === a.id ? 'var(--mint)' : 'var(--slate-700)'}`,
                borderRadius: 'var(--radius-lg)',
                cursor: a.status === 'planned' ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                opacity: a.status === 'planned' ? 0.5 : 1,
                transition: 'all var(--duration-fast) var(--ease-out)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
                  {a.name}
                </span>
                <span
                  style={{
                    fontSize: '0.625rem',
                    padding: '2px 8px',
                    borderRadius: '9999px',
                    backgroundColor:
                      a.status === 'available' ? 'var(--mint)' :
                      a.status === 'preview' ? 'var(--gold)' : 'var(--slate-600)',
                    color: 'var(--slate-950)',
                    fontWeight: 600,
                  }}
                >
                  {a.status}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>{a.description}</p>
            </button>
          ))}
        </div>

        {/* Outputs */}
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
          }}
        >
          <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--slate-300)', marginBottom: 'var(--sp-1)' }}>
            Generated Outputs
          </h4>
          {adapter.outputs.map((output) => (
            <div
              key={output}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-1)',
                padding: '4px 0',
                fontSize: '0.8125rem',
                color: 'var(--slate-200)',
              }}
            >
              <span style={{ color: 'var(--mint)' }}>+</span>
              {output}
            </div>
          ))}
        </div>
      </div>

      {/* Right: Scope Selection */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            Export Scope
          </h3>
          <button
            onClick={() =>
              setSelectedBrackets(
                selectedBrackets.size === brackets.length
                  ? new Set()
                  : new Set(brackets.map((b) => b.id))
              )
            }
            style={{
              fontSize: '0.75rem',
              color: 'var(--mint)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {selectedBrackets.size === brackets.length ? 'Deselect all' : 'Select all'}
          </button>
        </div>

        <div
          style={{
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
            overflow: 'hidden',
          }}
        >
          {brackets.map((bracket) => (
            <label
              key={bracket.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-1)',
                padding: 'var(--sp-1) var(--sp-1-5)',
                borderBottom: '1px solid var(--slate-700)',
                cursor: 'pointer',
                backgroundColor: selectedBrackets.has(bracket.id) ? 'var(--slate-750, #283548)' : 'transparent',
              }}
            >
              <input
                type="checkbox"
                checked={selectedBrackets.has(bracket.id)}
                onChange={() => toggleBracket(bracket.id)}
                style={{ accentColor: 'var(--mint)' }}
              />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--info)', width: '60px' }}>
                {bracket.id}
              </span>
              <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--slate-100)' }}>
                {bracket.title}
              </span>
              <span style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
                {bracket.kpiCount} KPIs · {bracket.actionCount} Actions
              </span>
            </label>
          ))}
        </div>

        {/* Summary & Export */}
        <div
          style={{
            padding: 'var(--sp-2)',
            backgroundColor: 'var(--slate-800)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
              {selectedBrackets.size} use cases · {totalKpis} KPIs · {totalActions} actions
            </p>
          </div>
          <button
            disabled={selectedBrackets.size === 0}
            style={{
              padding: 'var(--sp-1) var(--sp-3)',
              backgroundColor: selectedBrackets.size > 0 ? 'var(--mint)' : 'var(--slate-600)',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              color: 'var(--slate-950)',
              fontWeight: 700,
              fontSize: '0.875rem',
              cursor: selectedBrackets.size > 0 ? 'pointer' : 'not-allowed',
              transition: 'all var(--duration-fast) var(--ease-out)',
            }}
          >
            Export to {adapter.name.split('/')[0].trim()}
          </button>
        </div>
      </div>
    </div>
  );
}
