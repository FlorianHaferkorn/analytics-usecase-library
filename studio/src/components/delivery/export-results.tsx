'use client';

import { useState, useCallback } from 'react';
import { cardStyle } from '@/lib/ui-styles';

export interface ExportFile {
  filename: string;
  content: string;
}

export interface ExportResultItem {
  useCaseId: string;
  outputs?: Record<string, ExportFile | ExportFile[]>;
  error?: string;
}

interface Props {
  results: ExportResultItem[];
  adapterName: string;
}

function collectFiles(results: ExportResultItem[]): ExportFile[] {
  const files: ExportFile[] = [];
  for (const result of results) {
    if (!result.outputs) continue;
    for (const value of Object.values(result.outputs)) {
      if (Array.isArray(value)) files.push(...value);
      else files.push(value);
    }
  }
  return files;
}

export function ExportResults({ results, adapterName }: Props) {
  const [previewFile, setPreviewFile] = useState<ExportFile | null>(null);

  const handleDownloadAll = useCallback(() => {
    const files = collectFiles(results);
    const combined = files
      .map((f) => `// === ${f.filename} ===\n${f.content}`)
      .join('\n\n');
    const blob = new Blob([combined], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `actionready-export-${adapterName}-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [results, adapterName]);

  return (
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
          {results.map((result) => {
            if (result.error) {
              return (
                <div key={result.useCaseId} style={{ padding: 'var(--sp-1)', fontSize: '0.75rem', color: 'var(--danger)' }}>
                  {result.error}
                </div>
              );
            }
            const files = collectFiles([result]);
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
  );
}
