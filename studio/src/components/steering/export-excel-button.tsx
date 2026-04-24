'use client';

import { useState, useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { StudioButton } from '@/components/ui/studio-page';

/**
 * ExportExcelButton — downloads a CEO-grade .xlsx from the Steering view.
 *
 * Calls GET /api/export/excel?view=steering&projectId=...
 * Returns an xlsx with:
 *   - KPI Cards — Golden 20
 *   - Detail Matrix (brackets)
 *   - _Actions tab
 *   - _Notes tab
 */
export function ExportExcelButton() {
  const projectName = useProjectStore((s) => s.projectName);
  const [loading, setLoading] = useState(false);

  const handleExport = useCallback(async () => {
    setLoading(true);
    try {
      const projectId = encodeURIComponent(projectName ?? 'default');
      const res = await fetch(`/api/export/excel?view=steering&projectId=${projectId}`);
      if (!res.ok) {
        console.error('Excel export failed:', await res.text());
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `steering-export-${projectId}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  }, [projectName]);

  return (
    <StudioButton
      onClick={() => void handleExport()}
      disabled={loading}
      variant="secondary"
      style={{
        padding: '6px 12px',
        fontSize: '0.75rem',
      }}
    >
      {loading ? 'Exporting…' : 'Export to Excel'}
    </StudioButton>
  );
}
