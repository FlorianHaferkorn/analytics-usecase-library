/**
 * Route-level RBAC guard tests for /api/ai-config.
 *
 * Verifies that both `approve` and `reopen` require admin role,
 * while `submit` is accessible to any authenticated user.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import Database from 'better-sqlite3';
import type { AiConfigLayer } from '@/lib/ai/config/resolve';

let testDb: Database.Database;
vi.mock('@/lib/db/sqlite', () => ({ getDb: () => testDb }));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: vi.fn() }));

// vi.hoisted ensures the mock fn is initialized before the hoisted vi.mock factory runs.
const { mockRequireAuth } = vi.hoisted(() => ({ mockRequireAuth: vi.fn() }));
vi.mock('@/lib/auth/session', () => ({ requireAuth: mockRequireAuth }));

function freshDb(): Database.Database {
  const d = new Database(':memory:');
  d.exec(`
    CREATE TABLE ai_config_layers (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL DEFAULT 'default', layer TEXT NOT NULL,
      domain_id TEXT NOT NULL DEFAULT '', config_json TEXT NOT NULL,
      schema_version TEXT NOT NULL DEFAULT '1.0.0', status TEXT NOT NULL DEFAULT 'draft',
      submitted_by TEXT, approved_by TEXT, justification TEXT, effective_hash TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (project_id, layer, domain_id)
    );
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY DEFAULT 'default', name TEXT NOT NULL DEFAULT 'Test',
      strategy_anchor TEXT NOT NULL DEFAULT '', theme_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT OR IGNORE INTO projects (id) VALUES ('default');
    CREATE TABLE IF NOT EXISTS project_members (
      user_id TEXT NOT NULL, project_id TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'viewer',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (user_id, project_id),
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (project_id) REFERENCES projects(id)
    );
    INSERT INTO users (id, email, name) VALUES ('admin1', 'admin@co.com', 'Admin');
    INSERT INTO users (id, email, name) VALUES ('editor1', 'editor@co.com', 'Editor');
    INSERT INTO project_members (user_id, project_id, role) VALUES ('admin1', 'default', 'admin');
    INSERT INTO project_members (user_id, project_id, role) VALUES ('editor1', 'default', 'editor');
  `);
  return d;
}

const L1_CONFIG: AiConfigLayer = {
  schema_version: '1.0.0', layer: 'L1',
  providerPolicy: { allowedProviders: ['google', 'openai'] },
};

const ADMIN_SESSION = [{ email: 'admin@co.com', name: 'Admin', id: 'admin1' }, null] as const;
const EDITOR_SESSION = [{ email: 'editor@co.com', name: 'Editor', id: 'editor1' }, null] as const;

function makeRequest(body: object): Request {
  return new Request('http://localhost/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

import { POST } from '@/app/api/ai-config/route';
import {
  upsertConfigLayer,
  transitionConfigLayer,
} from '@/lib/db/ai-config-repo';

beforeEach(() => { testDb = freshDb(); });

describe('POST /api/ai-config — admin-gated operations', () => {
  it('reopen by non-admin returns 403', async () => {
    mockRequireAuth.mockResolvedValue(EDITOR_SESSION);

    upsertConfigLayer({ layer: 'L1', config: L1_CONFIG });
    transitionConfigLayer('default', 'L1', '', 'submit', 'editor@co.com', 'propose');
    transitionConfigLayer('default', 'L1', '', 'approve', 'admin@co.com', 'ok');

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1', justification: 'rollback' }));
    expect(res.status).toBe(403);
  });

  it('approve by non-admin returns 403', async () => {
    mockRequireAuth.mockResolvedValue(EDITOR_SESSION);

    upsertConfigLayer({ layer: 'L1', config: L1_CONFIG });
    transitionConfigLayer('default', 'L1', '', 'submit', 'editor@co.com', 'propose');

    const res = await POST(makeRequest({ op: 'approve', layer: 'L1', justification: 'ok' }));
    expect(res.status).toBe(403);
  });

  it('reopen by admin succeeds (returns approved-layer back to draft)', async () => {
    mockRequireAuth.mockResolvedValue(ADMIN_SESSION);

    upsertConfigLayer({ layer: 'L1', config: L1_CONFIG });
    transitionConfigLayer('default', 'L1', '', 'submit', 'editor@co.com', 'propose');
    transitionConfigLayer('default', 'L1', '', 'approve', 'admin2@co.com', 'ok');

    const res = await POST(makeRequest({ op: 'reopen', layer: 'L1', justification: 'fix needed' }));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.layer.status).toBe('draft');
  });

  it('submit by non-admin is allowed (no admin gate on submit)', async () => {
    mockRequireAuth.mockResolvedValue(EDITOR_SESSION);

    upsertConfigLayer({ layer: 'L1', config: L1_CONFIG });

    const res = await POST(makeRequest({ op: 'submit', layer: 'L1', justification: 'propose' }));
    expect(res.status).toBe(200);
  });
});
