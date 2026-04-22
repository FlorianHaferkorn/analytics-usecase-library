'use client';

import { useState, useEffect, useCallback } from 'react';

type ElementKind = 'kpi' | 'bracket' | 'action';

interface DraftResult {
  name: string;
  ref: string;
  domain: string;
  type: string;
  grain: string;
  description: string;
  sql?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave?: (kind: ElementKind, draft: DraftResult) => void;
}

const KINDS: Array<{ id: ElementKind; label: string; desc: string; letter: string }> = [
  { id: 'kpi',     letter: 'K', label: 'KPI',       desc: 'A measurable number — count, sum, ratio or model output.' },
  { id: 'bracket', letter: 'B', label: 'Use Case',  desc: 'An analytics use case linking strategy to driver KPIs.' },
  { id: 'action',  letter: 'A', label: 'Action',    desc: 'A triggered action code with KPI conditions and logic.' },
];

function titleCase(s: string) {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}
function slug(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40);
}

export function Wizard({ open, onClose, onSave }: Props) {
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState<ElementKind>('kpi');
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState<DraftResult | null>(null);

  useEffect(() => {
    if (!open) { setStep(0); setKind('kpi'); setPrompt(''); setDraft(null); }
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

  const generateDraft = useCallback(() => {
    setGenerating(true);
    setTimeout(() => {
      const name = prompt ? titleCase(prompt) : (kind === 'kpi' ? 'Qualified Pipeline Velocity' : kind === 'bracket' ? 'Revenue Optimisation' : 'Escalate at Risk Customer');
      setDraft({
        name,
        ref: `${kind === 'kpi' ? 'met' : kind === 'bracket' ? 'uc' : 'ac'}.draft.${slug(prompt || name)}`,
        domain: 'Revenue',
        type: kind === 'kpi' ? 'Ratio' : kind === 'bracket' ? 'Strategic' : 'Intervention',
        grain: 'week',
        description: `Draft definition for ${name}. Studio has pre-filled this from your prompt — review and edit each field before saving.`,
        sql: kind === 'kpi' ? `select\n  week,\n  count(*) / nullif(count(distinct user_id), 0) as value\nfrom {{ ref('fct_events') }}\ngroup by 1;` : undefined,
      });
      setGenerating(false);
      setStep(2);
    }, 850);
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
          <button onClick={onClose} style={{ width: 28, height: 28, display: 'grid', placeItems: 'center', borderRadius: 6, color: 'var(--ink-3)', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '0.875rem' }}>✕</button>
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
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
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
              <div style={{ padding: 14, borderRadius: 10, border: '1px solid var(--line)', background: 'var(--panel)' }}>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={`e.g. "Weekly activation rate for enterprise plan customers, segmented by cohort"`}
                  style={{ width: '100%', minHeight: 100, border: 0, outline: 0, background: 'transparent', fontSize: '0.9375rem', lineHeight: 1.5, resize: 'vertical', color: 'var(--ink)' }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--ink-4)' }}>Try:</span>
                  {['Weekly activation by cohort', 'Net new ARR per rep', 'P50 support response time'].map((s) => (
                    <button key={s} onClick={() => setPrompt(s)} style={{ fontSize: '0.6875rem', padding: '4px 10px', borderRadius: 99, border: '1px solid var(--line)', color: 'var(--ink-3)', background: 'transparent', cursor: 'pointer' }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              {generating && (
                <div style={{ marginTop: 14, padding: 12, borderRadius: 10, background: 'var(--accent-soft)', color: 'var(--accent)', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  ✦ Drafting definition and checking for duplicates…
                </div>
              )}
            </div>
          )}

          {step === 2 && draft && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'oklch(0.52 0.14 150)', fontSize: '0.75rem', marginBottom: 8 }}>
                ✦ Draft ready — review and edit before saving.
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--ink-4)' }}>{draft.ref}</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 500, margin: '4px 0 12px', letterSpacing: '-0.02em', color: 'var(--ink)' }}>{draft.name}</h2>
              <p style={{ color: 'var(--ink-2)', fontSize: '0.875rem', lineHeight: 1.6, marginBottom: 18 }}>{draft.description}</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 20 }}>
                {[['Domain', draft.domain], ['Type', draft.type], ['Grain', draft.grain]].map(([k, v]) => (
                  <div key={k} style={{ padding: 10, border: '1px solid var(--line)', borderRadius: 8, background: 'var(--bg-2)' }}>
                    <div style={{ fontSize: '0.5625rem', color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k}</div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 500, marginTop: 3, color: 'var(--ink)' }}>{v}</div>
                  </div>
                ))}
              </div>
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
            <button onClick={generateDraft} disabled={generating} style={{ ...primaryBtn, opacity: generating ? 0.7 : 1 }}>
              ✦ {generating ? 'Drafting…' : 'Generate draft'}
            </button>
          )}
          {step === 2 && draft && (
            <button onClick={() => { onSave?.(kind, draft); onClose(); }} style={primaryBtn}>
              ✓ Save to framework
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
