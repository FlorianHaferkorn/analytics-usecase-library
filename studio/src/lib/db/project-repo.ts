/**
 * Project Repository — CRUD operations for project state.
 */

import { getDb } from './sqlite';

export interface ProjectRow {
  id: string;
  name: string;
  strategy_anchor: string;
  theme_json: string;
  created_at: string;
  updated_at: string;
}

export function listProjects(): ProjectRow[] {
  const db = getDb();
  return db.prepare('SELECT * FROM projects ORDER BY updated_at DESC').all() as ProjectRow[];
}

export function getProject(id = 'default'): ProjectRow | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM projects WHERE id = ?').get(id) as ProjectRow | undefined;
}

export function createProject(name: string, strategyAnchor: string): ProjectRow {
  const db = getDb();
  const id = `proj-${Date.now().toString(36)}`;
  db.prepare(`
    INSERT INTO projects (id, name, strategy_anchor, theme_json)
    VALUES (?, ?, ?, '{}')
  `).run(id, name, strategyAnchor);
  return getProject(id)!;
}

export function deleteProject(id: string): boolean {
  if (id === 'default') return false;
  const db = getDb();
  db.prepare('DELETE FROM bracket_edits WHERE project_id = ?').run(id);
  db.prepare('DELETE FROM discovery_sessions WHERE project_id = ?').run(id);
  const result = db.prepare('DELETE FROM projects WHERE id = ?').run(id);
  return result.changes > 0;
}

export function updateProject(id: string, updates: Partial<Pick<ProjectRow, 'name' | 'strategy_anchor' | 'theme_json'>>) {
  const db = getDb();
  const fields: string[] = [];
  const values: unknown[] = [];

  if (updates.name !== undefined) { fields.push('name = ?'); values.push(updates.name); }
  if (updates.strategy_anchor !== undefined) { fields.push('strategy_anchor = ?'); values.push(updates.strategy_anchor); }
  if (updates.theme_json !== undefined) { fields.push('theme_json = ?'); values.push(updates.theme_json); }

  if (fields.length === 0) return;

  fields.push("updated_at = datetime('now')");
  values.push(id);

  db.prepare(`UPDATE projects SET ${fields.join(', ')} WHERE id = ?`).run(...values);
}

/** Convenience: persist a ThemeConfig to the project's theme_json column. */
export function saveTheme(projectId: string, theme: Record<string, unknown>) {
  updateProject(projectId, { theme_json: JSON.stringify(theme) });
}

/** Convenience: load a parsed ThemeConfig from the project's theme_json column. */
export function loadTheme(projectId: string): Record<string, unknown> | null {
  const project = getProject(projectId);
  if (!project?.theme_json) return null;
  try {
    return JSON.parse(project.theme_json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export interface BracketEditRow {
  bracket_id: string;
  project_id: string;
  yaml_content: string;
  updated_at: string;
}

export function getBracketEdit(bracketId: string, projectId = 'default'): BracketEditRow | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM bracket_edits WHERE bracket_id = ? AND project_id = ?').get(bracketId, projectId) as BracketEditRow | undefined;
}

export function saveBracketEdit(bracketId: string, yamlContent: string, projectId = 'default') {
  const db = getDb();
  db.prepare(`
    INSERT INTO bracket_edits (bracket_id, project_id, yaml_content, updated_at)
    VALUES (?, ?, ?, datetime('now'))
    ON CONFLICT(bracket_id) DO UPDATE SET yaml_content = excluded.yaml_content, updated_at = datetime('now')
  `).run(bracketId, projectId, yamlContent);
}

export function getAllBracketEdits(projectId = 'default'): BracketEditRow[] {
  const db = getDb();
  return db.prepare('SELECT * FROM bracket_edits WHERE project_id = ?').all(projectId) as BracketEditRow[];
}

export interface DiscoverySessionRow {
  id: string;
  project_id: string;
  messages_json: string;
  sources_json: string;
  extracted_json: string;
  created_at: string;
  updated_at: string;
}

export function getDiscoverySession(id: string): DiscoverySessionRow | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM discovery_sessions WHERE id = ?').get(id) as DiscoverySessionRow | undefined;
}

export function saveDiscoverySession(session: Pick<DiscoverySessionRow, 'id' | 'messages_json' | 'sources_json' | 'extracted_json'>) {
  const db = getDb();
  db.prepare(`
    INSERT INTO discovery_sessions (id, messages_json, sources_json, extracted_json, updated_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    ON CONFLICT(id) DO UPDATE SET
      messages_json = excluded.messages_json,
      sources_json = excluded.sources_json,
      extracted_json = excluded.extracted_json,
      updated_at = datetime('now')
  `).run(session.id, session.messages_json, session.sources_json, session.extracted_json);
}

export function listDiscoverySessions(projectId = 'default'): DiscoverySessionRow[] {
  const db = getDb();
  return db.prepare('SELECT * FROM discovery_sessions WHERE project_id = ? ORDER BY updated_at DESC').all(projectId) as DiscoverySessionRow[];
}
