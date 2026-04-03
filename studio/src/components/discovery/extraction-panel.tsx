'use client';

import { useRouter } from 'next/navigation';
import { useState, useMemo, useCallback, useEffect } from 'react';

export interface ExtractedElement {
  type: 'anchor' | 'kpi' | 'action';
  id: string;
  name: string;
  details: string;
  source: string;
  sourceContext: string;
}

interface DraftDecision {
  key: string;
  mode: 'create' | 'reuse' | 'merge';
  reusedId?: string;
}

interface DraftResult {
  branch: string;
  file: string;
  total: number;
  scaffold?: {
    id: string;
    file: string;
    title: string;
  };
  scaffoldYaml?: string;
}

interface Props {
  lastResponse: string;
  sourceNames: string[];
}

interface ReviewMatch {
  id: string;
  name: string;
  reason: 'exact-id' | 'exact-name' | 'similar-name';
}

interface ReviewItem {
  type: 'anchor' | 'kpi' | 'action';
  id: string;
  name: string;
  status: 'new' | 'warning' | 'conflict' | 'informational';
  recommendation: 'create' | 'reuse' | 'review' | 'capture';
  message: string;
  matches: ReviewMatch[];
}

interface ReviewSummary {
  total: number;
  newCount: number;
  warningCount: number;
  conflictCount: number;
  informationalCount: number;
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

const REVIEW_COLORS: Record<ReviewItem['status'], string> = {
  new: 'var(--mint)',
  warning: 'var(--gold)',
  conflict: 'var(--danger)',
  informational: 'var(--info)',
};

const REVIEW_LABELS: Record<ReviewItem['status'], string> = {
  new: 'New',
  warning: 'Review',
  conflict: 'Conflict',
  informational: 'Anchor',
};

const MATCH_REASON_LABELS: Record<ReviewMatch['reason'], string> = {
  'exact-id': 'Exact ID',
  'exact-name': 'Exact name',
  'similar-name': 'Similar name',
};

export function ExtractionPanel({ lastResponse, sourceNames }: Props) {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'anchor' | 'kpi' | 'action'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [drafting, setDrafting] = useState(false);
  const [draftResult, setDraftResult] = useState<DraftResult | null>(null);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewSummary, setReviewSummary] = useState<ReviewSummary | null>(null);
  const [reviewMap, setReviewMap] = useState<Record<string, ReviewItem>>({});
  const [reuseMap, setReuseMap] = useState<Record<string, string>>({});
  const [compareSelectionMap, setCompareSelectionMap] = useState<Record<string, string>>({});
  const elements = useMemo(() => parseElements(lastResponse, sourceNames), [lastResponse, sourceNames]);

  const filtered = filter === 'all' ? elements : elements.filter((e) => e.type === filter);

  const reviewKey = useMemo(
    () => elements.map((element) => `${element.type}:${element.id}:${element.name}`).join('|'),
    [elements],
  );

