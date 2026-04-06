'use client';

import { useState, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton } from '@/components/ui/studio-page';

type ReportMode = 'single' | 'board-pack';

export function ExportReportButton() {
  const theme = useProjectStore((s) => s.theme);
  const projectName = useProjectStore((s) => s.projectName);
  const [loading, setLoading] = useState(false);

  const handleExport = useCallback(async (mode: ReportMode) => {
    setLoading(true);
    try {
      const res = await fetch('/api/export/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, mode, projectName }),
      });
      if (!res.ok) throw new Error('Export failed');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${mode}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  }, [theme, projectName]);

  return (
    <div style={{ display: 'flex', gap: 'var(--sp-0-5)' }}>
      <StudioButton
        onClick={() => handleExport('single')}
        disabled={loading}
        variant="secondary"
        style={{
          padding: '6px var(--sp-1-5)',
          fontSize: '0.75rem',
        }}
      >
        Export Report
      </StudioButton>
      <StudioButton
        onClick={() => handleExport('board-pack')}
        disabled={loading}
        tone="warning"
        variant="primary"
        style={{
          padding: '6px var(--sp-1-5)',
          fontSize: '0.75rem',
        }}
      >
        Board Pack
      </StudioButton>
    </div>
  );
}
