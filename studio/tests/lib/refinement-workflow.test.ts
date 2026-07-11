/**
 * Tests for Refinement Workflow (Wirkungs-Loop proposal review, ADR-0009 §5).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY DEFAULT 'default',
      name TEXT NOT NULL DEFAULT 'Test',
      strategy_anchor TEXT NOT NULL DEFAULT '',
      theme_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT OR IGNORE INTO projects (id) VALUES ('default');

    CREATE TABLE IF NOT EXISTS audit_events (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      actor TEXT NOT NULL DEFAULT 'system',
      entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL,
      action TEXT NOT NULL,
      diff_json TEXT NOT NULL DEFAULT '{}',
      prev_hash TEXT,
      hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS refinement_lifecycle (
      proposal_key TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      action_code_id TEXT NOT NULL,
      kpi_id TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending_review',
      trigger_kind TEXT NOT NULL,
      rel_change REAL NOT NULL,
      rationale TEXT NOT NULL,
      decided_by TEXT,
      justification TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
  return d;
}

const testDb = createTestDb();

vi.mock('../../src/lib/db/sqlite', () => ({
  getDb: () => testDb,
}));

import {
  upsertPendingProposal,
  listRefinements,
  getRefinement,
  decideRefinement,
} from '../../src/lib/governance/refinement-workflow';
import { proposalKey } from '../../src/lib/governance/refinement-types';

const PROPOSAL = {
  actionCodeId: 'C-M2.1',
  kpiId: 'margin.gm.pct',
  triggerKind: 'material_effect' as const,
  relChange: 0.6,
  rationale: 'Materielle Bewegung',
};

describe('refinement-workflow', () => {
  beforeEach(() => {
    testDb.exec('DELETE FROM refinement_lifecycle');
    testDb.exec('DELETE FROM audit_events');
  });

  it('creates a proposal as pending_review on first upsert', () => {
    const record = upsertPendingProposal(PROPOSAL);
    expect(record.status).toBe('pending_review');
    expect(record.rel_change).toBe(0.6);
  });

  it('updates rel_change/rationale on recompute while still pending', () => {
    upsertPendingProposal(PROPOSAL);
    const updated = upsertPendingProposal({ ...PROPOSAL, relChange: 0.9, rationale: 'Bigger move' });
    expect(updated.rel_change).toBe(0.9);
    expect(updated.rationale).toBe('Bigger move');
  });

  it('does not overwrite an already-decided proposal on recompute', () => {
    upsertPendingProposal(PROPOSAL);
    decideRefinement(proposalKey(PROPOSAL.actionCodeId, PROPOSAL.kpiId), 'approve', 'admin@co.com', 'Looks real');
    const recomputed = upsertPendingProposal({ ...PROPOSAL, relChange: 0.9 });
    expect(recomputed.status).toBe('approved');
    expect(recomputed.rel_change).toBe(0.6); // untouched — decision history preserved
  });

  it('approves a pending proposal', () => {
    upsertPendingProposal(PROPOSAL);
    const result = decideRefinement(proposalKey(PROPOSAL.actionCodeId, PROPOSAL.kpiId), 'approve', 'admin@co.com', 'ok');
    expect(result.status).toBe('approved');
    expect(result.decided_by).toBe('admin@co.com');
  });

  it('rejects a pending proposal', () => {
    upsertPendingProposal(PROPOSAL);
    const result = decideRefinement(proposalKey(PROPOSAL.actionCodeId, PROPOSAL.kpiId), 'reject', 'admin@co.com', 'not real');
    expect(result.status).toBe('rejected');
  });

  it('throws deciding an unknown proposal', () => {
    expect(() => decideRefinement('nope::nope', 'approve', 'admin@co.com', '')).toThrow('Unknown refinement proposal');
  });

  it('throws deciding an already-decided proposal', () => {
    upsertPendingProposal(PROPOSAL);
    const key = proposalKey(PROPOSAL.actionCodeId, PROPOSAL.kpiId);
    decideRefinement(key, 'approve', 'admin@co.com', 'ok');
    expect(() => decideRefinement(key, 'reject', 'admin@co.com', 'changed my mind')).toThrow('already approved');
  });

  it('lists all persisted proposals', () => {
    upsertPendingProposal(PROPOSAL);
    upsertPendingProposal({ ...PROPOSAL, kpiId: 'sales.net_sales.amount' });
    expect(listRefinements()).toHaveLength(2);
  });

  it('logs an audit event for each decision', () => {
    upsertPendingProposal(PROPOSAL);
    decideRefinement(proposalKey(PROPOSAL.actionCodeId, PROPOSAL.kpiId), 'approve', 'admin@co.com', 'ok');
    const events = testDb.prepare('SELECT * FROM audit_events WHERE entity_type = ?').all('refinement');
    expect(events.length).toBeGreaterThanOrEqual(1);
  });

  it('getRefinement returns undefined for unknown key', () => {
    expect(getRefinement('nope::nope')).toBeUndefined();
  });
});
