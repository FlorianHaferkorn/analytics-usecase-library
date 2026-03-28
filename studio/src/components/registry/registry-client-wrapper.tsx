'use client';

import { useCallback } from 'react';
import { useProjectStore } from '@/lib/store/project-store';
import { DriftDetailPanel } from './drift-detail-panel';

export function RegistryClientWrapper() {
  const driftReport = useProjectStore((s) => s.driftReport);
  const driftLoading = useProjectStore((s) => s.driftLoading);
  const setDriftReport = useProjectStore((s) => s.setDriftReport);
  const setDriftLoading = useProjectStore((s) => s.setDriftLoading);

  const runScan = useCallback(async () => {
    setDriftLoading(true);
    try {
      const res = await fetch('/api/validate/drift');
      if (res.ok) setDriftReport(await res.json());
    } finally {
      setDriftLoading(false);
    }
  }, [setDriftReport, setDriftLoading]);

  return <DriftDetailPanel report={driftReport} loading={driftLoading} onScan={runScan} />;
}
