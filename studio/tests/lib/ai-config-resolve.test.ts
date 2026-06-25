import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  resolveAiConfig,
  MERGE_SPEC,
  AiConfigError,
  type AiConfigLayer,
} from '@/lib/ai/config/resolve';

const L0: AiConfigLayer = {
  schema_version: '1.0.0',
  layer: 'L0',
  routing: {
    roles: [
      { taskRole: 'kpi-draft', capabilityRole: 'fast-cheap', minCapabilityTier: 0 },
      { taskRole: 'bracket-synthesis', capabilityRole: 'deep-reasoner', minCapabilityTier: 1 },
    ],
  },
  tokenPolicy: { maxOutputTokens: 4096, maxContextTokens: 200000, temperatureDefault: 0.2 },
  providerPolicy: {
    allowedProviders: ['anthropic', 'google', 'openai'],
    preferenceOrder: ['anthropic', 'google', 'openai'],
    dataResidency: 'any',
  },
  eval: { thresholds: { value: 0.9 }, requireHumanReview: false },
  telemetry: { sampleRate: 1, redactPII: true },
  roi: { attributionMethod: 'before_after', weighting: { time: 1 } },
};

const resolve = (l1?: AiConfigLayer, l2?: AiConfigLayer, taskRole = 'kpi-draft') =>
  resolveAiConfig({ l0: L0, l1, l2 }, { taskRole });

describe('resolveAiConfig — L0 only', () => {
  it('returns L0 values when no overrides', () => {
    const e = resolve();
    expect(e.capabilityRole).toBe('fast-cheap');
    expect(e.tokenPolicy.maxOutputTokens).toBe(4096);
    expect(e.providerPolicy.allowedProviders).toEqual(['anthropic', 'google', 'openai']);
    expect(e.eval.requireHumanReview).toBe(false);
  });
});

describe('merge kinds', () => {
  it('override: most specific layer wins (L2 > L1 > L0)', () => {
    const l1: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', tokenPolicy: { temperatureDefault: 0.5 } };
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', tokenPolicy: { temperatureDefault: 0.7 } };
    expect(resolve(l1).tokenPolicy.temperatureDefault).toBe(0.5);
    expect(resolve(l1, l2).tokenPolicy.temperatureDefault).toBe(0.7);
  });

  it('override capabilityRole per role', () => {
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', routing: { roles: [{ taskRole: 'kpi-draft', capabilityRole: 'balanced' }] } };
    expect(resolve(undefined, l2).capabilityRole).toBe('balanced');
  });

  it('clamp-min: maxOutputTokens takes the smaller (tighter ceiling)', () => {
    const tighter: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', tokenPolicy: { maxOutputTokens: 1024 } };
    const looser: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', tokenPolicy: { maxOutputTokens: 8192 } };
    expect(resolve(tighter).tokenPolicy.maxOutputTokens).toBe(1024);
    expect(resolve(looser).tokenPolicy.maxOutputTokens).toBe(4096); // can't loosen past L0
  });

  it('clamp-max: minCapabilityTier takes the larger (stronger requirement)', () => {
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', routing: { roles: [{ taskRole: 'kpi-draft', capabilityRole: 'fast-cheap', minCapabilityTier: 2 }] } };
    expect(resolve(undefined, l2).minCapabilityTier).toBe(2);
  });

  it('intersect: allowedProviders narrows downward, never adds', () => {
    const l1: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', providerPolicy: { allowedProviders: ['anthropic', 'google'] } };
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', providerPolicy: { allowedProviders: ['anthropic', 'azure'] } };
    expect(resolve(l1).providerPolicy.allowedProviders).toEqual(['anthropic', 'google']);
    expect(resolve(l1, l2).providerPolicy.allowedProviders).toEqual(['anthropic']); // azure not in L0/L1
  });

  it('or: requireHumanReview / redactPII are sticky-true', () => {
    const l1: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', eval: { requireHumanReview: true } };
    expect(resolve(l1).eval.requireHumanReview).toBe(true);
    expect(resolve().telemetry.redactPII).toBe(true);
  });

  it('clamp-strict: residency tightens; conflicting specifics throw', () => {
    const eu: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', providerPolicy: { dataResidency: 'eu-only' } };
    expect(resolve(eu).providerPolicy.dataResidency).toBe('eu-only');
    const us: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', providerPolicy: { dataResidency: 'us-only' } };
    expect(() => resolve(eu, us)).toThrow(AiConfigError);
  });

  it('clamp-max-per-key: eval thresholds take the max per key, union of keys', () => {
    const l2: AiConfigLayer = { schema_version: '1.0.0', layer: 'L2', eval: { thresholds: { value: 0.95, extra: 0.5 } } };
    expect(resolve(undefined, l2).eval.thresholds).toEqual({ value: 0.95, extra: 0.5 });
  });
});

