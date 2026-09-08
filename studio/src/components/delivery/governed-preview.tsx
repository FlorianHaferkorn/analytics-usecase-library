'use client';

/**
 * GovernedPreview — Studio's Generate path calling the real Python core (I-10.3,
 * completing ADR-0007/I-6.2/I-6.3/I-6.4). Fetches the bridge-backed precore,
 * generate, and delivery-flow results for one bracket + target and renders the
 * three panels that were built for this but never wired into a page.
 *
 * Bridge is single-bracket-scoped, so this only renders when exactly one use
 * case is selected — the caller decides when that's the case.
 */

import { useEffect, useState } from 'react';
import { PreCorePanel } from '@/components/precore/precore-panel';
import { GateReportPanel } from '@/components/postcore/gate-report-panel';
import { DeliveryFlowPanel } from '@/components/postcore/delivery-flow-panel';
import { StudioInlineStat } from '@/components/ui/studio-data';
import { StudioPanel } from '@/components/ui/studio-page';
import type { PreCoreResult, GenerateResult } from '@/lib/bridge/superversion-bridge';
import type { DeliveryFlowState } from '@/lib/studio/delivery-flow';

interface Props {
  bracketId: string;
  target: string;
}

interface State {
  key: string;
  loading: boolean;
  precore: PreCoreResult | null;
  generate: GenerateResult | null;
  flow: DeliveryFlowState | null;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  return res.json() as Promise<T>;
}

export function GovernedPreview({ bracketId, target }: Props) {
  const requestKey = `${bracketId}:${target}`;
  const [state, setState] = useState<State>({ key: '', loading: true, precore: null, generate: null, flow: null });

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      fetchJson<PreCoreResult>(`/api/precore?bracketId=${encodeURIComponent(bracketId)}`),
      fetchJson<GenerateResult>(`/api/generate?bracketId=${encodeURIComponent(bracketId)}&target=${encodeURIComponent(target)}`),
      fetchJson<DeliveryFlowState>(`/api/delivery-flow?bracketId=${encodeURIComponent(bracketId)}&target=${encodeURIComponent(target)}`),
    ]).then(([precore, generate, flow]) => {
      if (!cancelled) setState({ key: requestKey, loading: false, precore, generate, flow });
    }).catch((err) => {
      if (cancelled) return;
      const error = err instanceof Error ? err.message : 'bridge request failed';
      setState({
        key: requestKey,
        loading: false,
        precore: { available: false, ok: false, engines: [], error },
        generate: { available: false, ok: false, targetsAvailable: [], artifacts: [], error },
        flow: null,
      });
    });

    return () => { cancelled = true; };
  }, [bracketId, requestKey, target]);

  if (state.loading || state.key !== requestKey) {
    return (
      <div data-testid="governed-preview-loading" style={{ fontSize: '0.75rem', color: 'var(--ink-3)' }}>
        Governed package detail is loading from the shared core…
      </div>
    );
  }

  return (
    <div data-testid="governed-preview" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {state.flow && <DeliveryFlowPanel flow={state.flow} />}
      {state.generate && <GateReportPanel result={state.generate} />}
      {state.precore && <PreCorePanel result={state.precore} />}
    </div>
  );
}

interface SectionProps {
  /** IDs of the currently selected use cases — the bridge is single-bracket-scoped. */
  selectedBracketIds: string[];
  /** The adapter's mapped bridge target, or null when it has no governed target. */
  bridgeTarget: string | null;
  adapterName: string;
}

/**
 * GovernedPreviewSection — the governed package-detail panel for the
 * Delivery page. Wraps GovernedPreview with the panel chrome and the
 * selection/target guards, so delivery-client.tsx only renders one component.
 */
export function GovernedPreviewSection({ selectedBracketIds, bridgeTarget, adapterName }: SectionProps) {
  return (
    <StudioPanel
      title="Governance & Gate Detail"
      description="Authoritative detail for the selected package: pre-core reality check, target artifacts, approval state, and the shared Gate-Report."
      tone="info"
    >
      {selectedBracketIds.length !== 1 ? (
        <StudioInlineStat>
          Select exactly one use case above to inspect its authoritative gate and package detail.
        </StudioInlineStat>
      ) : bridgeTarget === null ? (
        <StudioInlineStat>
          {adapterName} has no governed core target yet, so no authoritative package detail is available.
        </StudioInlineStat>
      ) : (
        <GovernedPreview bracketId={selectedBracketIds[0]} target={bridgeTarget} />
      )}
    </StudioPanel>
  );
}
