'use client';

import { useState, useCallback } from 'react';
import type { DriftReport } from '@/lib/validation/drift-scanner';
import { DriftDetailPanel } from '@/components/registry/drift-detail-panel';

interface Props {
  initialReport: DriftReport;
}

export function DriftPageClient({ initialReport }: Props) {
  const [report, setReport] = useState<DriftReport>(initialReport);
  const [loading, setLoading] = useState(false);

  const handleScan = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/validate/drift');
      const json = await res.json() as { data: DriftReport };
      setReport(json.data);
    } finally {
      setLoading(false);
    }
  }, []);

  return <DriftDetailPanel report={report} loading={loading} onScan={handleScan} />;
}
