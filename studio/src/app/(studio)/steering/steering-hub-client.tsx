'use client';

import { useCallback, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { useProjectStore } from '@/lib/store/project-store';
import { GoldenThreadFlow, type GoldenThreadData } from '@/components/flow/golden-thread-flow';
import { parseYaml, toYaml } from '@/lib/core/yaml-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { ExportReportButton } from '@/components/steering/export-report-button';
import { ExportExcelButton } from '@/components/steering/export-excel-button';
import { StudioFormField, StudioInput, StudioSelect } from '@/components/ui/studio-data';
import { StudioButton, StudioField, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioSegmentedControl, StudioToolbar } from '@/components/ui/studio-page';

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
  bracketYamls: Record<string, string>;
  kpiNames?: Record<string, string>;
  initialSelectedBracket?: string | null;
  draftBracketId?: string | null;
}

type ViewMode = 'flow' | 'split' | 'editor';

/** Extract BracketData fields from a parsed YAML bracket object. */
function extractBracketData(parsed: Record<string, unknown>): Partial<BracketData> | null {
  if (!parsed || typeof parsed !== 'object') return null;

  const orch = parsed.orchestration as Record<string, unknown> | undefined;
  const vdm = parsed.value_driver_model as Record<string, unknown> | undefined;

  const result: Partial<BracketData> = {};
  if (typeof parsed.title === 'string') result.title = parsed.title;
  if (typeof parsed.domain === 'string') result.domain = parsed.domain;
  if (orch) {
    if (typeof orch.strategic_kpi_id === 'string') result.strategicKpiId = orch.strategic_kpi_id;
    if (Array.isArray(orch.influencing_kpi_ids)) result.influencingKpiIds = orch.influencing_kpi_ids;
    if (Array.isArray(orch.action_code_ids)) result.actionCodeIds = orch.action_code_ids;
  }
  if (vdm && typeof vdm.impact_direction === 'string') result.impactDirection = vdm.impact_direction;

  return result;
}

