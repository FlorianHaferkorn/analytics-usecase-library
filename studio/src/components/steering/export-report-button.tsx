'use client';

import { useState, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';

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
      <button
        onClick={() => handleExport('single')}
        disabled={loading}
        style={{
          padding: '6px var(--sp-1-5)',
          backgroundColor: 'var(--slate-700)',
          border: '1px solid var(--slate-600)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--slate-200)',
          fontSize: '0.75rem',
          cursor: loading ? 'wait' : 'pointer',
          opacity: loading ? 0.6 : 1,
        }}
      >
        Export Report
      </button>
      <button
        onClick={() => handleExport('board-pack')}
        disabled={loading}
        style={{
          padding: '6px var(--sp-1-5)',
          backgroundColor: 'var(--gold)',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          color: 'var(--slate-950)',
          fontSize: '0.75rem',
          fontWeight: 600,
          cursor: loading ? 'wait' : 'pointer',
          opacity: loading ? 0.6 : 1,
        }}
      >
        Board Pack
      </button>
    </div>
  );
}
