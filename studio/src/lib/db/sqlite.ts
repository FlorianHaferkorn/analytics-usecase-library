/**
 * SQLite Persistence Layer — Server-side only.
 *
 * Uses better-sqlite3 for zero-cost, embedded persistence.
 * Stores project state, discovery sessions, and theme configs.
 */

import Database from 'better-sqlite3';
import { mkdirSync } from 'node:fs';
import { dirname, isAbsolute, join, resolve } from 'node:path';

const configuredDbPath = process.env.STUDIO_DB_PATH;
const DB_PATH = configuredDbPath
  ? (isAbsolute(configuredDbPath) ? configuredDbPath : resolve(process.cwd(), configuredDbPath))
  : join(process.cwd(), 'data', 'studio.db');

let _db: Database.Database | null = null;

/** Get or create the singleton database connection. */
export function getDb(): Database.Database {
  if (!_db) {
    mkdirSync(dirname(DB_PATH), { recursive: true });

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

    -- PRIMARY KEY is (bracket_id, project_id), not bracket_id alone: a bracket_id
    -- is only unique WITHIN a project, and with the org layer (ADR-0014) now
    -- grouping multiple projects together, two projects legitimately reusing the
    -- same bracket_id (e.g. both authoring "COM-001") must not collide onto one
    -- shared lifecycle row. See migrateBracketLifecyclePrimaryKey() below for the
    -- rebuild path on databases created before this fix.
    CREATE TABLE IF NOT EXISTS bracket_lifecycle (
      bracket_id TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'default',
      status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT,
      approved_by TEXT,
      justification TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (bracket_id, project_id),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE IF NOT EXISTS bracket_review_comments (
      id TEXT PRIMARY KEY,
      bracket_id TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'default',
      actor TEXT NOT NULL DEFAULT 'local-user',
      comment TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS bracket_versions (
      id TEXT PRIMARY KEY,
      bracket_id TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'default',
      label TEXT NOT NULL,
      note TEXT,
      yaml_content TEXT NOT NULL,
      created_by TEXT NOT NULL DEFAULT 'local-user',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS rule_executions (
      id TEXT PRIMARY KEY,
      rule_id TEXT NOT NULL,
      fired INTEGER NOT NULL DEFAULT 0,
      kpi_value REAL NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- AI usage telemetry, one row per LLM step (I-6.6 V3, ADR-0008 §6).
    -- Local-first; no prompt/response content (PII). cost_usd nullable = UNCOMPUTED
    -- (missing != zero); cost_verified flags unverified provider pricing.
    CREATE TABLE IF NOT EXISTS llm_step_events (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      use_case_id TEXT,
      domain TEXT,
      task_role TEXT NOT NULL,
      capability_role TEXT NOT NULL,
      provider TEXT NOT NULL,
      model TEXT NOT NULL,
      input_tokens INTEGER NOT NULL DEFAULT 0,
      output_tokens INTEGER NOT NULL DEFAULT 0,
      cache_read_tokens INTEGER NOT NULL DEFAULT 0,
      cache_write_tokens INTEGER NOT NULL DEFAULT 0,
      reasoning_tokens INTEGER NOT NULL DEFAULT 0,
      latency_ms INTEGER NOT NULL DEFAULT 0,
      ok INTEGER NOT NULL DEFAULT 1,
      error TEXT,
      cost_usd REAL,
      cost_verified INTEGER NOT NULL DEFAULT 0,
      price_table_version TEXT,
      raw_usage_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Customer (L1) / domain (L2) AI-config override layers (I-6.6 V5, ADR-0008 §9).
    -- Only status='approved' rows are served to the resolver; changes flow through the
    -- approval lifecycle (two-person rule + audit). domain_id '' = L1 (tenant-wide).
    CREATE TABLE IF NOT EXISTS ai_config_layers (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL DEFAULT 'default',
      layer TEXT NOT NULL,
      domain_id TEXT NOT NULL DEFAULT '',
      config_json TEXT NOT NULL,
      schema_version TEXT NOT NULL DEFAULT '1.0.0',
      status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT,
      approved_by TEXT,
      justification TEXT,
      effective_hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (project_id, layer, domain_id)
    );

    -- Org layer over local-first (ADR-0014, I-9.2). Additive: organizations/org_members are new
    -- tables, projects.org_id (added via migration below) is nullable -- NULL is the default,
    -- unchanged solo mode, not a degraded fallback. created_at on org_members (not just
    -- organizations) matches this repo's audit doctrine: a membership grant is a
    -- security-relevant event like any other status change.
    CREATE TABLE IF NOT EXISTS organizations (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- business_role_id (ADR-0014 O-3) is a display-only link to
    -- core/organization/org_roles.yaml (e.g. 'finance_bi_lead') -- purely
    -- informational, never consulted by checkAccess/checkOrgAccess. No FK:
    -- the role registry is a governed YAML file, not a DB table, same
    -- pattern as bracket owner_role/steward_role fields.
    CREATE TABLE IF NOT EXISTS org_members (
      user_id TEXT NOT NULL,
      org_id TEXT NOT NULL,
      org_role TEXT NOT NULL DEFAULT 'member',
      business_role_id TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, org_id),
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (org_id) REFERENCES organizations(id)
    );

    -- Wirkungs-Loop refinement proposals (I-8.3/Studio-Approval-Verdrahtung, ADR-0009 par 5).
    -- Proposals are re-derived from the Python core on each compute (bridge.py
    -- attribute command); this table only persists the human decision so a
    -- re-run doesn't lose it. proposal_key = action_code_id + '::' + kpi_id.
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
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- Ensure default project exists
    INSERT OR IGNORE INTO projects (id, name, strategy_anchor)
    VALUES ('default', 'Aurora Group', 'Profitable growth through margin quality, cash resilience & operational excellence');
  `);

  // Column migrations for existing databases (ALTER TABLE ignores if column exists via try-catch)
  const migrations: [string, string][] = [
    ['bracket_review_comments', 'project_id TEXT NOT NULL DEFAULT \'default\''],
    ['bracket_versions', 'project_id TEXT NOT NULL DEFAULT \'default\''],
    // ADR-0014: nullable, NULL = solo/local-first default (not a degraded fallback).
    // ON DELETE SET NULL: deleting an org reverts its projects to solo instead of
    // orphaning or blocking the delete.
    ['projects', 'org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL'],
    // ADR-0014 O-3: display-only link to core/organization/org_roles.yaml.
    ['org_members', 'business_role_id TEXT'],
  ];
  for (const [table, colDef] of migrations) {
    try {
      db.exec(`ALTER TABLE ${table} ADD COLUMN ${colDef}`);
    } catch {
      // Column already exists — safe to ignore
    }
  }

  migrateBracketLifecyclePrimaryKey(db);
}

/**
 * Rebuild bracket_lifecycle onto a composite (bracket_id, project_id) primary
 * key for databases created before this fix (which had bracket_id alone as PK
 * — a bracket_id is only unique within a project, so two projects reusing the
 * same bracket_id would collide onto one shared row). SQLite has no ALTER
 * TABLE for primary keys, hence the create-copy-drop-rename rebuild. Detected
 * via the stored CREATE TABLE SQL so this is a no-op once already migrated
 * (including on every fresh database, whose CREATE TABLE above already
 * declares the composite PK directly).
 */
export function migrateBracketLifecyclePrimaryKey(db: Database.Database) {
  const row = db.prepare(
    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'bracket_lifecycle'",
  ).get() as { sql: string } | undefined;
  if (!row || row.sql.includes('PRIMARY KEY (bracket_id, project_id)')) {
    return;
  }

  // Wrapped in a transaction so a crash between DROP and RENAME can't orphan
  // bracket_lifecycle_new or leave the database without a bracket_lifecycle table.
  db.transaction(() => {
    db.exec(`
      CREATE TABLE bracket_lifecycle_new (
        bracket_id TEXT NOT NULL,
        project_id TEXT NOT NULL DEFAULT 'default',
        status TEXT NOT NULL DEFAULT 'draft',
        submitted_by TEXT,
        approved_by TEXT,
        justification TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (bracket_id, project_id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
      );

      INSERT INTO bracket_lifecycle_new
        (bracket_id, project_id, status, submitted_by, approved_by, justification, created_at, updated_at)
      SELECT
        bracket_id,
        -- Fall back to 'default' both when project_id is NULL and when it
        -- references a project that no longer exists (e.g. a since-deleted
        -- project) — the new FOREIGN KEY below would otherwise reject the
        -- row and abort the whole migration. The old bracket_id-only PK
        -- means at most one row per bracket_id can exist here, so this
        -- fallback can never collide with an existing 'default' row for the
        -- same bracket_id.
        CASE
          WHEN project_id IS NULL OR project_id NOT IN (SELECT id FROM projects) THEN 'default'
          ELSE project_id
        END,
        status, submitted_by, approved_by, justification, created_at, updated_at
      FROM bracket_lifecycle;

      DROP TABLE bracket_lifecycle;
      ALTER TABLE bracket_lifecycle_new RENAME TO bracket_lifecycle;
    `);
  })();
}
