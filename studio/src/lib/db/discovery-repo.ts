import { createHash } from 'node:crypto';
import { getDb } from './sqlite';
import { logAuditEvent } from './audit-repo';
import { emptyDiscovery, validateDiscovery, type DiscoveryDocument } from '@/lib/discovery/document';

interface Row { messages_json: string; sources_json: string; extracted_json: string; updated_at: string }
export interface DiscoverySnapshot { document: DiscoveryDocument; revision: string | null; updatedAt: string | null }
const sessionId = (projectId: string) => `workspace:${projectId}`;
const hash = (row: Row) => createHash('sha256').update(JSON.stringify([row.messages_json, row.sources_json, row.extracted_json])).digest('hex');

export function readDiscovery(projectId: string): DiscoverySnapshot {
  const row = getDb().prepare('SELECT messages_json, sources_json, extracted_json, updated_at FROM discovery_sessions WHERE id = ? AND project_id = ?').get(sessionId(projectId), projectId) as Row | undefined;
  if (!row) return { document: emptyDiscovery(), revision: null, updatedAt: null };
  const stored = JSON.parse(row.extracted_json) as { schemaVersion: number; candidates: unknown; lastResponse: unknown };
  const result = validateDiscovery({ schemaVersion: stored.schemaVersion, sources: JSON.parse(row.sources_json), messages: JSON.parse(row.messages_json), candidates: stored.candidates, lastResponse: stored.lastResponse });
  if (!result.document) throw new Error('Stored Discovery draft is invalid. It has not been overwritten.');
  return { document: result.document, revision: hash(row), updatedAt: row.updated_at };
}

export function writeDiscovery(projectId: string, document: DiscoveryDocument, expectedRevision: string | null, actor: string): DiscoverySnapshot | null {
  const validated = validateDiscovery(document);
  if (!validated.document) throw new Error('Invalid Discovery document');
  const db = getDb();
  return db.transaction(() => {
    const current = readDiscovery(projectId);
    if (current.revision !== expectedRevision) return null;
    db.prepare(`INSERT INTO discovery_sessions (id, project_id, messages_json, sources_json, extracted_json, updated_at)
      VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
      ON CONFLICT(id) DO UPDATE SET messages_json=excluded.messages_json, sources_json=excluded.sources_json,
      extracted_json=excluded.extracted_json, updated_at=excluded.updated_at WHERE project_id=excluded.project_id`).run(
      sessionId(projectId), projectId, JSON.stringify(document.messages), JSON.stringify(document.sources),
      JSON.stringify({ schemaVersion: 1, lastResponse: document.lastResponse, candidates: document.candidates }));
    const saved = readDiscovery(projectId);
    logAuditEvent('discovery', sessionId(projectId), current.revision ? 'update' : 'create', {
      before: { revision: current.revision }, after: { revision: saved.revision, sourceCount: document.sources.length, candidateCount: document.candidates.length, status: 'draft' },
    }, projectId, actor);
    return saved;
  })();
}
