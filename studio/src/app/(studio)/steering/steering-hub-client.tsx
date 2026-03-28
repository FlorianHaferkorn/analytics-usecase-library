'use client';

import { useCallback, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { GoldenThreadFlow, type GoldenThreadData } from '@/components/flow/golden-thread-flow';
import { toYaml } from '@/lib/core/yaml-loader';

const YamlEditor = dynamic(
  () => import('@/components/editor/yaml-editor').then((m) => m.YamlEditor),
  { ssr: false, loading: () => <div style={{ padding: 'var(--sp-3)', color: 'var(--slate-500)' }}>Loading editor...</div> }
);

interface BracketData {
  id: string;
  title: string;
  domain: string;
  strategicKpiId: string;
  impactDirection: string;
  influencingKpiIds: string[];
  actionCodeIds: string[];
}

interface Props {
  strategyAnchor: string;
  brackets: BracketData[];
  actionDetails: Array<[string, { name: string; status: string; domain: string; triggerKpis: string[] }]>;
  /** Full bracket YAML strings keyed by ID, for editor display. */
  bracketYamls: Record<string, string>;
}

type ViewMode = 'flow' | 'split' | 'editor';

export function SteeringHubClient({ strategyAnchor, brackets, actionDetails, bracketYamls }: Props) {
  const [selectedBracket, setSelectedBracket] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('flow');

  const flowData = useMemo<GoldenThreadData>(() => {
    const filtered = selectedBracket
      ? brackets.filter((b) => b.id === selectedBracket)
      : brackets;
    return {
      strategyAnchor,
      brackets: filtered,
      actionDetails: new Map(actionDetails),
    };
  }, [strategyAnchor, brackets, actionDetails, selectedBracket]);

  // Compute action gap stats (memoized)
  const { totalDrivers, actionGapCount } = useMemo(() => {
    const aMap = new Map(actionDetails);
    const total = brackets.reduce((sum, b) => sum + b.influencingKpiIds.length, 0);
    let withAction = 0;
    for (const b of brackets) {
      for (const driverId of b.influencingKpiIds) {
        const hasAction = b.actionCodeIds.some((aid) => aMap.get(aid)?.triggerKpis.includes(driverId));
        if (hasAction) withAction++;
      }
    }
    return { totalDrivers: total, actionGapCount: total - withAction };
  }, [brackets, actionDetails]);

  // YAML content for the editor
  const editorContent = useMemo(() => {
    if (selectedBracket && bracketYamls[selectedBracket]) {
      return bracketYamls[selectedBracket];
    }
    // Show summary of all brackets
    const summary = brackets.map((b) => ({
      id: b.id,
      title: b.title,
      domain: b.domain,
      strategic_kpi: b.strategicKpiId,
      drivers: b.influencingKpiIds.length,
      actions: b.actionCodeIds.length,
    }));
    return toYaml(summary);
  }, [selectedBracket, brackets, bracketYamls]);

  const handleYamlChange = useCallback((_value: string, _parsed: unknown) => {
    // TODO: bi-directional sync — validate and update flow
  }, []);

  const showFlow = viewMode === 'flow' || viewMode === 'split';
  const showEditor = viewMode === 'editor' || viewMode === 'split';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', flexShrink: 0 }}>
        <select
          value={selectedBracket ?? ''}
          onChange={(e) => setSelectedBracket(e.target.value || null)}
          style={{
            padding: 'var(--sp-1) var(--sp-1-5)',
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--slate-100)',
            fontSize: '0.875rem',
          }}
        >
          <option value="">All Use Cases ({brackets.length})</option>
          {brackets.map((b) => (
            <option key={b.id} value={b.id}>{b.id} — {b.title}</option>
          ))}
        </select>

        {/* View mode toggle */}
        <div style={{ display: 'flex', backgroundColor: 'var(--slate-800)', borderRadius: 'var(--radius-md)', border: '1px solid var(--slate-700)', overflow: 'hidden' }}>
          {(['flow', 'split', 'editor'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                padding: 'var(--sp-0-5) var(--sp-1-5)',
                backgroundColor: viewMode === mode ? 'var(--slate-700)' : 'transparent',
                border: 'none',
                color: viewMode === mode ? 'var(--slate-50)' : 'var(--slate-500)',
                fontSize: '0.75rem',
                fontWeight: viewMode === mode ? 600 : 400,
                cursor: 'pointer',
                textTransform: 'capitalize',
              }}
            >
              {mode === 'split' ? 'Flow + YAML' : mode === 'flow' ? 'Flow' : 'YAML'}
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', gap: 'var(--sp-2)', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--mint)' }}>{brackets.length} Use Cases</span>
          <span style={{ color: 'var(--slate-400)' }}>{totalDrivers} Drivers</span>
          {actionGapCount > 0 && (
            <span style={{ color: 'var(--gold)' }}>{actionGapCount} Action Gaps</span>
          )}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', gap: 'var(--sp-2)', minHeight: 0 }}>
        {showFlow && (
          <div
            style={{
              flex: 1,
              backgroundColor: 'var(--slate-950)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--slate-700)',
              overflow: 'hidden',
            }}
          >
            <GoldenThreadFlow data={flowData} />
          </div>
        )}
        {showEditor && (
          <div
            style={{
              flex: 1,
              backgroundColor: 'var(--slate-950)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--slate-700)',
              overflow: 'hidden',
            }}
          >
            <YamlEditor
              initialValue={editorContent}
              onChange={handleYamlChange}
              height="100%"
            />
          </div>
        )}
      </div>
    </div>
  );
}
