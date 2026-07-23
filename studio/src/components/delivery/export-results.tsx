'use client';

import { useState, useCallback } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';

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
    a.download = `aluca-export-${adapterName}-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [results, adapterName]);

  return (
    <StudioPanel
      title="Export Results"
      description="Inspect generated files, review errors and download the combined export bundle."
      action={<StudioButton onClick={handleDownloadAll} tone="success" variant="primary">Download All</StudioButton>}
      style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}
    >

      <div style={{ display: 'flex', gap: '16px', flex: 1, minHeight: 0 }}>
        {/* File list */}
        <div style={{ width: '260px', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {results.map((result) => {
            if (result.error) {
              return (
                <div key={result.useCaseId} style={{
                  padding: '8px',
                  fontSize: '0.75rem',
                  color: 'var(--danger)',
                  backgroundColor: 'color-mix(in srgb, var(--danger) 12%, transparent)',
                  border: '1px solid color-mix(in srgb, var(--danger) 40%, transparent)',
                  borderRadius: 'var(--radius-sm)',
                }}>
                  <strong>{result.useCaseId}</strong>: {result.error}
                </div>
              );
            }
            const files = collectFiles([result]);
            return files.map((file) => (
              <StudioButton
                key={file.filename}
                onClick={() => setPreviewFile(file)}
                variant="ghost"
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '4px 8px',
                  backgroundColor: previewFile?.filename === file.filename ? 'var(--bg-2)' : 'var(--bg)',
                  border: `1px solid ${previewFile?.filename === file.filename ? 'var(--accent)' : 'var(--line)'}`,
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--ink-2)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
                  justifyContent: 'flex-start',
                }}
              >
                {file.filename}
              </StudioButton>
            ));
          })}
        </div>

        {/* File preview */}
        <div style={{ flex: 1, backgroundColor: 'var(--bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--line)', overflow: 'auto' }}>
          {previewFile ? (
            <pre style={{ padding: '16px', fontSize: '0.75rem', color: 'var(--ink-2)', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', margin: 0 }}>
              {previewFile.content}
            </pre>
          ) : (
            <div style={{ height: '100%' }}>
              <StudioEmptyState title="No preview selected" description="Select a generated file from the left column to inspect its content." />
            </div>
          )}
        </div>
      </div>
    </StudioPanel>
  );
}
