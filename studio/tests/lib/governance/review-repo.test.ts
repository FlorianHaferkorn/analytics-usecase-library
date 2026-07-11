/**
 * Tests for review-repo project_id scoping (Major finding #2 on the
 * bracket_lifecycle composite-PK fix): bracket_review_comments/bracket_versions
 * must not leak across projects that reuse the same bracket_id.
 */

import { describe, it, expect, vi } from 'vitest';
import Database from 'better-sqlite3';

function createTestDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE bracket_review_comments (
      id TEXT PRIMARY KEY,
      bracket_id TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'default',
      actor TEXT NOT NULL DEFAULT 'local-user',
      comment TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE bracket_versions (
      id TEXT PRIMARY KEY,
      bracket_id TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'default',
      label TEXT NOT NULL,
      note TEXT,
      yaml_content TEXT NOT NULL,
      created_by TEXT NOT NULL DEFAULT 'local-user',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
  return d;
}

const testDb = createTestDb();

vi.mock('../../../src/lib/db/sqlite', () => ({
  getDb: () => testDb,
}));

import {
  getBracketComments,
  addBracketComment,
  getBracketVersions,
  createBracketVersion,
  getBracketVersionById,
} from '../../../src/lib/governance/review-repo';

describe('review-repo project scoping', () => {
  it('comments added under one project do not appear when reading another project with the same bracket_id', () => {
    addBracketComment('COM-001', 'user-a@co.com', 'Comment in project A', 'proj-a');
    addBracketComment('COM-001', 'user-b@co.com', 'Comment in project B', 'proj-b');

    const inA = getBracketComments('COM-001', 'proj-a');
    const inB = getBracketComments('COM-001', 'proj-b');

    expect(inA).toHaveLength(1);
    expect(inA[0].comment).toBe('Comment in project A');
    expect(inB).toHaveLength(1);
    expect(inB[0].comment).toBe('Comment in project B');
  });

  it('versions added under one project do not appear when reading another project with the same bracket_id', () => {
    createBracketVersion('COM-002', 'Snapshot A', '', 'yaml: a', 'user-a@co.com', 'proj-a');
    createBracketVersion('COM-002', 'Snapshot B', '', 'yaml: b', 'user-b@co.com', 'proj-b');

    const inA = getBracketVersions('COM-002', 'proj-a');
    const inB = getBracketVersions('COM-002', 'proj-b');

    expect(inA).toHaveLength(1);
    expect(inA[0].label).toBe('Snapshot A');
    expect(inB).toHaveLength(1);
    expect(inB[0].label).toBe('Snapshot B');
  });

  it('defaults to the "default" project when projectId is omitted (backward compatible)', () => {
    addBracketComment('COM-003', 'user@co.com', 'Untagged comment');
    const comments = getBracketComments('COM-003');
    expect(comments).toHaveLength(1);

    const explicitDefault = getBracketComments('COM-003', 'default');
    expect(explicitDefault).toEqual(comments);
  });

  it('getBracketVersionById returns the project_id so callers can cross-check ownership', () => {
    const version = createBracketVersion('COM-004', 'Snapshot', '', 'yaml: x', 'user@co.com', 'proj-a');
    const fetched = getBracketVersionById(version.id);
    expect(fetched?.project_id).toBe('proj-a');
  });
});
