/**
 * The generated schema types match their JSON Schemas (29.09.2026).
 *
 * Anlass: `scripts/generate-types.mjs` las aus `tooling/ai/schemas/`, das es nicht mehr gibt;
 * `data-contract.ts` war als generiert markiert und kannte weder `quality_rules` noch konforme
 * Referenzen. Der Test erzeugt jedes Modul mit der Funktion des Generators neu und vergleicht es
 * mit der eingecheckten Datei. Liest der Generator aus einem falschen Ordner, schlägt schon der
 * erste Test fehl, nicht erst der Vergleich.
 */
import { describe, it, expect } from 'vitest';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { SCHEMA_DIR, OUTPUT_DIR, generatedModules, renderModule, toModuleName } from '../../scripts/generate-types.mjs';

/**
 * Module, deren eingecheckte Fassung nicht der Neuerzeugung entspricht (gemessen 29.09.2026:
 * volle Neuerzeugung ergibt 15 tsc-Fehler in Verbrauchern; trigger-map* und
 * technical-factsheet tragen Handkorrekturen `Record<string, unknown>` statt `{}`).
 * Exakte Sperrklinke: wer eines neu erzeugt, streicht es hier; ein neu driftendes Modul
 * macht den Test rot.
 */
const KNOWN_DRIFT = new Set([
  'action-code',
  'business-factsheet-v1-2',
  'kpi-definition',
  'layout-330300',
  'technical-factsheet-v1-2',
  'trigger-map',
  'trigger-map-deploy',
  'trigger-map-template',
  'usecase-bracket',
]);

describe('generated schema types', () => {
  it('reads from the schema authority tooling/generator/schemas', () => {
    expect(SCHEMA_DIR.replace(/\\/g, '/')).toMatch(/\/tooling\/generator\/schemas$/);
    expect(existsSync(join(SCHEMA_DIR, 'data_contract.schema.json'))).toBe(true);
  });

  it('every generated module matches its schema, except the known drift', async () => {
    const modules: string[] = await generatedModules();
    expect(modules).toContain('data-contract');
    const drift: string[] = [];
    for (const name of modules) {
      const file = `${name.replace(/-/g, '_')}.schema.json`;
      expect(toModuleName(file)).toBe(name);
      const committed = await readFile(join(OUTPUT_DIR, `${name}.ts`), 'utf-8');
      if ((await renderModule(file)) !== committed) drift.push(name);
    }
    expect(drift.sort()).toEqual([...KNOWN_DRIFT].sort());
  }, 60_000);
});
