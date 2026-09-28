/**
 * C-22: retention of AI egress evidence and AI policy reviews (A-22.1 to A-22.5, A-22.7).
 * Real audit repository and hash chain against an in-memory database with an injected clock.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Database from 'better-sqlite3';

let db: Database.Database;
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => db }));
vi.mock('../../src/lib/db/sqlite', () => ({ getDb: () => db }));

import { chainEvent, verifyChain } from '@/lib/db/audit-chain';
import {
  AI_RETENTION_PROPOSAL, AiRetentionError, approvedRetentionEnd, placeLegalHold, releaseLegalHold,
  resolveAiRetentionPolicy, runAiRetention,
} from '@/lib/db/ai-retention';

const NOW = new Date('2026-09-27T12:00:00Z');
const P = 'project_demo';

function schema() {
  db = new Database(':memory:');
  db.exec(`
    CREATE TABLE projects (id TEXT PRIMARY KEY);
    INSERT INTO projects (id) VALUES ('default'), ('${P}');
    CREATE TABLE audit_events (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL DEFAULT 'default', actor TEXT NOT NULL DEFAULT 'system',
      entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, action TEXT NOT NULL,
      diff_json TEXT NOT NULL DEFAULT '{}', prev_hash TEXT, hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE ai_policy_reviews (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL, revision_hash TEXT NOT NULL, route_id TEXT NOT NULL,
      route_hash TEXT NOT NULL, decision_ref TEXT NOT NULL,
      status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
      submitted_by TEXT NOT NULL, submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
      reviewed_by TEXT, reviewed_at TEXT, rationale TEXT, route_expires_at TEXT
    );
    CREATE TABLE audit_legal_holds (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL, reference TEXT NOT NULL, created_by TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')), released_by TEXT, released_at TEXT
    );
  `);
}

function event(id: string, createdAt: string, entityType = 'ai_egress', entityId = 'route', project = 'default') {
  db.prepare(`INSERT INTO audit_events (id, project_id, actor, entity_type, entity_id, action, diff_json, created_at)
    VALUES (?, ?, 'person@example.com', ?, ?, 'block', '{"payload_sha256":"x"}', ?)`).run(id, project, entityType, entityId, createdAt);
  chainEvent(id, project);
}

function review(id: string, status: string, submittedAt: string, reviewedAt: string | null, routeExpiresAt: string | null) {
  db.prepare(`INSERT INTO ai_policy_reviews (id, project_id, revision_hash, route_id, route_hash, decision_ref, status,
    submitted_by, submitted_at, reviewed_by, reviewed_at, rationale, route_expires_at)
    VALUES (?, ?, 'r', 'route', 'h', 'd', ?, 'author@example.com', ?, ?, ?, 'Reviewed by Jane Doe', ?)`)
    .run(id, P, status, submittedAt, reviewedAt ? 'reviewer@example.com' : null, reviewedAt, routeExpiresAt);
  event(`ev-${id}`, submittedAt, 'ai_policy_review', id, P);
}

function ids(project = 'default'): string[] {
  return (db.prepare('SELECT id FROM audit_events WHERE project_id = ? ORDER BY created_at, rowid').all(project) as { id: string }[]).map((r) => r.id);
}

beforeEach(schema);

describe('AI egress evidence retention (category A)', () => {
  function seed() {
    event('old-1', '2025-01-10 10:00:00');
    event('bracket', '2025-02-01 10:00:00', 'bracket', 'B-1');
    event('old-2', '2025-03-10 10:00:00');
    event('young', '2026-01-10 10:00:00');
  }

  it('dry run reports what is due and changes nothing (A-22.3)', () => {
    seed();
    const before = ids();
    const report = runAiRetention({ now: NOW });
    expect(report.dry_run).toBe(true);
    expect(report.projects.find((p) => p.project_id === 'default')).toMatchObject({ state: 'pruned', delete_ai_egress_events: 2 });
    expect(ids()).toEqual(before);
  });

  it('deletes evidence older than 13 months, keeps younger and non-AI events, chain stays valid (A-22.1, A-22.3)', () => {
    seed();
    const report = runAiRetention({ now: NOW, dryRun: false });
    const remaining = ids();
    expect(remaining.slice(0, 2)).toEqual(['bracket', 'young']);
    expect(remaining).toHaveLength(3); // plus the attesting retention event
    expect(report.projects[0].gaps.map((g) => g.resume_event_id)).toEqual(['bracket', 'young']);
    const check = verifyChain('default');
    expect(check).toMatchObject({ valid: true, gaps: 2 });
  });

  it('still detects tampering and unattested deletion after a run (A-22.1, A-22.2)', () => {
    seed();
    event('later-1', '2026-06-01 10:00:00');
    event('later-2', '2026-07-01 10:00:00');
    runAiRetention({ now: NOW, dryRun: false });
    db.prepare("DELETE FROM audit_events WHERE id = 'later-1'").run();
    expect(verifyChain('default')).toMatchObject({ valid: false, brokenAt: 'later-2' });
  });

  it('detects an edited event that survived the run', () => {
    seed();
    runAiRetention({ now: NOW, dryRun: false });
    db.prepare("UPDATE audit_events SET diff_json = '{}' WHERE id = 'young'").run();
    expect(verifyChain('default').valid).toBe(false);
  });

  it('a legal hold stops the run for the project until released', () => {
    seed();
    const hold = placeLegalHold('default', 'CASE-2026-17', 'dpo@example.com');
    const report = runAiRetention({ now: NOW, dryRun: false });
    expect(report.projects[0].state).toBe('legal_hold');
    expect(ids()).toContain('old-1');
    expect(() => placeLegalHold('default', 'Anfrage von Max Mustermann', 'dpo@example.com')).toThrow(AiRetentionError);
    releaseLegalHold(hold.id, 'dpo@example.com');
    runAiRetention({ now: NOW, dryRun: false });
    expect(ids()).not.toContain('old-1');
    expect(verifyChain('default').valid).toBe(true);
  });

  it('does not prune a project whose chain is already broken', () => {
    seed();
    db.prepare("UPDATE audit_events SET diff_json = '{}' WHERE id = 'young'").run();
    const report = runAiRetention({ now: NOW, dryRun: false });
    expect(report.projects[0].state).toBe('chain_invalid');
    expect(ids()).toContain('old-1');
  });
});

describe('AI policy review retention (categories D, E, F)', () => {
  it('expires stale pending reviews, deletes closed ones after 13 months and approved ones after route year + 3 (A-22.5)', () => {
    // Chronological, as in operation: the chain links each event to the latest earlier one.
    review('approved-legacy', 'approved', '2020-01-10 10:00:00', '2020-01-11 10:00:00', null);
    review('approved-2022', 'approved', '2022-01-10 10:00:00', '2022-01-11 10:00:00', '2022-06-30T00:00:00Z');
    review('approved-2023', 'approved', '2023-01-10 10:00:00', '2023-01-11 10:00:00', '2023-06-30T00:00:00Z');
    review('rejected-old', 'rejected', '2025-05-01 10:00:00', '2025-06-01 10:00:00', '2026-01-01T00:00:00Z');
    review('rejected-young', 'rejected', '2025-10-01 10:00:00', '2025-10-02 10:00:00', '2026-01-01T00:00:00Z');
    review('pending-old', 'pending', '2026-02-01 10:00:00', null, '2027-01-01T00:00:00Z');
    review('pending-young', 'pending', '2026-08-01 10:00:00', null, '2027-01-01T00:00:00Z');

    const report = runAiRetention({ now: NOW, dryRun: false });
    const project = report.projects.find((p) => p.project_id === P)!;
    expect(project).toMatchObject({ state: 'pruned', expire_pending_reviews: 1, delete_reviews: 2, approved_without_route_expiry: 1 });
    const left = Object.fromEntries((db.prepare('SELECT id, status FROM ai_policy_reviews').all() as { id: string; status: string }[])
      .map((r) => [r.id, r.status]));
    expect(left).toEqual({
      'pending-old': 'expired', 'pending-young': 'pending', 'rejected-young': 'rejected',
      'approved-2023': 'approved', 'approved-legacy': 'approved',
    });
    expect(ids(P)).not.toContain('ev-rejected-old');
    expect(ids(P)).not.toContain('ev-approved-2022');
    expect(verifyChain(P).valid).toBe(true);
  });

  it('keeps an approved review until the end of the route year plus three years', () => {
    expect(approvedRetentionEnd('2023-06-30T00:00:00Z', 3)?.toISOString()).toBe('2027-01-01T00:00:00.000Z');
    expect(approvedRetentionEnd(null, 3)).toBeNull();
    expect(approvedRetentionEnd('not a date', 3)).toBeNull();
  });
});

describe('content-free report and attestation (A-22.7)', () => {
  it('names no actor and no free text', () => {
    event('old-1', '2025-01-10 10:00:00');
    review('rejected-old', 'rejected', '2025-05-01 10:00:00', '2025-06-01 10:00:00', null);
    const report = runAiRetention({ now: NOW, dryRun: false });
    const retention = db.prepare("SELECT actor, diff_json FROM audit_events WHERE entity_type = 'audit_retention'").all() as { actor: string; diff_json: string }[];
    expect(retention.length).toBeGreaterThan(0);
    for (const text of [JSON.stringify(report), ...retention.map((r) => r.diff_json)]) {
      expect(text).not.toContain('@');
      expect(text).not.toContain('Jane Doe');
    }
    expect(retention.every((r) => r.actor === 'system')).toBe(true);
  });

  it('marks the periods as an unconfirmed proposal', () => {
    const report = runAiRetention({ now: NOW });
    expect(report.policy).toEqual(AI_RETENTION_PROPOSAL);
    expect(report.policy_status).toBe('proposal_pending_legal_confirmation');
  });
});

describe('policy configuration', () => {
  it('takes whole-number overrides and rejects anything else', () => {
    expect(resolveAiRetentionPolicy({})).toEqual({ policy: { ...AI_RETENTION_PROPOSAL }, overridden: [] });
    expect(resolveAiRetentionPolicy({ STUDIO_AI_RETENTION_EGRESS_MONTHS: '24' })).toEqual({
      policy: { ...AI_RETENTION_PROPOSAL, egressMonths: 24 }, overridden: ['egressMonths'] });
    for (const bad of ['0', '-1', '1.5', 'zwoelf', '121']) {
      expect(() => resolveAiRetentionPolicy({ STUDIO_AI_RETENTION_PENDING_MONTHS: bad })).toThrow(AiRetentionError);
    }
  });
});
