'use client';

import { useState, useMemo, useCallback } from 'react';
import type { ThemeConfig } from '@/lib/store/project-store';
import { generateCssCustomProperties } from '@/lib/theme/export-css';
import { generateTailwindConfig } from '@/lib/theme/export-tailwind';
import { generateJsonConfig } from '@/lib/theme/export-json';

type PreviewFormat = 'css' | 'tailwind' | 'json';

interface Props {
  theme: ThemeConfig;
  onSave: () => void;
  saving: boolean;
}

const FORMAT_LABELS: Record<PreviewFormat, string> = {
  css: 'CSS',
  tailwind: 'Tailwind',
  json: 'JSON',
};

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ThemeExportPanel({ theme, onSave, saving }: Props) {
  const [activeFormat, setActiveFormat] = useState<PreviewFormat>('css');
  const [bundleLoading, setBundleLoading] = useState(false);

  const preview = useMemo(() => {
    switch (activeFormat) {
      case 'css': return generateCssCustomProperties(theme);
      case 'tailwind': return generateTailwindConfig(theme);
      case 'json': return generateJsonConfig(theme);
    }
  }, [theme, activeFormat]);

  const handleDownload = useCallback(() => {
    const map: Record<PreviewFormat, { filename: string; mime: string }> = {
      css: { filename: 'theme.css', mime: 'text/css' },
      tailwind: { filename: 'tailwind.config.ts', mime: 'text/typescript' },
      json: { filename: 'theme.json', mime: 'application/json' },
    };
    const { filename, mime } = map[activeFormat];
    downloadFile(preview, filename, mime);
  }, [activeFormat, preview]);

  const handleDownloadBundle = useCallback(async () => {
    setBundleLoading(true);
    try {
      const res = await fetch('/api/export/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, format: 'bundle' }),
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'actionready-theme.zip';
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setBundleLoading(false);
    }
  }, [theme]);

  return (
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--sp-1-5)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--slate-100)' }}>
          Export Theme
        </h3>
        <button
          onClick={onSave}
          disabled={saving}
          style={{
            padding: '4px var(--sp-1-5)',
            backgroundColor: 'var(--mint)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-950)',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: saving ? 'wait' : 'pointer',
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? 'Saving...' : 'Save Theme'}
        </button>
      </div>

      {/* Format tabs */}
      <div style={{ display: 'flex', gap: 'var(--sp-0-5)' }}>
        {(Object.entries(FORMAT_LABELS) as [PreviewFormat, string][]).map(([fmt, label]) => (
          <button
            key={fmt}
            onClick={() => setActiveFormat(fmt)}
            style={{
              padding: '4px var(--sp-1)',
              backgroundColor: activeFormat === fmt ? 'var(--slate-700)' : 'transparent',
              border: `1px solid ${activeFormat === fmt ? 'var(--mint)' : 'var(--slate-700)'}`,
              borderRadius: 'var(--radius-sm)',
              color: activeFormat === fmt ? 'var(--slate-50)' : 'var(--slate-400)',
              fontSize: '0.75rem',
              cursor: 'pointer',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Preview */}
      <pre
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
          color: 'var(--slate-300)',
          backgroundColor: 'var(--slate-900)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--slate-700)',
          padding: 'var(--sp-1-5)',
          overflow: 'auto',
          maxHeight: '200px',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
        }}
      >
        {preview}
      </pre>

      {/* Download buttons */}
      <div style={{ display: 'flex', gap: 'var(--sp-1)' }}>
        <button
          onClick={handleDownload}
          style={{
            flex: 1,
            padding: '6px var(--sp-1)',
            backgroundColor: 'var(--slate-700)',
            border: '1px solid var(--slate-600)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-200)',
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          Download {FORMAT_LABELS[activeFormat]}
        </button>
        <button
          onClick={handleDownloadBundle}
          disabled={bundleLoading}
          style={{
            flex: 1,
            padding: '6px var(--sp-1)',
            backgroundColor: 'var(--gold)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-950)',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: bundleLoading ? 'wait' : 'pointer',
            opacity: bundleLoading ? 0.6 : 1,
          }}
        >
          {bundleLoading ? 'Bundling...' : 'Download All (ZIP)'}
        </button>
      </div>
    </div>
  );
}
