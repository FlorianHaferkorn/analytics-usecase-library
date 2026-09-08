import { describe, expect, it } from 'vitest';
import { emptyDiscovery, extractDiscoveryCandidates, mergeDiscoveryCandidates, detachRemovedSources, validateDiscovery, type DiscoverySource } from '@/lib/discovery/document';

const sources: DiscoverySource[] = [
  { id: 'src-a', name: 'Workshop A', content: 'Net sales requires a governed reference.', type: 'text', addedAt: '2026-09-07T10:00:00Z' },
  { id: 'src-b', name: 'Workshop B', content: 'Cash needs a separate review.', type: 'text', addedAt: '2026-09-07T10:00:00Z' },
];
describe('Discovery draft schema and evidence', () => {
  it('links each candidate to its cited block and verifies exact quotes', () => {
    const text = 'Source: src-a\nQuote: Net sales requires a governed reference.\nkpi_id: sales.net_sales.amount\nname: Net sales\n\nSource: src-b\nQuote: Cash needs a separate review.\nkpi_id: finance.cash.amount\nname: Cash';
    const candidates = extractDiscoveryCandidates(text, sources);
    expect(candidates.map((candidate) => candidate.sourceId)).toEqual(['src-a', 'src-b']);
    expect(candidates.every((candidate) => candidate.status === 'draft' && candidate.evidenceStatus === 'quote-verified')).toBe(true);
    expect(validateDiscovery({ ...emptyDiscovery(), sources, lastResponse: text, candidates }).errors).toEqual([]);
  });
  it('does not invent provenance from the first source or accept an invented quote', () => {
    const unlinked = extractDiscoveryCandidates('kpi_id: sales.net_sales.amount\nname: Net sales', sources)[0];
    expect(unlinked.sourceId).toBeNull(); expect(unlinked.evidenceStatus).toBe('unverified');
    const linked = extractDiscoveryCandidates('Source: src-a\nQuote: Invented\nkpi_id: sales.net_sales.amount\nname: Net sales', sources)[0];
    expect(linked.evidenceStatus).toBe('source-linked'); expect(linked.sourceContext).toBe('');
  });
  it('rejects forged approval, missing source references, forged quotes and duplicate source IDs', () => {
    const candidate = extractDiscoveryCandidates('Source: src-a\nkpi_id: sales.net_sales.amount\nname: Net sales', sources)[0];
    expect(validateDiscovery({ ...emptyDiscovery(), sources, candidates: [{ ...candidate, status: 'approved' }] }).errors.length).toBeGreaterThan(0);
    expect(validateDiscovery({ ...emptyDiscovery(), sources, candidates: [{ ...candidate, sourceId: 'foreign' }] }).errors.join()).toContain('Unknown source');
    expect(validateDiscovery({ ...emptyDiscovery(), sources, candidates: [{ ...candidate, evidenceStatus: 'quote-verified', sourceContext: 'not there' }] }).errors.join()).toContain('Quote not found');
    expect(validateDiscovery({ ...emptyDiscovery(), sources: [sources[0], sources[0]] }).errors.join()).toContain('Duplicate source');
  });
  it('deduplicates references and does not claim valid arbitrary prose as candidates', () => {
    expect(extractDiscoveryCandidates('Please review the evidence.', sources)).toEqual([]);
    expect(extractDiscoveryCandidates('kpi_id: sales.x\nname: Sales\nkpi_id: sales.x\nname: Sales', sources)).toHaveLength(1);
  });
  it('preserves earlier candidates through prose-only replies and invalidates removed-source evidence', () => {
    const candidates = extractDiscoveryCandidates('Source: src-a\nkpi_id: sales.x\nname: Sales', sources);
    expect(mergeDiscoveryCandidates(candidates, [])).toEqual(candidates);
    const detached = detachRemovedSources(candidates, []);
    expect(detached[0].evidenceStatus).toBe('unverified'); expect(detached[0].sourceId).toBeNull();
    expect(detached[0].id).toBe('sales.x');
  });
});