export function SteeringHubClient({ strategyAnchor: initialAnchor, brackets: initialBrackets, actionDetails, bracketYamls: initialYamls, kpiNames = {}, initialSelectedBracket = null, draftBracketId = null }: Props) {
  const storeAnchor = useProjectStore((s) => s.strategyAnchor);
  const strategyAnchor = storeAnchor || initialAnchor;

  const [selectedBracket, setSelectedBracket] = useState<string | null>(initialSelectedBracket);
  const [viewMode, setViewMode] = useState<ViewMode>('flow');
  const [brackets, setBrackets] = useState<BracketData[]>(initialBrackets);
  const [bracketYamls, setBracketYamls] = useState<Record<string, string>>(initialYamls);
  const [syncStatus, setSyncStatus] = useState<'synced' | 'dirty' | 'error'>('synced');
  const [isSaving, setIsSaving] = useState(false);
  const [activeDraftBracketId, setActiveDraftBracketId] = useState<string | null>(draftBracketId);
  const [createTargetId, setCreateTargetId] = useState(() => (draftBracketId && /^DRAFT-/.test(draftBracketId) ? 'XD-900' : draftBracketId ?? ''));
  const [createTargetTitle, setCreateTargetTitle] = useState(() => (initialSelectedBracket ? initialBrackets.find((bracket) => bracket.id === initialSelectedBracket)?.title ?? '' : ''));
  const [createError, setCreateError] = useState<string | null>(null);
  const [creatingBracket, setCreatingBracket] = useState(false);

  const handleSave = useCallback(async () => {
    if (!selectedBracket || syncStatus !== 'dirty') return;
    if (activeDraftBracketId && selectedBracket === activeDraftBracketId) return;
    const yaml = bracketYamls[selectedBracket];
    if (!yaml) return;
    setIsSaving(true);
    try {
      const res = await fetch(`/api/core/brackets/${encodeURIComponent(selectedBracket)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml }),
      });
      if (res.ok) {
        setSyncStatus('synced');
      } else {
        console.error('Save failed', await res.text());
      }
    } catch (err) {
      console.error('Save error', err);
    } finally {
      setIsSaving(false);
    }
  }, [selectedBracket, syncStatus, bracketYamls, activeDraftBracketId]);

  const handleCreateFromDraft = useCallback(async () => {
    if (!selectedBracket || !activeDraftBracketId || selectedBracket !== activeDraftBracketId) return;
    const yaml = bracketYamls[selectedBracket];
    if (!yaml || !createTargetId.trim() || !createTargetTitle.trim()) return;

    setCreatingBracket(true);
    setCreateError(null);
    try {
      const parsed = parseYaml<UseCaseBracketV20Lean>(yaml);
      parsed.id = createTargetId.trim();
      parsed.title = createTargetTitle.trim();
      parsed.documentation = { business_factsheet: './Business_Factsheet.md' };

      const response = await fetch('/api/core/brackets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: createTargetId.trim(), title: createTargetTitle.trim(), yaml: toYaml(parsed) }),
      });
      const json = await response.json() as { error?: { message?: string } };
      if (!response.ok) {
        setCreateError(json.error?.message ?? `HTTP ${response.status}`);
        return;
      }

      const nextYaml = toYaml(parsed);
      const previousDraftId = selectedBracket;
      setBrackets((prev) => prev.map((bracket) => bracket.id === previousDraftId ? {
        ...bracket,
        id: createTargetId.trim(),
        title: createTargetTitle.trim(),
      } : bracket));
      setBracketYamls((prev) => {
        const next = { ...prev };
        delete next[previousDraftId];
        next[createTargetId.trim()] = nextYaml;
        return next;
      });
      setSelectedBracket(createTargetId.trim());
      setActiveDraftBracketId(null);
      setSyncStatus('synced');
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : 'Bracket creation failed');
    } finally {
      setCreatingBracket(false);
    }
  }, [selectedBracket, activeDraftBracketId, bracketYamls, createTargetId, createTargetTitle]);

  const flowData = useMemo<GoldenThreadData>(() => {
    const filtered = selectedBracket
      ? brackets.filter((b) => b.id === selectedBracket)
      : brackets;
    return {
      strategyAnchor,
      brackets: filtered,
      actionDetails: new Map(actionDetails),
      kpiNames,
    };
  }, [strategyAnchor, brackets, actionDetails, selectedBracket, kpiNames]);

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

  const editorContent = useMemo(() => {
    if (selectedBracket && bracketYamls[selectedBracket]) {
      return bracketYamls[selectedBracket];
    }
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

  const handleYamlChange = useCallback(
    (value: string, parsed: unknown) => {
      if (!selectedBracket) return;

      const data = extractBracketData(parsed as Record<string, unknown>);
      if (!data) {
        setSyncStatus('error');
        return;
      }

      setBrackets((prev) =>
        prev.map((b) => (b.id === selectedBracket ? { ...b, ...data } : b))
      );
      setBracketYamls((prev) => ({ ...prev, [selectedBracket]: value }));
      setSyncStatus('dirty');
    },
    [selectedBracket]
  );

  const showFlow = viewMode === 'flow' || viewMode === 'split';
  const showEditor = viewMode === 'editor' || viewMode === 'split';

  const handleBracketSelectFromFlow = useCallback((useCaseId: string) => {
    setSelectedBracket(useCaseId);
    setViewMode('split');
    setSyncStatus('synced');
  }, []);

  const syncIndicator = syncStatus === 'synced'
    ? { color: 'var(--mint)', label: 'Synced' }
    : syncStatus === 'dirty'
      ? { color: 'var(--gold)', label: 'Modified' }
      : { color: 'var(--danger)', label: 'Parse Error' };

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Decision Design"
        title="Steering"
        description="Navigate the golden thread, refine bracket YAML, and turn draft scaffolds into governed use cases without leaving the same working surface."
        badge={selectedBracket ?? `All ${brackets.length}`}
        tone="success"
        actions={<><ExportReportButton /><ExportExcelButton /></>}
      />

      <StudioMetricBar>
        <StudioMetric label="Use Cases" value={brackets.length} meta="loaded into steering graph" tone="info" />
        <StudioMetric label="Drivers" value={totalDrivers} meta="in linked brackets" />
        <StudioMetric label="Action gaps" value={actionGapCount} meta={actionGapCount > 0 ? 'resolve in Registry →' : 'all drivers covered'} tone={actionGapCount > 0 ? 'warning' : 'success'} />
        <StudioMetric label="Sync" value={selectedBracket ? syncIndicator.label : 'overview'} meta={selectedBracket ? 'current bracket state' : 'aggregate mode'} tone={syncStatus === 'error' ? 'warning' : syncStatus === 'dirty' ? 'warning' : 'success'} />
      </StudioMetricBar>

      <StudioToolbar>
        <StudioField label="Bracket focus">
          <StudioSelect
            value={selectedBracket ?? ''}
            onChange={(e) => { setSelectedBracket(e.target.value || null); setSyncStatus('synced'); }}
            style={{
              fontSize: '0.875rem',
              minWidth: '280px',
            }}
          >
            <option value="">All Use Cases ({brackets.length})</option>
            {Object.entries(
              brackets.reduce<Record<string, BracketData[]>>((acc, b) => {
                (acc[b.domain] ??= []).push(b);
                return acc;
              }, {})
            ).sort(([a], [b]) => a.localeCompare(b)).map(([domain, items]) => (
              <optgroup key={domain} label={domain}>
                {items.map((b) => (
                  <option key={b.id} value={b.id}>{b.id}{activeDraftBracketId === b.id ? ' [Draft]' : ''} — {b.title}</option>
                ))}
              </optgroup>
            ))}
          </StudioSelect>
        </StudioField>

        <StudioField label="Workspace mode">
          <StudioSegmentedControl
            value={viewMode}
            onChange={setViewMode}
            options={[
              { value: 'flow', label: 'Flow' },
              { value: 'split', label: 'Flow + YAML' },
              { value: 'editor', label: 'YAML' },
            ]}
          />
        </StudioField>

        <div style={{ flex: 1 }} />

        {selectedBracket ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {activeDraftBracketId === selectedBracket && (
              <span style={{ fontSize: '0.6875rem', color: 'var(--info)' }}>Draft scaffold loaded</span>
            )}
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: syncIndicator.color }} />
            <span style={{ fontSize: '0.6875rem', color: syncIndicator.color }}>{syncIndicator.label}</span>
            {syncStatus === 'dirty' && activeDraftBracketId !== selectedBracket && (
              <StudioButton onClick={() => void handleSave()} tone="success" variant="secondary" disabled={isSaving} style={{ padding: '6px 10px' }}>
                {isSaving ? 'Saving…' : 'Save to core/'}
              </StudioButton>
            )}
          </div>
        ) : null}
      </StudioToolbar>

      <div style={{ flex: 1, display: 'flex', gap: 'var(--sp-2)', minHeight: 0 }}>
        {showFlow && (
          <StudioPanel title="Golden Thread Flow" description="Explore strategy anchors, drivers, and action-code coverage visually." tone="success" style={{ flex: 1, overflow: 'hidden' }}>
            <GoldenThreadFlow data={flowData} onBracketSelect={handleBracketSelectFromFlow} />
          </StudioPanel>
        )}
        {showEditor && (
          <StudioPanel title="Bracket YAML" description="Inspect and refine the machine-readable source of truth for the selected bracket." tone="info" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {activeDraftBracketId === selectedBracket && (
              <div style={{ padding: 'var(--sp-1)', borderBottom: '1px solid var(--slate-700)', backgroundColor: 'var(--slate-900)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr auto', gap: '8px', alignItems: 'end' }}>
                  <StudioFormField label="Target ID">
                    <StudioInput
                      value={createTargetId}
                      onChange={(event) => setCreateTargetId(event.target.value.toUpperCase())}
                      style={{ padding: '6px 8px', backgroundColor: 'var(--slate-950)', fontSize: '0.75rem' }}
                    />
                  </StudioFormField>
                  <StudioFormField label="Title">
                    <StudioInput
                      value={createTargetTitle}
                      onChange={(event) => setCreateTargetTitle(event.target.value)}
                      style={{ padding: '6px 8px', backgroundColor: 'var(--slate-950)', fontSize: '0.75rem' }}
                    />
                  </StudioFormField>
                  <StudioButton
                    onClick={() => void handleCreateFromDraft()}
                    disabled={creatingBracket || !createTargetId.trim() || !createTargetTitle.trim()}
                    tone="success"
                    variant="secondary"
                    style={{ padding: '7px 10px' }}
                  >
                    {creatingBracket ? 'Creating...' : 'Create in core/'}
                  </StudioButton>
                </div>
                {createError && <p style={{ fontSize: '0.6875rem', color: 'var(--danger)' }}>{createError}</p>}
              </div>
            )}
            <YamlEditor
              initialValue={editorContent}
              onChange={handleYamlChange}
              readOnly={!selectedBracket}
              height="100%"
            />
          </StudioPanel>
        )}
      </div>
    </StudioPage>
  );
}
