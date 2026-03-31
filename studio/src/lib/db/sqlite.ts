/**
 * SQLite Persistence Layer — Server-side only.
 *
 * Uses better-sqlite3 for zero-cost, embedded persistence.
 * Stores project state, discovery sessions, and theme configs.
 */

import Database from 'better-sqlite3';
import { join } from 'node:path';

const DB_PATH = join(process.cwd(), 'data', 'studio.db');

let _db: Database.Database | null = null;

/** Get or create the singleton database connection. */
export function getDb(): Database.Database {
  if (!_db) {
    const { mkdirSync } = require('node:fs');
    mkdirSync(join(process.cwd(), 'data'), { recursive: true });

    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
    initSchema(_db);
  }
  return _db;
}

function initSchema(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY DEFAULT 'default',
      name TEXT NOT NULL DEFAULT 'Aurora Group',
      strategy_anchor TEXT NOT NULL DEFAULT '',
      theme_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS project_members (
      user_id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'viewer',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, project_id),
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS discovery_sessions (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      messages_json TEXT NOT NULL DEFAULT '[]',
      sources_json TEXT NOT NULL DEFAULT '[]',
      extracted_json TEXT NOT NULL DEFAULT '[]',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS bracket_edits (
      bracket_id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      yaml_content TEXT NOT NULL,
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

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

    CREATE TABLE IF NOT EXISTS notification_rules (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      name TEXT NOT NULL,
      kpi_id TEXT NOT NULL,
      condition TEXT NOT NULL,
      threshold REAL NOT NULL,
      threshold_upper REAL,
      severity TEXT NOT NULL,
      spine_id TEXT,
      enabled INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS bracket_lifecycle (
      bracket_id TEXT PRIMARY KEY,
      status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT,
      approved_by TEXT,
      justification TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS rule_executions (
      id TEXT PRIMARY KEY,
      rule_id TEXT NOT NULL,
      fired INTEGER NOT NULL DEFAULT 0,
      kpi_value REAL NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Ensure default project exists
    INSERT OR IGNORE INTO projects (id, name, strategy_anchor)
    VALUES ('default', 'Aurora Group', 'Profitable growth through margin quality, cash resilience & operational excellence');
  `);
}
