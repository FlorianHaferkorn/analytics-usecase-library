import { describe, it, expect } from 'vitest';
import { parseYaml, toYaml } from '@/lib/core/yaml-loader';

describe('parseYaml', () => {
  it('parses simple YAML into an object', () => {
    const raw = 'name: Test\nversion: 1';
    const result = parseYaml<{ name: string; version: number }>(raw);
    expect(result).toEqual({ name: 'Test', version: 1 });
  });

  it('parses nested YAML', () => {
    const raw = `
parent:
  child: value
  list:
    - one
    - two
`;
    const result = parseYaml<{ parent: { child: string; list: string[] } }>(raw);
    expect(result.parent.child).toBe('value');
    expect(result.parent.list).toEqual(['one', 'two']);
  });

  it('throws on invalid YAML', () => {
    expect(() => parseYaml('{')).toThrow();
  });
});

describe('toYaml', () => {
  it('serializes an object to YAML string', () => {
    const data = { name: 'Test', items: ['a', 'b'] };
    const result = toYaml(data);
    expect(result).toContain('name: Test');
    expect(result).toContain('- a');
    expect(result).toContain('- b');
  });

  it('roundtrips correctly', () => {
    const original = { id: 'UC001', domain: 'Finance', score: 42 };
    const yaml = toYaml(original);
    const parsed = parseYaml<typeof original>(yaml);
    expect(parsed).toEqual(original);
  });
});
