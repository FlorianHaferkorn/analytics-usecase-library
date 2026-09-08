'use client';

import { useState, useMemo, useCallback } from 'react';
import type { ThemeConfig } from '@/lib/store/project-store';
import { generateCssCustomProperties } from '@/lib/theme/export-css';
import { generateTailwindConfig } from '@/lib/theme/export-tailwind';
import { generateJsonConfig } from '@/lib/theme/export-json';
import { StudioButton, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';

type PreviewFormat = 'css' | 'tailwind' | 'json';

interface Props {
  theme: ThemeConfig;
  onSave?: () => void;
  saving?: boolean;
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

export function ThemeExportPanel({ theme, onSave, saving = false }: Props) {
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
    <StudioPanel
      title="Export Theme"
      description="Preview generated theme artifacts and export them in the target format or as a bundle."
      action={onSave ? (
        <StudioButton onClick={onSave} disabled={saving} tone="success" variant="primary" style={{ padding: '4px 12px' }}>
          {saving ? 'Saving...' : 'Save Theme'}
        </StudioButton>
      ) : undefined}
      style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
    >
      {/* Format tabs */}
      <StudioSegmentedControl
        value={activeFormat}
        onChange={setActiveFormat}
        options={(Object.entries(FORMAT_LABELS) as [PreviewFormat, string][]).map(([fmt, label]) => ({ value: fmt, label }))}
      />

      {/* Preview */}
      <pre
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--ink-2)',
          backgroundColor: 'var(--bg-2)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--line)',
          padding: '12px',
          overflow: 'auto',
          maxHeight: '200px',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
        }}
      >
        {preview}
      </pre>

      {/* Download buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <StudioButton
          onClick={handleDownload}
          variant="secondary"
          style={{
            flex: 1,
            padding: '6px 8px',
            fontSize: '0.75rem',
          }}
        >
          Download {FORMAT_LABELS[activeFormat]}
        </StudioButton>
        <StudioButton
          onClick={handleDownloadBundle}
          disabled={bundleLoading}
          tone="warning"
          variant="primary"
          style={{
            flex: 1,
            padding: '6px 8px',
            fontSize: '0.75rem',
          }}
        >
          {bundleLoading ? 'Bundling...' : 'Download All (ZIP)'}
        </StudioButton>
      </div>
    </StudioPanel>
  );
}
