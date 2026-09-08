// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Database from 'better-sqlite3';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { emptyDiscovery } from '@/lib/discovery/document';

const h = vi.hoisted(() => ({ db: null as unknown as Database.Database }));
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => h.db }));
import { readDiscovery, writeDiscovery } from '@/lib/db/discovery-repo';
let folder: string;
beforeEach(() => {
  folder = mkdtempSync(join(tmpdir(), 'studio-discovery-test-'));
  h.db = new Database(join(folder, 'test.db'));
  h.db.pragma('foreign_keys=ON');
  h.db.exec(`CREATE TABLE projects (id TEXT PRIMARY KEY); INSERT INTO projects VALUES ('a'), ('b');
    CREATE TABLE discovery_sessions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), messages_json TEXT, sources_json TEXT, extracted_json TEXT, updated_at TEXT);
    CREATE TABLE audit_events (id TEXT PRIMARY KEY, project_id TEXT, actor TEXT, entity_type TEXT, entity_id TEXT, action TEXT, diff_json TEXT, prev_hash TEXT, hash TEXT, created_at TEXT DEFAULT (datetime('now')));`);
});
afterEach(() => { h.db.close(); rmSync(folder, { recursive: true, force: true }); });
describe('Discovery SQLite persistence', () => {
  it('survives closing/reopening SQLite and isolates project evidence', () => {
    const document = { ...emptyDiscovery(), sources: [{ id: 'same-id', name: 'A only', content: 'Private A', type: 'text' as const, addedAt: '2026-09-07T10:00:00Z' }] };
    const saved = writeDiscovery('a', document, null, 'editor@example.com');
    expect(saved?.revision).toHaveLength(64);
    writeDiscovery('b', { ...document, sources: [{ ...document.sources[0], name: 'B only', content: 'Private B' }] }, null, 'editor@example.com');
    h.db.close(); h.db = new Database(join(folder, 'test.db'));
    expect(readDiscovery('a').document.sources[0].content).toBe('Private A');
    expect(readDiscovery('b').document.sources[0].content).toBe('Private B');
    expect(readDiscovery('a').revision).toBe(saved?.revision);
    const audit = h.db.prepare('SELECT actor, diff_json FROM audit_events WHERE project_id=?').get('a') as { actor: string; diff_json: string };
    expect(audit.actor).toBe('editor@example.com'); expect(audit.diff_json).not.toContain('Private A');
  });
  it('rejects stale writes without mutating evidence or creating an audit event', () => {
    const first = writeDiscovery('a', emptyDiscovery(), null, 'editor@example.com')!;
    const second = writeDiscovery('a', { ...emptyDiscovery(), lastResponse: 'A later answer' }, first.revision, 'editor@example.com')!;
    expect(writeDiscovery('a', { ...emptyDiscovery(), lastResponse: 'stale' }, first.revision, 'editor@example.com')).toBeNull();
    expect(readDiscovery('a').revision).toBe(second.revision);
    expect(h.db.prepare('SELECT count(*) AS count FROM audit_events').get()).toEqual({ count: 2 });
  });
  it('refuses malformed persisted evidence and preserves the row', () => {
    writeDiscovery('a', emptyDiscovery(), null, 'editor@example.com');
    h.db.prepare('UPDATE discovery_sessions SET extracted_json=? WHERE project_id=?').run('{bad', 'a');
    expect(() => readDiscovery('a')).toThrow();
    expect(() => writeDiscovery('a', emptyDiscovery(), null, 'editor@example.com')).toThrow();
    expect(h.db.prepare('SELECT extracted_json FROM discovery_sessions WHERE project_id=?').get('a')).toEqual({ extracted_json: '{bad' });
  });
});
