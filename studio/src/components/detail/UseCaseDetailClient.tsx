'use client';

import { useCallback, useState, Suspense } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { useRouter, useSearchParams } from 'next/navigation';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { FactsheetSummary } from '@/lib/core/factsheet-loader';
import { Pill } from './Pill';
import { CascadingDiffPanel, type CascadingProposal } from './CascadingDiffPanel';
import { DetailHistoryTab } from './DetailHistoryTab';
import { MarkdownEditor } from '@/components/editor/markdown-editor';
import { detailPath } from '@/lib/studio/entity-ia';
import { StudioButton, StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

const YamlEditor = dynamic(
  () => import('@/components/editor/yaml-editor').then((m) => m.YamlEditor),
  { ssr: false, loading: () => <div className="text-foreground-muted text-sm p-4">Loading editor…</div> },
);

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'factsheet', label: 'Factsheet' },
  { id: 'bracket', label: 'Bracket' },
  { id: 'contracts', label: 'Data Contracts' },
  { id: 'history', label: 'History' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export interface UseCaseDetailClientProps {
  bracket: UseCaseBracketV20Lean;
  initialYaml: string;
  initialMarkdown: string;
  factsheet: FactsheetSummary | null;
  bracketSchema?: Record<string, unknown>;
}

function UseCaseDetailInner({
  bracket,
  initialYaml,
  initialMarkdown,
  factsheet,
  bracketSchema,
}: UseCaseDetailClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const compareMode = searchParams.get('compare') === '1';

  const [tab, setTab] = useState<TabId>('overview');
  const [prose, setProse] = useState(initialMarkdown);
  const [yaml, setYaml] = useState(initialYaml);
  const [proseDirty, setProseDirty] = useState(false);
  const [yamlDirty, setYamlDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proposal, setProposal] = useState<CascadingProposal | null>(null);

  const toggleCompare = () => {
    const params = new URLSearchParams(searchParams.toString());
    if (compareMode) params.delete('compare');
    else params.set('compare', '1');
    router.replace(`/detail/usecase/${bracket.id}?${params.toString()}`);
  };

  const saveFactsheet = useCallback(async () => {
    const res = await fetch(`/api/factsheets/${encodeURIComponent(bracket.id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: prose }),
    });
    if (!res.ok) throw new Error(await res.text());
    setProseDirty(false);
  }, [bracket.id, prose]);

  const saveBracket = useCallback(async (content?: string) => {
    const body = content ?? yaml;
    const res = await fetch(`/api/core/brackets/${encodeURIComponent(bracket.id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yaml: body }),
    });
    if (!res.ok) throw new Error(await res.text());
    if (content) setYaml(content);
    setYamlDirty(false);
  }, [bracket.id, yaml]);

  const runReconcile = useCallback(
    async (editedSource: 'factsheet' | 'bracket') => {
      const res = await fetch('/api/ai/factsheet-draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: 'reconcile',
          editedSource,
          prose,
          bracket: yaml,
          change_hint: `User saved ${editedSource}`,
        }),
      });
      if (!res.ok) return null;
      const data = (await res.json()) as CascadingProposal & { patch?: string | null; target?: string | null };
      if (!data.patch || !data.target) return null;
      if (data.target !== 'factsheet' && data.target !== 'bracket') return null;
      return data as CascadingProposal;
    },
    [prose, yaml],
  );

  const handleSave = useCallback(
    async (source: 'factsheet' | 'bracket') => {
      setSaving(true);
      setError(null);
      setProposal(null);
      try {
        if (source === 'factsheet') {
          await saveFactsheet();
          const next = await runReconcile('factsheet');
          if (next) setProposal(next);
        } else {
          await saveBracket();
          const next = await runReconcile('bracket');
          if (next) setProposal(next);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Save failed');
      } finally {
        setSaving(false);
      }
    },
    [saveFactsheet, saveBracket, runReconcile],
  );

  const handleAcceptProposal = useCallback(async () => {
    if (!proposal) return;
    setSaving(true);
    setError(null);
    try {
      if (proposal.target === 'factsheet') {
        setProse(proposal.patch);
        await fetch(`/api/factsheets/${encodeURIComponent(bracket.id)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ markdown: proposal.patch }),
        });
        setProseDirty(false);
      } else {
        await saveBracket(proposal.patch);
      }
      setProposal(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Apply failed');
    } finally {
      setSaving(false);
    }
  }, [proposal, bracket.id, saveBracket]);

  const owner =
    factsheet?.business_owner ??
    bracket.governance?.owner_role ??
    'Unassigned';

  const kpiLinks = [
    { id: bracket.orchestration.strategic_kpi_id, role: 'Strategic' },
    ...bracket.orchestration.influencing_kpi_ids.map((id) => ({ id, role: 'Influencing' })),
    ...(bracket.orchestration.supporting_kpi_ids ?? []).map((id) => ({ id, role: 'Supporting' })),
  ];

  return (
    <StudioPage>
      <StudioPageHeader
        eyebrow="Registry / Use Case Detail"
        title={bracket.title}
        description={`Strategic KPI: ${bracket.orchestration.strategic_kpi_id} · ${bracket.orchestration.action_code_ids.length} actions`}
        badge={bracket.id}
        tone="info"
        actions={
          <>
            <Link href="/library?tab=usecases" style={{ fontSize: 13, color: 'var(--accent)', textDecoration: 'none', marginRight: 8 }}>
              ← Library
            </Link>
            <StudioButton variant={compareMode ? 'primary' : 'secondary'} onClick={toggleCompare} style={{ padding: '6px 12px', fontSize: 13 }}>
              {compareMode ? 'Exit compare' : 'Compare view'}
            </StudioButton>
          </>
        }
      />
    <div className="flex flex-col min-h-0">

      {!compareMode && (
        <div className="flex gap-0.5 border-b border-border mb-4">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`px-3.5 py-2.5 text-[13px] border-b-2 -mb-px transition-colors ${
                tab === t.id
                  ? 'font-medium text-foreground border-accent'
                  : 'text-foreground-muted border-transparent hover:text-foreground'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      {error && <p className="text-2xs text-red-400 mb-3">{error}</p>}
      {proposal && (
        <div className="mb-4">
          <CascadingDiffPanel
            proposal={proposal}
            onAccept={handleAcceptProposal}
            onReject={() => setProposal(null)}
            busy={saving}
          />
        </div>
      )}

      {compareMode ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-[520px]">
          <div className="flex flex-col gap-2 min-h-0">
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-foreground">Factsheet</span>
              <button
                type="button"
                disabled={!proseDirty || saving}
                onClick={() => handleSave('factsheet')}
                className="px-3 py-1.5 rounded-lg bg-foreground text-background text-[12px] font-medium disabled:opacity-40"
              >
                Save factsheet
              </button>
            </div>
            <div className="flex-1 rounded-lg border border-border overflow-hidden">
              <MarkdownEditor value={prose} onChange={(v) => { setProse(v); setProseDirty(true); }} height="520px" />
            </div>
          </div>
          <div className="flex flex-col gap-2 min-h-0">
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-foreground">Bracket</span>
              <button
                type="button"
                disabled={!yamlDirty || saving}
                onClick={() => handleSave('bracket')}
                className="px-3 py-1.5 rounded-lg bg-foreground text-background text-[12px] font-medium disabled:opacity-40"
              >
                Save bracket
              </button>
            </div>
            <div className="flex-1 rounded-lg border border-border overflow-hidden">
              <YamlEditor
                key={`compare-${bracket.id}`}
                initialValue={yaml}
                schema={bracketSchema}
                height="520px"
                onChange={(v) => { setYaml(v); setYamlDirty(true); }}
              />
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div className="space-y-4 max-w-3xl">
              <div className="rounded-lg border border-border bg-panel p-4 space-y-2 text-[13px]">
                <p className="text-foreground-muted">
                  <span className="text-foreground font-medium">Purpose: </span>
                  {factsheet?.purpose ?? '—'}
                </p>
                <p className="text-foreground-muted">
                  <span className="text-foreground font-medium">Business value: </span>
                  {factsheet?.business_value ?? '—'}
                </p>
                <p className="text-foreground-muted">
                  <span className="text-foreground font-medium">Impact: </span>
                  {bracket.value_driver_model.impact_direction} · {bracket.value_driver_model.primary_driver}
                </p>
              </div>
              {factsheet?.business_questions && factsheet.business_questions.length > 0 && (
                <ul className="list-disc pl-5 text-[13px] text-foreground-muted space-y-1">
                  {factsheet.business_questions.map((q) => (
                    <li key={q}>{q}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {tab === 'factsheet' && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <button
                  type="button"
                  disabled={!proseDirty || saving}
                  onClick={() => handleSave('factsheet')}
                  className="px-3.5 py-2 rounded-lg bg-foreground text-background text-[13px] font-medium disabled:opacity-40"
                >
                  {saving ? 'Saving…' : 'Save factsheet'}
                </button>
              </div>
              <div className="rounded-lg border border-border overflow-hidden">
                <MarkdownEditor value={prose} onChange={(v) => { setProse(v); setProseDirty(true); }} />
              </div>
            </div>
          )}

          {tab === 'bracket' && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <button
                  type="button"
                  disabled={!yamlDirty || saving}
                  onClick={() => handleSave('bracket')}
                  className="px-3.5 py-2 rounded-lg bg-foreground text-background text-[13px] font-medium disabled:opacity-40"
                >
                  {saving ? 'Saving…' : 'Save bracket'}
                </button>
              </div>
              <div className="rounded-lg border border-border overflow-hidden min-h-[420px]">
                <YamlEditor
                  key={bracket.id}
                  initialValue={yaml}
                  schema={bracketSchema}
                  height="480px"
                  onChange={(v) => { setYaml(v); setYamlDirty(true); }}
                />
              </div>
            </div>
          )}

          {tab === 'contracts' && (
            <div className="space-y-3 max-w-3xl">
              <p className="text-[13px] text-foreground-muted">
                KPIs and actions referenced by this use case (open in Detail or Canvas).
              </p>
              <div className="rounded-lg border border-border divide-y divide-border">
                {kpiLinks.map((k) => (
                  <Link
                    key={k.id}
                    href={detailPath('kpi', k.id)}
                    className="flex items-center justify-between px-4 py-3 text-[13px] hover:bg-hover"
                  >
                    <span className="font-mono text-foreground">{k.id}</span>
                    <span className="text-foreground-muted">{k.role}</span>
                  </Link>
                ))}
                {bracket.orchestration.action_code_ids.map((aid) => (
                  <Link
                    key={aid}
                    href={detailPath('action', aid)}
                    className="flex items-center justify-between px-4 py-3 text-[13px] hover:bg-hover"
                  >
                    <span className="font-mono text-foreground">{aid}</span>
                    <span className="text-foreground-muted">Action code</span>
                  </Link>
                ))}
              </div>
              <Link href={`/canvas?view=golden-thread`} className="text-[13px] text-accent hover:opacity-80">
                Open Golden Thread in Canvas →
              </Link>
            </div>
          )}

          {tab === 'history' && (
            <DetailHistoryTab entityId={bracket.id} entityTypes={['bracket', 'factsheet']} />
          )}
        </>
      )}
    </div>
    </StudioPage>
  );
}

export function UseCaseDetailClient(props: UseCaseDetailClientProps) {
  return (
    <Suspense fallback={<div className="text-foreground-muted text-sm">Loading…</div>}>
      <UseCaseDetailInner {...props} />
    </Suspense>
  );
}
