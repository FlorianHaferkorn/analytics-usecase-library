'use client';

import { useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';

export type WizardElementKind = 'kpi' | 'bracket' | 'action' | 'source';

export interface WizardDraftPayload {
  name: string;
  ref: string;
  domain: string;
  type: string;
  grain: string;
  description: string;
  sql?: string;
}

export function useWizardSave() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveDraft = useCallback(
    async (kind: WizardElementKind, draft: WizardDraftPayload) => {
      setSaving(true);
      setError(null);
      try {
        const res = await fetch('/api/ai/wizard/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind, draft }),
        });
        const json = (await res.json()) as {
          detailHref?: string;
          error?: { message?: string };
        };
        if (!res.ok) {
          const msg = json.error?.message ?? `Save failed (${res.status})`;
          setError(msg);
          return false;
        }
        const href = json.detailHref;
        if (href) router.push(href);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Network error');
        return false;
      } finally {
        setSaving(false);
      }
    },
    [router],
  );

  return { saveDraft, saving, error, clearError: () => setError(null) };
}
