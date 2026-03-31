'use client';

import { useState, useMemo } from 'react';

export interface ExtractedElement {
  type: 'anchor' | 'kpi' | 'action';
  id: string;
  name: string;
  details: string;
  source: string;
  sourceContext: string;
}

interface Props {
  lastResponse: string;
  sourceNames: string[];
}

/** Parse AI response for structured elements with source traceability. */
function parseElements(text: string, sourceNames: string[]): ExtractedElement[] {
  const elements: ExtractedElement[] = [];
  if (!text) return elements;

  const defaultSource = sourceNames.length > 0 ? sourceNames[0] : 'AI Discovery';

  // Match KPI patterns: kpi_id: XXX
  const kpiPattern = /kpi_id:\s*"?([^"\n]+)"?[\s\S]*?name:\s*"?([^"\n]+)"?/gi;
  let match;
  while ((match = kpiPattern.exec(text)) !== null) {
    const context = text.slice(Math.max(0, match.index - 200), match.index + match[0].length + 200);
    const sourceRef = extractSourceRef(context, sourceNames) ?? defaultSource;
    elements.push({
      type: 'kpi',
      id: match[1].trim(),
      name: match[2].trim(),
      details: text.slice(Math.max(0, match.index - 20), match.index + match[0].length + 100).trim(),
      source: sourceRef,
      sourceContext: extractQuote(context),
    });
  }

  // Match Action patterns: action_id: XXX
  const actionPattern = /action_id:\s*"?([^"\n]+)"?[\s\S]*?name:\s*"?([^"\n]+)"?/gi;
  while ((match = actionPattern.exec(text)) !== null) {
    const context = text.slice(Math.max(0, match.index - 200), match.index + match[0].length + 200);
    const sourceRef = extractSourceRef(context, sourceNames) ?? defaultSource;
    elements.push({
      type: 'action',
      id: match[1].trim(),
      name: match[2].trim(),
      details: text.slice(Math.max(0, match.index - 20), match.index + match[0].length + 100).trim(),
      source: sourceRef,
      sourceContext: extractQuote(context),
    });
  }

  // Match Strategy Anchor patterns
  const anchorPattern = /strategy\s*anchor[:\s]*"?([^"\n]{5,})"?/gi;
  while ((match = anchorPattern.exec(text)) !== null) {
    const context = text.slice(Math.max(0, match.index - 200), match.index + match[0].length + 200);
    const sourceRef = extractSourceRef(context, sourceNames) ?? defaultSource;
    elements.push({
      type: 'anchor',
      id: `SA-${elements.length + 1}`,
      name: match[1].trim(),
      details: '',
      source: sourceRef,
      sourceContext: extractQuote(context),
    });
  }

  return elements;
}

/** Try to find a source reference near the matched element. */
function extractSourceRef(context: string, sourceNames: string[]): string | null {
  // Look for "Source: filename" or "from filename" patterns
  const sourcePattern = /(?:source|from|reference|cited in|see|page|paragraph)[:\s]+["']?([^"'\n,]+)/i;
  const sourceMatch = sourcePattern.exec(context);
  if (sourceMatch) return sourceMatch[1].trim();

  // Check if any source name is mentioned nearby
  for (const name of sourceNames) {
    if (context.toLowerCase().includes(name.toLowerCase())) return name;
  }

  return null;
}

/** Extract a quoted passage from context. */
function extractQuote(context: string): string {
  const quoteMatch = /"([^"]{10,200})"/.exec(context);
  if (quoteMatch) return quoteMatch[1];
  // Fallback: take the first sentence-ish chunk
  const firstSentence = context.match(/[A-Z][^.!?]*[.!?]/);
  return firstSentence ? firstSentence[0].slice(0, 150) : '';
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

export function ExtractionPanel({ lastResponse, sourceNames }: Props) {
  const [filter, setFilter] = useState<'all' | 'anchor' | 'kpi' | 'action'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const elements = useMemo(() => parseElements(lastResponse, sourceNames), [lastResponse, sourceNames]);

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
            {filtered.map((el, i) => {
              const key = `${el.id}-${i}`;
              const isExpanded = expandedId === key;
              return (
                <div key={key}>
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : key)}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: 'var(--sp-1)',
                      backgroundColor: 'var(--slate-900)',
                      borderRadius: 'var(--radius-md)',
                      borderLeft: `3px solid ${TYPE_COLORS[el.type]}`,
                      border: 'none',
                      borderLeftWidth: '3px',
                      borderLeftStyle: 'solid',
                      borderLeftColor: TYPE_COLORS[el.type],
                      cursor: 'pointer',
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
                    <p style={{ fontSize: '0.5625rem', color: 'var(--slate-500)', marginTop: '2px' }}>
                      {el.source}
                    </p>
                  </button>

                  {isExpanded && (
                    <div style={{ marginTop: '4px', padding: 'var(--sp-1)', backgroundColor: 'var(--slate-950)', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem' }}>
                      {el.sourceContext && (
                        <div style={{ marginBottom: 'var(--sp-1)' }}>
                          <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginBottom: '2px' }}>Source Quote:</p>
                          <p style={{ color: 'var(--slate-300)', fontStyle: 'italic', lineHeight: 1.4 }}>
                            &ldquo;{el.sourceContext}&rdquo;
                          </p>
                        </div>
                      )}
                      <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginBottom: '2px' }}>Traced to:</p>
                      <p style={{ color: 'var(--info)', fontSize: '0.6875rem' }}>{el.source}</p>
                    </div>
                  )}
                </div>
              );
            })}
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
