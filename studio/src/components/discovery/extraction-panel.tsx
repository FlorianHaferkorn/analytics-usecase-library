'use client';

import { useState, useMemo } from 'react';

interface ExtractedElement {
  type: 'anchor' | 'kpi' | 'action';
  id: string;
  name: string;
  details: string;
  source: string;
}

interface Props {
  lastResponse: string;
}

/** Parse AI response for structured elements. */
function parseElements(text: string): ExtractedElement[] {
  const elements: ExtractedElement[] = [];
  if (!text) return elements;

  // Match KPI patterns: kpi_id: XXX
  const kpiPattern = /kpi_id:\s*"?([^"\n]+)"?[\s\S]*?name:\s*"?([^"\n]+)"?/gi;
  let match;
  while ((match = kpiPattern.exec(text)) !== null) {
    elements.push({
      type: 'kpi',
      id: match[1].trim(),
      name: match[2].trim(),
      details: text.slice(Math.max(0, match.index - 20), match.index + match[0].length + 100).trim(),
      source: 'AI Discovery',
    });
  }

  // Match Action patterns: action_id: XXX
  const actionPattern = /action_id:\s*"?([^"\n]+)"?[\s\S]*?name:\s*"?([^"\n]+)"?/gi;
  while ((match = actionPattern.exec(text)) !== null) {
    elements.push({
      type: 'action',
      id: match[1].trim(),
      name: match[2].trim(),
      details: text.slice(Math.max(0, match.index - 20), match.index + match[0].length + 100).trim(),
      source: 'AI Discovery',
    });
  }

  // Match Strategy Anchor patterns
  const anchorPattern = /strategy\s*anchor[:\s]*"?([^"\n]{5,})"?/gi;
  while ((match = anchorPattern.exec(text)) !== null) {
    elements.push({
      type: 'anchor',
      id: `SA-${elements.length + 1}`,
      name: match[1].trim(),
      details: '',
      source: 'AI Discovery',
    });
  }

  return elements;
}

const TYPE_COLORS: Record<string, string> = {
  anchor: 'var(--slate-400)',
  kpi: 'var(--mint)',
  action: 'var(--gold)',
};

const TYPE_LABELS: Record<string, string> = {
  anchor: 'Strategy Anchor',
  kpi: 'KPI',
  action: 'Action Code',
};

export function ExtractionPanel({ lastResponse }: Props) {
  const [filter, setFilter] = useState<'all' | 'anchor' | 'kpi' | 'action'>('all');
  const elements = useMemo(() => parseElements(lastResponse), [lastResponse]);

  const filtered = filter === 'all' ? elements : elements.filter((e) => e.type === filter);

  return (
    <div
      style={{
        width: '280px',
        flexShrink: 0,
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: '4px' }}>
          Extracted Elements
        </h3>
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {(['all', 'anchor', 'kpi', 'action'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '2px 8px',
                fontSize: '0.625rem',
                borderRadius: '9999px',
                border: `1px solid ${filter === f ? 'var(--mint)' : 'var(--slate-600)'}`,
                backgroundColor: filter === f ? 'var(--slate-700)' : 'transparent',
                color: filter === f ? 'var(--slate-100)' : 'var(--slate-400)',
                cursor: 'pointer',
              }}
            >
              {f === 'all' ? `All (${elements.length})` : `${TYPE_LABELS[f]}s`}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 'var(--sp-1-5)' }}>
        {filtered.length === 0 ? (
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)', textAlign: 'center', padding: 'var(--sp-3)' }}>
            {elements.length === 0
              ? 'Strategy anchors, KPIs, and action codes will appear here after discovery.'
              : 'No elements match the current filter.'}
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
            {filtered.map((el, i) => (
              <div
                key={`${el.id}-${i}`}
                style={{
                  padding: 'var(--sp-1)',
                  backgroundColor: 'var(--slate-900)',
                  borderRadius: 'var(--radius-md)',
                  borderLeft: `3px solid ${TYPE_COLORS[el.type]}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <span style={{ fontSize: '0.625rem', color: TYPE_COLORS[el.type], fontWeight: 600, textTransform: 'uppercase' }}>
                    {TYPE_LABELS[el.type]}
                  </span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--slate-500)', fontFamily: 'var(--font-mono)' }}>
                    {el.id}
                  </span>
                </div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--slate-100)', fontWeight: 500 }}>
                  {el.name}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {elements.length > 0 && (
        <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)' }}>
          <button
            style={{
              width: '100%',
              padding: 'var(--sp-1)',
              backgroundColor: 'var(--mint)',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              color: 'var(--slate-950)',
              fontWeight: 600,
              fontSize: '0.8125rem',
              cursor: 'pointer',
            }}
          >
            Accept & Push to Registry
          </button>
        </div>
      )}
    </div>
  );
}
