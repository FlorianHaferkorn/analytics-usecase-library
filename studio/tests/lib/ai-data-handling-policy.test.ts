import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { evaluateAiDataHandling, AiDataHandlingViolation, isInternalAiEndpoint } from '@/lib/ai/data-handling-policy';
import { validate } from '@/lib/validation/schema-validator';

const fixturePath = resolve(process.cwd(), '../core/fixtures/neutral/ai-data-handling-policy/data_handling_cases.json');
const mirrorPath = resolve(process.cwd(), '../core/fixtures/neutral/ai-data-handling-policy/MIRROR.json');
const schemaPath = resolve(process.cwd(), '../tooling/generator/schemas/ai_data_handling_policy.schema.json');
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8')) as {
  contract_version: string;
  cases: Array<{ id: string; profile: Record<string, unknown>; context: Record<string, unknown>; allowed: boolean }>;
};
const mirror = JSON.parse(readFileSync(mirrorPath, 'utf8')) as {
  contract_version: string; source_path: string; sha256: string; shared_executable_runtime: boolean;
};
const schema = JSON.parse(readFileSync(schemaPath, 'utf8')) as Record<string, unknown>;
const meridianRoot = process.env.MERIDIAN_ROOT || resolve(process.cwd(), '../../Freelancing');
const meridianFixture = resolve(meridianRoot, mirror.source_path);
const strictParity = process.env.AI_CONTRACT_STRICT_PARITY === '1';

describe('neutral ai-data-handling-policy/1.0.0 mirror', () => {
  it('pins the neutral fixture without mirroring executable runtime', () => {
    expect(fixture.contract_version).toBe('ai-data-handling-policy/1.0.0');
    expect(mirror.contract_version).toBe(fixture.contract_version);
    expect(mirror.shared_executable_runtime).toBe(false);
    expect(fixture.cases.length).toBe(14);
    const digest = createHash('sha256').update(readFileSync(fixturePath)).digest('hex');
    expect(digest).toBe(mirror.sha256);
  });

  it.skipIf(!existsSync(meridianFixture) && !strictParity)('detects drift against the available Meridian source', () => {
    expect(existsSync(meridianFixture)).toBe(true);
    expect(readFileSync(fixturePath).equals(readFileSync(meridianFixture))).toBe(true);
  });

  it.each(fixture.cases)('$id: evaluator returns the shared allow/block result', ({ profile, context, allowed }) => {
    if (allowed) expect(evaluateAiDataHandling(profile, context)).toMatchObject({ decision: 'allow' });
    else expect(() => evaluateAiDataHandling(profile, context)).toThrow(AiDataHandlingViolation);
  });

  it('validates complete approval inputs against the AUL schema', () => {
    const allowed = fixture.cases.find((entry) => entry.id === 'public-external')!;
    expect(validate(schema, { contract_version: fixture.contract_version, profile: allowed.profile, context: allowed.context }).valid).toBe(true);
    const missingEvidence = fixture.cases.find((entry) => entry.id === 'customer-managed-without-evidence')!;
    expect(validate(schema, { contract_version: fixture.contract_version, profile: missingEvidence.profile, context: missingEvidence.context }).valid).toBe(false);
    const training = structuredClone(allowed.profile);
    (training.data_handling as Record<string, unknown>).provider_training_allowed = true;
    expect(validate(schema, { contract_version: fixture.contract_version, profile: training, context: allowed.context }).valid).toBe(false);
  });

  it('does not let a profile waive redaction of non-public external-cloud input', () => {
    const example = fixture.cases.find((entry) => entry.id === 'internal-external-not-redacted')!;
    const profile = structuredClone(example.profile);
    (profile.data_handling as Record<string, unknown>).require_redaction_for_egress = false;
    expect(() => evaluateAiDataHandling(profile, example.context)).toThrow(AiDataHandlingViolation);
  });

  it('does not equate a provider name with an internal endpoint', () => {
    expect(isInternalAiEndpoint('https://10.12.1.9/v1')).toBe(true);
    expect(isInternalAiEndpoint('http://localhost:9000')).toBe(true);
    expect(isInternalAiEndpoint('https://openrouter.ai/api/v1')).toBe(false);
    expect(isInternalAiEndpoint('https://localhost@openrouter.ai')).toBe(false);
  });
});