describe('safety invariants (customer can only tighten L0)', () => {
  const overrides: Array<Partial<AiConfigLayer['tokenPolicy']> & { providers?: string[] }> = [
    { maxOutputTokens: 1, providers: ['anthropic'] },
    { maxOutputTokens: 99999, providers: ['google', 'openai'] },
    { maxContextTokens: 50, providers: ['anthropic', 'google', 'openai'] },
  ];
  it('effective ceilings never exceed L0; providers always a subset of L0', () => {
    for (const o of overrides) {
      const l1: AiConfigLayer = {
        schema_version: '1.0.0', layer: 'L1',
        tokenPolicy: { maxOutputTokens: o.maxOutputTokens, maxContextTokens: o.maxContextTokens },
        providerPolicy: o.providers ? { allowedProviders: o.providers } : undefined,
      };
      const e = resolve(l1);
      expect(e.tokenPolicy.maxOutputTokens).toBeLessThanOrEqual(L0.tokenPolicy!.maxOutputTokens!);
      expect(e.tokenPolicy.maxContextTokens).toBeLessThanOrEqual(L0.tokenPolicy!.maxContextTokens!);
      for (const p of e.providerPolicy.allowedProviders) {
        expect(L0.providerPolicy!.allowedProviders).toContain(p);
      }
    }
  });
});

describe('errors', () => {
  it('throws when the task-role is undefined in all layers', () => {
    expect(() => resolve(undefined, undefined, 'nope')).toThrow(AiConfigError);
  });
  it('throws when the provider intersection is empty', () => {
    const l1: AiConfigLayer = { schema_version: '1.0.0', layer: 'L1', providerPolicy: { allowedProviders: ['azure'] } };
    expect(() => resolve(l1)).toThrow(/empty/);
  });
  it('throws when L0 is incomplete', () => {
    const { tokenPolicy, ...incompleteL0 } = L0;
    void tokenPolicy;
    expect(() => resolveAiConfig({ l0: incompleteL0 as AiConfigLayer }, { taskRole: 'kpi-draft' })).toThrow(/incomplete/);
  });
});

describe('schema ↔ MERGE_SPEC parity', () => {
  it('every x-merge in ai_config.schema.json matches MERGE_SPEC', () => {
    const schemaPath = join(process.cwd(), '..', 'tooling', 'generator', 'schemas', 'ai_config.schema.json');
    const schema = JSON.parse(readFileSync(schemaPath, 'utf-8'));
    const found: Record<string, string> = {};
    const walk = (node: any, path: string) => {
      if (!node || typeof node !== 'object') return;
      if (typeof node['x-merge'] === 'string') found[path] = node['x-merge'];
      if (node.properties) for (const [k, child] of Object.entries(node.properties)) walk(child, path ? `${path}.${k}` : k);
      if (node.type === 'array' && node.items) walk(node.items, `${path}[]`);
    };
    walk(schema, '');
    expect(found).toEqual(MERGE_SPEC);
  });
});