  const runReview = useCallback(async () => {
    if (elements.length === 0) {
      setReviewSummary(null);
      setReviewMap({});
      setReviewError(null);
      return;
    }

    setReviewLoading(true);
    setReviewError(null);
    try {
      const response = await fetch('/api/core/discovery/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ elements }),
      });
      const json = await response.json() as {
        error?: { message?: string };
        summary?: ReviewSummary;
        results?: ReviewItem[];
      };

      if (!response.ok) {
        setReviewError(json.error?.message ?? `HTTP ${response.status}`);
        setReviewSummary(null);
        setReviewMap({});
        return;
      }

      const nextMap: Record<string, ReviewItem> = {};
      for (const item of json.results ?? []) {
        nextMap[`${item.type}:${item.id}:${item.name}`] = item;
      }

      setReviewSummary(json.summary ?? null);
      setReviewMap(nextMap);
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : 'Review failed');
      setReviewSummary(null);
      setReviewMap({});
    } finally {
      setReviewLoading(false);
    }
  }, [elements]);

  useEffect(() => {
    void runReview();
  }, [runReview, reviewKey]);

  const unresolvedConflicts = useMemo(
    () => Object.entries(reviewMap).filter(([key, item]) => item.status === 'conflict' && !reuseMap[key]),
    [reviewMap, reuseMap],
  );

  const hasConflicts = unresolvedConflicts.length > 0;

  const decisions = useMemo<DraftDecision[]>(() => (
    Object.entries(reuseMap).map(([key, reusedId]) => ({
      key,
      mode: reviewMap[key]?.status === 'conflict' ? 'merge' : 'reuse',
      reusedId,
    }))
  ), [reuseMap, reviewMap]);

  const handleCreateDraft = useCallback(async () => {
    if (drafting || elements.length === 0 || hasConflicts) return;
    setDrafting(true);
    setDraftResult(null);
    setDraftError(null);
    try {
      const res = await fetch('/api/core/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ elements, decisions }),
      });
      const json = await res.json() as Record<string, unknown>;
      if (!res.ok) {
        const errMsg = (json.error as Record<string, unknown> | undefined)?.message;
        setDraftError(typeof errMsg === 'string' ? errMsg : `HTTP ${res.status}`);
      } else {
        setDraftResult({
          branch: json.branch as string,
          file: json.file as string,
          total: json.total as number,
          scaffold: json.scaffold as DraftResult['scaffold'],
          scaffoldYaml: json.scaffoldYaml as string | undefined,
        });
      }
    } catch (err) {
      setDraftError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setDrafting(false);
    }
  }, [elements, drafting, hasConflicts, decisions]);

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
        {reviewSummary && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', marginBottom: 'var(--sp-1)' }}>
            <ReviewStat label="New" value={reviewSummary.newCount} color="var(--mint)" />
            <ReviewStat label="Review" value={reviewSummary.warningCount} color="var(--gold)" />
            <ReviewStat label="Conflicts" value={reviewSummary.conflictCount} color="var(--danger)" />
            <ReviewStat label="Anchors" value={reviewSummary.informationalCount} color="var(--info)" />
          </div>
        )}
        {reviewError && (
          <div style={{ marginBottom: 'var(--sp-1)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'color-mix(in srgb, var(--danger) 12%, transparent)', color: 'var(--danger)', fontSize: '0.6875rem' }}>
            {reviewError}
          </div>
        )}
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
              const reviewKey = `${el.type}:${el.id}:${el.name}`;
              const review = reviewMap[reviewKey];
              const reusedId = reuseMap[reviewKey];
              const selectedMatchId = compareSelectionMap[reviewKey] ?? review?.matches[0]?.id ?? null;
              const selectedMatch = review?.matches.find((match) => match.id === selectedMatchId) ?? review?.matches[0] ?? null;
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {review && (
                          <span style={{ fontSize: '0.5625rem', padding: '1px 6px', borderRadius: '9999px', backgroundColor: `color-mix(in srgb, ${REVIEW_COLORS[review.status]} 16%, transparent)`, color: REVIEW_COLORS[review.status], border: `1px solid color-mix(in srgb, ${REVIEW_COLORS[review.status]} 45%, transparent)` }}>
                            {REVIEW_LABELS[review.status]}
                          </span>
                        )}
                        <span style={{ fontSize: '0.625rem', color: 'var(--slate-500)', fontFamily: 'var(--font-mono)' }}>
                          {el.id}
                        </span>
                      </div>
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
                      {review && (
                        <div style={{ marginBottom: 'var(--sp-1)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: `color-mix(in srgb, ${REVIEW_COLORS[review.status]} 8%, transparent)`, border: `1px solid color-mix(in srgb, ${REVIEW_COLORS[review.status]} 24%, transparent)` }}>
                          <p style={{ color: REVIEW_COLORS[review.status], fontWeight: 600, marginBottom: '2px' }}>
                            Recommendation: {review.status === 'conflict' && reusedId ? 'merge' : review.recommendation}
                          </p>
                          <p style={{ color: 'var(--slate-300)', lineHeight: 1.4 }}>{review.message}</p>
                          {review.matches.length > 0 && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                              {review.matches.map((match) => {
                                const isActive = selectedMatchId === match.id;
                                return (
                                  <button
                                    key={`${match.id}-${match.reason}`}
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      setCompareSelectionMap((prev) => ({ ...prev, [reviewKey]: match.id }));
                                    }}
                                    style={{
                                      padding: '4px 8px',
                                      borderRadius: 'var(--radius-sm)',
                                      border: `1px solid ${isActive ? 'var(--info)' : 'var(--slate-700)'}`,
                                      backgroundColor: isActive ? 'color-mix(in srgb, var(--info) 14%, transparent)' : 'transparent',
                                      color: isActive ? 'var(--info)' : 'var(--slate-400)',
                                      fontSize: '0.625rem',
                                      cursor: 'pointer',
                                    }}
                                  >
                                    Compare {match.id}
                                  </button>
                                );
                              })}
                              <button
                                onClick={(event) => {
                                  event.stopPropagation();
                                  setReuseMap((prev) => {
                                    const next = { ...prev };
                                    if (reusedId) delete next[reviewKey];
                                    else if (selectedMatchId) next[reviewKey] = selectedMatchId;
                                    return next;
                                  });
                                }}
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: 'var(--radius-sm)',
                                  border: `1px solid ${reusedId ? 'var(--mint)' : 'var(--slate-600)'}`,
                                  backgroundColor: reusedId ? 'color-mix(in srgb, var(--mint) 12%, transparent)' : 'transparent',
                                  color: reusedId ? 'var(--mint)' : 'var(--slate-300)',
                                  fontSize: '0.625rem',
                                  cursor: 'pointer',
                                }}
                              >
                                {reusedId
                                  ? `${review.status === 'conflict' ? 'Merge' : 'Reuse'} ${reusedId}`
                                  : `${review.status === 'conflict' ? 'Merge into' : 'Reuse'} ${selectedMatchId ?? review.matches[0].id}`}
                              </button>
                              {reusedId && (
                                <button
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    setReuseMap((prev) => {
                                      const next = { ...prev };
                                      delete next[reviewKey];
                                      return next;
                                    });
                                  }}
                                  style={{
                                    padding: '4px 8px',
                                    borderRadius: 'var(--radius-sm)',
                                    border: '1px solid var(--slate-600)',
                                    backgroundColor: 'transparent',
                                    color: 'var(--slate-400)',
                                    fontSize: '0.625rem',
                                    cursor: 'pointer',
                                  }}
                                >
                                  Create new instead
                                </button>
                              )}
                            </div>
                          )}
                          {selectedMatch && (
                            <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                              <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-800)' }}>
                                <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginBottom: '4px', textTransform: 'uppercase' }}>Discovery Draft</p>
                                <p style={{ color: 'var(--slate-200)', fontSize: '0.625rem', fontFamily: 'var(--font-mono)' }}>{el.id}</p>
                                <p style={{ color: 'var(--slate-100)', fontSize: '0.6875rem', fontWeight: 600, marginTop: '3px' }}>{el.name}</p>
                                <p style={{ color: 'var(--slate-400)', fontSize: '0.625rem', marginTop: '6px', lineHeight: 1.4 }}>{el.details || 'No extra draft detail available.'}</p>
                                {el.sourceContext && (
                                  <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginTop: '6px', lineHeight: 1.4 }}>&ldquo;{el.sourceContext}&rdquo;</p>
                                )}
                              </div>
                              <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-800)' }}>
                                <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginBottom: '4px', textTransform: 'uppercase' }}>Registry Candidate</p>
                                <p style={{ color: 'var(--slate-200)', fontSize: '0.625rem', fontFamily: 'var(--font-mono)' }}>{selectedMatch.id}</p>
                                <p style={{ color: 'var(--slate-100)', fontSize: '0.6875rem', fontWeight: 600, marginTop: '3px' }}>{selectedMatch.name}</p>
                                <p style={{ color: 'var(--slate-400)', fontSize: '0.625rem', marginTop: '6px' }}>{MATCH_REASON_LABELS[selectedMatch.reason]}</p>
                                <p style={{ color: 'var(--slate-500)', fontSize: '0.5625rem', marginTop: '6px', lineHeight: 1.4 }}>
                                  Compare semantic overlap before promoting. Exact-ID conflicts should usually merge; name-only overlaps still need manual governance review.
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
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
        <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <div>
              <p style={{ fontSize: '0.6875rem', color: 'var(--slate-300)', fontWeight: 600 }}>
                Review before drafting
              </p>
              <p style={{ fontSize: '0.625rem', color: 'var(--slate-500)' }}>
                {reviewLoading ? 'Checking registry matches...' : hasConflicts ? 'Resolve or merge exact-ID conflicts before drafting.' : 'Draft branch will include reviewed extracted items.'}
              </p>
            </div>
            <button
              onClick={() => void runReview()}
              disabled={reviewLoading}
              style={{
                padding: '6px 8px',
                backgroundColor: 'transparent',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--slate-600)',
                color: reviewLoading ? 'var(--slate-600)' : 'var(--slate-300)',
                fontSize: '0.6875rem',
                cursor: reviewLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {reviewLoading ? 'Review...' : 'Review refresh'}
            </button>
          </div>
          {draftResult && (
            <div style={{ padding: 'var(--sp-1)', backgroundColor: 'color-mix(in srgb, var(--mint) 12%, transparent)', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem', color: 'var(--mint)' }}>
              <p style={{ fontWeight: 600 }}>Branch erstellt ✓</p>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', marginTop: '2px', wordBreak: 'break-all' }}>{draftResult.branch}</p>
              <p style={{ color: 'var(--slate-400)', marginTop: '2px' }}>{draftResult.total} Elemente → {draftResult.file}</p>
              {draftResult.scaffold && (
                <>
                  <p style={{ color: 'var(--slate-400)', marginTop: '2px' }}>
                    Scaffold → {draftResult.scaffold.file}
                  </p>
                  {draftResult.scaffoldYaml && (
                    <button
                      onClick={() => {
                        router.push(`/steering?draftId=${encodeURIComponent(draftResult.scaffold!.id)}&draftYaml=${encodeURIComponent(draftResult.scaffoldYaml!)}`);
                      }}
                      style={{
                        marginTop: '8px',
                        padding: '5px 8px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--mint)',
                        backgroundColor: 'transparent',
                        color: 'var(--mint)',
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Open scaffold in Steering
                    </button>
                  )}
                </>
              )}
            </div>
          )}
          {draftError && (
            <div style={{ padding: 'var(--sp-1)', backgroundColor: 'color-mix(in srgb, var(--danger) 12%, transparent)', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem', color: 'var(--danger)' }}>
              {draftError}
            </div>
          )}
          <button
            onClick={handleCreateDraft}
            disabled={drafting || reviewLoading || hasConflicts}
            style={{
              width: '100%',
              padding: 'var(--sp-1)',
              backgroundColor: drafting || reviewLoading || hasConflicts ? 'var(--slate-700)' : 'var(--mint)',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              color: drafting || reviewLoading || hasConflicts ? 'var(--slate-400)' : 'var(--slate-950)',
              fontWeight: 600,
              fontSize: '0.8125rem',
              cursor: drafting || reviewLoading || hasConflicts ? 'not-allowed' : 'pointer',
            }}
          >
            {drafting ? 'Branch wird erstellt...' : hasConflicts ? 'Conflicts zuerst prüfen' : 'Draft-Branch erstellen'}
          </button>
        </div>
      )}
    </div>
  );
}

function ReviewStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ padding: '6px 4px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)', textAlign: 'center' }}>
      <p style={{ fontSize: '0.75rem', fontWeight: 700, color }}>{value}</p>
      <p style={{ fontSize: '0.5rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
    </div>
  );
}
