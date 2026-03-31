import { describe, it, expect } from 'vitest';
import { validate, compileSchema } from '@/lib/validation/schema-validator';

const testSchema = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    age: { type: 'number', minimum: 0 },
  },
  required: ['name'],
  additionalProperties: false,
};

describe('validate', () => {
  it('returns valid for conforming data', () => {
    const result = validate(testSchema, { name: 'Alice', age: 30 });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns errors for missing required field', () => {
    const result = validate(testSchema, { age: 30 });
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors[0].keyword).toBe('required');
  });

  it('returns errors for wrong type', () => {
    const result = validate(testSchema, { name: 123 });
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.keyword === 'type')).toBe(true);
  });

  it('returns errors for additional properties', () => {
    const result = validate(testSchema, { name: 'Alice', extra: true });
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.keyword === 'additionalProperties')).toBe(true);
  });
});

describe('compileSchema', () => {
  it('returns a reusable validator function', () => {
    const validator = compileSchema(testSchema);
    const good = validator({ name: 'Bob' });
    expect(good.valid).toBe(true);

    const bad = validator({});
    expect(bad.valid).toBe(false);
    expect(bad.errors.length).toBeGreaterThan(0);
  });
});
