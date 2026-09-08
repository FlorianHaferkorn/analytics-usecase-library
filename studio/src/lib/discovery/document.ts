import Ajv from 'ajv';

export interface DiscoverySource { id: string; type: 'file' | 'text'; name: string; content: string; addedAt: string }
export interface DiscoveryMessage { role: 'user' | 'assistant'; content: string }
export interface DiscoveryCandidate {
  type: 'anchor' | 'kpi' | 'action'; id: string; name: string; details: string;
  source: string; sourceContext: string; sourceId: string | null;
  evidenceStatus: 'quote-verified' | 'source-linked' | 'unverified'; status: 'draft';
}
export interface DiscoveryDocument {
  schemaVersion: 1; sources: DiscoverySource[]; messages: DiscoveryMessage[];
  lastResponse: string; candidates: DiscoveryCandidate[];
}
export const emptyDiscovery = (): DiscoveryDocument => ({ schemaVersion: 1, sources: [], messages: [], lastResponse: '', candidates: [] });

export function mergeDiscoveryCandidates(existing: DiscoveryCandidate[], suggested: DiscoveryCandidate[]): DiscoveryCandidate[] {
  const byId = new Map(existing.map((candidate) => [`${candidate.type}:${candidate.id}`, candidate]));
  for (const candidate of suggested) byId.set(`${candidate.type}:${candidate.id}`, candidate);
  return [...byId.values()];
}

export function detachRemovedSources(candidates: DiscoveryCandidate[], sources: DiscoverySource[]): DiscoveryCandidate[] {
  return candidates.map((candidate) => candidate.sourceId && !sources.some((source) => source.id === candidate.sourceId)
    ? { ...candidate, sourceId: null, source: 'Evidence not linked', sourceContext: '', evidenceStatus: 'unverified' }
    : candidate);
}

const string = (maxLength: number, minLength = 0) => ({ type: 'string', minLength, maxLength });
const schema = {
  type: 'object', additionalProperties: false, required: ['schemaVersion', 'sources', 'messages', 'lastResponse', 'candidates'],
  properties: {
    schemaVersion: { const: 1 },
    sources: { type: 'array', maxItems: 50, items: { type: 'object', additionalProperties: false,
      required: ['id', 'type', 'name', 'content', 'addedAt'], properties: {
        id: string(160, 1), type: { enum: ['file', 'text'] }, name: string(500, 1), content: string(10 * 1024 * 1024, 1), addedAt: string(40, 1),
      } } },
    messages: { type: 'array', maxItems: 200, items: { type: 'object', additionalProperties: false,
      required: ['role', 'content'], properties: { role: { enum: ['user', 'assistant'] }, content: string(200000, 1) } } },
    lastResponse: string(200000),
    candidates: { type: 'array', maxItems: 500, items: { type: 'object', additionalProperties: false,
      required: ['type', 'id', 'name', 'details', 'source', 'sourceContext', 'sourceId', 'evidenceStatus', 'status'], properties: {
        type: { enum: ['anchor', 'kpi', 'action'] }, id: { ...string(200, 1), pattern: '^[A-Za-z0-9][A-Za-z0-9_.-]*$' },
        name: string(500, 1), details: string(4000), source: string(500), sourceContext: string(2000),
        sourceId: { anyOf: [string(160, 1), { type: 'null' }] }, evidenceStatus: { enum: ['quote-verified', 'source-linked', 'unverified'] }, status: { const: 'draft' },
      } } },
  },
};
const validate = new Ajv({ allErrors: true }).compile<DiscoveryDocument>(schema);

/** Structural validation is not acceptance of business meaning or registry IDs. */
export function validateDiscovery(value: unknown): { document?: DiscoveryDocument; errors: string[] } {
  if (!validate(value)) return { errors: (validate.errors ?? []).map((error) => `${error.instancePath || '/'} ${error.message}`) };
  const document = value as DiscoveryDocument;
  const errors: string[] = [];
  const ids = new Set<string>();
  for (const source of document.sources) {
    if (ids.has(source.id)) errors.push(`Duplicate source ID: ${source.id}`);
    if (!Number.isFinite(Date.parse(source.addedAt))) errors.push(`Invalid source date: ${source.id}`);
    ids.add(source.id);
  }
  const candidateIds = new Set<string>();
  for (const candidate of document.candidates) {
    const key = `${candidate.type}:${candidate.id}`;
    if (candidateIds.has(key)) errors.push(`Duplicate candidate: ${key}`);
    candidateIds.add(key);
    const source = document.sources.find((entry) => entry.id === candidate.sourceId);
    if (candidate.sourceId && !source) errors.push(`Unknown source ID: ${candidate.sourceId}`);
    if (source && candidate.source !== source.name) errors.push(`Source name does not match: ${key}`);
    if (candidate.evidenceStatus !== 'unverified' && !source) errors.push(`Missing evidence source: ${key}`);
    if (candidate.evidenceStatus === 'quote-verified' && (!candidate.sourceContext || !source?.content.includes(candidate.sourceContext))) errors.push(`Quote not found in source: ${key}`);
  }
  return { document: errors.length ? undefined : document, errors };
}

/** Candidate suggestions only. A source is never inferred from list position. */
export function extractDiscoveryCandidates(text: string, sources: DiscoverySource[]): DiscoveryCandidate[] {
  const candidates: DiscoveryCandidate[] = [];
  const seen = new Set<string>();
  const pattern = /(?:kpi_id|action_id):\s*["']?([A-Za-z0-9][A-Za-z0-9_.-]*)["']?\s*\r?\n\s*name:\s*["']?([^\r\n"']+)|strategy\s+anchor:\s*["']?([^\r\n"']{5,})/gi;
  for (const match of text.matchAll(pattern)) {
    if (candidates.length >= 500) break;
    const type = match[3] ? 'anchor' : /^action_id/i.test(match[0]) ? 'action' : 'kpi';
    const id = match[1] ?? `SA-${candidates.length + 1}`;
    if (seen.has(`${type}:${id}`)) continue;
    seen.add(`${type}:${id}`);
    const sourceMarkers = [...text.matchAll(/(?:^|\n)\s*source:/gi)];
    const blockStart = sourceMarkers.filter((marker) => marker.index! <= match.index!).at(-1)?.index ?? match.index!;
    const blockEnd = sourceMarkers.find((marker) => marker.index! > match.index!)?.index ?? text.length;
    const context = text.slice(blockStart, blockEnd);
    const citedName = /(?:^|\n)\s*source:\s*["']?([^\r\n"']+)/i.exec(context)?.[1].trim();
    const matchingSources = sources.filter((source) => source.name === citedName || source.id === citedName);
    const source = matchingSources.length === 1 ? matchingSources[0] : undefined;
    const quote = /(?:^|\n)\s*quote:\s*["']?([^\r\n"']+)/i.exec(context)?.[1].trim() ?? '';
    const verified = !!quote && !!source?.content.includes(quote);
    candidates.push({ type, id, name: (match[2] ?? match[3]).trim().slice(0, 500), details: match[0].slice(0, 4000),
      source: source?.name ?? 'Evidence not linked', sourceContext: verified ? quote : '', sourceId: source?.id ?? null,
      evidenceStatus: verified ? 'quote-verified' : source ? 'source-linked' : 'unverified', status: 'draft' });
  }
  return candidates;
}
