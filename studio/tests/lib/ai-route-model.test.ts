import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { chooseModel } from '@/lib/ai/config/route-model';
import { L0_DEFAULT, CAPABILITY_MODEL_MAP, PROVIDER_RESIDENCY, type Provider } from '@/lib/ai/config/defaults';
import type { CapabilityRole } from '@/lib/ai/config/resolve';

const ALL = (): ((p: Provider) => boolean) => () => true;
const only = (...present: Provider[]) => (p: Provider) => present.includes(p);

describe('chooseModel (config-driven routing)', () => {
  it('follows preferenceOrder among secret-present providers', () => {
    // L0 preferenceOrder = [anthropic, google, openai]; all present → anthropic wins.
    const c = chooseModel('default', { secretPresent: ALL() });
    expect(c?.provider).toBe('anthropic');
    expect(c?.capabilityRole).toBe('balanced');
    expect(c?.modelId).toBe(CAPABILITY_MODEL_MAP['balanced'].anthropic);
  });

  it('skips providers without a configured secret', () => {
    const c = chooseModel('default', { secretPresent: only('openai') });
    expect(c?.provider).toBe('openai');
    expect(c?.modelId).toBe(CAPABILITY_MODEL_MAP['balanced'].openai);
  });

  it('maps task-roles to the right capability role + model', () => {
    const reason = chooseModel('bracket-synthesis', { secretPresent: ALL() });
    expect(reason?.capabilityRole).toBe('deep-reasoner');
    expect(reason?.modelId).toBe(CAPABILITY_MODEL_MAP['deep-reasoner'].anthropic);

    const doc = chooseModel('documentation', { secretPresent: ALL() });
    expect(doc?.capabilityRole).toBe('fast-cheap');
  });

  it('returns null when no provider has a secret', () => {
    expect(chooseModel('default', { secretPresent: () => false })).toBeNull();
  });

  it('returns null when residency cannot be satisfied by any provider', () => {
    // Tighten L0 to eu-only via an L1 layer; no provider advertises eu-only → no choice.
    const l1 = {
      schema_version: '1.0.0' as const, layer: 'L1' as const,
      providerPolicy: { dataResidency: 'eu-only' as const },
    };
    const c = chooseModel('default', { secretPresent: ALL(), layers: { l0: L0_DEFAULT, l1 } });
    expect(c).toBeNull();
  });

  it('respects an L1 provider ban (intersect tightens, never loosens)', () => {
    const l1 = {
      schema_version: '1.0.0' as const, layer: 'L1' as const,
      providerPolicy: { allowedProviders: ['google', 'openai'] }, // bans anthropic
    };
    const c = chooseModel('default', { secretPresent: ALL(), layers: { l0: L0_DEFAULT, l1 } });
    expect(c?.provider).toBe('google'); // anthropic removed, next in preferenceOrder
  });
});

describe('capability→model map invariants (ADR-0008 §3)', () => {
  it('every capability role is servable by ≥2 providers (no lock-in)', () => {
    for (const role of Object.keys(CAPABILITY_MODEL_MAP) as CapabilityRole[]) {
      const providers = Object.entries(CAPABILITY_MODEL_MAP[role]).filter(([, id]) => id).map(([p]) => p);
      expect(providers.length, `role ${role}`).toBeGreaterThanOrEqual(2);
    }
  });

  it('every known provider has a residency entry', () => {
    for (const p of Object.keys(CAPABILITY_MODEL_MAP['balanced']) as Provider[]) {
      expect(PROVIDER_RESIDENCY[p]).toBeDefined();
    }
  });
});

describe('agnostic invariant (ADR-0008 §9a)', () => {
  it('orchestrator.ts names no concrete model id', () => {
    const src = readFileSync(join(__dirname, '../../src/lib/ai/orchestrator.ts'), 'utf-8');
    expect(src).not.toMatch(/claude-[a-z0-9]/i);
    expect(src).not.toMatch(/gemini-[0-9]/i);
    expect(src).not.toMatch(/gpt-[0-9o]/i);
  });

  it('route-model.ts names no concrete model id (only the L0 map does)', () => {
    const src = readFileSync(join(__dirname, '../../src/lib/ai/config/route-model.ts'), 'utf-8');
    expect(src).not.toMatch(/claude-[a-z0-9]/i);
    expect(src).not.toMatch(/gemini-[0-9]/i);
    expect(src).not.toMatch(/gpt-[0-9o]/i);
  });
});
