/**
 * Every Studio API error uses { error: { code, message } } (lib/api/response.ts).
 * This scans the route sources for the flat legacy form { error: '<text>' } so it
 * cannot come back unnoticed.
 */

import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const API_ROOT = join(process.cwd(), 'src', 'app', 'api');
const FLAT_ERROR = /\{\s*error:\s*[`'"]/;

function routeFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return routeFiles(path);
    return /\.(ts|tsx)$/.test(entry.name) ? [path] : [];
  });
}

describe('API error shape', () => {
  it('no route answers with a flat { error: string } body', () => {
    const files = routeFiles(API_ROOT);
    expect(files.length, 'scanned no route files').toBeGreaterThan(50);
    const offenders = files.flatMap((file) => readFileSync(file, 'utf-8').split('\n')
      .map((line, index) => (FLAT_ERROR.test(line) ? `${relative(process.cwd(), file)}:${index + 1}` : null))
      .filter((hit): hit is string => hit !== null));
    expect(offenders).toEqual([]);
  });
});
