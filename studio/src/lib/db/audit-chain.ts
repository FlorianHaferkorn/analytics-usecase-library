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
 * Gaps a retention run has attested (C-22, M-22.1): resume event id -> hash of the last deleted
 * event before it. The attestation lives in the chained `audit_retention` event itself, so
 * changing it breaks that event's hash like any other edit.
 */
function attestedGaps(events: AuditEvent[]): Map<string, string> {
  const gaps = new Map<string, string>();
  for (const event of events) {
    if (event.entity_type !== 'audit_retention' || event.action !== 'delete') continue;
    try {
      const diff = JSON.parse(event.diff_json) as { after?: { gaps?: unknown } };
      const list = Array.isArray(diff.after?.gaps) ? diff.after.gaps : [];
      for (const gap of list as { resume_event_id?: unknown; expected_prev_hash?: unknown }[]) {
        if (typeof gap?.resume_event_id === 'string' && typeof gap.expected_prev_hash === 'string') {
          gaps.set(gap.resume_event_id, gap.expected_prev_hash);
        }
      }
    } catch {
      // A malformed attestation attests nothing; the chain check below decides.
    }
  }
  return gaps;
}

/**
 * Verify the integrity of the entire audit chain for a project.
 * Returns { valid: true } if chain is intact, or { valid: false, brokenAt } if tampered.
 *
 * A retention run deletes expired events and attests each resulting gap in its own chained
 * event. A gap is accepted only where such an attestation names exactly this resume event and
 * the hash it continues from; deleting any other event is still reported as tampering.
 */
export function verifyChain(projectId = 'default'): { valid: boolean; brokenAt?: string; checked: number; gaps: number } {
  const db = getDb();
  const events = db.prepare(
    'SELECT * FROM audit_events WHERE project_id = ? ORDER BY created_at ASC, rowid ASC',
  ).all(projectId) as (AuditEvent & { prev_hash?: string; hash?: string })[];

  if (events.length === 0) return { valid: true, checked: 0, gaps: 0 };

  const attested = attestedGaps(events);
  let prevHash = '';
  let gaps = 0;
  for (const [index, event] of events.entries()) {
    // Skip events that were created before hash chain was enabled
    if (!event.hash) continue;

    if (event.prev_hash !== prevHash) {
      if (event.prev_hash && attested.get(event.id) === event.prev_hash) {
        prevHash = event.prev_hash;
        gaps += 1;
      } else {
        return { valid: false, brokenAt: event.id, checked: index + 1, gaps };
      }
    }
    const expectedHash = computeEventHash(event, prevHash);
    if (event.hash !== expectedHash) {
      return { valid: false, brokenAt: event.id, checked: index + 1, gaps };
    }
    prevHash = event.hash;
  }

  return { valid: true, checked: events.length, gaps };
}
