/**
 * Audit Hash Chain — tamper detection via SHA-256 chaining.
 *
 * Each audit event's hash includes the previous event's hash,
 * creating an immutable chain. If any event is modified or deleted,
 * the chain breaks and verification fails.
 */

import { createHash } from 'node:crypto';
import { getDb } from './sqlite';
import type { AuditEvent } from './audit-repo';

/** Compute SHA-256 hash for an event, chaining to the previous hash. */
export function computeEventHash(event: AuditEvent, prevHash: string): string {
  const payload = `${prevHash}|${event.id}|${event.actor}|${event.entity_type}|${event.entity_id}|${event.action}|${event.diff_json}|${event.created_at}`;
  return createHash('sha256').update(payload).digest('hex');
}

/** Get the hash of the most recent audit event, or empty string if none. */
export function getLastHash(projectId = 'default'): string {
  const db = getDb();
  const row = db.prepare(
    'SELECT hash FROM audit_events WHERE project_id = ? AND hash IS NOT NULL ORDER BY created_at DESC, rowid DESC LIMIT 1',
  ).get(projectId) as { hash: string } | undefined;
  return row?.hash ?? '';
}

/**
 * Compute and store hash for an event, linking it to the chain.
 * Call this right after inserting the event.
 */
export function chainEvent(eventId: string, projectId = 'default'): string {
  const db = getDb();
  const event = db.prepare('SELECT * FROM audit_events WHERE id = ?').get(eventId) as AuditEvent;
  if (!event) throw new Error(`Audit event not found: ${eventId}`);

  // Get the previous hash (excluding the current event)
  const prevRow = db.prepare(
    'SELECT hash FROM audit_events WHERE project_id = ? AND id != ? AND hash IS NOT NULL ORDER BY created_at DESC, rowid DESC LIMIT 1',
  ).get(projectId, eventId) as { hash: string } | undefined;
  const prevHash = prevRow?.hash ?? '';

  const hash = computeEventHash(event, prevHash);
  db.prepare('UPDATE audit_events SET prev_hash = ?, hash = ? WHERE id = ?').run(prevHash, hash, eventId);
  return hash;
}

/**
 * Verify the integrity of the entire audit chain for a project.
 * Returns { valid: true } if chain is intact, or { valid: false, brokenAt } if tampered.
 */
export function verifyChain(projectId = 'default'): { valid: boolean; brokenAt?: string; checked: number } {
  const db = getDb();
  const events = db.prepare(
    'SELECT * FROM audit_events WHERE project_id = ? ORDER BY created_at ASC, rowid ASC',
  ).all(projectId) as (AuditEvent & { prev_hash?: string; hash?: string })[];

  if (events.length === 0) return { valid: true, checked: 0 };

  let prevHash = '';
  for (const event of events) {
    // Skip events that were created before hash chain was enabled
    if (!event.hash) continue;

    const expectedHash = computeEventHash(event, prevHash);
    if (event.hash !== expectedHash) {
      return { valid: false, brokenAt: event.id, checked: events.indexOf(event) + 1 };
    }
    if (event.prev_hash !== prevHash) {
      return { valid: false, brokenAt: event.id, checked: events.indexOf(event) + 1 };
    }
    prevHash = event.hash;
  }

  return { valid: true, checked: events.length };
}
