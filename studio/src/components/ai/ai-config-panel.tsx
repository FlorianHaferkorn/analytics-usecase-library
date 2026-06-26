'use client';

/**
 * AiConfigPanel — L1/L2 AI-config governance editor (I-6.6 UI).
 *
 * Edit a customer (L1) / domain (L2) override layer and drive it through the
 * Freigabe-Schleuse (draft → review → approved). Buttons are gated by the SAME
 * transition rules the server enforces (`governance-types`); the server is still the
 * authority (Ajv validation, two-person rule). Only approved layers ever serve.
 */

import { useState } from 'react';
import { allowedActions, type LayerAction, type LayerStatus } from '@/lib/ai/config/governance-types';

type Status = LayerStatus | 'none';

const STATUS_LABEL: Record<Status, string> = {
  none: 'kein Layer',
  draft: 'Entwurf',
  review: 'in Review',
  approved: 'freigegeben',
  rejected: 'abgelehnt',
};

const ACTION_LABEL: Record<LayerAction, string> = {
  submit: 'Zur Review einreichen',
  approve: 'Freigeben',
  reject: 'Ablehnen',
  reopen: 'Wieder öffnen',
};

export function AiConfigPanel({
  layer = 'L1',
  domainId = '',
  initialStatus = 'none',
  initialConfig = '',
}: {
  layer?: 'L1' | 'L2';
  domainId?: string;
  initialStatus?: Status;
  initialConfig?: string;
}) {
  const [status, setStatus] = useState<Status>(initialStatus);
  const [configText, setConfigText] = useState(
    initialConfig || JSON.stringify({ schema_version: '1.0.0', layer }, null, 2),
  );
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function call(op: string, withConfig: boolean) {
    setBusy(true);
    setMessage(null);
    try {
      const payload: Record<string, unknown> = { op, layer, domainId };
      if (withConfig) {
        try {
          payload.config = JSON.parse(configText);
        } catch {
          setMessage('Config ist kein gültiges JSON');
          setBusy(false);
          return;
        }
      }
      const res = await fetch('/api/ai-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(data?.error ?? `Fehler (${res.status})`);
      } else {
        setStatus((data?.data?.layer?.status as Status) ?? status);
        setMessage(op === 'save' ? 'Gespeichert (Entwurf)' : `OK: ${op}`);
      }
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const actions = status === 'none' ? [] : allowedActions(status);

  return (
    <section data-testid="ai-config-panel" className="ai-config-panel">
      <header>
        <h2>AI-Config — {layer}{domainId ? ` · ${domainId}` : ' (Tenant)'}</h2>
        <p>
          Status: <strong data-testid="config-status" data-status={status}>{STATUS_LABEL[status]}</strong>
          {' '}· Der Server validiert + erzwingt die Zwei-Personen-Regel; nur freigegebene Layer greifen.
        </p>
      </header>

      <textarea
        data-testid="config-editor"
        aria-label="AI config JSON"
        value={configText}
        onChange={(e) => setConfigText(e.target.value)}
        rows={14}
        spellCheck={false}
      />

      <div className="ai-config-actions">
        <button type="button" data-testid="act-save" disabled={busy} onClick={() => call('save', true)}>
          Speichern (Entwurf)
        </button>
        {actions.map((a) => (
          <button key={a} type="button" data-testid={`act-${a}`} disabled={busy} onClick={() => call(a, false)}>
            {ACTION_LABEL[a]}
          </button>
        ))}
      </div>

      {message && <p data-testid="config-message" role="status">{message}</p>}
    </section>
  );
}
