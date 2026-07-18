import { getDb } from '@/lib/db/sqlite';

export interface BracketReviewComment {
  id: string;
  bracket_id: string;
  project_id: string;
  actor: string;
  comment: string;
  created_at: string;
}

export interface BracketVersion {
  id: string;
  bracket_id: string;
  project_id: string;
  label: string;
  note: string | null;
  yaml_content: string;
  created_by: string;
  created_at: string;
}

function generateId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

export function getBracketComments(bracketId: string, projectId = 'default'): BracketReviewComment[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM bracket_review_comments WHERE bracket_id = ? AND project_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 25',
  ).all(bracketId, projectId) as BracketReviewComment[];
}

export function addBracketComment(
  bracketId: string,
  actor: string,
  comment: string,
  projectId = 'default',
): BracketReviewComment {
  const db = getDb();
  const id = generateId('cmt');
  db.prepare(
    'INSERT INTO bracket_review_comments (id, bracket_id, project_id, actor, comment) VALUES (?, ?, ?, ?, ?)',
  ).run(id, bracketId, projectId, actor, comment);
  return db.prepare('SELECT * FROM bracket_review_comments WHERE id = ?').get(id) as BracketReviewComment;
}

export function getBracketVersions(bracketId: string, projectId = 'default'): BracketVersion[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM bracket_versions WHERE bracket_id = ? AND project_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 20',
  ).all(bracketId, projectId) as BracketVersion[];
}

/**
 * Fetch a version by its own (globally unique) id. When projectId is given,
 * scopes the lookup so a caller can never receive a row belonging to a
 * different project — matching the scoping convention every other function
 * in this file uses, instead of leaving the check to be repeated by callers.
 */
export function getBracketVersionById(versionId: string, projectId?: string): BracketVersion | null {
  const db = getDb();
  const row = projectId
    ? db.prepare('SELECT * FROM bracket_versions WHERE id = ? AND project_id = ?').get(versionId, projectId)
    : db.prepare('SELECT * FROM bracket_versions WHERE id = ?').get(versionId);
  return (row as BracketVersion | undefined) ?? null;
}

export function createBracketVersion(
  bracketId: string,
  label: string,
  note: string,
  yamlContent: string,
  actor: string,
  projectId = 'default',
): BracketVersion {
  const db = getDb();
  const id = generateId('ver');
  db.prepare(
    'INSERT INTO bracket_versions (id, bracket_id, project_id, label, note, yaml_content, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
  ).run(id, bracketId, projectId, label, note || null, yamlContent, actor);
  return db.prepare('SELECT * FROM bracket_versions WHERE id = ?').get(id) as BracketVersion;
}