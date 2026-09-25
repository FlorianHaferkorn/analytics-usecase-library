import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it, vi } from 'vitest';

const audit = vi.hoisted(() => vi.fn((entityType, entityId, action, diff, projectId, actor) => ({
  id: 'aud-test', entity_type: entityType, entity_id: entityId, action,
  diff_json: JSON.stringify(diff), project_id: projectId, actor, created_at: '2026-09-25T00:00:00Z',
})));
vi.mock('@/lib/db/audit-repo', () => ({ logAuditEvent: audit }));

import { buildAiEgressEvidence, canonicalPayload, persistAiEgressEvidence } from '@/lib/ai/egress-preflight';

const fixturePath = resolve(process.cwd(), '../core/fixtures/neutral/ai-egress-preflight/egress_preflight_cases.json');
const mirrorPath = resolve(process.cwd(), '../core/fixtures/neutral/ai-egress-preflight/MIRROR.json');
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8')) as {
  contract_version: string;
  cases: Array<{ id: string; profile: Record<string, unknown>; context: Record<string, unknown>; payload: unknown; allowed: boolean; rule_ids: string[]; payload_sha256: string }>;
};
const mirror = JSON.parse(readFileSync(mirrorPath, 'utf8')) as { source_path: string; sha256: string; shared_executable_runtime: boolean };

describe('neutral final-payload preflight', () => {
  it('pins the byte-identical neutral fixture without sharing runtime code', () => {
    expect(fixture.cases).toHaveLength(9);
    expect(mirror.shared_executable_runtime).toBe(false);
    expect(createHash('sha256').update(readFileSync(fixturePath)).digest('hex')).toBe(mirror.sha256);
    const source = resolve(process.env.MERIDIAN_ROOT || resolve(process.cwd(), '../../Freelancing'), mirror.source_path);
    if (existsSync(source)) expect(readFileSync(source).equals(readFileSync(fixturePath))).toBe(true);
  });

  it.each(fixture.cases)('$id: returns the shared allow/block and rule ids', (example) => {
    const evidence = buildAiEgressEvidence({
      profile: example.profile, context: example.context, payload: example.payload,
      approvalGranted: true, now: () => new Date('2026-09-25T00:00:00Z'),
    });
    expect(evidence.contract_version).toBe(fixture.contract_version);
    expect(evidence.decision).toBe(example.allowed ? 'allow' : 'block');
    expect(evidence.rule_ids).toEqual(example.rule_ids);
    expect(evidence.payload_sha256).toBe(example.payload_sha256);
    expect(evidence).not.toHaveProperty('payload');
  });

  it('hashes canonical key ordering identically', () => {
    expect(canonicalPayload({ b: 2, a: { d: 4, c: 3 } })).toBe(canonicalPayload({ a: { c: 3, d: 4 }, b: 2 }));
  });

  it('persists only evidence through the project audit hash-chain owner', () => {
    const example = fixture.cases[1];
    const evidence = buildAiEgressEvidence({
      profile: example.profile, context: example.context, payload: example.payload,
      approvalGranted: true,
    });
    const event = persistAiEgressEvidence(evidence, 'p1', 'editor@example.com');
    expect(event.id).toBe('aud-test');
    expect(audit).toHaveBeenCalledWith('ai_egress', evidence.event_id, 'block', expect.objectContaining({ after: evidence }), 'p1', 'editor@example.com');
    expect(audit.mock.calls[0][3]).not.toHaveProperty('payload');
  });
});
