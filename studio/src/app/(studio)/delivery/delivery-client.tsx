'use client';

import { useState, useCallback } from 'react';
import { cardStyle } from '@/lib/ui-styles';

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

interface ExportFile {
  filename: string;
  content: string;
}

interface ExportResultItem {
  useCaseId: string;
  outputs?: Record<string, ExportFile | ExportFile[]>;
  error?: string;
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
    outputs: ['GitHub Actions workflow', 'Fabric API deploy script', 'Validation pipeline'],
    status: 'planned' as const,
    endpoint: '',
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(
    new Set(brackets.map((b) => b.id))
  );
  const [isExporting, setIsExporting] = useState(false);
  const [exportResults, setExportResults] = useState<ExportResultItem[] | null>(null);
  const [previewFile, setPreviewFile] = useState<ExportFile | null>(null);

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
    setPreviewFile(null);

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

  const handleDownloadAll = useCallback(() => {
    if (!exportResults) return;

    const files: ExportFile[] = [];
    for (const result of exportResults) {
      if (!result.outputs) continue;
      for (const value of Object.values(result.outputs)) {
        if (Array.isArray(value)) files.push(...value);
        else files.push(value);
      }
    }

    // Create a combined download as a single text file manifest
    const combined = files
      .map((f) => `// === ${f.filename} ===\n${f.content}`)
      .join('\n\n');

    const blob = new Blob([combined], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `actionready-export-${selectedAdapter}-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [exportResults, selectedAdapter]);

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
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>{a.name}</span>
                  <span style={{
                    fontSize: '0.625rem', padding: '2px 8px', borderRadius: '9999px', fontWeight: 600,
                    backgroundColor: a.status === 'available' ? 'var(--mint)' : a.status === 'preview' ? 'var(--gold)' : 'var(--slate-600)',
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

      {/* Export Results Panel */}
      {exportResults && (
        <div style={{ ...cardStyle, flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
              Export Results
            </h3>
            <button
              onClick={handleDownloadAll}
              style={{
                padding: 'var(--sp-0-5) var(--sp-2)',
                backgroundColor: 'var(--mint)', borderRadius: 'var(--radius-sm)',
                border: 'none', color: 'var(--slate-950)', fontWeight: 600, fontSize: '0.75rem', cursor: 'pointer',
              }}
            >
              Download All
            </button>
          </div>

          <div style={{ display: 'flex', gap: 'var(--sp-2)', flex: 1, minHeight: 0 }}>
            {/* File list */}
            <div style={{ width: '260px', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {exportResults.map((result) => {
                if (result.error) {
                  return (
                    <div key={result.useCaseId} style={{ padding: 'var(--sp-1)', fontSize: '0.75rem', color: 'var(--danger)' }}>
                      {result.error}
                    </div>
                  );
                }
                const files: ExportFile[] = [];
                if (result.outputs) {
                  for (const value of Object.values(result.outputs)) {
                    if (Array.isArray(value)) files.push(...value);
                    else files.push(value);
                  }
                }
                return files.map((file) => (
                  <button
                    key={file.filename}
                    onClick={() => setPreviewFile(file)}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: 'var(--sp-0-5) var(--sp-1)',
                      backgroundColor: previewFile?.filename === file.filename ? 'var(--slate-700)' : 'var(--slate-900)',
                      border: `1px solid ${previewFile?.filename === file.filename ? 'var(--mint)' : 'var(--slate-700)'}`,
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--slate-200)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
                      cursor: 'pointer',
                    }}
                  >
                    {file.filename}
                  </button>
                ));
              })}
            </div>

            {/* File preview */}
            <div style={{ flex: 1, backgroundColor: 'var(--slate-900)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)', overflow: 'auto' }}>
              {previewFile ? (
                <pre style={{ padding: 'var(--sp-2)', fontSize: '0.75rem', color: 'var(--slate-200)', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', margin: 0 }}>
                  {previewFile.content}
                </pre>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--slate-500)' }}>Select a file to preview</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
