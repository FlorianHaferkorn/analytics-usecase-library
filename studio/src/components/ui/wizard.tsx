'use client';

import { useState, useEffect, useCallback } from 'react';
import { AiField } from '@/components/ai/ai-field';

type ElementKind = 'kpi' | 'bracket' | 'action' | 'source';

interface DraftResult {
  name: string;
  ref: string;
  domain: string;
  type: string;
  grain: string;
  unit?: string;
  description: string;
  sql?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave?: (kind: ElementKind, draft: DraftResult) => void | Promise<void>;
  saving?: boolean;
  saveError?: string | null;
}

const KINDS: Array<{ id: ElementKind; label: string; desc: string; letter: string }> = [
  { id: 'kpi', letter: 'K', label: 'KPI', desc: 'A measurable number — count, sum, ratio or model output.' },
  { id: 'source', letter: 'S', label: 'Data Source', desc: 'A governed source system or fact table contract.' },
  { id: 'bracket', letter: 'B', label: 'Use Case', desc: 'Factsheet + bracket for an analytics use case.' },
  { id: 'action', letter: 'A', label: 'Action', desc: 'A triggered action code with KPI conditions and logic.' },
];

function slug(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40);
}

export function Wizard({ open, onClose, onSave, saving = false, saveError = null }: Props) {
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState<ElementKind>('kpi');
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [isLoadingDraft, setIsLoadingDraft] = useState(false);
  const [draft, setDraft] = useState<DraftResult | null>(null);
  const [draftName, setDraftName] = useState('');
  const [draftDescription, setDraftDescription] = useState('');
  const [genError, setGenError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setStep(0); setKind('kpi'); setPrompt(''); setDraft(null); setGenError(null);
      setDraftName(''); setDraftDescription(''); setIsLoadingDraft(false);
    }
  }, [open]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'n' && !(e.target as HTMLElement).matches('input,textarea')) {
        window.dispatchEvent(new CustomEvent('studio:open-wizard'));
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const generateDraft = useCallback(async () => {
    setGenerating(true);
    setIsLoadingDraft(true);
    setGenError(null);

    // Pre-populate Step 2 fields from lightweight factsheet-draft endpoint.
    // Capture pre-draft values directly so they're available in the merge below
    // (React state updates are async — relying on draftName/draftDescription
    // would read stale closure values after setDraftName/setDraftDescription).
    let preName = '';
    let preDescription = '';
    try {
      const preRes = await fetch('/api/ai/factsheet-draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      if (preRes.ok) {
        const pre = await preRes.json() as { name?: string; description?: string };
        preName = pre.name ?? '';
        preDescription = pre.description ?? '';
        if (preName) setDraftName(preName);
        if (preDescription) setDraftDescription(preDescription);
      }
    } catch {
      // Silently fail — step 2 fields stay empty
    } finally {
      setIsLoadingDraft(false);
    }

    try {
      const res = await fetch('/api/ai/wizard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind, prompt }),
      });
      const json = await res.json() as { draft?: DraftResult; error?: string };
      if (!res.ok || json.error) {
        setGenError(json.error ?? `HTTP ${res.status}`);
        return;
      }
      if (json.draft) {
        const merged = {
          ...json.draft,
          name: preName || json.draft.name,
          description: preDescription || json.draft.description,
        };
        setDraft(merged);
        setDraftName(merged.name);
        setDraftDescription(merged.description);
        setStep(2);
      }
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setGenerating(false);
    }
  }, [kind, prompt]);

  if (!open) return null;

  const steps = ['Choose', 'Describe', 'Review'];

  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 'var(--z-modal)' as never, background: 'rgba(11,11,12,0.4)', backdropFilter: 'blur(4px)', display: 'grid', placeItems: 'center', padding: 40 }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 680, maxWidth: '100%', maxHeight: '88vh', background: 'var(--panel)', borderRadius: 14, border: '1px solid var(--line)', boxShadow: 'var(--shadow-lg)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
      >
        {/* Stepper */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--line-2)', display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: '0.625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>New element</span>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
            {steps.map((s, i) => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: i === step ? 'var(--ink)' : 'var(--ink-4)', fontWeight: i === step ? 500 : 400 }}>
                <span style={{
                  width: 18, height: 18, borderRadius: 99, display: 'grid', placeItems: 'center',
                  fontSize: '0.5625rem', fontWeight: 600,
                  background: i <= step ? 'var(--accent)' : 'var(--bg-2)',
                  color: i <= step ? 'var(--accent-ink)' : 'var(--ink-4)',
                }}>
                  {i < step ? '✓' : i + 1}
                </span>
                {s}
                {i < 2 && <span style={{ width: 16, height: 1, background: 'var(--line)', marginLeft: 2 }} />}
              </div>
            ))}
          </div>
          <button onClick={onClose} aria-label="Close" style={{ width: 28, height: 28, display: 'grid', placeItems: 'center', borderRadius: 6, color: 'var(--ink-3)', border: 'none', background: 'transparent', cursor: 'pointer' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="m4 4 8 8M12 4l-8 8" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', padding: 28 }}>
          {step === 0 && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.375rem', fontWeight: 500, margin: '0 0 6px', letterSpacing: '-0.02em', color: 'var(--ink)' }}>
                What are you creating?
              </h2>
              <p style={{ color: 'var(--ink-3)', margin: '0 0 20px', fontSize: '0.875rem' }}>
                Pick a primitive. You can change the type at any time.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                {KINDS.map((o) => {
                  const active = kind === o.id;
                  return (
                    <button
                      key={o.id}
                      onClick={() => setKind(o.id)}
                      style={{
                        padding: 16, borderRadius: 10, textAlign: 'left',
                        border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
                        boxShadow: active ? `0 0 0 3px var(--accent-soft)` : 'none',
                        background: 'var(--panel)', cursor: 'pointer',
                        display: 'flex', flexDirection: 'column', gap: 10,
                        transition: 'all 120ms',
                      }}
                    >
                      <span style={{ width: 28, height: 28, borderRadius: 7, background: active ? 'var(--accent)' : 'var(--bg-2)', color: active ? 'var(--accent-ink)' : 'var(--ink-3)', display: 'grid', placeItems: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
                        {o.letter}
                      </span>
                      <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--ink)' }}>{o.label}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--ink-3)', lineHeight: 1.5 }}>{o.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 1 && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.375rem', fontWeight: 500, margin: '0 0 6px', letterSpacing: '-0.02em', color: 'var(--ink)' }}>
                Describe your {kind}
              </h2>
              <p style={{ color: 'var(--ink-3)', margin: '0 0 16px', fontSize: '0.875rem' }}>
                Studio will draft the definition, ref, domain and SQL. Edit anything after.
              </p>
              <AiField
                entityType="use_case"
                entityId="new"
                entityName="New Use Case"
                fieldName="description"
                fieldLabel="Use Case Description"
                value={prompt}
                onChange={setPrompt}
                multiline
                rows={6}
                placeholder={`e.g. "Weekly activation rate for enterprise plan customers, segmented by cohort"`}
              />
              {/* Suggestion chips */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Try:</span>
                {[
                  'Weekly activation rate by cohort',
                  'Net new revenue per sales rep',
                  'Support response time P50',
                ].map((s) => (
                  <button
                    key={s}
                    onClick={() => setPrompt(s)}
                    style={{
                      fontSize: '0.6875rem', padding: '3px 10px', borderRadius: 999,
                      border: '1px solid var(--line)', color: 'var(--ink-3)',
                      background: 'transparent', cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; (e.currentTarget as HTMLElement).style.color = 'var(--accent)'; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)'; (e.currentTarget as HTMLElement).style.color = 'var(--ink-3)'; }}
                  >
                    {s}
                  </button>
                ))}
              </div>
              {(generating || isLoadingDraft) && (
                <div style={{ marginTop: 14, padding: 12, borderRadius: 10, background: 'var(--accent-soft)', color: 'var(--accent)', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M4 12l2-2" />
                  </svg>
                  {isLoadingDraft ? 'Analyzing…' : 'Drafting definition and checking for duplicates…'}
                </div>
              )}
              {genError && (
                <div style={{ marginTop: 14, padding: 12, borderRadius: 10, background: 'color-mix(in srgb, var(--warning) 10%, transparent)', color: 'var(--warning)', fontSize: '0.8125rem' }}>
                  {genError}
                </div>
              )}
            </div>
          )}

          {step === 2 && draft && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'oklch(0.52 0.14 150)', fontSize: '0.75rem', marginBottom: 8 }}>
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M4 12l2-2" />
                </svg>
                Draft ready — review and edit before saving.
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: 4 }}>{draft.ref}</div>
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Name</div>
                <AiField
                  entityType="use_case"
                  entityId={slug(draftName) || 'new'}
                  entityName={draftName}
                  fieldName="name"
                  fieldLabel="Name"
                  value={draftName}
                  onChange={(v) => { setDraftName(v); setDraft((d) => d ? { ...d, name: v } : d); }}
                  placeholder="Short name (max 5 words)"
                />
              </div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Description</div>
                <AiField
                  entityType="use_case"
                  entityId={slug(draftName) || 'new'}
                  entityName={draftName}
                  fieldName="description"
                  fieldLabel="Description"
                  value={draftDescription}
                  onChange={(v) => { setDraftDescription(v); setDraft((d) => d ? { ...d, description: v } : d); }}
                  multiline
                  rows={3}
                  placeholder="1-2 sentences describing the use case."
                />
              </div>
              {(draft.domain ?? draft.type ?? draft.grain) && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 18 }}>
                  {[
                    ['Domain', draft.domain ?? '—'],
                    ['Type', draft.type ?? '—'],
                    ['Grain', draft.grain ?? '—'],
                    ['Unit', draft.unit ?? '—'],
                  ].map(([k, v]) => (
                    <div key={k} style={{ padding: 10, border: '1px solid var(--line)', borderRadius: 8, background: 'var(--bg-2)' }}>
                      <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k}</div>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 500, marginTop: 2 }}>{v}</div>
                    </div>
                  ))}
                </div>
              )}
              {draft.sql && (
                <>
                  <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>SQL</div>
                  <pre style={{ margin: 0, padding: 14, borderRadius: 10, background: 'var(--bg-2)', border: '1px solid var(--line)', fontSize: '0.75rem', lineHeight: 1.7, color: 'var(--ink-2)', overflow: 'auto', fontFamily: 'var(--font-mono)' }}>
                    {draft.sql}
                  </pre>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '14px 20px', borderTop: '1px solid var(--line-2)', display: 'flex', justifyContent: 'space-between', gap: 8 }}>
          <button
            onClick={() => step === 0 ? onClose() : setStep(step - 1)}
            style={{ height: 32, padding: '0 14px', borderRadius: 7, border: '1px solid var(--line)', background: 'var(--panel)', color: 'var(--ink-2)', fontSize: '0.8125rem', cursor: 'pointer' }}
          >
            {step === 0 ? 'Cancel' : 'Back'}
          </button>
          {step === 0 && (
            <button onClick={() => setStep(1)} style={primaryBtn}>Continue →</button>
          )}
          {step === 1 && (
            <button onClick={() => void generateDraft()} disabled={generating || isLoadingDraft} style={{ ...primaryBtn, opacity: (generating || isLoadingDraft) ? 0.7 : 1 }}>
              ✦ {isLoadingDraft ? 'Analyzing…' : generating ? 'Drafting…' : 'Generate draft'}
            </button>
          )}
          {saveError && step === 2 && (
            <div style={{ marginRight: 'auto', fontSize: '0.75rem', color: 'var(--warning)' }}>{saveError}</div>
          )}
          {step === 2 && draft && (
            <button
              onClick={() => void onSave?.(kind, draft)}
              disabled={saving}
              style={{ ...primaryBtn, opacity: saving ? 0.7 : 1 }}
            >
              {saving ? 'Saving…' : '✓ Save to framework'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const primaryBtn: React.CSSProperties = {
  height: 32, padding: '0 16px', borderRadius: 7,
  background: 'var(--ink)', color: 'var(--bg)',
  fontSize: '0.8125rem', fontWeight: 500,
  border: 'none', cursor: 'pointer',
  display: 'inline-flex', alignItems: 'center', gap: 6,
};
