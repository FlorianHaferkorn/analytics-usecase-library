/**
 * User Repository — CRUD for users table.
 *
 * Auto-provisions users on first login via findOrCreateUser().
 */

import { getDb } from './sqlite';
import type { UserRecord } from '@/lib/auth/rbac-types';

function generateUserId(): string {
  return `usr-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

/** Find a user by email, or create one if they don't exist. */
export function findOrCreateUser(email: string, name?: string): UserRecord {
  const db = getDb();
  const existing = db.prepare('SELECT * FROM users WHERE email = ?').get(email) as UserRecord | undefined;
  if (existing) return existing;

  const id = generateUserId();
  const displayName = name ?? email.split('@')[0];
  db.prepare(
    'INSERT INTO users (id, email, name) VALUES (?, ?, ?)',
  ).run(id, email, displayName);

  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as UserRecord;
}

/** Find a user by ID. */
export function findUserById(id: string): UserRecord | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as UserRecord | undefined;
}

/** Find a user by email. */
export function findUserByEmail(email: string): UserRecord | undefined {
  const db = getDb();
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as UserRecord | undefined;
}

/** List all users. */
export function listUsers(): UserRecord[] {
  const db = getDb();
  return db.prepare('SELECT * FROM users ORDER BY created_at DESC').all() as UserRecord[];
}
