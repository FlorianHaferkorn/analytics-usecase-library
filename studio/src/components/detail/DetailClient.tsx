'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { CatalogKpi } from '@/lib/core/catalog-loader';
import { Pill } from './Pill';
import { DetailHistoryTab } from './DetailHistoryTab';

interface Comment {
  who: string;
  when: string;
  text: string;
}

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'definition', label: 'Definition' },
  { id: 'lineage', label: 'Lineage' },
  { id: 'comments', label: 'Comments' },
  { id: 'history', label: 'History' },
] as const;

type TabId = (typeof TABS)[number]['id'];

interface DetailClientProps {
  kpi: CatalogKpi | null;
  type: string;
  id: string;
}

export function DetailClient({ kpi, id }: DetailClientProps) {
  const [tab, setTab] = useState<TabId>('overview');
  const [name, setName] = useState(kpi?.kpi_key ?? id);
  const [editingName, setEditingName] = useState(false);
  const [desc, setDesc] = useState(
    kpi?.business.definition ??
      'Measures how revenue from existing customers evolves over time, inclusive of expansions, downgrades, and churn.'
  );
  const [editingDesc, setEditingDesc] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [draft, setDraft] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const persistKpi = useCallback(async (patch: { kpi_key?: string; business?: { definition?: string } }) => {
    if (!kpi) return;
    setSaveStatus('saving');
    try {
      const res = await fetch('/api/core/kpis', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kpi_id: kpi.kpi_id, ...patch }),
      });
      setSaveStatus(res.ok ? 'saved' : 'error');
    } catch {
      setSaveStatus('error');
    }
  }, [kpi]);

  const domain = kpi?.domain_tag?.[0] ?? 'Revenue';
  const kpiType = kpi?.kpi_type ?? 'Ratio';
  const owner = kpi?.governance.business_owner ?? 'R. Okafor';
  const grain = kpi?.business.grain_scope ?? 'Month';
  const unit = kpi?.business.unit_format ?? '%';
  const ref = kpi?.technical.dax_name ?? id;

  function addComment() {
    if (!draft.trim()) return;
    setComments([...comments, { who: 'A. Haferkorn', when: 'just now', text: draft }]);
    setDraft('');
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main */}
      <div className="flex-1 overflow-auto">
        <div style={{ maxWidth: 900, margin: '0 auto', padding: 'var(--pad)', width: '100%', paddingTop: 8 }}>

          {/* Back */}
          <Link
            href="/library"
            className="inline-flex items-center gap-1.5 text-[13px] text-foreground-subtle hover:text-foreground mb-[14px] transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <polyline points="8 2 4 6 8 10" />
            </svg>
            Back to library
          </Link>

          {saveStatus === 'saved' && (
            <p className="text-2xs text-positive mb-2">Saved to KPI catalog</p>
          )}
          {saveStatus === 'error' && (
            <p className="text-2xs text-red-400 mb-2">Save failed — check auth and try again</p>
          )}

          {/* Pill row */}
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-[11px] text-foreground-subtle">{ref}</span>
            <Pill tone="positive">Certified</Pill>
            <Pill tone="neutral">{kpiType}</Pill>
            <Pill tone="neutral">{domain}</Pill>
          </div>

          {/* Inline-editable title */}
          {editingName ? (
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => {
                setEditingName(false);
                if (kpi && name !== kpi.kpi_key) void persistKpi({ kpi_key: name });
              }}
              onKeyDown={(e) => e.key === 'Enter' && setEditingName(false)}
              className="w-full bg-transparent text-foreground outline-none border-b-2 border-accent"
              style={{ fontSize: 36, fontWeight: 500, letterSpacing: '-0.025em', padding: '0 4px', marginLeft: -4 }}
            />
          ) : (
            <h1
              onClick={() => setEditingName(true)}
              className="text-foreground cursor-text rounded-md transition-colors hover:bg-hover"
              style={{ fontSize: 36, fontWeight: 500, letterSpacing: '-0.025em', margin: 0, padding: '0 4px', marginLeft: -4 }}
            >
              {name}
            </h1>
          )}

          {/* Inline-editable description */}
          {editingDesc ? (
            <textarea
              autoFocus
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              onBlur={() => {
                setEditingDesc(false);
                if (kpi && desc !== kpi.business.definition) {
                  void persistKpi({ business: { definition: desc } });
                }
              }}
              className="w-full bg-transparent text-foreground-muted outline-none border border-accent rounded-lg resize-vertical"
              style={{ fontSize: 14.5, lineHeight: 1.6, padding: 10, marginTop: 10, minHeight: 80 }}
            />
          ) : (
            <p
              onClick={() => setEditingDesc(true)}
              className="text-foreground-muted cursor-text rounded-md transition-colors hover:bg-hover"
              style={{ fontSize: 14.5, lineHeight: 1.6, marginTop: 12, padding: '8px 4px', marginLeft: -4 }}
            >
              {desc}
            </p>
          )}

          {/* Tab bar */}
          <div className="flex gap-0.5 border-b border-border mt-[22px] mb-5">
            {TABS.map((t) => {
              const active = tab === t.id;
              const count = t.id === 'comments' ? comments.length : undefined;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`px-3.5 py-2.5 text-[13px] flex items-center gap-2 transition-colors ${
                    active ? 'font-medium text-foreground' : 'font-normal text-foreground-muted hover:text-foreground'
                  }`}
                  style={{ borderBottom: active ? '1.5px solid var(--accent)' : '1.5px solid transparent', marginBottom: -1 }}
                >
                  {t.label}
                  {count != null && (
                    <span className={`text-2xs font-mono ${active ? 'text-foreground-muted' : 'text-foreground-subtle'}`}>
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab: Overview */}
          {tab === 'overview' && (
            <div className="flex flex-col gap-[var(--gap)]">
              <div className="rounded-[var(--radius-card)] border border-border bg-panel overflow-hidden">
                <div className="flex items-center justify-between px-[var(--pad)] py-3.5 border-b border-border-subtle">
                  <span className="text-[11px] font-semibold text-foreground-muted uppercase tracking-[0.08em]">Latest value</span>
                  <span className="font-mono text-[11px] text-foreground-subtle">as of today</span>
                </div>
                <div className="p-[var(--pad)]">
                  <div className="font-mono text-foreground" style={{ fontSize: 48, fontWeight: 500, letterSpacing: '-0.03em', lineHeight: 1.05 }}>
                    114%
                  </div>
                  <div className="text-[12px] text-positive mt-1">+2 pts vs last month</div>
                </div>
              </div>
              <div className="rounded-[var(--radius-card)] border border-border bg-panel overflow-hidden">
                <div className="flex items-center justify-between px-[var(--pad)] py-3.5 border-b border-border-subtle">
                  <span className="text-[11px] font-semibold text-foreground-muted uppercase tracking-[0.08em]">Dimensions</span>
                  <button className="text-[12px] text-foreground-subtle hover:text-foreground transition-colors">+ Add</button>
                </div>
                <div className="p-[var(--pad)] flex flex-wrap gap-2">
                  {['Plan Tier', 'Region', 'Signup Cohort', 'Channel'].map((d) => (
                    <Pill key={d} tone="neutral">{d}</Pill>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab: Definition */}
          {tab === 'definition' && (
            <div className="rounded-[var(--radius-card)] border border-border bg-panel overflow-hidden">
              <div className="flex items-center justify-between px-[var(--pad)] py-3.5 border-b border-border-subtle">
                <div>
                  <div className="text-[11px] font-semibold text-foreground-muted uppercase tracking-[0.08em]">DAX / SQL</div>
                  <div className="text-[11.5px] text-foreground-subtle mt-0.5">{kpi?.technical.description || 'Compiled expression'}</div>
                </div>
                <button className="text-[12px] text-foreground-subtle hover:text-foreground transition-colors">Copy</button>
              </div>
              <pre
                className="font-mono text-foreground-muted overflow-auto bg-background-muted"
                style={{ fontSize: 12.5, lineHeight: 1.7, padding: 'var(--pad)', margin: 0 }}
              >
                {kpi?.technical.dax_expression ||
                  `select\n  cohort_month,\n  sum(ending_arr) / nullif(sum(starting_arr), 0) as nrr\nfrom {{ ref('fct_customer_arr') }}\nwhere cohort_month >= date_trunc('month', current_date) - interval '12 month'\ngroup by 1;`}
              </pre>
            </div>
          )}

          {/* Tab: Lineage */}
          {tab === 'lineage' && (
            <div className="rounded-[var(--radius-card)] border border-border bg-panel p-[var(--pad)] text-[13px] text-foreground-muted">
              {kpi?.technical.lineage?.length ? (
                kpi.technical.lineage.map((l, i) => (
                  <span key={l}><span className="font-mono text-foreground">{l}</span>{i < kpi.technical.lineage.length - 1 ? ' → ' : ''}</span>
                ))
              ) : (
                <span>
                  Upstream: <span className="font-mono text-foreground">src.billing</span> →{' '}
                  <span className="font-mono text-foreground">met.revenue.mrr</span>. Downstream:{' '}
                  <span className="font-mono text-foreground">goal.efficient_growth</span>.
                </span>
              )}
              <div className="mt-3">
                <Link href="/canvas" className="text-[13px] text-accent hover:opacity-80 transition-opacity">
                  Open in Canvas →
                </Link>
              </div>
            </div>
          )}

          {/* Tab: Comments */}
          {tab === 'comments' && (
            <div className="flex flex-col gap-3">
              {comments.map((c, i) => (
                <div key={i} className="rounded-[var(--radius-card)] border border-border bg-panel" style={{ padding: '14px var(--pad)' }}>
                  <div className="flex items-center gap-2.5 mb-1.5">
                    <div
                      className="flex-shrink-0 grid place-items-center rounded-full text-white"
                      style={{ width: 24, height: 24, fontSize: 10, fontWeight: 600, background: `oklch(0.65 0.12 ${(i * 80) % 360})` }}
                    >
                      {c.who.split(/[.\s]/).map((s) => s[0]).join('')}
                    </div>
                    <span className="text-[12.5px] font-medium text-foreground">{c.who}</span>
                    <span className="text-[11.5px] text-foreground-subtle">{c.when}</span>
                  </div>
                  <p className="text-foreground-muted" style={{ fontSize: 13.5, lineHeight: 1.55 }}>{c.text}</p>
                </div>
              ))}
              <div className="rounded-[var(--radius-card)] border border-border bg-panel flex items-center gap-2.5 px-3 py-2">
                <input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addComment()}
                  placeholder="Leave a comment or @mention someone…"
                  className="flex-1 bg-transparent text-[13px] text-foreground outline-none"
                />
                <button
                  onClick={addComment}
                  className="px-3 py-1.5 rounded-lg bg-accent text-accent-ink text-[13px] font-medium hover:opacity-90 transition-opacity"
                >
                  Comment
                </button>
              </div>
            </div>
          )}

          {/* Tab: History */}
          {tab === 'history' && kpi && (
            <DetailHistoryTab entityId={kpi.kpi_id} entityTypes={['kpi']} />
          )}

        </div>
      </div>

      {/* Right rail */}
      <aside className="w-[300px] flex-shrink-0 border-l border-border bg-background overflow-auto" style={{ padding: 'var(--pad)' }}>
        <div className="text-[11px] text-foreground-subtle uppercase tracking-[0.08em] mb-3">Properties</div>
        <div className="flex flex-col gap-3.5 text-[12.5px]">
          {([
            ['Owner', owner],
            ['Domain', domain],
            ['Type', kpiType],
            ['Grain', grain],
            ['Unit', unit],
            ['Version', kpi?.governance.version ?? '1.0'],
          ] as [string, string][]).map(([label, value]) => (
            <div key={label} className="grid gap-2" style={{ gridTemplateColumns: '90px 1fr' }}>
              <span className="text-[11.5px] text-foreground-subtle">{label}</span>
              <span className="text-foreground-muted">{value}</span>
            </div>
          ))}
        </div>

        <div className="mt-6 mb-3 text-[11px] text-foreground-subtle uppercase tracking-[0.08em]">Studio AI</div>
        <div
          className="rounded-[var(--radius-card)] border border-border p-3.5"
          style={{ background: 'linear-gradient(180deg, var(--accent-soft), transparent)' }}
        >
          <div className="flex items-center gap-1.5 text-[12px] font-medium text-foreground mb-2">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M6 1l1.2 3.6L11 6 7.2 7.4 6 11 4.8 7.4 1 6l3.8-1.4z" />
            </svg>
            Suggestions
          </div>
          <p className="text-[12.5px] text-foreground-muted leading-[1.5] mb-2.5">
            Your definition references <span className="font-mono">fct_customer_arr</span> but omits mid-month contractions. Shall I draft a fix?
          </p>
          <button className="w-full px-3 py-1.5 rounded-lg bg-accent text-accent-ink text-[13px] font-medium hover:opacity-90 transition-opacity flex items-center justify-center">
            Review draft
          </button>
        </div>
      </aside>
    </div>
  );
}
