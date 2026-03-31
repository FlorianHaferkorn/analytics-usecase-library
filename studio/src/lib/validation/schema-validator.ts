/**
 * Schema Validator — Runtime JSON Schema validation using Ajv.
 *
 * Validates Core artifacts against their canonical JSON Schemas.
 * Used both server-side (API routes) and client-side (Monaco hints).
 */

import Ajv from 'ajv';

const ajv = new Ajv({
  allErrors: true,
  strict: false,
  verbose: true,
});

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  path: string;
  message: string;
  keyword: string;
}

/** Validate data against a JSON Schema object. */
export function validate(
  schema: Record<string, unknown>,
  data: unknown
): ValidationResult {
  const valid = ajv.validate(schema, data) as boolean;

  if (valid) {
    return { valid: true, errors: [] };
  }

  const errors: ValidationError[] = (ajv.errors ?? []).map((err) => ({
    path: err.instancePath || '/',
    message: err.message ?? 'Unknown validation error',
    keyword: err.keyword,
  }));

  return { valid: false, errors };
}

/** Compile a schema for repeated validation (performance optimization). */
export function compileSchema(schema: Record<string, unknown>) {
  const validateFn = ajv.compile(schema);

  return (data: unknown): ValidationResult => {
    const valid = validateFn(data);
    if (valid) {
      return { valid: true, errors: [] };
    }
    const errors: ValidationError[] = (validateFn.errors ?? []).map((err) => ({
      path: err.instancePath || '/',
      message: err.message ?? 'Unknown validation error',
      keyword: err.keyword,
    }));
    return { valid: false, errors };
  };
}
