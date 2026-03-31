/**
 * YAML Loader — Parse and stringify YAML files.
 *
 * Bridges the YAML-based Core artifacts with the TypeScript runtime.
 * All Core artifacts are stored as YAML; the Studio works with typed objects.
 */

import { parse, stringify } from 'yaml';

/** Parse a YAML string into a typed object. Throws on invalid YAML. */
export function parseYaml<T>(raw: string): T {
  return parse(raw) as T;
}

/** Stringify a typed object into a YAML string. */
export function toYaml<T>(data: T): string {
  return stringify(data, {
    lineWidth: 120,
    defaultKeyType: 'PLAIN',
    defaultStringType: 'PLAIN',
  });
}
