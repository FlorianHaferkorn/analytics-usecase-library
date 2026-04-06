import { getDb } from '@/lib/db/sqlite';

export interface BracketReviewComment {
  id: string;
  bracket_id: string;
  actor: string;
  comment: string;
  created_at: string;
}

export interface BracketVersion {
  id: string;
  bracket_id: string;
  label: string;
  note: string | null;
  yaml_content: string;
  created_by: string;
  created_at: string;
}

function generateId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

export function getBracketComments(bracketId: string): BracketReviewComment[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM bracket_review_comments WHERE bracket_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 25',
  ).all(bracketId) as BracketReviewComment[];
}

export function addBracketComment(bracketId: string, actor: string, comment: string): BracketReviewComment {
  const db = getDb();
  const id = generateId('cmt');
  db.prepare(
    'INSERT INTO bracket_review_comments (id, bracket_id, actor, comment) VALUES (?, ?, ?, ?)',
  ).run(id, bracketId, actor, comment);
  return db.prepare('SELECT * FROM bracket_review_comments WHERE id = ?').get(id) as BracketReviewComment;
}

export function getBracketVersions(bracketId: string): BracketVersion[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM bracket_versions WHERE bracket_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 20',
  ).all(bracketId) as BracketVersion[];
}

export function getBracketVersionById(versionId: string): BracketVersion | null {
  const db = getDb();
  return (db.prepare('SELECT * FROM bracket_versions WHERE id = ?').get(versionId) as BracketVersion | undefined) ?? null;
}

export function createBracketVersion(
  bracketId: string,
  label: string,
  note: string,
  yamlContent: string,
  actor: string,
): BracketVersion {
  const db = getDb();
  const id = generateId('ver');
  db.prepare(
    'INSERT INTO bracket_versions (id, bracket_id, label, note, yaml_content, created_by) VALUES (?, ?, ?, ?, ?, ?)',
  ).run(id, bracketId, label, note || null, yamlContent, actor);
  return db.prepare('SELECT * FROM bracket_versions WHERE id = ?').get(id) as BracketVersion;
}